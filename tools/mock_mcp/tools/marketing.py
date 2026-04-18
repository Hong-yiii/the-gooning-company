"""``marketing.*`` — tools exposed to the marketing agent (Crumb demo fixtures)."""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec


async def _list_campaigns(args: Mapping[str, Any]) -> dict[str, Any]:
    _ = args
    return {
        "campaigns": [
            {
                "id": "M-001",
                "name": "Holiday gifting teaser",
                "audience": "buyer",
                "channels": ["instagram_reels", "referral"],
                "status": "scheduled",
                "launch": "2026-11-25",
                "budget_usd": 9500,
                "expected_cac": 7.2,
            },
            {
                "id": "M-002",
                "name": "Baker Saturdays",
                "audience": "baker",
                "channels": ["local_partnerships"],
                "status": "live",
                "launch": "2026-04-10",
                "budget_usd": 6000,
                "expected_cac": 32.0,
            },
            {
                "id": "M-EB1",
                "name": "East Brooklyn Reels buy",
                "audience": "buyer",
                "channels": ["instagram_reels", "tiktok"],
                "status": "live",
                "launch": "2026-04-05",
                "budget_usd": 3500,
                "expected_cac": 8.1,
            },
        ],
        "note": "3 campaigns: 2 live, 1 scheduled",
    }


async def _get_channel_performance(args: Mapping[str, Any]) -> dict[str, Any]:
    window = (args.get("window") or "last_30d").strip()
    return {
        "window": window,
        "channels": [
            {
                "channel": "instagram_reels",
                "impressions": 184000,
                "ctr": 0.028,
                "cpc_usd": 0.42,
                "conversion_rate": 0.061,
                "cac_usd": 6.90,
                "orders_driven": 314,
            },
            {
                "channel": "tiktok",
                "impressions": 210000,
                "ctr": 0.019,
                "cpc_usd": 0.31,
                "conversion_rate": 0.038,
                "cac_usd": 8.15,
                "orders_driven": 152,
            },
            {
                "channel": "referral",
                "impressions": 12000,
                "ctr": 0.144,
                "cpc_usd": 0.00,
                "conversion_rate": 0.22,
                "cac_usd": 3.20,
                "orders_driven": 380,
            },
            {
                "channel": "local_partnerships",
                "impressions": 3200,
                "ctr": 0.21,
                "cpc_usd": 0.00,
                "conversion_rate": 0.31,
                "cac_usd": 28.50,
                "orders_driven": 82,
                "audience": "baker",
            },
            {
                "channel": "google_search",
                "impressions": 41000,
                "ctr": 0.036,
                "cpc_usd": 1.12,
                "conversion_rate": 0.042,
                "cac_usd": 18.90,
                "orders_driven": 62,
            },
        ],
        "note": "last_30d: referral best CAC $3.20; IG Reels volume leader 314 orders",
    }


async def _get_funnel_metrics(args: Mapping[str, Any]) -> dict[str, Any]:
    side = (args.get("side") or "buyer").strip().lower()
    if side == "baker":
        return {
            "side": "baker",
            "funnel": {
                "visits": 3400,
                "signup": {"count": 380, "rate_from_visits": 0.11},
                "first_listing": {"count": 228, "rate_from_signup": 0.60},
                "listing_with_sale": {"count": 164, "rate_from_first_listing": 0.72},
            },
            "note": "baker funnel: visits→first_listing 6.7%; listing_with_sale 72% of first listings",
        }
    return {
        "side": "buyer",
        "funnel": {
            "visits": 42000,
            "signup": {"count": 6720, "rate_from_visits": 0.16},
            "first_order": {"count": 2150, "rate_from_signup": 0.32},
            "repeat_within_30d": {"count": 731, "rate_from_first_order": 0.34},
        },
        "note": "buyer funnel: visits→first_order 5.1%; repeat 34% of first orders",
    }


async def _draft_campaign(args: Mapping[str, Any]) -> dict[str, Any]:
    objective = (args.get("objective") or "").strip()
    audience = (args.get("audience") or "").strip().lower()
    if not objective or audience not in ("buyer", "baker"):
        return {
            "ok": False,
            "note": "objective and audience (buyer|baker) required",
        }

    if audience == "buyer":
        outline = (
            f"# Campaign draft — buyers\n\n"
            f"**Objective:** {objective}\n\n"
            f"**Channels:** Instagram Reels + referral (Crumb mock CAC ~$7–9).\n"
            f"**Hook:** neighborhood freshness + pickup-only trust.\n"
            f"**CTA:** first order bundle; track CAC weekly.\n"
        )
        note = "buyer draft: Reels + referral; expected_cac band ~7–9 USD"
    else:
        outline = (
            f"# Campaign draft — bakers\n\n"
            f"**Objective:** {objective}\n\n"
            f"**Channels:** local partnerships + markets (mock CAC ~$28–35).\n"
            f"**Hook:** income + community, not gig-economy vibes.\n"
            f"**CTA:** first listing live within 7 days.\n"
        )
        note = "baker draft: local partnerships; expected_cac band ~28–35 USD"

    return {
        "ok": True,
        "objective": objective,
        "audience": audience,
        "outline_md": outline,
        "note": note,
    }


async def _estimate_reach(args: Mapping[str, Any]) -> dict[str, Any]:
    draft_id = (args.get("draft_id") or "").strip()
    if not draft_id:
        return {"ok": False, "note": "draft_id required"}
    ch = draft_id[0].lower()
    bands = {
        "a": (12000, 22000),
        "b": (9000, 16000),
        "c": (7000, 13000),
        "d": (5000, 9000),
        "e": (4000, 8000),
        "f": (3000, 7000),
        "g": (2500, 6000),
        "h": (2000, 5500),
        "i": (1800, 5000),
        "j": (1600, 4800),
        "k": (1400, 4500),
        "l": (1200, 4200),
        "m": (11000, 21000),
        "n": (1000, 4000),
        "o": (950, 3800),
        "p": (13000, 24000),
        "q": (800, 3200),
        "r": (750, 3000),
        "s": (6500, 12000),
        "t": (600, 2600),
        "u": (550, 2400),
        "v": (500, 2200),
        "w": (480, 2000),
        "x": (450, 1900),
        "y": (420, 1800),
        "z": (400, 1700),
    }
    low, high = bands.get(ch, (5000, 15000))
    return {
        "draft_id": draft_id,
        "reach_low": low,
        "reach_high": high,
        "assumptions": [
            "Mock reach: keyed off first letter of draft_id for determinism.",
            "Assumes NYC geo targeting; excludes non-NYC test accounts.",
        ],
        "note": f"reach band {low:,}–{high:,} impressions (deterministic)",
    }


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="marketing.list_campaigns",
        description="List campaigns currently in flight or scheduled (Crumb demo seed).",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_list_campaigns,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.get_channel_performance",
        description="Return CTR/CPC/CAC and orders by channel for a time window (mock).",
        input_schema={
            "type": "object",
            "properties": {"window": {"type": "string", "default": "last_30d"}},
            "additionalProperties": False,
        },
        handler=_get_channel_performance,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.get_funnel_metrics",
        description="Buyer or baker funnel counts and conversion rates (mock).",
        input_schema={
            "type": "object",
            "properties": {
                "side": {"type": "string", "enum": ["buyer", "baker"], "default": "buyer"},
            },
            "additionalProperties": False,
        },
        handler=_get_funnel_metrics,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.draft_campaign",
        description="Draft a campaign outline for a given objective and audience (buyer|baker).",
        input_schema={
            "type": "object",
            "properties": {
                "objective": {"type": "string"},
                "audience": {"type": "string", "enum": ["buyer", "baker"]},
            },
            "additionalProperties": False,
        },
        handler=_draft_campaign,
        allowed_callers=("marketing",),
    ),
    ToolSpec(
        name="marketing.estimate_reach",
        description="Mocked reach band for a campaign draft id (deterministic).",
        input_schema={
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_estimate_reach,
        allowed_callers=("marketing",),
    ),
]
