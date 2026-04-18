# Agent spec: Marketing

> **Status:** placeholder — fill before implementation.

## Role

Owns campaigns, messaging, and go-to-market plans. **Reads** the shared roadmap; does **not** silently edit Product’s `god.md`. Surfaces roadmap gaps or conflicts **through the router** to Product.

## Private god.md

- Campaign briefs, channel plans, narrative decisions, experiment results.

## MCP tools (namespaced)

- `marketing.*`: e.g. `marketing.create_campaign`, `marketing.list_campaigns` — mock OK.
- Read-only `roadmap.*` reads if exposed — TBD.

## Cascade — inbound

- Roadmap updates from router (summaries from Product).
- Founder or router requests for launches / positioning.

## Cascade — outbound

- `marketing.campaign_started` / `marketing.issue_raised` (conceptual): router forwards **Finance** (spend) and/or **Product** (roadmap item).

## Open questions

- Which events always require Finance vs optional — define thresholds in stubs or dev-concepts.
