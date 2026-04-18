# `state/` — shared run state

Two artifacts live here:

| File | Owner | Readers | Git |
|------|-------|---------|-----|
| `roadmap.md` | `product` (sole writer) | `product` (rw), `marketing` + `finance` + `router` (read) | **committed** |
| `cascade-trace.jsonl` | Router hook (append-only) | All agents + dashboard | gitignored |

`cascade-trace.jsonl` is regenerated each run. Do not commit it. One JSON object per line, written by the router's `PostToolUse` hook after every `SendMessage` and after every `roadmap.*` mutation. Schema TBD in `dev-concepts/implementation.md`.
