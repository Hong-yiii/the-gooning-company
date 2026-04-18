"""``marketing.*`` — tools exposed to the marketing agent.

TODO(marketing-owner): flesh out specs and mocked payloads.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec


async def _list_campaigns(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(marketing): return campaigns in flight. Mock ok."""
    return {"campaigns": []}


async def _draft_campaign(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(marketing): given an objective + audience, return a campaign outline."""
    return {
        "objective": args.get("objective"),
        "audience": args.get("audience"),
        "outline_md": "# TODO campaign outline\n",
    }


async def _estimate_reach(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(marketing): mock reach/engagement estimates for a draft."""
    return {"reach_low": 0, "reach_high": 0, "assumptions": ["TODO"]}


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="marketing.list_campaigns",
        description="List campaigns currently in flight or scheduled.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_list_campaigns,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.draft_campaign",
        description="Draft a campaign outline for a given objective and audience.",
        input_schema={
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "audience": {"type": "string"},
            },
            "required": ["objective", "audience"],
            "additionalProperties": False,
        },
        handler=_draft_campaign,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.estimate_reach",
        description="Mocked reach / engagement estimate for a campaign draft.",
        input_schema={
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "required": ["draft_id"],
            "additionalProperties": False,
        },
        handler=_estimate_reach,
        allowed_callers=("marketing",),
    ),
]
