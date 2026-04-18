# Agent spec: Finance

> **Status:** placeholder — fill before implementation.

## Role

Owns projections, budgets, and financial implications of roadmap and marketing actions. **Reads** the shared roadmap; reacts to cascades from the router.

## Private god.md

- Model assumptions, scenario notes, approval gates, **not** source ledger data (mock tools only).

## MCP tools (namespaced)

- `finance.*`: e.g. `finance.project_runway`, `finance.estimate_campaign_cost` — mock OK.
- Read-only `roadmap.*` if needed for context — TBD.

## Cascade — inbound

- `roadmap.changed` (via router summary).
- `marketing.campaign_started` or equivalent (via router).

## Cascade — outbound

- `finance.risk_flag`, `finance.budget_signal` (conceptual): router may forward to **Product** (scope) or **Marketing** (spend cap).

## Open questions

- Currency / units in mock payloads — keep consistent across tools.
