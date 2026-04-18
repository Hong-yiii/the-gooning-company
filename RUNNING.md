# Running the-gooning-company from zero

This is the operational guide. If you want the product pitch, read [`README.md`](README.md); if you want the concepts, read [`AGENTS.md`](AGENTS.md) and [`dev-concepts/`](dev-concepts/README.md).

One command — `python -m orchestrator.launch` — boots the whole system once you have `.env` filled in:

1. Loads `.env` (OpenAI key + model).
2. Writes `state/.openharness/settings.json` + `state/.openharness/agents/{product,marketing,finance}.md` and points `$OPENHARNESS_CONFIG_DIR` at that dir so OpenHarness reads our config instead of `~/.openharness`.
3. Starts the mock MCP server as a subprocess (Streamable-HTTP on `127.0.0.1:8765/mcp`).
4. Launches `ohmo --workspace workspaces/router` interactive against that config. The router can delegate to `product` / `marketing` / `finance` by name via the builtin `agent` tool.

Two smoke paths that run without an API key and without OpenHarness-level plumbing are still documented in §3 — use them to confirm the scaffold is intact before you hit OpenAI.

---

## 1. Prerequisites

| Need | Why |
|------|-----|
| Python **3.11+** | `pyproject.toml` pins `requires-python = ">=3.11"`. |
| `git` | You are reading this inside a git repo. |
| macOS or Linux | `workspaces/<role>/user.md` is a symlink to `workspaces/_shared/user.md`. On Windows you need `core.symlinks=true` or run under WSL. |
| An LLM provider API key | OpenAI / Anthropic / whichever OpenHarness provider you wire in step 5. Only needed once you run the real agent loop — not for the smoke paths. |

Check:

```bash
python3 --version            # 3.11+
git --version
ls -la workspaces/router/user.md  # should print ... -> ../_shared/user.md
```

---

## 2. First-time setup

Using [`uv`](https://github.com/astral-sh/uv) (recommended):

```bash
git clone <this repo>
cd the-gooning-company

uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Or with stdlib tooling:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

What this installs:

- `openharness-ai>=0.1.6,<0.2` — the harness. Ships `oh` + `ohmo` CLIs.
- `mcp>=1.8,<2` — MCP Python SDK, used by the mock server (`FastMCP` + streamable-http).
- `python-dotenv` — loads `.env` at orchestrator startup.
- `pytest` + `ruff` — the `dev` extra.

Then copy the env template and fill in your OpenAI key:

```bash
cp .env.example .env
# edit .env and set OPENAI_API_KEY (rotate regularly; never commit)
```

`.env` is gitignored. The orchestrator reads it before any OpenHarness code touches `os.environ`.

---

## 3. Smoke test — things that work today without any config

These commands don't need OpenHarness installed and don't touch any LLM provider. Run them first to confirm the scaffold is intact.

### 3.1 Mock MCP server

```bash
# List every registered mock tool with its allowed callers.
python3 -m tools.mock_mcp.server --list

# Run every handler with {} to confirm no crashes.
python3 -m tools.mock_mcp.server --smoke

# Dump JSON-schema-ish tool definitions.
python3 -m tools.mock_mcp.server --dump-schema
```

Expected: 13 tools across `product.*`, `marketing.*`, `finance.*`, `roadmap.*`.

### 3.2 Orchestrator config resolution

```bash
# Shows the router + three teammates it found, plus shared paths.
python3 -m orchestrator.launch --describe

# Shows each agent's settings.json with workspaces/_shared/mcp.json merged in.
python3 -m orchestrator.launch --dump-settings
```

If either command prints `preflight failed`, see §7.

---

## 4. The full picture of what you'll run

```bash
python -m orchestrator.launch
```

That command:

1. Loads `.env`; refuses to start if `OPENAI_API_KEY` is unset.
2. Reads every `workspaces/<role>/` into a typed config.
3. Preflights that `soul.md`, `identity.md`, `BOOTSTRAP.md`, and `state/roadmap.md` exist.
4. Writes `state/.openharness/settings.json` (provider profile + mcp_servers + path rules) and `state/.openharness/agents/{product,marketing,finance}.md` (AgentDefinition per teammate, body = shared base-system + role soul + role identity + role `memory/god.md`).
5. Points `$OPENHARNESS_CONFIG_DIR` at `state/.openharness/` so OpenHarness/ohmo load the generated config instead of `~/.openharness/`.
6. Starts the mock MCP server as a subprocess on `127.0.0.1:8765/mcp` (Streamable HTTP).
7. Execs `ohmo --workspace workspaces/router --profile gooning-openai --model $GOONING_MODEL` — that's your founder-facing interactive session.

Delegation: the router's built-in `agent` tool can spawn `product` / `marketing` / `finance` by name. Each delegation is a **fresh subprocess** (upstream `SubprocessBackend.spawn` → `create_agent_task`) whose system prompt is the full AgentDefinition body — so god.md is re-read every time. Teammates never message each other; every cross-domain effect goes back through the router.

Useful modifiers:

```bash
python -m orchestrator.launch --describe          # dump resolved config, exit
python -m orchestrator.launch --dump-settings     # show per-agent settings (with shared MCP merged)
python -m orchestrator.launch --dump-composed     # write state/.openharness/ and show paths, exit
python -m orchestrator.launch --no-router         # bootstrap + MCP only; keep MCP up, ^C to stop
python -m orchestrator.launch --print "summarise the roadmap"  # non-interactive, one-shot to the router
```

---

## 5. Config files you must fill in before launching for real

Everything below is in the scaffold already; you are just filling in the blanks marked with HTML comments or `TODO(...)` tags.

### 5.1 Founder profile — `workspaces/_shared/user.md`

One file; symlinked into all four agent workspaces. Fill in:

- Name, timezone, languages.
- Preferred tone / answer length / decision style.
- Company + stage + current pressures.

No code changes needed — just edit the markdown.

### 5.2 Company-wide prompt — `workspaces/_shared/base-system.md`

Fill the `TODO` block at the bottom: company one-liner, top 3 strategic priorities, hard no-goes. This file is passed as `extra_prompt` to every agent (router + 3 teammates).

### 5.3 Per-agent persona — `workspaces/<role>/soul.md`

Each of `router`, `product`, `marketing`, `finance` has its own `soul.md` with a `TODO` section listing the contract decisions that role still owes (delta envelope, campaign outcome envelope, projection envelope, etc.).

### 5.4 Provider and model — `.env`

Model + API key live in `.env`, not in any committed file:

```bash
OPENAI_API_KEY=sk-...            # required; rotate regularly
GOONING_MODEL=gpt-5.4            # any OpenAI-served model id
OPENAI_BASE_URL=https://api.openai.com/v1   # override for Azure/OpenRouter/etc.
GOONING_MCP_HOST=127.0.0.1
GOONING_MCP_PORT=8765
```

The orchestrator composes a single `gooning-openai` provider profile from these values and writes it to `state/.openharness/settings.json`. If you need a non-OpenAI provider, edit `orchestrator/bootstrap.py::_build_settings` — there's one entry point for this.

The per-workspace `workspaces/<role>/settings.json` files are **intent documentation** now, not live config. Only their `permissions.path_rules` get merged into the composed settings; `model` / `tools` fields are unused (OpenHarness's `load_settings()` only reads `$OPENHARNESS_CONFIG_DIR/settings.json`).

Secrets never go into any committed file. `.gitignore` already covers `.env`, `**/.credentials*`, `**/auth.json`, `**/*.secret`, `**/*.token`.

### 5.5 Shared MCP URL — `workspaces/_shared/mcp.json`

Default is `http://127.0.0.1:8765/mcp`. You only need to change this if you run the mock server on a different port, or if you move it to another host.

### 5.6 Roadmap — `state/roadmap.md`

Seed it with one or two real rows before you launch, so the agents have something to read on first turn. Only the `product` agent will mutate it afterward.

---

## 6. How the boot actually works

The glue used to be three separate `TODO(glue)` wires. They're landed. Here's the current control flow so you can debug it when it breaks:

### 6.1 `.env` → orchestrator → OpenHarness config

`orchestrator/launch.py` calls `orchestrator.bootstrap.run_bootstrap(cfg)` before it touches OpenHarness. That function:

1. Calls `dotenv.load_dotenv(repo_root / ".env", override=False)`.
2. Reads `OPENAI_API_KEY`, `GOONING_MODEL`, `OPENAI_BASE_URL`, `GOONING_MCP_{HOST,PORT}`.
3. Composes a `settings.json` dict: one provider profile (`gooning-openai`), one MCP server entry pointing at the mock server URL (`x-agent` header templated per caller), and a `permissions.path_rules` section unioned across every workspace's `settings.json`.
4. Writes `state/.openharness/settings.json` and sets `os.environ["OPENHARNESS_CONFIG_DIR"]` to that directory. Upstream `load_settings()` only reads `$OPENHARNESS_CONFIG_DIR/settings.json` — nothing else is consulted.

### 6.2 AgentDefinition files — `state/.openharness/agents/{product,marketing,finance}.md`

Upstream's `AgentRegistry` globs `$OPENHARNESS_CONFIG_DIR/agents/*.md` and parses YAML frontmatter + markdown body into `AgentDefinition`. The body becomes the system prompt for any delegation to that agent.

`bootstrap._compose_agent_md` builds each file as:

```
---
name: product
description: Product / UX agent...
model: inherit
color: cyan
---

<contents of workspaces/_shared/base-system.md, H1 stripped>

<contents of workspaces/product/soul.md, H1 stripped>

<contents of workspaces/product/identity.md, H1 stripped>

<contents of workspaces/product/memory/god.md, H1 stripped>
```

Each delegation is a fresh subprocess — the god.md is read at spawn time, so edits between turns take effect on the next delegation.

### 6.3 Mock MCP server — `tools/mock_mcp/server.py`

`mcp.server.lowlevel.Server` + `StreamableHTTPSessionManager` serve the tool surface on `http://127.0.0.1:8765/mcp`.

- Tool listing, invocation, and JSON-schema introspection go through the low-level server's `list_tools` / `call_tool` decorators.
- Each request's `x-agent` HTTP header is read via the Starlette request context to attribute the call.
- `allowed_callers` is enforced **softly** by default (warning log on mismatch). Set `GOONING_STRICT_CALLERS=1` to flip to hard denial (raises `PermissionError`, surfaces as an MCP tool error to the caller).

### 6.4 Router session

After bootstrap + MCP startup, `launch.py` execs:

```
ohmo --workspace workspaces/router --profile gooning-openai --model $GOONING_MODEL
```

with `OPENHARNESS_CONFIG_DIR` and `OPENAI_API_KEY` inherited. Interactive founder chat runs here. Delegation uses the builtin `agent` tool — e.g. `agent(name="product", task="propose a roadmap delta …")`. Each call is a `SubprocessBackend.spawn(...)` that loads the AgentDefinition for that name, runs the teammate in its own subprocess, and streams the final reply back to the router.

---

## 7. Troubleshooting

### 7.1 `preflight failed; missing: ...`

`orchestrator.launch` checks that every workspace has `identity.md`, `soul.md`, `BOOTSTRAP.md`, and that `state/roadmap.md` exists. Missing files are listed. Usually means someone deleted a stub; restore from git.

### 7.2 `python3 -m orchestrator.launch --describe` shows fewer than four agents

`config.load_config()` globs `workspaces/*/`. If a teammate directory was renamed or the `router/` folder moved, fix the directory layout — everything in the orchestrator assumes `workspaces/router`, `workspaces/product`, `workspaces/marketing`, `workspaces/finance`.

### 7.3 `pip install -e ".[dev]"` fails on `openharness-ai`

Likely the package name on PyPI has changed, or the version range is wrong. Check the upstream README. Update `pyproject.toml` → `dependencies`. Don't bypass it with a local clone unless you have a specific reason (see [`dev-concepts/implementation.md`](dev-concepts/implementation.md) §5 on forking).

### 7.3a `OPENAI_API_KEY not set` on `python -m orchestrator.launch`

`.env` either doesn't exist or doesn't have the key. Copy `.env.example`, fill it in, rerun. Don't `export` it in your shell instead of using `.env` — the orchestrator intentionally reads the dotfile so both the launcher and the MCP subprocess and the `ohmo` subprocess all see the same value.

### 7.3b `ohmo: command not found`

You're not in the venv, or `openharness-ai` didn't install its console scripts. Activate the venv (`source .venv/bin/activate`) and rerun `uv pip install -e ".[dev]"`. Confirm with `which ohmo` — it should resolve inside `.venv/bin/`.

### 7.3c MCP tool calls fail with `caller 'unknown' not allowed for tool …`

Only happens when `GOONING_STRICT_CALLERS=1`. The `x-agent` header isn't being propagated by the MCP client — check that `state/.openharness/settings.json`'s `mcp_servers.gooning_mock.headers` includes `x-agent`. Fall back to soft mode (`unset GOONING_STRICT_CALLERS`) while debugging.

### 7.4 I think I committed a key

```bash
git log -p -S "<key prefix>"   # find the commit
```

Rotate the key **first**, then scrub history with `git filter-repo` or BFG. The `.gitignore` has `**/.credentials*`, `**/auth.json`, `**/*.secret`, `**/*.token` — add the file that leaked if it has a different name.

### 7.5 The mock MCP smoke test prints `! <tool>: <error>`

A handler crashed on empty args. Either the handler's mock needs to guard against missing keys, or the spec says a field is required and the smoke test is correctly catching it. Fix the handler to return a stub result; the smoke test deliberately calls with `{}`.

### 7.6 `workspaces/<role>/user.md` shows up as a regular file after `git clone`

Your git config is not preserving symlinks. Fix with:

```bash
git config core.symlinks true
git checkout -- workspaces/router/user.md workspaces/product/user.md workspaces/marketing/user.md workspaces/finance/user.md
```

Or on Windows, run under WSL.

---

## 8. Who does what

See [`dev-concepts/implementation.md`](dev-concepts/implementation.md) §8. Short version:

- **Marketing teammate** → `workspaces/marketing/**` + `tools/mock_mcp/tools/marketing.py`.
- **Finance teammate** → `workspaces/finance/**` + `tools/mock_mcp/tools/finance.py`.
- **Product / glue (you)** → `workspaces/product/**`, `workspaces/router/**`, `tools/mock_mcp/tools/{product,roadmap,router}.py`, `orchestrator/**`, `state/roadmap.md`, all `TODO(glue)` tags.

Every TODO in the scaffold is tagged with its owner:

- `TODO(glue)` — wiring / arch calls.
- `TODO(product-owner)` / `TODO(marketing-owner)` / `TODO(finance-owner)` — domain content.

Search for them with:

```bash
grep -rn "TODO(" --include='*.py' --include='*.md' --include='*.json' .
```
