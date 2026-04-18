"""Resolve the in-repo workspace layout into typed configs for launch.

This module is intentionally import-light: no OpenHarness, no networking. It
only reads files so the team can iterate on the structure and write tests
before the harness is wired.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACES = REPO_ROOT / "workspaces"
SHARED = WORKSPACES / "_shared"
STATE = REPO_ROOT / "state"


@dataclass
class AgentConfig:
    """Everything the launcher needs to start one agent."""

    name: str
    workspace: Path
    settings: dict[str, Any]
    gateway: dict[str, Any]
    is_router: bool = False

    @property
    def teammate_id(self) -> str:
        """Swarm teammate id — matches the workspace directory name."""
        return self.workspace.name


@dataclass
class OrchestratorConfig:
    """Aggregate config: shared bits + one :class:`AgentConfig` per agent."""

    repo_root: Path
    shared_prompt_path: Path
    shared_skills_dir: Path
    shared_mcp: dict[str, Any]
    state_dir: Path
    roadmap_path: Path
    agents: list[AgentConfig] = field(default_factory=list)

    def router(self) -> AgentConfig:
        return next(a for a in self.agents if a.is_router)

    def teammates(self) -> list[AgentConfig]:
        return [a for a in self.agents if not a.is_router]


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_agent(workspace: Path, *, is_router: bool) -> AgentConfig:
    if not workspace.is_dir():
        raise FileNotFoundError(f"workspace missing: {workspace}")
    return AgentConfig(
        name=workspace.name,
        workspace=workspace,
        settings=_read_json(workspace / "settings.json"),
        gateway=_read_json(workspace / "gateway.json"),
        is_router=is_router,
    )


def load_config() -> OrchestratorConfig:
    """Scan ``workspaces/`` and build the :class:`OrchestratorConfig`."""

    shared_prompt = SHARED / "base-system.md"
    shared_skills = SHARED / "skills"
    shared_mcp = _read_json(SHARED / "mcp.json")

    # Router is the single folder named "router" (= the-gooning-company workspace).
    # Everything else under workspaces/ that isn't _shared or router is a teammate.
    agents: list[AgentConfig] = [_load_agent(WORKSPACES / "router", is_router=True)]
    for path in sorted(WORKSPACES.iterdir()):
        if not path.is_dir() or path.name.startswith("_") or path.name == "router":
            continue
        agents.append(_load_agent(path, is_router=False))

    return OrchestratorConfig(
        repo_root=REPO_ROOT,
        shared_prompt_path=shared_prompt,
        shared_skills_dir=shared_skills,
        shared_mcp=shared_mcp,
        state_dir=STATE,
        roadmap_path=STATE / "roadmap.md",
        agents=agents,
    )


def merge_mcp_into_settings(
    per_agent_settings: dict[str, Any], shared_mcp: dict[str, Any]
) -> dict[str, Any]:
    """Merge the shared ``mcp.json`` fragment into a workspace's settings.

    Keeps the agent's own keys and adds ``mcp_servers`` from the shared file.
    Shared entries do not overwrite an agent's already-defined server of the
    same id, on the assumption that an agent overriding locally meant it.

    TODO(glue): confirm the final key name once the harness version is pinned
    (``mcp_servers`` vs ``mcp`` — check upstream ``src/openharness/mcp/config.py``).
    """

    merged = dict(per_agent_settings)
    shared_servers = dict(shared_mcp.get("mcp_servers", {}))
    existing_servers = dict(merged.get("mcp_servers", {}))
    for sid, spec in shared_servers.items():
        existing_servers.setdefault(sid, spec)
    merged["mcp_servers"] = existing_servers
    return merged
