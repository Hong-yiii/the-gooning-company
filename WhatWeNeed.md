# What we need — Marketing phase

This list is derived from [`Product-requirement-doc/marketing.md`](Product-requirement-doc/marketing.md), [`router.md`](Product-requirement-doc/router.md), [`product.md`](Product-requirement-doc/product.md), and [`finance.md`](Product-requirement-doc/finance.md). All cascades are **router-brokered** (no Marketing → Finance peer calls in spec).

---

## 1. Lock the spec (Marketing owner)

- [ ] Replace placeholder status in `Product-requirement-doc/marketing.md` with **concrete**:
  - Exact `marketing.*` tool names, arguments, and return shapes (mock OK).
  - Whether Marketing uses **read-only** `roadmap.*` tools — align with Product (`product.md` says Product owns mutating `roadmap.*`).
- [ ] Resolve **open question** in `marketing.md`: which outbound events **always** go to Finance vs only above a threshold (document numbers or rule-of-thumb for the demo).
- [ ] Agree **event names + JSON payloads** with whoever owns `router.md` (router still says “define in a follow-up pass”).

---

## 2. Private `god.md` (Marketing)

- [ ] Create the real file path the app will use (e.g. `god-md/marketing.md` — match `dev-concepts` if defined).
- [ ] Seed sections: campaign briefs, channel plans, narrative, experiments — per `marketing.md` **Private god.md**.
- [ ] **Update rules:** Marketing writes **its** `god.md` only; it does **not** edit Product’s `god.md`; roadmap gaps go **through the router** to Product (`marketing.md`).

---

## 3. Cascade — inbound (what Marketing must handle)

- [ ] **Roadmap updates:** router delivers summaries originating from Product’s `roadmap.changed` fan-out — Marketing agent (or MCP layer) should refresh context before answering GTM questions.
- [ ] **Founder / router requests:** launches, positioning, messaging — classify and respond using roadmap + Marketing `god.md`.

---

## 4. Cascade — outbound (what Marketing must emit via router)

- [ ] **`marketing.campaign_started`** (or the name you standardize on): router forwards to **Finance** for spend / projections (`finance.md` cascade inbound).
- [ ] **`marketing.issue_raised`** (or equivalent): router forwards to **Product** when Marketing surfaces roadmap gaps or conflicts (`marketing.md` outbound).
- [ ] Ensure router fan-out rules are documented in `router.md` once payloads exist.

---

## 5. Integration checklist (connect code at the end)

- [ ] Router: intent → **dispatch.marketing** with enough context (recent roadmap summary, founder ask).
- [ ] Marketing harness: registers `marketing.*` MCP tools (mock implementations acceptable per `AGENTS.md`).
- [ ] On tool side effects that matter to others: emit structured events **back to router** (not directly to Finance/Product).
- [ ] Dashboard / demo script: at least one path **roadmap change → router → Marketing** and one path **campaign start → router → Finance**.

---

## 6. Dependencies on teammates (unblock Marketing)

| Dependency | Owner | Why |
|------------|--------|-----|
| Shared roadmap schema + `roadmap.changed` summary shape | Product + router | Marketing inbound cascade |
| `dispatch.marketing` + fan-out rules | Router | All cross-agent traffic |
| Finance tool stubs + what they need on `campaign_started` | Finance | Mock runway / cost |

---

## 7. Nice-to-have after core path works

- [ ] Link from [`Product-requirement-doc/README.md`](Product-requirement-doc/README.md) if file names or event catalog move.
- [ ] Short paragraph in `dev-concepts` for event log vs in-memory bus (if the team adds it).
