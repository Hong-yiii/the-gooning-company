# Dev concepts — implementation invariants

Companion to root [`AGENTS.md`](../AGENTS.md). **Product** contracts live in [`../Product-requirement-doc/`](../Product-requirement-doc/README.md).

---

## 1. Agent workspace layout (ohmo-shaped)

Each of the four agents runs in an **isolated** long-lived workspace (mirror OpenHarness **ohmo** layout conceptually):

| Path (per agent) | Purpose |
|------------------|---------|
| `soul.md` / `identity.md` | Personality and role boundary |
| `user.md` (if applicable) | Founder prefs when scoped per agent |
| `memory/` | Durable memory across sessions |
| `god.md` | **Private** living doc for that agent’s worldview (see below) |
| `gateway.json` (or equivalent) | Provider + channel config for that process |

Exact paths and filenames follow OpenHarness docs when wiring `ohmo` / harness config.

---

## 2. Cascade invariant: router-brokered only

- **No peer-to-peer** messages between Product, Marketing, and Finance.
- Domain agents return structured outcomes to **`the-gooning-company`**; the router performs **fan-out** and **summarization** for the next hop.
- Implementation options (pick one later): gateway hub, shared message queue, or harness `SendMessage` only from router identities — document the choice here once implemented.

---

## 3. Shared roadmap artifact vs `god.md`

| Artifact | Visibility | Owner (writes) |
|----------|------------|------------------|
| Shared roadmap file | All agents read; dashboard shows kanban | **Product** via `roadmap.*` MCP tools only |
| `god.md` | **Private** to that agent; founders see via dashboard observability | That agent only |

**Format TBD:** `roadmap.md` (human-first) vs `roadmap.json` (machine-first) vs split (JSON source + generated MD). Decision and schema version live in a follow-up doc under this folder (e.g. `roadmap-schema.md`).

---

## 4. MCP tool server: one server, namespaced tools

- **One** mock MCP process for the hackathon.
- Tool names use prefixes: `product.*`, `marketing.*`, `finance.*`, `roadmap.*`, optional `router.*`.
- Responses are **mocked** but should match **stable JSON shapes** once schemas are defined alongside Product-requirement-doc events.

---

## 5. `god.md` and harness context injection

- OpenHarness discovers and injects project context (e.g. **`CLAUDE.md`**, **`MEMORY.md`**) per harness conventions; align `god.md` with **“always load for this agent”** via agent-specific workspace root or `--append-system-prompt` / plugin hooks — **exact mechanism TBD** when wiring `oh`.
- **Invariant:** `god.md` is not a substitute for the shared roadmap file; roadmap rows are not duplicated as the source of truth.

---

## 6. Dashboard observability

- **Read-only** views of each `god.md` and the shared roadmap for founders.
- **Cascade trace:** append-only or queryable log of router dispatches (timestamp, from-agent, to-agent, event type, redacted payload).
- Chat attaches to **router** gateway only unless product decision says otherwise.

---

## Follow-up docs (optional stubs)

Add as needed:

- `roadmap-schema.md` — columns, IDs, domain tags, state machine.
- `mcp-tool-registry.md` — full list of tool names + JSON schemas.
- `context-injection.md` — exact OpenHarness flags / files per agent process.
