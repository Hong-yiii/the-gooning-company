# Marketing agent — scope, tools, and integration contracts

This document is the **single source of truth** for the Marketing slice of the hackathon harness. Implementers (router, roadmap UI, MCP mocks) should treat sections **5–7** as the wiring checklist.

---

## 1. Purpose

- Turn product and company direction into **coherent messaging and campaigns** (mocked tools OK).
- **Consume** roadmap/product changes; **emit** campaign and escalation events so Finance and Product stay aligned (`AGENTS.md`).

---

## 2. Ownership: Marketing `god md`

**File (suggested path):** `god-md/marketing.md` (exact path to match whatever the repo standardizes on).

**Minimum sections (living doc):**

| Section | Purpose |
|---------|---------|
| Positioning & ICP | Who we sell to; one-liner |
| Narrative / pillars | 3–5 message pillars |
| Channel strategy | Where we show up (mock is fine) |
| Active & planned campaigns | Name, dates, goal, status |
| Dependencies on Product | Features/launches we message |
| Open risks / roadmap asks | Problems Marketing raises to the roadmap |

**Update rule:** Any tool that “starts a campaign,” “updates positioning,” or “flags a roadmap issue” should **append or patch** this file (or call a shared writer that does), so the dashboard “god md observability” stays honest.

---

## 3. System prompt (high level — for whoever configures OpenHarness)

- Role: Marketing lead for the company; concise; cite internal state (`god md`, roadmap) before inventing details.
- Boundaries: No real spend authority — campaign objects carry **budget hints** for Finance; final numbers are Finance’s domain.
- Always log **structured events** (see §7) when campaigns change state or when Marketing escalates to the roadmap.

*(Full prompt text can live in repo `prompts/marketing.md` when the team adds it.)*

---

## 4. Tools (MCP / tool server — mock data acceptable)

Expose **clear names** so the router and other agents can reason about them. Suggested set:

| Tool name | Input (conceptual) | Output (conceptual) | Side effects |
|-----------|-------------------|---------------------|----------------|
| `marketing.get_god_md` | — | Current marketing `god md` text or JSON | Read only |
| `marketing.upsert_campaign` | `id`, `name`, `start`, `end`, `goal`, `channels[]`, `budget_estimate` | Campaign record | Append campaign; **emit** `campaign.updated` |
| `marketing.list_campaigns` | optional `status` | List of campaigns | Read only |
| `marketing.raise_roadmap_issue` | `title`, `description`, `severity`, `suggested_column` | Ticket/issue id (mock) | **Emit** `roadmap.issue_raised` for Product/router |
| `marketing.sync_from_roadmap` | roadmap snapshot or diff | Summary of marketing-relevant changes | Updates local view / `god md` “Dependencies on Product” |

Finance-relevant fields on campaigns: `budget_estimate`, `start`, `end`, `channels` — enough for mock projections.

---

## 5. Inputs (what Marketing must accept from the system)

| Source | Event / data | Expected behavior |
|--------|----------------|-------------------|
| Product / roadmap | Roadmap item created/updated/moved | `marketing.sync_from_roadmap` or equivalent; refresh “Dependencies”; optionally draft message angles (mock) |
| Router | User asks for GTM, copy, campaign plan | Read `god md` + roadmap; respond; call tools if creating/updating artifacts |
| Finance | _(optional)_ Budget constraint message | Adjust campaign recommendations or flag conflicts in `god md` |

**Payload shape (suggested JSON, for shared bus or files):**

```json
{
  "type": "roadmap.updated",
  "version": 1,
  "timestamp": "ISO-8601",
  "diff": { "added": [], "updated": [], "removed": [] }
}
```

Marketing implementation should tolerate **extra fields** without breaking.

---

## 6. Outputs (what Marketing must emit for others)

| Consumer | Event / artifact | When |
|----------|------------------|------|
| Finance | `campaign.updated` | Campaign created/updated; include `budget_estimate`, dates, status |
| Product / roadmap | `roadmap.issue_raised` | Marketing raises blocker/opportunity (see tool above) |
| Dashboard | `god md` file + optional event log | Any material change |

**Suggested `campaign.updated` payload:**

```json
{
  "type": "campaign.updated",
  "version": 1,
  "timestamp": "ISO-8601",
  "campaign": {
    "id": "string",
    "name": "string",
    "status": "draft|active|paused|ended",
    "start": "ISO-8601",
    "end": "ISO-8601",
    "budget_estimate": { "currency": "USD", "amount": 0 },
    "channels": ["string"]
  }
}
```

**Suggested `roadmap.issue_raised` payload:**

```json
{
  "type": "roadmap.issue_raised",
  "version": 1,
  "timestamp": "ISO-8601",
  "issue": {
    "title": "string",
    "description": "string",
    "severity": "low|medium|high",
    "suggested_column": "optional string"
  },
  "source_agent": "marketing"
}
```

Implementation note: for the hackathon, **JSONL append-only log** or **shared `events/` folder** is enough if there is no message bus yet.

---

## 7. Integration checklist (for “connecting the code in the end”)

- [ ] `god-md/marketing.md` exists and is read/written by Marketing tools or a shared doc service.
- [ ] Tool names match §4 (or this doc is updated to match code).
- [ ] On roadmap change, something calls **sync** into Marketing (push from roadmap service **or** polling — document which).
- [ ] On campaign write, **Finance** receives `campaign.updated` (same process as other inter-agent events).
- [ ] On `raise_roadmap_issue`, Product/router receives `roadmap.issue_raised`.
- [ ] Router agent prompt lists Marketing tools and when to delegate to Marketing.

---

## 8. Open decisions (fill in as a team)

- Exact file paths for `god md` and event log.
- Whether roadmap is **files**, **SQLite**, or **in-memory** for demo.
- Idempotency: e.g. `campaign.id` required on updates.

---

*Last updated: hackathon scaffold — extend when Product/Finance docs land.*
