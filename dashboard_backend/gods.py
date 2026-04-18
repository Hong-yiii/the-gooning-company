"""Read per-agent ``memory/god.md`` files for the dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

AGENTS = ("router", "product", "marketing", "finance")


@dataclass
class GodFile:
    agent: str
    content: str
    updated_at: str  # ISO 8601 UTC

    def as_dict(self) -> dict[str, str]:
        return {
            "agent": self.agent,
            "content": self.content,
            "updatedAt": self.updated_at,
        }


def god_path(workspaces_dir: Path, agent: str) -> Path:
    return workspaces_dir / agent / "memory" / "god.md"


def read_god_file(workspaces_dir: Path, agent: str) -> GodFile:
    path = god_path(workspaces_dir, agent)
    if not path.is_file():
        return GodFile(agent=agent, content="", updated_at=_now())
    stat = path.stat()
    return GodFile(
        agent=agent,
        content=path.read_text(encoding="utf-8"),
        updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(
            timespec="seconds"
        ),
    )


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
