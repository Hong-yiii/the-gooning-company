# the-gooning-company

If the AI handles ur biz ops, u have more time to goon

## Current scaffold status

This repo now includes a starter runnable scaffold for:
- a founder-facing router
- a router-visible Marketing Lead
- private marketing specialists documented as Marketing-local playbooks
- a mock MCP-style HTTP server
- a simple scripted router -> marketing flow demo

## Folders

- `workspaces/` — starter in-repo OpenHarness workspace files
- `Product-requirement-doc/` — agent contracts
- `dev-concepts/` — architecture and schema docs
- `tools/mock_mcp/` — runnable mock MCP server
- `orchestrator/` — runnable demo flow and future launch wiring

## Run the demo

Run the launcher in probe mode:

```bash
python3 orchestrator/launch.py
```

Try real ohmo process spawn mode:

```bash
python3 orchestrator/launch.py --ohmo
```

Start the mock MCP server in one terminal:

```bash
python3 tools/mock_mcp/server.py
```

Then run the marketing flow in another terminal:

```bash
python3 orchestrator/demo_marketing_flow.py
```

## What the demo does

- router classifies a founder request as Marketing
- Marketing Lead reads a mocked roadmap item
- Marketing Lead delegates work to mocked internal specialists
- Marketing Lead creates a campaign and spend request via the mock MCP server
- Marketing returns a final `marketing.plan_ready` event to the router

## Important limitation

This is a scaffolded demo flow, not a full OpenHarness deployment yet.
It does not yet include:
- Product runtime
- Finance runtime
- successful authenticated LLM-backed ohmo sessions by default
- real dashboard integration
- swarm mailbox wiring
- full workspace bootstrapping (permissions, sessions/log handling) for every domain
