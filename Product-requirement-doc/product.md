# Agent spec: Product / UX

> **Status:** placeholder — fill before implementation.

## Role

Owns product direction and the **shared roadmap artifact**. Proposes and applies roadmap changes through `roadmap.*` tools; summarizes impact for the router to cascade.

## Private god.md

- PRD snippets, UX principles, prioritization rationale, **not** the canonical roadmap rows (those live in the shared artifact).
- Product is the **only** agent that should call mutating `roadmap.*` tools (unless dev-concepts say otherwise).

## MCP tools (namespaced)

- `roadmap.*`: list, create, update status, reorder — **mock** implementations OK.
- `product.*`: e.g. user research summaries, feature specs — TBD.

## Cascade — inbound

- Requests from router: founder asks, Marketing asks for roadmap insertion, Finance flags capacity/risk.

## Cascade — outbound

- `roadmap.changed` (conceptual): summary + item IDs for router to forward to Marketing and Finance.

## Open questions

- Kanban columns vs domain tags — align with dashboard and [`../dev-concepts/README.md`](../dev-concepts/README.md).
