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

Markdown kanban tables below are parsed by the dashboard (`dashboard_backend/roadmap.py`). **Dropped** items are stored in **Done** with `shipped` prefixed `dropped —` (no separate column).

---

## Backlog

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| P-003 | Safari iOS 17 checkout fix | product | product | 4 weekly complaints; ~8% of orders affected per support logs |
| P-004 | Recurring weekly-order subscription | product | product | Requested by 23 repeat buyers; lifts repeat-rate lever |
| F-001 | Unit economics refresh — 17% take-rate scenario | finance | finance | Maya asked 2026-04-18; baker-churn risk must be quantified |
| M-003 | Baker referral-credit program | marketing | marketing | $20 credit per referred active baker; blocked on P-004 |

## Next

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| P-002 | Pickup-scheduler v2 (late-afternoon slots) | product | product | Unblocks holiday volume; ship before 2026-11-20 |
| M-001 | Holiday gifting teaser | marketing | marketing | IG Reels + referral; launch 2026-11-25 |
| F-002 | Series A narrative deck v1 | finance | finance | Target close in 6 mo; needs GMV + repeat-rate slides |

## In progress

| id | title | domain | owner | notes |
|----|-------|--------|-------|-------|
| P-001 | East Brooklyn baker-supply sprint | product | product | Target 40 new bakers by 2026-05-30; supply/demand ratio currently 0.42 |
| M-002 | Baker Saturdays local-partnership campaign | marketing | marketing | Coffee shops + farmers' markets; CAC target under $35 |

## Blocked

| id | title | domain | owner | blocker |
|----|-------|--------|-------|---------|

## Done

| id | title | domain | owner | shipped |
|----|-------|--------|-------|---------|
| P-000 | Baker dashboard v1 | product | product | 2026-03-14 — adoption 71% in week one |

---

## Change log

Append a one-line entry every time the roadmap changes. Helps the router cascade concisely.

- 2026-03-14 — product — P-000 — shipped — baker dashboard v1 out; adoption 71% wk1
- 2026-04-02 — product — P-001 — added — East Brooklyn supply gap (supply/demand 0.42)
- 2026-04-10 — marketing — M-002 — moved to in-progress — local partnerships kicked off
- 2026-04-17 — finance — F-002 — added — Series A prep begins
