# the-gooning-company

If the AI handles ur biz ops, u have more time to goon.

A router + three domain agents (**Product / UX**, **Marketing**, **Finance**) built on [OpenHarness](https://github.com/HKUDS/OpenHarness). Founders chat with the router; the router brokers cascades between the domain agents so changes in one function automatically surface where they matter in the others.

## Read first

| If you are... | Read |
|---------------|------|
| **Trying to run it** | [`RUNNING.md`](RUNNING.md) ← zero-to-working guide |
| New to the project | [`AGENTS.md`](AGENTS.md) |
| New to OpenHarness | [`dev-concepts/implementation.md`](dev-concepts/implementation.md) section 2 |
| About to write code | [`dev-concepts/implementation.md`](dev-concepts/implementation.md) section 8 (your track) |
| Filling in a PRD stub | [`Product-requirement-doc/`](Product-requirement-doc/README.md) |
| Looking for invariants | [`dev-concepts/README.md`](dev-concepts/README.md) |

## Repo layout

```
workspaces/
  _shared/                 # committed, read by all four agents
    base-system.md         # -> extra_prompt for every agent
    user.md                # founder profile; each workspace symlinks to this
    skills/                # shared playbooks (on-demand)
    mcp.json               # shared MCP server fragment, merged at launch
  router/                  # the-gooning-company (founder entrypoint)
  product/                 # Product / UX
  marketing/               # Marketing
  finance/                 # Finance
state/
  roadmap.md               # shared kanban artifact (product is sole writer)
  cascade-trace.jsonl      # run log (gitignored)
tools/
  mock_mcp/                # mock MCP server scaffold (transport TODO)
orchestrator/
  config.py                # resolves workspaces + merges shared MCP
  launch.py                # preflight + MCP boot + router/teammate spawn
```

Each agent workspace has the ohmo shape: `soul.md`, `identity.md`, `BOOTSTRAP.md`, `user.md` (symlink), `memory/` (with `god.md` + `MEMORY.md`), `skills/`, `plugins/`, `settings.json`, `gateway.json`.

## Getting it running

See **[`RUNNING.md`](RUNNING.md)** for the full zero-to-working walkthrough: prerequisites, first-time setup, which files to fill in, smoke paths that work today without any LLM credentials, and the exact `TODO(glue)` points that need to land before `python3 -m orchestrator.launch` boots the whole system.

Every TODO in the scaffold is tagged with its owner:

- `TODO(glue)` — wiring / arch decisions (transport, spawn API, model/provider).
- `TODO(product-owner)` / `TODO(marketing-owner)` / `TODO(finance-owner)` — domain content.

No secrets in the repo. Configure provider credentials per machine via env vars; see [`RUNNING.md`](RUNNING.md) §5.7.
