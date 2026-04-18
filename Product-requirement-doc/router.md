# Agent spec: `the-gooning-company` (router)

> **Status:** placeholder — fill before implementation.

## Role

Founder-facing entry agent. Classifies intent, pulls minimal context, delegates to Product / Marketing / Finance via harness messaging, and **brokers all cascades** (no peer-to-peer between domain agents).

## Private god.md

- Router-only notes: routing heuristics, founder preferences, recent dispatch decisions (not company domain truth).
- **Do not** duplicate the full roadmap or domain `god.md` contents; link or summarize for dispatch only.

## MCP tools (namespaced)

- `router.*` (optional): e.g. `router.log_cascade`, `router.resolve_intent` — TBD.
- Router may have **read-only** observability tools for dashboard trace export — TBD in [`../dev-concepts/README.md`](../dev-concepts/README.md).

## Cascade — inbound

- Final replies from domain agents after delegated work.
- Founder messages from dashboard / gateway.

## Cascade — outbound

- `dispatch.product`, `dispatch.marketing`, `dispatch.finance` (conceptual): structured handoff to one or more domain agents with **why** and **what changed**.
- Fan-out notifications when one domain’s outcome requires others (e.g. roadmap updated → notify Marketing + Finance).

## Open questions

- Exact event payload schema (JSON) — define in a follow-up pass.
