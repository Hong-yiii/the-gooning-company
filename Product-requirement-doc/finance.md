# Agent spec: Finance (Crumb)

> **Status:** demo-ready — mock P&L, runway, and unit economics.

## Role

Owns projections, budgets, and financial implications of roadmap and marketing actions for **Crumb**. **Reads** the shared roadmap; reacts to router briefs.

## Private god.md

- Model assumptions, scenario notes, approval gates — not a real ledger (tools are mocked).

## MCP tools (namespaced)

| Tool | Purpose | Callers |
|------|---------|---------|
| `finance.get_projection` | Snapshot: horizon, runway, burn, assumptions. | finance |
| `finance.get_financial_report` | Monthly-style P&L-lite (`month`, default `2026-04`). | finance |
| `finance.get_unit_economics` | `side`: `order` \| `buyer` \| `baker`. | finance |
| `finance.project_runway` | `scenario`: `base` \| `aggressive_growth` \| `conservative` (optional). | finance |
| `finance.cost_campaign` | Cash timing + orders for a `campaign_id`. | finance |
| `finance.simulate_roadmap_delta` | Plausible runway impact from a **`delta`** object. | finance |
| `roadmap.read_all` / `roadmap.read_item` | Read-only roadmap context. | finance (+ others) |

## Cascade — inbound

- **`roadmap.changed`** (via router).
- **`marketing.campaign_drafted`** or spend asks (via router).

## Cascade — outbound

```json
{
  "event": "finance.implication",
  "metric": "runway_months",
  "before": 13.4,
  "after": 11.8,
  "delta": -1.6,
  "assumption": "marketing spend +$12k/mo for 3 mo",
  "severity": "warn"
}
```

```json
{
  "event": "finance.risk_flag",
  "reason": "runway<9mo",
  "recommend": "pause M-001 until F-001 resolves"
}
```

## Open questions

- Currency is **USD** in all mock payloads for the demo.
