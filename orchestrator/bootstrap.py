"""Materialise a per-repo OpenHarness config + agent registry from the workspaces tree.

OpenHarness reads a single ``$OPENHARNESS_CONFIG_DIR/settings.json`` (defaults
to ``~/.openharness/settings.json``) and discovers user agents from
``$OPENHARNESS_CONFIG_DIR/agents/*.md``. To keep the hackathon repo isolated
from a user's global config, we point ``OPENHARNESS_CONFIG_DIR`` at
``state/.openharness/`` and regenerate its contents every launch.

This module:

1. Loads ``.env`` so ``OPENAI_API_KEY``/``GOONING_MODEL`` are available.
2. Builds a :class:`Bootstrap` that knows where things go.
3. Writes ``state/.openharness/settings.json`` with a single OpenAI-compatible
   provider profile + the shared MCP server entry pulled from
   ``workspaces/_shared/mcp.json`` + a permissive ``path_rules`` set.
4. Writes one ``state/.openharness/agents/<teammate>.md`` per domain workspace,
   with frontmatter and a composed system-prompt body of
   ``_shared/base-system.md`` + ``<role>/soul.md`` + ``<role>/identity.md``
   + ``<role>/memory/god.md``. This is what lets the router's ``agent`` tool
   delegate to ``product`` / ``marketing`` / ``finance`` by name — each call
   spawns a fresh subprocess teammate whose prompt re-reads all three files.

The design choices here are grounded in installed upstream behaviour, not
guesses. See comments referencing specific upstream files where relevant.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from .config import OrchestratorConfig


CONFIG_DIR_ENV = "OPENHARNESS_CONFIG_DIR"
CONFIG_FILENAME = "settings.json"
AGENTS_SUBDIR = "agents"
PROVIDER_PROFILE = "gooning-openai"
DEFAULT_MODEL_FALLBACK = "gpt-5.4"


@dataclass
class Bootstrap:
    """Everything the launcher needs in hand after bootstrap."""

    config_dir: Path  # state/.openharness
    settings_path: Path  # state/.openharness/settings.json
    agents_dir: Path  # state/.openharness/agents
    model: str
    mcp_url: str


# ---------------------------------------------------------------------------
# Settings.json composition
# ---------------------------------------------------------------------------


def _normalise_mcp_server(raw: dict[str, Any], *, url: str) -> dict[str, Any]:
    """Shape the shared ``mcp.json`` entry into OpenHarness' McpHttpServerConfig.

    Upstream ``McpHttpServerConfig`` requires ``type: "http"`` and ``url``
    (see openharness/mcp/types.py). We drop ``transport`` and ``enabled``
    which only existed in our shared fragment, and attach a default
    ``x-agent`` header for observability. Enforcement is soft unless
    ``GOONING_STRICT_CALLERS=1`` is set server-side.
    """
    headers = dict(raw.get("headers") or {})
    headers.setdefault("x-agent", "the-gooning-company")
    return {"type": "http", "url": url, "headers": headers}


def _compose_path_rules(cfg: OrchestratorConfig) -> list[dict[str, Any]]:
    """Union of every workspace's ``permissions.path_rules``.

    Ideally each agent would get its own rules, but OpenHarness' permission
    checker is built once from one :class:`Settings` instance (``build_runtime``
    → ``load_settings()`` → ``PermissionChecker(settings.permission)``). Per-
    process config-dir isolation is on the roadmap; for now we union the
    workspace rules and rely on ``AgentDefinition.tools`` for tighter per-
    agent tool gating.
    """
    rules: list[dict[str, Any]] = []
    seen: set[tuple[str, bool]] = set()
    for agent in cfg.agents:
        perm = agent.settings.get("permissions") or {}
        for rule in perm.get("path_rules") or []:
            pattern = str(rule.get("pattern", ""))
            if not pattern:
                continue
            # Our repo encodes {"mode": "read"|"write"|"append"} which isn't
            # upstream's shape. PathRuleConfig accepts {"pattern", "allow"}.
            # Translate: any mode we grant = allow; anything missing = allow.
            allow = True
            key = (pattern, allow)
            if key in seen:
                continue
            seen.add(key)
            rules.append({"pattern": pattern, "allow": allow})
    return rules


def _build_settings(
    cfg: OrchestratorConfig,
    *,
    model: str,
    base_url: str,
    mcp_url: str,
) -> dict[str, Any]:
    mcp_servers_raw = (cfg.shared_mcp.get("mcp_servers") or {}).get("gooning-mock") or {}
    mcp_entry = _normalise_mcp_server(mcp_servers_raw, url=mcp_url)

    return {
        "active_profile": PROVIDER_PROFILE,
        "profiles": {
            PROVIDER_PROFILE: {
                "label": "OpenAI API (the-gooning-company)",
                "provider": "openai",
                "api_format": "openai",
                "auth_source": "openai_api_key",
                "default_model": model,
                "base_url": base_url,
            }
        },
        "model": model,
        "mcp_servers": {"gooning-mock": mcp_entry},
        "permission": {
            "mode": "default",
            "path_rules": _compose_path_rules(cfg),
        },
    }


# ---------------------------------------------------------------------------
# AgentDefinition .md composition
# ---------------------------------------------------------------------------


_TEAMMATE_DESCRIPTIONS = {
    "product": (
        "Product / UX lead. Sole owner of the shared roadmap at state/roadmap.md. "
        "Use when the founder's ask affects scope, sequencing, or user experience, "
        "or when a marketing/finance signal should become a roadmap item."
    ),
    "marketing": (
        "Marketing lead. Owns campaigns, positioning, and launch timing. "
        "Use when the founder asks about launches, campaigns, or positioning — "
        "or when a roadmap change needs downstream campaign implications."
    ),
    "finance": (
        "Finance lead. Owns projections, burn, and cost implications. "
        "Use when the founder asks about runway, unit economics, or when a "
        "roadmap/marketing change needs financial implications evaluated."
    ),
}


def _read_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip() if path.is_file() else ""


def _compose_system_prompt(cfg: OrchestratorConfig, workspace: Path) -> str:
    """Compose the body of a teammate's AgentDefinition.

    Each teammate is spawned fresh per ``agent`` tool call (upstream
    ``AgentTool.execute`` calls ``SubprocessBackend.spawn`` which invokes
    ``create_agent_task`` on every delegation — there is no long-lived
    in-process teammate). That means any state we want the teammate to see
    must live on disk and be composed into the system prompt. We build it
    as: shared base-system + role soul + role identity + role god.md.
    """
    shared = _read_or_empty(cfg.shared_prompt_path)
    soul = _read_or_empty(workspace / "soul.md")
    identity = _read_or_empty(workspace / "identity.md")
    god = _read_or_empty(workspace / "memory" / "god.md")

    sections: list[str] = []
    if shared:
        sections.append("# Company base system\n\n" + shared)
    if identity:
        sections.append("# Your identity\n\n" + identity)
    if soul:
        sections.append("# Your role\n\n" + soul)
    if god:
        sections.append(
            "# Your living doc (god.md)\n\n"
            "This is your private running notes from prior turns. Treat it as "
            "state you wrote to yourself. Update it via the Write tool on the "
            f"path `{workspace / 'memory' / 'god.md'}` when your worldview "
            "materially changes.\n\n"
            + god
        )
    return "\n\n".join(sections).strip() + "\n"


def _compose_agent_md(cfg: OrchestratorConfig, workspace: Path) -> str:
    name = workspace.name
    description = _TEAMMATE_DESCRIPTIONS.get(name, f"Domain agent: {name}")
    body = _compose_system_prompt(cfg, workspace)
    frontmatter = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "model: inherit",
        "color: cyan" if name == "product" else ("color: magenta" if name == "marketing" else "color: yellow"),
        "---",
        "",
    ]
    return "\n".join(frontmatter) + body


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(
            f"missing required environment variable: {name}\n"
            "Copy .env.example to .env and fill it in, or export the variable "
            "in your shell before running `python -m orchestrator.launch`."
        )
    return value


def run_bootstrap(cfg: OrchestratorConfig, *, verbose: bool = False) -> Bootstrap:
    """Materialise ``state/.openharness/`` and set ``$OPENHARNESS_CONFIG_DIR``.

    Must run before importing any OpenHarness code that triggers
    ``load_settings()`` / ``get_config_dir()``. Setting the env var here is
    enough — ``openharness/config/paths.py`` reads it lazily per-call.
    """
    env_path = cfg.repo_root / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)

    config_dir = cfg.state_dir / ".openharness"
    agents_dir = config_dir / AGENTS_SUBDIR
    settings_path = config_dir / CONFIG_FILENAME

    config_dir.mkdir(parents=True, exist_ok=True)
    agents_dir.mkdir(parents=True, exist_ok=True)

    model = os.environ.get("GOONING_MODEL", "").strip() or DEFAULT_MODEL_FALLBACK
    base_url = os.environ.get("OPENAI_BASE_URL", "").strip() or "https://api.openai.com/v1"
    mcp_host = os.environ.get("GOONING_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    mcp_port = os.environ.get("GOONING_MCP_PORT", "8765").strip() or "8765"
    mcp_url = f"http://{mcp_host}:{mcp_port}/mcp"

    _require_env("OPENAI_API_KEY")

    settings = _build_settings(cfg, model=model, base_url=base_url, mcp_url=mcp_url)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    for agent in cfg.teammates():
        agent_md = _compose_agent_md(cfg, agent.workspace)
        (agents_dir / f"{agent.name}.md").write_text(agent_md, encoding="utf-8")

    os.environ[CONFIG_DIR_ENV] = str(config_dir)

    if verbose:
        print(f"[bootstrap] OPENHARNESS_CONFIG_DIR={config_dir}")
        print(f"[bootstrap] wrote {settings_path.relative_to(cfg.repo_root)}")
        for agent in cfg.teammates():
            print(
                f"[bootstrap] wrote {(agents_dir / (agent.name + '.md')).relative_to(cfg.repo_root)}"
            )

    return Bootstrap(
        config_dir=config_dir,
        settings_path=settings_path,
        agents_dir=agents_dir,
        model=model,
        mcp_url=mcp_url,
    )
