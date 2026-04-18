"""``finance.*`` — tools exposed to the finance agent.

TODO(finance-owner): flesh out specs and mocked payloads.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec


async def _get_projection(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(finance): return the current projection snapshot. Mock ok."""
    return {"horizon_months": 18, "runway_months": 0, "burn_monthly": 0, "assumptions": ["TODO"]}


async def _simulate_roadmap_delta(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(finance): given a roadmap delta, return the projection change."""
    return {"delta": args.get("delta"), "impact": {}, "assumptions": ["TODO"]}


async def _cost_campaign(args: Mapping[str, Any]) -> dict[str, Any]:
    """TODO(finance): cost a marketing campaign outline; return cash-timing impact."""
    return {"campaign_id": args.get("campaign_id"), "cost_usd": 0, "timing": "TODO"}


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="finance.get_projection",
        description="Return the current projection snapshot (runway, burn, assumptions).",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_get_projection,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.simulate_roadmap_delta",
        description="Given a roadmap delta envelope, return the projection impact.",
        input_schema={
            "type": "object",
            "properties": {"delta": {"type": "object"}},
            "required": ["delta"],
            "additionalProperties": False,
        },
        handler=_simulate_roadmap_delta,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.cost_campaign",
        description="Cost a marketing campaign outline and report cash-timing impact.",
        input_schema={
            "type": "object",
            "properties": {"campaign_id": {"type": "string"}},
            "required": ["campaign_id"],
            "additionalProperties": False,
        },
        handler=_cost_campaign,
        allowed_callers=("finance",),
    ),
]
