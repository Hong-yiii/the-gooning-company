"""``finance.*`` — tools exposed to the finance agent (Crumb demo fixtures)."""

from __future__ import annotations

from typing import Any, Mapping

from ..spec import ToolSpec

_MONTH_FIXTURES: dict[str, dict[str, Any]] = {
    "2026-02": {
        "month": "2026-02",
        "gmv": 198000,
        "revenue": 29700,
        "cogs": {"payments_fees": 5940, "refunds": 900, "baker_credits": 1200},
        "gross_profit": 21660,
        "opex": {"salaries": 138000, "marketing": 18000, "tools": 4100, "office": 3600},
        "burn": 142040,
        "cash": 2120000,
        "runway_months": 14.9,
    },
    "2026-03": {
        "month": "2026-03",
        "gmv": 210000,
        "revenue": 31500,
        "cogs": {"payments_fees": 6300, "refunds": 1000, "baker_credits": 1350},
        "gross_profit": 22850,
        "opex": {"salaries": 140000, "marketing": 20000, "tools": 4150, "office": 3700},
        "burn": 145000,
        "cash": 2050000,
        "runway_months": 14.1,
    },
    "2026-04": {
        "month": "2026-04",
        "gmv": 220000,
        "revenue": 33000,
        "cogs": {"payments_fees": 6600, "refunds": 1100, "baker_credits": 1500},
        "gross_profit": 23800,
        "opex": {"salaries": 142000, "marketing": 22000, "tools": 4200, "office": 3800},
        "burn": 148200,
        "cash": 1980000,
        "runway_months": 13.4,
    },
}

_CAMPAIGNS: dict[str, dict[str, Any]] = {
    "M-001": {
        "budget_usd": 9500,
        "expected_orders": 820,
        "expected_cac": 7.2,
        "cash_timing": [
            {"month": "2026-11", "spend_usd": 3200},
            {"month": "2026-12", "spend_usd": 6300},
        ],
    },
    "M-002": {
        "budget_usd": 6000,
        "expected_orders": 95,
        "expected_cac": 32.0,
        "cash_timing": [
            {"month": "2026-04", "spend_usd": 2500},
            {"month": "2026-05", "spend_usd": 3500},
        ],
    },
    "M-EB1": {
        "budget_usd": 3500,
        "expected_orders": 210,
        "expected_cac": 8.1,
        "cash_timing": [{"month": "2026-04", "spend_usd": 3500}],
    },
    "M-003": {
        "budget_usd": 12000,
        "expected_orders": 40,
        "expected_cac": 30.0,
        "cash_timing": [{"month": "2026-06", "spend_usd": 12000}],
    },
}


async def _get_projection(args: Mapping[str, Any]) -> dict[str, Any]:
    _ = args
    return {
        "horizon_months": 18,
        "runway_months": 13.4,
        "burn_monthly": 148200,
        "gmv_monthly": 220000,
        "assumptions": [
            "Base case aligned to finance.get_financial_report month 2026-04.",
            "Take rate 15% on GMV; illustrative only.",
        ],
        "note": "projection snapshot: runway 13.4 mo, burn $148k/mo",
    }


async def _get_financial_report(args: Mapping[str, Any]) -> dict[str, Any]:
    month = (args.get("month") or "2026-04").strip()
    base = _MONTH_FIXTURES.get(month)
    if base is None:
        # deterministic fallback from last digit of month
        tail = month[-1] if month else "0"
        key = {"0": "2026-04", "1": "2026-03", "2": "2026-02"}.get(tail, "2026-04")
        base = dict(_MONTH_FIXTURES[key])
        base["month"] = month
        base["note"] = f"month {month!r}: seeded from {key} template"
    else:
        base = dict(base)
        base["note"] = f"{month}: GMV ${base['gmv']:,}, burn ${base['burn']:,}, runway {base['runway_months']} mo"
    return base


async def _get_unit_economics(args: Mapping[str, Any]) -> dict[str, Any]:
    side = (args.get("side") or "order").strip().lower()
    if side == "buyer":
        return {
            "side": "buyer",
            "cac": 7.80,
            "ltv": 48.00,
            "payback_months": 3.9,
            "orders_per_year": 8.1,
            "note": "buyer unit economics: CAC $7.80, LTV $48, payback ~3.9 mo",
        }
    if side == "baker":
        return {
            "side": "baker",
            "cac": 32.00,
            "ltv": 420.00,
            "payback_months": 5.2,
            "gmv_per_baker_per_mo": 1220,
            "note": "baker unit economics: CAC $32, LTV $420, payback ~5.2 mo",
        }
    return {
        "side": "order",
        "avg_order_usd": 22.40,
        "contribution_margin_pct": 54,
        "variable_cost_usd": 10.30,
        "note": "per-order: avg $22.40, contribution margin 54%",
    }


async def _project_runway(args: Mapping[str, Any]) -> dict[str, Any]:
    scenario = (args.get("scenario") or "base").strip().lower()
    scenarios = {
        "base": {
            "runway_months": 13.4,
            "burn_monthly": 148200,
            "gmv_now": 220000,
            "gmv_m_plus_6": 360000,
            "note": "base: runway 13.4 mo; GMV $220k→$360k by M+6",
        },
        "aggressive_growth": {
            "runway_months": 10.1,
            "burn_monthly": 205000,
            "gmv_now": 220000,
            "gmv_m_plus_6": 490000,
            "note": "aggressive: extra marketing; runway 10.1 mo; GMV→$490k M+6",
        },
        "conservative": {
            "runway_months": 17.2,
            "burn_monthly": 115000,
            "gmv_now": 220000,
            "gmv_m_plus_6": 290000,
            "note": "conservative: hiring freeze; runway 17.2 mo; GMV→$290k M+6",
        },
    }
    payload = dict(scenarios.get(scenario, scenarios["base"]))
    payload["scenario"] = scenario
    return payload


async def _simulate_roadmap_delta(args: Mapping[str, Any]) -> dict[str, Any]:
    delta = args.get("delta")
    if not isinstance(delta, dict):
        return {"ok": False, "note": "delta object required"}

    rid = str(delta.get("id") or "").strip()
    domain = str(delta.get("domain") or "").strip().lower()
    to_status = str(delta.get("to_status") or "").strip().lower()
    title = str(delta.get("title") or "").strip()

    runway_before = 13.4
    burn_before = 148200
    burn_delta = 0.0
    assumptions: list[str] = []

    if domain == "marketing" and to_status in ("in-progress", "in progress", "in_progress"):
        extra = 4000.0 if "local" in title.lower() else 2500.0
        burn_delta = extra
        assumptions.append("Marketing item moved in-flight: +$2.5–4k/mo opex in mock model.")
    elif domain == "product" and rid.upper().startswith("P-"):
        burn_delta = 8000.0 if "subscription" in title.lower() else 6000.0
        assumptions.append("Product net-new work: +eng/vendor spend from M+2 in mock model.")
    elif domain == "finance":
        burn_delta = 0.0
        assumptions.append("Finance roadmap rows: assumption refresh only in mock model.")
    else:
        assumptions.append("Generic roadmap delta: small burn nudge in mock model.")
        burn_delta = 3000.0

    runway_after = runway_before - (burn_delta / max(burn_before, 1)) * 0.8
    return {
        "ok": True,
        "delta": delta,
        "runway_before": runway_before,
        "runway_after": round(runway_after, 2),
        "burn_before_monthly": burn_before,
        "burn_delta_monthly": burn_delta,
        "assumptions": assumptions,
        "note": f"simulate delta {rid or title!r}: runway {runway_before}→{round(runway_after, 2)} mo",
    }


async def _cost_campaign(args: Mapping[str, Any]) -> dict[str, Any]:
    cid = (args.get("campaign_id") or "").strip()
    if not cid:
        return {"ok": False, "note": "campaign_id required"}
    hit = _CAMPAIGNS.get(cid)
    if hit is None:
        return {"ok": False, "note": f"unknown campaign_id: {cid}"}
    return {
        "ok": True,
        "campaign_id": cid,
        "budget_usd": hit["budget_usd"],
        "expected_orders": hit["expected_orders"],
        "expected_cac": hit["expected_cac"],
        "cash_timing": hit["cash_timing"],
        "note": f"{cid}: budget ${hit['budget_usd']:,}, expected_orders {hit['expected_orders']}",
    }


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="finance.get_projection",
        description="Return the current projection snapshot (runway, burn, assumptions).",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_get_projection,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.get_financial_report",
        description="Monthly P&L-lite for Crumb (mock); month default 2026-04.",
        input_schema={
            "type": "object",
            "properties": {"month": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_get_financial_report,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.get_unit_economics",
        description="Unit economics for order, buyer, or baker side (mock).",
        input_schema={
            "type": "object",
            "properties": {
                "side": {"type": "string", "enum": ["order", "buyer", "baker"]},
            },
            "additionalProperties": False,
        },
        handler=_get_unit_economics,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.project_runway",
        description="Runway scenarios: base | aggressive_growth | conservative (mock).",
        input_schema={
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "enum": ["base", "aggressive_growth", "conservative"],
                },
            },
            "additionalProperties": False,
        },
        handler=_project_runway,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.simulate_roadmap_delta",
        description="Given a roadmap delta envelope, return plausible runway impact (mock).",
        input_schema={
            "type": "object",
            "properties": {"delta": {"type": "object"}},
            "additionalProperties": False,
        },
        handler=_simulate_roadmap_delta,
        allowed_callers=("finance",),
    ),
    ToolSpec(
        name="finance.cost_campaign",
        description="Cost a marketing campaign by id and report cash-timing impact (mock).",
        input_schema={
            "type": "object",
            "properties": {"campaign_id": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_cost_campaign,
        allowed_callers=("finance",),
    ),
]
