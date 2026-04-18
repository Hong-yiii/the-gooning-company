# Agent spec: Product / UX (Crumb)

> **Status:** demo-ready — Crumb marketplace; mock MCP tools return deterministic fixtures.

## Role

Owns product direction and the **shared roadmap artifact** (`state/roadmap.md`). Proposes and applies roadmap changes through **`roadmap.*`** tools; returns structured **`roadmap.changed`** envelopes to the router for cascade.

## Private god.md

- UX principles, prioritization rationale, neighborhood liquidity notes — **not** the canonical roadmap rows (those live in `state/roadmap.md`).
- Product is the **only** agent that calls mutating **`roadmap.add_item`**, **`roadmap.move_item`**, **`roadmap.drop_item`**.

## MCP tools (namespaced)

| Tool | Purpose | Callers |
|------|---------|---------|
| `roadmap.read_all` | Full roadmap markdown (+ parsed items in mock). | product, marketing, finance, the-gooning-company |
| `roadmap.read_item` | Single row by `id`. | same |
| `roadmap.add_item` | Append to **Backlog**; allocates `P-` / `M-` / `F-` id. | **product** only |
| `roadmap.move_item` | Move row between columns; `status` may be `dropped` (stored in **Done** as `shipped=dropped — …`). | **product** only |
| `roadmap.drop_item` | Alias: move to **Done** with `shipped` = `dropped — {reason}` or shipped note. | **product** only |
| `product.list_ux_signals` | Open UX / research signals (mock list). | product |
| `product.get_marketplace_metrics` | Per-neighborhood liquidity (buyers, bakers, ratios); optional `neighborhood`. | product |
| `product.get_feature_usage` | Adoption / DAU for a `feature_id` (mock). | product |
| `product.draft_spec` | Stub spec markdown for a roadmap `item_id`. | product |

## Cascade — inbound

- Router briefs: founder asks, Marketing **`marketing.issue_raised`**, Finance risk flags implying reprioritization.

## Cascade — outbound

After any mutating roadmap tool, include in the reply to the router:

```json
{
  "event": "roadmap.changed",
  "id": "P-001",
  "title": "…",
  "domain": "product",
  "from_status": "backlog",
  "to_status": "in-progress",
  "reason": "…"
}
```

## Open questions

- v1 roadmap remains markdown tables; JSON sidecar optional later per [`../dev-concepts/README.md`](../dev-concepts/README.md).
