# Agent spec: Marketing (Crumb)

> **Status:** demo-ready — mock analytics and campaign fixtures.

## Role

Owns positioning, campaigns, and GTM for **Crumb**. **Reads** the shared roadmap; does **not** mutate it. Surfaces roadmap gaps via the router as structured **`marketing.issue_raised`**.

## Private god.md

- Campaign briefs, channel plans, two-sided messaging (buyers vs bakers), experiment readouts.

## MCP tools (namespaced)

| Tool | Purpose | Callers |
|------|---------|---------|
| `marketing.list_campaigns` | Seeded campaigns (`M-001`, `M-002`, `M-EB1`, …). | marketing |
| `marketing.get_channel_performance` | CTR, CPC, CAC, orders by channel (`window`, default `last_30d`). | marketing |
| `marketing.get_funnel_metrics` | Buyer or baker funnel counts and rates (`side`). | marketing |
| `marketing.draft_campaign` | Deterministic outline from `objective` + `audience`. | marketing |
| `marketing.estimate_reach` | Reach band for a `draft_id` (deterministic). | marketing |
| `roadmap.read_all` / `roadmap.read_item` | Read-only roadmap context. | marketing (+ others) |

## Cascade — inbound

- **`roadmap.changed`** summaries from the router (after Product).
- Founder / router asks for launches, messaging, or channel plans.

## Cascade — outbound

```json
{
  "event": "marketing.campaign_drafted",
  "id": "M-00X",
  "audience": "buyer",
  "channels": ["instagram_reels", "referral"],
  "budget_usd": 9500,
  "expected_cac": 7.2,
  "launch": "2026-11-25"
}
```

```json
{
  "event": "marketing.issue_raised",
  "summary": "Cannot run holiday CTA without pickup windows in product.",
  "suggested_item": {
    "title": "Ship pickup-scheduler v2 before holiday campaign",
    "domain": "product"
  }
}
```

## Open questions

- Thresholds for when every campaign ping requires Finance (`finance.cost_campaign`) — default: any net-new spend over **$5k** in mock briefs.
