"""``product.*`` — tools exposed to the product agent.

These DO NOT mutate the shared roadmap. For roadmap writes, product calls
``roadmap.*`` tools defined in :mod:`tools.mock_mcp.tools.roadmap`.

TODO(product-owner): flesh out tool specs. Suggested starter set below.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec

# ---------------------------------------------------------------------------
# Handlers (all mocked). Replace with real logic only if the hackathon demands.
# ---------------------------------------------------------------------------


async def _list_ux_signals(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(product): return structured user-pain signals. Mock ok."""
    return {"signals": [], "note": "mock: wire to a fake research dataset"}


async def _draft_spec(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(product): given a roadmap item id, return a stub spec doc."""
    return {"item_id": args.get("item_id"), "spec_md": "# TODO draft\n"}


# ---------------------------------------------------------------------------
# Specs — the product agent sees these. Add more as needed.
# ---------------------------------------------------------------------------

TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="product.list_ux_signals",
        description="List open UX signals and user-pain observations worth turning into roadmap items.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_list_ux_signals,
        allowed_callers=("product",),
    ),
    ToolSpec(
        name="product.draft_spec",
        description="Draft a short spec doc for a given roadmap item id.",
        input_schema={
            "type": "object",
            "properties": {"item_id": {"type": "string"}},
            "required": ["item_id"],
            "additionalProperties": False,
        },
        handler=_draft_spec,
        allowed_callers=("product",),
    ),
]
