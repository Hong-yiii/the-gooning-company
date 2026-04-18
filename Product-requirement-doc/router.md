# Agent spec: `the-gooning-company` (router) — Crumb demo

> **Status:** demo-ready — routing + cascade fan-out via `agent(...)`; no peer-to-peer.

## Role

Founder-facing entry for **Crumb** (within The Gooning Company harness). Classifies intent, delegates to **product** / **marketing** / **finance** via the harness `agent` tool, and **brokers cascades** (no domain agent talks to another directly).

## Private god.md

- Router-only notes: open threads, pending cascades, last routing decisions — not canonical business truth (roadmap + domain `god.md`).

## MCP tools (namespaced)

- **`router.*`:** none required for v0 (optional helpers deferred).
- Router may use **`roadmap.read_*`** for observability when citing status to the founder.

## Cascade — inbound

- Final replies from domain agents after delegated work.
- Founder messages from dashboard / gateway.

## Cascade — outbound

Dispatch is via **`agent(subagent_type=…, prompt=…)`** — not a separate MCP tool.

Fan-out pattern (conceptual):

1. If Product returns **`roadmap.changed`**, router calls **marketing** then **finance** with the same delta summary.
2. If Marketing returns **`marketing.campaign_drafted`**, router calls **finance** for **`finance.cost_campaign`** / implications.
3. If Finance returns **`finance.risk_flag`**, router calls **product** and/or **marketing** with the constraint.

### Envelope reference (copy-paste)

| Event | When | Key fields |
|-------|------|--------------|
| `roadmap.changed` | After roadmap mutation | `id`, `title`, `domain`, `from_status`, `to_status`, `reason` |
| `marketing.campaign_drafted` | Campaign outline approved | `id`, `audience`, `channels[]`, `budget_usd`, `expected_cac`, `launch` |
| `marketing.issue_raised` | Needs Product | `summary`, `suggested_item{title,domain}` |
| `finance.implication` | Numeric delta | `metric`, `before`, `after`, `delta`, `assumption`, `severity` |
| `finance.risk_flag` | Escalation | `reason`, `recommend` |

## Open questions

- Mailbox / plugin fan-out deferred — router prompt is source of truth for v0 demo.
