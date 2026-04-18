# Agent spec: Marketing

## Role

Marketing is represented externally by a **Marketing Lead** who owns campaigns, positioning, launch planning, and the final marketing point of view delivered to the router. The lead reads the shared roadmap, turns product changes into go-to-market plans, and surfaces roadmap gaps or budget implications back through the router. Internally, the lead may orchestrate specialist sub-agents to do the work of a normal marketing team, but only the lead speaks for the Marketing domain.

## Private god.md

- The Marketing Lead owns Marketing’s private `god.md`.
- It stores campaign briefs, narrative decisions, experiment summaries, launch plans, KPI notes, and unresolved risks.
- It does **not** replace the shared roadmap as the source of truth for product delivery.
- Internal sub-agents may draft material for inclusion, but the lead is the final approver for durable updates.

## MCP tools (namespaced)

Lead-level tools:
- `marketing.create_campaign` — create a campaign record with objective, audience, channels, owner, and status.
- `marketing.update_campaign` — update campaign scope, timing, messaging, or status.
- `marketing.list_campaigns` — inspect current and past campaigns.
- `marketing.get_metrics` — return mocked marketing KPIs and campaign performance snapshots.
- `marketing.record_experiment` — save experiment setup and outcome summary.
- `marketing.submit_spend_request` — produce a structured spend request for router handoff to Finance.
- `roadmap.list_items` — read shared roadmap items relevant to launches or messaging.
- `roadmap.get_item` — inspect a specific roadmap item and its status.

Internal specialist responsibilities may be implemented as sub-agents rather than MCP tools. If explicit internal tools are needed later, they should remain Marketing-private.

## Internal team structure

### Marketing Lead
- Router-facing owner of the Marketing domain.
- Prioritizes work, delegates to specialists, reconciles tradeoffs, and approves final outputs.
- Owns domain-level outbound events and `god.md` updates.

### Content Strategist
- Drafts campaign messaging, content briefs, editorial ideas, landing-page copy direction, and launch materials.

### Performance Marketer
- Proposes acquisition experiments, paid channel plans, budget allocations, and funnel improvement ideas.

### Brand / Positioning Strategist
- Sharpens ICP, value proposition, differentiation, and launch narrative for roadmap changes.

### Social / Community Manager
- Creates social distribution plans, community motions, launch cadence, and audience engagement ideas.

### Marketing Ops / Analyst
- Summarizes KPIs, experiment results, reporting cadence, and attribution assumptions for decision-making.

### Delegation and approval rules
- The router talks only to the **Marketing Lead**.
- Sub-agents may work in parallel under the lead for specialist tasks.
- Sub-agents do not directly message Product, Finance, or the router.
- Sub-agents do not emit domain-level cascade events.
- The lead approves final campaign plans, spend requests, roadmap feedback, and persistent memory updates.

## Cascade — inbound

Router may deliver:
- `roadmap.updated` — summarized product changes that affect messaging, launches, or demand generation.
- `founder.request_launch_plan` — request for launch strategy around a roadmap item or date.
- `founder.request_campaign` — request for a campaign, channel plan, or messaging work.
- `product.launch_date_changed` — timeline change requiring revised marketing timing.
- `finance.ask_spend_justification` — request for rationale, expected outcomes, or tradeoffs behind marketing spend.

## Cascade — outbound

Only the Marketing Lead returns these outcomes to the router:
- `marketing.plan_ready` — complete GTM or launch plan ready for founder review.
- `marketing.campaign_ready` — campaign proposal or updated campaign package is ready.
- `marketing.spend_request` — marketing requests budget or spend approval from Finance.
- `marketing.product_feedback` — messaging or demand evidence suggests a roadmap gap, dependency, or launch risk for Product.
- `marketing.performance_report` — experiment or campaign results summarized for founder and Finance visibility.
- `marketing.blocker_raised` — marketing cannot proceed due to missing product clarity, timing, assets, or budget.

## Open questions

- Which spend thresholds should always trigger Finance review versus simple notification?
- Should the first implementation model all specialist roles as explicit agents, or start with Lead + 3 core specialists (content, performance, ops)?
- Which KPI schema should `marketing.get_metrics` return so Finance and dashboard views stay stable?
