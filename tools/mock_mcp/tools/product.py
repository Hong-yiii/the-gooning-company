"""``product.*`` — tools exposed to the product agent (Crumb demo fixtures).

Roadmap writes remain in :mod:`tools.mock_mcp.tools.roadmap`.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec

_NEIGHBORHOODS: list[dict[str, Any]] = [
    {
        "neighborhood": "east_brooklyn",
        "active_buyers": 180,
        "active_bakers": 42,
        "supply_demand_ratio": 0.42,
        "listings_per_baker": 2.1,
        "listing_to_order_rate": 0.68,
        "repeat_buyer_rate_30d": 0.29,
        "fulfillment_on_time_pct": 0.88,
    },
    {
        "neighborhood": "williamsburg",
        "active_buyers": 310,
        "active_bakers": 58,
        "supply_demand_ratio": 1.02,
        "listings_per_baker": 3.6,
        "listing_to_order_rate": 0.41,
        "repeat_buyer_rate_30d": 0.38,
        "fulfillment_on_time_pct": 0.93,
    },
    {
        "neighborhood": "park_slope",
        "active_buyers": 240,
        "active_bakers": 38,
        "supply_demand_ratio": 0.81,
        "listings_per_baker": 3.1,
        "listing_to_order_rate": 0.52,
        "repeat_buyer_rate_30d": 0.35,
        "fulfillment_on_time_pct": 0.91,
    },
    {
        "neighborhood": "astoria",
        "active_buyers": 150,
        "active_bakers": 22,
        "supply_demand_ratio": 0.73,
        "listings_per_baker": 2.4,
        "listing_to_order_rate": 0.58,
        "repeat_buyer_rate_30d": 0.32,
        "fulfillment_on_time_pct": 0.86,
    },
    {
        "neighborhood": "lic",
        "active_buyers": 95,
        "active_bakers": 14,
        "supply_demand_ratio": 0.64,
        "listings_per_baker": 2.0,
        "listing_to_order_rate": 0.61,
        "repeat_buyer_rate_30d": 0.27,
        "fulfillment_on_time_pct": 0.84,
    },
    {
        "neighborhood": "bed_stuy",
        "active_buyers": 220,
        "active_bakers": 46,
        "supply_demand_ratio": 0.96,
        "listings_per_baker": 3.2,
        "listing_to_order_rate": 0.49,
        "repeat_buyer_rate_30d": 0.36,
        "fulfillment_on_time_pct": 0.92,
    },
]

_SPECS: dict[str, str] = {
    "P-001": (
        "## Problem\nEast Brooklyn has demand but thin baker supply; orders time out.\n\n"
        "## Proposal\nBaker-supply sprint: partnerships + onboarding blitz; target +40 bakers by 2026-05-30.\n\n"
        "## Risks\nQuality dilution if we onboard too fast.\n\n"
        "## Success\nSupply/demand ratio ≥0.65; fulfillment_on_time ≥90%.\n"
    ),
    "P-002": (
        "## Problem\nBuyers need late-afternoon pickup slots; current windows cap holiday volume.\n\n"
        "## Proposal\nPickup-scheduler v2 with per-baker slot templates + reminders.\n\n"
        "## Risks\nBaker operational load; notification fatigue.\n\n"
        "## Success\n+15% slot utilization; -20% Sunday morning misses.\n"
    ),
    "P-003": (
        "## Problem\nSafari iOS 17 checkout failures (~8% of orders in support sample).\n\n"
        "## Proposal\nPatch payment sheet + regression tests on WebKit.\n\n"
        "## Risks\nNone major; ship as hotfix.\n\n"
        "## Success\nCheckout error rate <1% on iOS 17 within 14 days of ship.\n"
    ),
    "P-004": (
        "## Problem\nRepeat buyers ask for weekly cadence; one-off orders cap LTV.\n\n"
        "## Proposal\nSubscriptions v0: weekly basket from a favorite baker + skip week.\n\n"
        "## Risks\nInventory planning; churn if product quality varies.\n\n"
        "## Success\nRepeat-buyer rate +6pp within 60 days in pilot nbhd.\n"
    ),
}


async def _list_ux_signals(args: Mapping[str, Any]) -> dict[str, Any]:
    _ = args
    return {
        "signals": [
            {
                "id": "S-11",
                "pain": "bakers miss orders on Sunday mornings",
                "volume": 14,
                "source": "support_tickets",
                "suggests": "push notifications to bakers + 2h prep buffer",
            },
            {
                "id": "S-12",
                "pain": "no late-afternoon pickup slots",
                "volume": 22,
                "source": "buyer_exit_survey",
                "suggests": "P-002 pickup-scheduler v2",
            },
            {
                "id": "S-13",
                "pain": "checkout fails on Safari iOS 17",
                "volume": 8,
                "source": "bug_reports",
                "suggests": "P-003",
            },
            {
                "id": "S-14",
                "pain": "buyers want recurring weekly orders",
                "volume": 23,
                "source": "in_app_feedback",
                "suggests": "P-004 subscriptions",
            },
            {
                "id": "S-15",
                "pain": "basket min of $15 feels high in new nbhds",
                "volume": 11,
                "source": "new_market_survey",
                "suggests": "basket min test in east_brooklyn",
            },
        ],
        "note": "5 open signals; biggest volume: subscriptions (23) + scheduler (22)",
    }


async def _get_marketplace_metrics(args: Mapping[str, Any]) -> dict[str, Any]:
    raw = (args.get("neighborhood") or "").strip().lower().replace(" ", "_").replace("-", "_")
    aggregate = {"active_buyers": 1195, "active_bakers": 220, "repeat_buyer_rate_30d": 0.34}
    if not raw:
        return {
            "as_of": "2026-04-18",
            "neighborhoods": list(_NEIGHBORHOODS),
            "aggregate": aggregate,
            "note": "6 nbhds; east_brooklyn supply/demand 0.42 (gap); williamsburg saturated 1.02",
        }
    hit = next((n for n in _NEIGHBORHOODS if n["neighborhood"] == raw), None)
    if hit is None:
        return {
            "ok": False,
            "neighborhood": raw,
            "note": f"unknown neighborhood: {raw}",
        }
    return {
        "ok": True,
        "as_of": "2026-04-18",
        "neighborhood": hit,
        "aggregate": aggregate,
        "note": f"metrics for {hit['neighborhood']}: supply/demand {hit['supply_demand_ratio']}",
    }


async def _get_feature_usage(args: Mapping[str, Any]) -> dict[str, Any]:
    fid = (args.get("feature_id") or "baker-dashboard").strip().lower().replace(" ", "-")
    if fid == "pickup-scheduler-v2":
        return {
            "feature_id": fid,
            "dau": 0,
            "adoption_pct": 0.0,
            "d7_retention": 0.0,
            "complaints_last_30d": 0,
            "note": "not shipped yet (scheduled under P-002)",
        }
    if fid == "baker-dashboard":
        return {
            "feature_id": fid,
            "dau": 142,
            "adoption_pct": 0.71,
            "d7_retention": 0.58,
            "complaints_last_30d": 6,
            "top_complaint": "can't edit past listings",
            "note": "baker-dashboard: 71% adoption, 6 complaints/30d",
        }
    if fid == "basket-bundles":
        return {
            "feature_id": fid,
            "dau": 380,
            "adoption_pct": 0.29,
            "d7_retention": 0.42,
            "complaints_last_30d": 2,
            "note": "basket-bundles: 29% adoption among buyers",
        }
    return {
        "feature_id": fid,
        "dau": 0,
        "adoption_pct": 0.0,
        "note": f"no fixture for feature_id={fid!r}; try pickup-scheduler-v2|baker-dashboard|basket-bundles",
    }


async def _draft_spec(args: Mapping[str, Any]) -> dict[str, Any]:
    item_id = (args.get("item_id") or "").strip().upper()
    if not item_id:
        return {"ok": False, "note": "item_id required"}
    body = _SPECS.get(item_id)
    if body is None:
        body = (
            f"## Draft spec\n\n"
            f"Roadmap item `{item_id}` — no long-form stub yet.\n"
            f"Use `product.list_ux_signals` + `roadmap.read_item` to tighten scope.\n"
        )
    return {
        "item_id": item_id,
        "spec_md": body,
        "note": f"draft spec for {item_id}",
    }


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="product.list_ux_signals",
        description="List open UX signals and user-pain observations worth turning into roadmap items.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_list_ux_signals,
        allowed_callers=("product",),
    ),
    ToolSpec(
        name="product.get_marketplace_metrics",
        description="Per-neighborhood liquidity metrics for Crumb (mock). Optional neighborhood filter.",
        input_schema={
            "type": "object",
            "properties": {"neighborhood": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_get_marketplace_metrics,
        allowed_callers=("product",),
    ),
    ToolSpec(
        name="product.get_feature_usage",
        description="Adoption / DAU for a feature_id (mock): pickup-scheduler-v2 | baker-dashboard | basket-bundles.",
        input_schema={
            "type": "object",
            "properties": {"feature_id": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_get_feature_usage,
        allowed_callers=("product",),
    ),
    ToolSpec(
        name="product.draft_spec",
        description="Draft a short spec doc for a given roadmap item id.",
        input_schema={
            "type": "object",
            "properties": {"item_id": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_draft_spec,
        allowed_callers=("product",),
    ),
]
