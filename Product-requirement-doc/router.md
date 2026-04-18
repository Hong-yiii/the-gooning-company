# Agent spec: `the-gooning-company` (router)

## Role

Founder-facing entry agent. The router classifies intent, pulls minimal context, delegates work to Product, Marketing, or Finance, and brokers all cross-domain cascades. It treats each domain as a single endpoint even if that domain runs internal sub-agents. For Marketing, the router communicates only with the **Marketing Lead**, never directly with marketing specialists.

## Private god.md

- Router-only notes: routing heuristics, founder preferences, dispatch history, escalation patterns, and summarization preferences.
- It should store enough durable context to make better routing decisions over time.
- It must **not** become a duplicate source of truth for the roadmap or domain `god.md` files.
- When the router stores cross-domain outcomes, it should keep compact summaries and references rather than full internal domain reasoning.

## MCP tools (namespaced)

- `router.resolve_intent` — classify founder input into one or more domain tasks.
- `router.log_cascade` — append a structured trace entry for routing and fan-out decisions.
- `router.get_dispatch_history` — retrieve prior dispatches and outcomes for observability.
- `router.build_context_packet` — assemble the minimum context payload for a domain handoff.
- Read-only dashboard support tools may be added later for trace and observability export.

## Internal team structure

- None for now. The router is a single top-level orchestration identity.
- If helper workers are introduced later, they remain router-private and may not bypass the router’s final dispatch authority.

## Cascade — inbound

Router may receive:
- Founder requests from the dashboard or gateway.
- `product.*` domain outcomes from Product.
- `marketing.*` domain outcomes from the **Marketing Lead** only.
- `finance.*` domain outcomes from Finance.
- Follow-up replies to prior dispatches, correlated by `correlation_id`.

## Cascade — outbound

Router may emit:
- `dispatch.product` — structured handoff to Product with task, context, and why now.
- `dispatch.marketing` — structured handoff to Marketing Lead with task, context, and why now.
- `dispatch.finance` — structured handoff to Finance with task, context, and why now.
- Fan-out notifications when one domain outcome affects another domain.
- Founder-facing summaries after routing results are available.

## Routing rules

- No peer-to-peer cross-domain messaging: Product, Marketing, and Finance never message each other directly.
- The router is the only cross-domain fan-out authority.
- The router sees Marketing as one domain endpoint, even if Marketing internally orchestrates specialists.
- Only the **Marketing Lead** may return Marketing domain outcomes to the router.
- The router should forward compact deltas, not raw internal chain-of-thought or unnecessary memory dumps.
- A single founder request may produce multiple correlated dispatches if the work truly spans domains.

## Open questions

- Should router dispatch envelopes be identical to domain event envelopes, or versioned separately?
- What threshold should trigger automatic fan-out versus manual founder confirmation?
- Should the router maintain explicit priority queues for urgent launch blockers versus normal planning work?
