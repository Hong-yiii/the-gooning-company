# OpenHarness workspaces

This folder contains starter in-repo workspace files aligned with the OpenHarness/ohmo direction documented in `dev-concepts/README.md` and `dev-concepts/implementation.md`.

## Included now
- `_shared/` — shared base system, founder profile, and MCP config fragment
- `router/` — founder-facing router
- `marketing/` — router-visible Marketing endpoint implemented as Marketing Lead

## Marketing internal structure
Marketing is represented externally by the Marketing Lead. Specialist roles are documented as Marketing-local skills/playbooks:
- Content Strategist
- Performance Marketer
- Marketing Ops / Analyst

## Notes
- This is still a scaffold, not a full long-running OpenHarness deployment.
- Product and Finance workspace files are not scaffolded yet.
- The previous `agents/` folder has been superseded by this `workspaces/` structure.
