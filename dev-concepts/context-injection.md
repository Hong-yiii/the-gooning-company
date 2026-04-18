# Context injection and runtime scaffold

This document describes the current starter runtime shape for the repo.

## Current scaffold

The runnable demo uses in-repo workspace files plus lightweight Python subprocess launching rather than full OpenHarness process orchestration.

## Agent workspace paths

- `workspaces/_shared/`
- `workspaces/router/`
- `workspaces/marketing/`

## Loaded context per agent

### Shared
- `workspaces/_shared/base-system.md`
- `workspaces/_shared/user.md`
- `workspaces/_shared/mcp.json`

### Router
- `workspaces/router/soul.md`
- `workspaces/router/identity.md`
- `workspaces/router/BOOTSTRAP.md`
- `workspaces/router/memory/god.md`
- `workspaces/router/settings.json`

### Marketing Lead
- `workspaces/marketing/soul.md`
- `workspaces/marketing/identity.md`
- `workspaces/marketing/BOOTSTRAP.md`
- `workspaces/marketing/memory/god.md`
- `workspaces/marketing/settings.json`

### Marketing specialists
- specialist roles are currently documented as Marketing-local skills in `workspaces/marketing/skills/`
- they are modeled in the demo as functions inside `orchestrator/demo_marketing_flow.py`

## Runtime phases

1. `orchestrator/launch.py` starts lightweight router and marketing workspace processes
2. founder sends request to router
3. router classifies domain
4. router dispatches to Marketing Lead
5. Marketing Lead consults roadmap via mock MCP server
6. Marketing Lead delegates to internal specialists
7. Marketing Lead creates campaign + spend request through mock MCP endpoints
8. Marketing Lead returns a domain event to router

## Next step toward OpenHarness

To convert this scaffold into true OpenHarness runtime:
- replace lightweight subprocess launch with actual OpenHarness / ohmo backend startup
- wire shared and per-workspace context loading into actual OpenHarness startup
- replace function-based sub-agents with actual agent tasks or teammate processes
- register the mock server as a real MCP endpoint
- add router dispatch through OpenHarness messaging primitives
