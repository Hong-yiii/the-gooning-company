"""``roadmap.*`` — the shared roadmap. Read by everyone; mutated only by product.

Mutations land in ``state/roadmap.md`` (v0 format). Parsing/serializing the
markdown tables is the job of helpers in this module, not of the agents.

TODO(product-owner): decide whether v1 persists as JSON alongside the .md or
keeps markdown as canonical and derives JSON on read. Keep this file the only
place that owns that detail.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..spec import ToolSpec

# Resolve from this file: repo_root = tools/mock_mcp/tools -> ../../../
ROADMAP_PATH = Path(__file__).resolve().parents[3] / "state" / "roadmap.md"


# ---------------------------------------------------------------------------
# Handlers — mocked for now. Replace with real parse/write helpers when ready.
# ---------------------------------------------------------------------------


async def _read_all(args: Mapping[str, Any]) -> dict[str, Any]:
    """Return the full roadmap. For v0, just return the raw markdown."""
    if not ROADMAP_PATH.exists():
        return {"markdown": "", "note": "roadmap not initialised"}
    return {"markdown": ROADMAP_PATH.read_text(encoding="utf-8")}


async def _read_item(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(glue): parse out a single row by id once we have a parser."""
    return {"id": args.get("id"), "item": None, "note": "mock: parser not wired"}


async def _add_item(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(product-owner): append a row to the Backlog table. Product-only."""
    return {"ok": False, "note": "mock: writer not wired"}


async def _move_item(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(product-owner): move a row between status tables. Product-only."""
    return {"ok": False, "note": "mock: writer not wired"}


async def _drop_item(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(product-owner): move a row to Done/Dropped. Product-only."""
    return {"ok": False, "note": "mock: writer not wired"}


# ---------------------------------------------------------------------------
# Specs
# ---------------------------------------------------------------------------

_READ_CALLERS = ("product", "marketing", "finance", "the-gooning-company")
_WRITE_CALLERS = ("product",)


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="roadmap.read_all",
        description="Return the full roadmap as markdown.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_read_all,
        allowed_callers=_READ_CALLERS,
    ),
    ToolSpec(
        name="roadmap.read_item",
        description="Return a single roadmap item by id.",
        input_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
            "additionalProperties": False,
        },
        handler=_read_item,
        allowed_callers=_READ_CALLERS,
    ),
    ToolSpec(
        name="roadmap.add_item",
        description="Add a new roadmap item to the backlog. Product only.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "domain": {"type": "string", "enum": ["product", "marketing", "finance"]},
                "owner": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["title", "domain", "owner"],
            "additionalProperties": False,
        },
        handler=_add_item,
        allowed_callers=_WRITE_CALLERS,
    ),
    ToolSpec(
        name="roadmap.move_item",
        description="Move an item between status columns. Product only.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["backlog", "next", "in-progress", "blocked", "done", "dropped"],
                },
                "reason": {"type": "string"},
            },
            "required": ["id", "status"],
            "additionalProperties": False,
        },
        handler=_move_item,
        allowed_callers=_WRITE_CALLERS,
    ),
    ToolSpec(
        name="roadmap.drop_item",
        description="Drop an item (move to dropped). Product only.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["id", "reason"],
            "additionalProperties": False,
        },
        handler=_drop_item,
        allowed_callers=_WRITE_CALLERS,
    ),
]
