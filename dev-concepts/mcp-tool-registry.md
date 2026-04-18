# MCP tool registry and event schemas

Defines stable mock contracts for hackathon implementation. Domain agents may use richer private prompts internally, but cross-domain and dashboard-facing data should follow these shapes.

---

## 1. Naming conventions

- Shared roadmap tools: `roadmap.*`
- Domain tools: `product.*`, `marketing.*`, `finance.*`
- Router-facing events use `<domain>.<event_name>`
- Only router-visible domain leads emit cross-domain events

---

## 2. Shared envelope

All router-delivered events and domain-returned outcomes should fit this envelope:

```json
{
  "event_type": "marketing.plan_ready",
  "source": "marketing",
  "target": "router",
  "timestamp": "2026-04-18T12:00:00Z",
  "correlation_id": "evt_123",
  "payload": {}
}
```

### Required fields
- `event_type`: stable event identifier
- `source`: emitting domain (`router`, `product`, `marketing`, `finance`)
- `target`: intended receiver
- `timestamp`: ISO-8601 string
- `correlation_id`: ties related work across cascades
- `payload`: event-specific object

---

## 3. Marketing tool schemas

## `marketing.create_campaign`
Create a campaign record.

### Input
```json
{
  "name": "Spring launch",
  "objective": "Acquire waitlist signups",
  "audience": "Seed-stage founders",
  "channels": ["x", "email", "landing_page"],
  "owner": "marketing_lead",
  "start_date": "2026-05-01",
  "end_date": "2026-05-21"
}
```

### Output
```json
{
  "campaign_id": "mkt_cmp_001",
  "status": "draft",
  "created_at": "2026-04-18T12:00:00Z"
}
```

## `marketing.update_campaign`

### Input
```json
{
  "campaign_id": "mkt_cmp_001",
  "status": "active",
  "channels": ["x", "email"],
  "message": "Refined positioning for launch week"
}
```

### Output
```json
{
  "campaign_id": "mkt_cmp_001",
  "status": "active",
  "updated_at": "2026-04-18T12:30:00Z"
}
```

## `marketing.list_campaigns`

### Input
```json
{
  "status": "active"
}
```

### Output
```json
{
  "campaigns": [
    {
      "campaign_id": "mkt_cmp_001",
      "name": "Spring launch",
      "status": "active",
      "objective": "Acquire waitlist signups"
    }
  ]
}
```

## `marketing.get_metrics`

### Input
```json
{
  "campaign_id": "mkt_cmp_001",
  "window": "last_7_days"
}
```

### Output
```json
{
  "campaign_id": "mkt_cmp_001",
  "window": "last_7_days",
  "metrics": {
    "impressions": 12000,
    "clicks": 430,
    "signups": 39,
    "ctr": 0.0358,
    "cvr": 0.0907,
    "spend": 420.0,
    "cac": 10.77
  }
}
```

## `marketing.record_experiment`

### Input
```json
{
  "campaign_id": "mkt_cmp_001",
  "hypothesis": "Founder-led messaging beats product-led messaging",
  "channel": "landing_page",
  "variant_a": "Automate ops",
  "variant_b": "Delegate work to AI teams",
  "result_summary": "Variant B improved signup conversion by 18%"
}
```

### Output
```json
{
  "experiment_id": "mkt_exp_001",
  "saved": true
}
```

## `marketing.submit_spend_request`

### Input
```json
{
  "campaign_id": "mkt_cmp_001",
  "amount": 1500,
  "reason": "Paid test budget for launch week",
  "expected_outcome": "150 qualified signups",
  "time_horizon": "14_days"
}
```

### Output
```json
{
  "request_id": "mkt_spend_001",
  "status": "submitted"
}
```

---

## 4. Marketing event schemas

## `marketing.plan_ready`

```json
{
  "plan_id": "mkt_plan_001",
  "title": "Launch plan for onboarding revamp",
  "objective": "Drive awareness and waitlist conversions",
  "audience": ["startup founders", "operators"],
  "channels": ["x", "email", "landing_page"],
  "timeline": {
    "start_date": "2026-05-01",
    "launch_date": "2026-05-10",
    "end_date": "2026-05-21"
  },
  "dependencies": ["final product screenshots", "confirmed launch date"],
  "risks": ["positioning still in flux"]
}
```

## `marketing.campaign_ready`

```json
{
  "campaign_id": "mkt_cmp_001",
  "name": "Spring launch",
  "objective": "Acquire waitlist signups",
  "brief": "Narrative and channel package ready for execution",
  "channels": ["x", "email"],
  "budget_needed": 1500
}
```

## `marketing.spend_request`

```json
{
  "request_id": "mkt_spend_001",
  "campaign_id": "mkt_cmp_001",
  "amount": 1500,
  "reason": "Paid test budget for launch week",
  "expected_outcome": {
    "qualified_signups": 150,
    "target_cac": 10
  },
  "priority": "high"
}
```

## `marketing.product_feedback`

```json
{
  "related_roadmap_item_id": "rdm_024",
  "feedback_type": "launch_risk",
  "summary": "Messaging is blocked by unclear differentiation",
  "evidence": ["landing-page test confusion", "founder interviews"],
  "requested_action": "Clarify target persona and primary use case"
}
```

## `marketing.performance_report`

```json
{
  "campaign_id": "mkt_cmp_001",
  "window": "last_7_days",
  "summary": "CTR healthy, signup conversion below target",
  "metrics": {
    "impressions": 12000,
    "clicks": 430,
    "signups": 39,
    "spend": 420.0,
    "cac": 10.77
  },
  "recommendation": "Shift budget toward email retargeting"
}
```

## `marketing.blocker_raised`

```json
{
  "blocker_type": "missing_asset",
  "severity": "medium",
  "summary": "Launch copy is ready but product screenshots are not",
  "needed_from": "product",
  "impact": "Launch timeline at risk"
}
```

---

## 5. Roadmap read tool shapes

## `roadmap.list_items`

### Input
```json
{
  "status": "planned",
  "domain": "marketing"
}
```

### Output
```json
{
  "items": [
    {
      "roadmap_item_id": "rdm_024",
      "title": "Onboarding revamp",
      "status": "planned",
      "owner": "product",
      "target_date": "2026-05-10"
    }
  ]
}
```

## `roadmap.get_item`

### Input
```json
{
  "roadmap_item_id": "rdm_024"
}
```

### Output
```json
{
  "roadmap_item_id": "rdm_024",
  "title": "Onboarding revamp",
  "status": "planned",
  "summary": "Improve first-run activation",
  "owner": "product",
  "target_date": "2026-05-10",
  "notes": ["Marketing launch support required"]
}
```

---

## 6. Notes

- These shapes are intentionally small and stable.
- Add product and finance schemas in the same style when those domains are expanded.
- Dashboard rendering should prefer these stable fields over freeform agent prose.
