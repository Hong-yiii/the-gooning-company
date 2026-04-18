"""Launch the router + three domain teammates.

Flow:

  1. Build the :class:`OrchestratorConfig` from the in-repo workspace tree.
  2. Compute the ``extra_prompt`` (the shared ``base-system.md``).
  3. Compute ``extra_skill_dirs`` (the shared ``skills/`` directory).
  4. Merge the shared MCP fragment into every agent's settings.
  5. Start the mock MCP server (subprocess).
  6. Spawn the three teammates under the router via OpenHarness swarm
     ``SubprocessBackend``. TODO(glue) — actual spawn wiring.
  7. Start the router as the founder-facing session.

Every step that depends on an OpenHarness API we have not pinned yet is marked
``TODO(glue)``. The rest is regular Python we can unit-test today.
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
from typing import Any

from .config import AgentConfig, OrchestratorConfig, load_config, merge_mcp_into_settings

MCP_MODULE = "tools.mock_mcp.server"


# ---------------------------------------------------------------------------
# Prep: compute per-agent effective settings (shared prompt path, shared skills,
# merged MCP) without touching the workspaces on disk.
# ---------------------------------------------------------------------------


def _preflight(cfg: OrchestratorConfig) -> None:
    """Cheap sanity checks. Fail loud, fail early."""
    missing = []
    if not cfg.shared_prompt_path.is_file():
        missing.append(cfg.shared_prompt_path)
    if not cfg.shared_skills_dir.is_dir():
        missing.append(cfg.shared_skills_dir)
    if not cfg.roadmap_path.is_file():
        missing.append(cfg.roadmap_path)
    for a in cfg.agents:
        for required in ("identity.md", "soul.md", "BOOTSTRAP.md"):
            if not (a.workspace / required).is_file():
                missing.append(a.workspace / required)
    if missing:
        raise SystemExit(
            "preflight failed; missing:\n  - " + "\n  - ".join(str(p) for p in missing)
        )


def _effective_settings(cfg: OrchestratorConfig, agent: AgentConfig) -> dict[str, Any]:
    """Per-agent settings merged with the shared MCP fragment (no write)."""
    return merge_mcp_into_settings(agent.settings, cfg.shared_mcp)


def _describe(cfg: OrchestratorConfig) -> str:
    lines: list[str] = []
    lines.append(f"repo_root:        {cfg.repo_root}")
    lines.append(f"shared_prompt:    {cfg.shared_prompt_path}")
    lines.append(f"shared_skills:    {cfg.shared_skills_dir}")
    lines.append(f"state_dir:        {cfg.state_dir}")
    lines.append(f"roadmap:          {cfg.roadmap_path}")
    lines.append("agents:")
    for a in cfg.agents:
        tag = "router" if a.is_router else "teammate"
        lines.append(f"  - {a.name:16s} ({tag})  {a.workspace}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mock MCP lifecycle (subprocess — deliberately dumb for now).
# ---------------------------------------------------------------------------


def _start_mock_mcp(cfg: OrchestratorConfig) -> subprocess.Popen[bytes] | None:
    """Start the mock MCP server as a child process. Returns None if deferred."""
    py = sys.executable
    # TODO(glue): once server.py has a real transport, drop --smoke.
    cmd = [py, "-m", MCP_MODULE, "--smoke"]
    print(f"[orchestrator] starting mock MCP: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cfg.repo_root)


# ---------------------------------------------------------------------------
# Agent lifecycle (OpenHarness — actual wiring TODO).
# ---------------------------------------------------------------------------


def _spawn_teammates(cfg: OrchestratorConfig) -> None:
    """Spawn product / marketing / finance under the router via swarm.

    TODO(glue): implement with:
        from openharness.swarm import SubprocessBackend, TeammateSpawnConfig, TeammateIdentity

        backend = SubprocessBackend(...)
        for a in cfg.teammates():
            backend.spawn(
                TeammateSpawnConfig(
                    identity=TeammateIdentity(id=a.teammate_id, display_name=a.name),
                    workspace=a.workspace,
                    extra_prompt=cfg.shared_prompt_path.read_text(),
                    extra_skill_dirs=[cfg.shared_skills_dir],
                    settings_override=_effective_settings(cfg, a),
                )
            )

    Keep this function the single place that knows the OpenHarness swarm API
    so a version bump only touches one file.
    """
    print("[orchestrator] TODO(glue): spawn teammates via openharness.swarm.SubprocessBackend")
    for a in cfg.teammates():
        print(f"  would spawn: {a.teammate_id:10s} workspace={a.workspace}")


def _run_router(cfg: OrchestratorConfig) -> int:
    """Start the router session (the founder's entrypoint).

    TODO(glue): implement with:
        from ohmo.runtime import run_ohmo_backend
        run_ohmo_backend(
            workspace=cfg.router().workspace,
            extra_prompt=cfg.shared_prompt_path.read_text(),
            extra_skill_dirs=[cfg.shared_skills_dir],
            settings_override=_effective_settings(cfg, cfg.router()),
        )
    """
    router = cfg.router()
    print(f"[orchestrator] TODO(glue): run_ohmo_backend for router at {router.workspace}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _dump_effective_settings(cfg: OrchestratorConfig) -> None:
    for a in cfg.agents:
        print(f"# ----- {a.name} -----")
        print(json.dumps(_effective_settings(cfg, a), indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the-gooning-company")
    parser.add_argument("--describe", action="store_true", help="Print resolved config and exit.")
    parser.add_argument(
        "--dump-settings",
        action="store_true",
        help="Print the effective per-agent settings (shared MCP merged in).",
    )
    parser.add_argument(
        "--no-mcp", action="store_true", help="Skip starting the mock MCP subprocess."
    )
    args = parser.parse_args(argv)

    cfg = load_config()
    _preflight(cfg)

    if args.describe:
        print(_describe(cfg))
        return 0

    if args.dump_settings:
        _dump_effective_settings(cfg)
        return 0

    mcp_proc: subprocess.Popen[bytes] | None = None
    try:
        if not args.no_mcp:
            mcp_proc = _start_mock_mcp(cfg)

        _spawn_teammates(cfg)
        return _run_router(cfg)
    finally:
        if mcp_proc and mcp_proc.poll() is None:
            mcp_proc.send_signal(signal.SIGINT)
            try:
                mcp_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                mcp_proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
