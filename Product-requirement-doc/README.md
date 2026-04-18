# Product requirement doc — agent index

Specs for each agent: **role**, **private `god.md`**, **MCP tools used**, **cascade events consumed / emitted**. All cross-agent traffic is **router-brokered**; see root [`AGENTS.md`](../AGENTS.md).

| Agent | Spec |
|-------|------|
| `the-gooning-company` (router) | [`router.md`](router.md) |
| Product / UX | [`product.md`](product.md) |
| Marketing | [`marketing.md`](marketing.md) |
| Finance | [`finance.md`](finance.md) |

---

## Shared template (fill in each stub)

Use this structure in every `*.md` below.

```markdown
## Role
(one paragraph)

## Private god.md
- What lives here vs what lives in shared roadmap
- Update rules (who may edit)

## MCP tools (namespaced)
- List tool names (e.g. roadmap.list_items) — mock OK
- Preconditions / ownership (who may call)

## Cascade — inbound
- Event types + payload summary the router may deliver

## Cascade — outbound
- Event types + payload summary this agent returns to the router for fan-out

## Open questions
- (optional)
```

Next step: replace placeholders inside each linked file with concrete tools and event shapes.
