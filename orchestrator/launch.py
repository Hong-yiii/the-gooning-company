"""Launch the router + expose teammates as AgentDefinitions.

Reality-checked against installed OpenHarness v0.1.6 + ohmo 0.1.6:

* ``load_settings()`` only reads ``$OPENHARNESS_CONFIG_DIR/settings.json``
  (defaults to ``~/.openharness/``). It does **not** merge per-workspace
  ``settings.json`` files. We therefore materialise one settings.json
  under ``state/.openharness/`` and point ``$OPENHARNESS_CONFIG_DIR``
  there.
* Teammates are not spawned at boot. They're spawned **fresh** each time
  the router calls the ``agent`` tool (see upstream
  ``openharness/tools/agent_tool.py`` → ``SubprocessBackend.spawn`` →
  ``BackgroundTaskManager.create_agent_task``). We ship AgentDefinition
  files so the router can delegate by name.
* The router is launched as an interactive ``ohmo`` subprocess against
  ``workspaces/router``. OpenHarness picks up the composed settings +
  agent defs from ``$OPENHARNESS_CONFIG_DIR`` automatically.

Flow:

  1. Load ``.env`` + build :class:`OrchestratorConfig`.
  2. :func:`orchestrator.bootstrap.run_bootstrap` writes
     ``state/.openharness/{settings.json,agents/*.md}`` and sets
     ``OPENHARNESS_CONFIG_DIR`` in the current process' env.
  3. Preflight check all workspace files exist.
  4. Start the mock MCP server as a child process on
     ``$GOONING_MCP_HOST:$GOONING_MCP_PORT``.
  5. Exec ``ohmo --workspace workspaces/router`` inheriting the prepared
     env. On ^C, tear down the MCP child.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .bootstrap import CONFIG_DIR_ENV, Bootstrap, run_bootstrap
from .config import AgentConfig, OrchestratorConfig, load_config, merge_mcp_into_settings

MCP_MODULE = "tools.mock_mcp.server"


# ---------------------------------------------------------------------------
# Preflight (unchanged semantics — fail loud on missing scaffold).
# ---------------------------------------------------------------------------


def _preflight(cfg: OrchestratorConfig) -> None:
    missing: list[Path] = []
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
    return merge_mcp_into_settings(agent.settings, cfg.shared_mcp)


def _describe(cfg: OrchestratorConfig) -> str:
    lines = [
        f"repo_root:        {cfg.repo_root}",
        f"shared_prompt:    {cfg.shared_prompt_path}",
        f"shared_skills:    {cfg.shared_skills_dir}",
        f"state_dir:        {cfg.state_dir}",
        f"roadmap:          {cfg.roadmap_path}",
        "agents:",
    ]
    for a in cfg.agents:
        tag = "router" if a.is_router else "teammate"
        lines.append(f"  - {a.name:16s} ({tag})  {a.workspace}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mock MCP lifecycle
# ---------------------------------------------------------------------------


def _start_mock_mcp(cfg: OrchestratorConfig) -> subprocess.Popen[bytes]:
    py = sys.executable
    host = os.environ.get("GOONING_MCP_HOST", "127.0.0.1")
    port = os.environ.get("GOONING_MCP_PORT", "8765")
    cmd = [py, "-m", MCP_MODULE, "--host", host, "--port", port]
    print(f"[orchestrator] starting mock MCP: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=cfg.repo_root)

    # Tiny ready probe — give the HTTP server a moment to bind. Not a
    # liveness check; just enough that the router's first tool call doesn't
    # race the bind. The MCP client also retries on disconnect.
    time.sleep(0.8)
    if proc.poll() is not None:
        raise SystemExit(
            f"mock MCP exited immediately with code {proc.returncode}. "
            "Check that the port isn't already in use."
        )
    return proc


def _stop_mock_mcp(proc: subprocess.Popen[bytes] | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()


# ---------------------------------------------------------------------------
# Router launch — interactive ohmo subprocess.
# ---------------------------------------------------------------------------


def _run_router(cfg: OrchestratorConfig, bootstrap: Bootstrap, *, extra_args: list[str]) -> int:
    """Exec ``ohmo --workspace <router>`` inheriting the prepared environment.

    We intentionally do **not** call ``ohmo.runtime.run_ohmo_backend`` in
    process:
      1. ``run_ohmo_backend`` has no ``extra_prompt`` / ``extra_skill_dirs``
         kwargs; using it would silently drop the shared preamble.
      2. The interactive TUI that founders want is what ``ohmo`` gives by
         default. Re-implementing that shell in-process is out of scope.

    Instead we hand off to the installed ``ohmo`` entrypoint with
    ``$OPENHARNESS_CONFIG_DIR`` already pointing at our generated config
    dir, which gives ohmo:
      * our OpenAI provider profile + ``OPENAI_API_KEY`` env,
      * our ``gooning-mock`` MCP server URL + headers,
      * the three ``agents/<teammate>.md`` files so the ``agent`` tool
        can delegate by name.
    """
    # Prefer the binary that installed alongside openharness-ai in our venv
    # (so we don't accidentally pick up a system-wide ohmo of a different
    # version). `sys.executable` is the active Python; its bin/ohmo is
    # what was installed with it.
    venv_bin = Path(sys.executable).parent
    ohmo_bin = venv_bin / "ohmo"
    if not ohmo_bin.is_file():
        # Fall back to PATH-resolved ohmo.
        ohmo_bin = Path("ohmo")

    router = cfg.router()
    cmd: list[str] = [
        str(ohmo_bin),
        "--workspace",
        str(router.workspace),
        "--profile",
        "gooning-openai",
        "--model",
        bootstrap.model,
        *extra_args,
    ]
    print(f"[orchestrator] launching router: {' '.join(cmd)}")
    # Inherit stdio so the TUI is usable. Propagate env (incl. our
    # OPENHARNESS_CONFIG_DIR + OPENAI_API_KEY from .env).
    try:
        return subprocess.call(cmd, cwd=cfg.repo_root, env=os.environ.copy())
    except FileNotFoundError:
        raise SystemExit(
            f"could not execute {ohmo_bin}. Activate the venv with "
            "`source .venv/bin/activate` or reinstall with `uv pip install -e .[dev]`."
        )


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
        help="Print the effective per-agent settings (shared MCP merged in) and exit.",
    )
    parser.add_argument(
        "--dump-composed",
        action="store_true",
        help="Write state/.openharness/ (settings.json + agents/) and print the resolved paths, then exit. No MCP boot, no router.",
    )
    parser.add_argument(
        "--no-mcp", action="store_true", help="Skip starting the mock MCP subprocess."
    )
    parser.add_argument(
        "--no-router",
        action="store_true",
        help="Start the mock MCP and bootstrap config, but do not launch the router.",
    )
    parser.add_argument(
        "--print",
        dest="print_prompt",
        metavar="PROMPT",
        help="Non-interactive: pass this prompt to the router with `ohmo --print`.",
    )
    args, extra = parser.parse_known_args(argv)

    cfg = load_config()
    _preflight(cfg)

    if args.describe:
        print(_describe(cfg))
        return 0

    if args.dump_settings:
        _dump_effective_settings(cfg)
        return 0

    bootstrap = run_bootstrap(cfg, verbose=True)

    if args.dump_composed:
        print(f"[orchestrator] {CONFIG_DIR_ENV}={os.environ[CONFIG_DIR_ENV]}")
        print(f"[orchestrator] settings={bootstrap.settings_path}")
        print(f"[orchestrator] agents_dir={bootstrap.agents_dir}")
        for p in sorted(bootstrap.agents_dir.glob("*.md")):
            print(f"  - {p.name}")
        return 0

    mcp_proc: subprocess.Popen[bytes] | None = None
    try:
        if not args.no_mcp:
            mcp_proc = _start_mock_mcp(cfg)

        if args.no_router:
            print("[orchestrator] --no-router: skipping router launch. ^C to stop MCP.")
            if mcp_proc is not None:
                mcp_proc.wait()
            return 0

        router_extra: list[str] = list(extra)
        if args.print_prompt is not None:
            router_extra.extend(["--print", args.print_prompt])

        return _run_router(cfg, bootstrap, extra_args=router_extra)
    finally:
        _stop_mock_mcp(mcp_proc)


if __name__ == "__main__":
    raise SystemExit(main())
