# Roadmap

Single source of truth for what the company is doing. **Product** is the only agent that mutates this file; **Marketing** and **Finance** read it.

## Format

Rows are keyed by a stable `id` that other agents can reference in their `god.md` and in router briefs. Columns:

| Field | Meaning |
|-------|---------|
| `id` | Stable short id, e.g. `P-001`, `M-001`, `F-001`. Never reused. |
| `title` | One line the founder can scan. |
| `domain` | `product` \| `marketing` \| `finance` (origin of the item). |
| `status` | `backlog` \| `next` \| `in-progress` \| `blocked` \| `done` \| `dropped` |
| `owner` | Which agent drives the work. |
| `notes` | Short context, links, or implications. Never replaces `god.md`. |

> TODO(product): decide final format. Keeping markdown tables for v0. Revisit JSON once `roadmap.*` tools stabilise so diffs are machine-readable.

---

## Backlog

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| <!-- TODO --> | | | | |

## Next

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| <!-- TODO --> | | | | |

## In progress

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| <!-- TODO --> | | | | |

## Blocked

| id | title | domain | owner | blocker |
|----|-------|--------|-------|---------|
| <!-- TODO --> | | | | |

## Done

| id | title | domain | owner | shipped |
|----|-------|--------|-------|---------|
| <!-- TODO --> | | | | |

---

## Change log

Append a one-line entry every time the roadmap changes. Helps the router cascade concisely.

- <!-- YYYY-MM-DD — agent — id — action — one-line reason -->
