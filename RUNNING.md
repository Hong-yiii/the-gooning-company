# Running the-gooning-company from zero

This is the operational guide. If you want the product pitch, read [`README.md`](README.md); if you want the concepts, read [`AGENTS.md`](AGENTS.md) and [`dev-concepts/`](dev-concepts/README.md).

Two things are true at the same time:

1. The **scaffold runs today** with only Python — you can inspect the MCP tool surface and the orchestrator's resolved config without installing OpenHarness or touching any API keys.
2. The **full agent loop** needs a few `TODO(glue)` wires to land first (transport pick, model/provider config, OpenHarness spawn calls). Those are called out below with the exact files that need editing.

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

```bash
git clone <this repo>
cd the-gooning-company

python3 -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

What this installs:

- `openharness-ai>=0.1.6,<0.2` — the harness (pin is loose on purpose; tighten once we have a known-good release).
- `pytest` + `ruff` — the `dev` extra.

> If the `openharness-ai` pip name is stale, confirm the current package name at [HKUDS/OpenHarness README](https://github.com/HKUDS/OpenHarness/blob/main/README.md) and update `pyproject.toml`. No guessing.

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

Once glue lands (§6), one command starts the whole system:

```bash
python3 -m orchestrator.launch
```

That command:

1. Reads every `workspaces/<role>/` into a typed config.
2. Preflights that `soul.md`, `identity.md`, `BOOTSTRAP.md`, and `state/roadmap.md` exist.
3. Starts the mock MCP server as a subprocess.
4. Spawns `product`, `marketing`, `finance` as swarm teammates under the router (via `openharness.swarm.SubprocessBackend`).
5. Runs the router (`the-gooning-company`) as the founder-facing ohmo session.

You talk to the router. It talks to the teammates. Teammates talk back via the file-backed swarm mailbox. No direct peer-to-peer.

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

### 5.4 Per-agent `settings.json` — model / provider

Open each `workspaces/<role>/settings.json`. The `"model"` block is an explicit `TODO(glue)` placeholder:

```json
"model": {
  "_comment": "TODO(glue): set provider/model..."
}
```

What to put there depends on which provider OpenHarness hands you. For the hackathon, prefer:

- **API key via environment variable**, not in the file. e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`.
- **Model id** in the file (`"provider": "openai", "model": "gpt-4o-mini"` etc. — match the actual OpenHarness schema).

Check the current settings schema at [HKUDS/OpenHarness `src/openharness/mcp/config.py`](https://github.com/HKUDS/OpenHarness/blob/main/src/openharness/mcp/config.py) and upstream docs before copy-pasting.

Secrets never go into `settings.json` or `gateway.json`. The repo-root `.gitignore` already ignores `**/.credentials*`, `**/auth.json`, `**/*.secret`, `**/*.token` defensively, but don't rely on it — keep keys in your shell environment.

### 5.5 Shared MCP URL — `workspaces/_shared/mcp.json`

Default is `http://127.0.0.1:8765/mcp`. You only need to change this if you run the mock server on a different port, or if you move it to another host.

### 5.6 Roadmap — `state/roadmap.md`

Seed it with one or two real rows before you launch, so the agents have something to read on first turn. Only the `product` agent will mutate it afterward.

### 5.7 Provider credentials — **never** in the repo

Put these in your shell before running the orchestrator:

```bash
export OPENAI_API_KEY=...
# or
export ANTHROPIC_API_KEY=...
```

If a teammate claims they committed a key, see §7.4.

---

## 6. TODO(glue) — what needs to land before `python3 -m orchestrator.launch` actually boots agents

The scaffold is intentionally one step short of running agents, so the wiring decisions happen in visible PRs. The three remaining glue points:

### 6.1 Mock MCP transport — `tools/mock_mcp/server.py`

- Pick the HTTP stack (`fastmcp` / `aiohttp` / `starlette`).
- Add it to `[project.optional-dependencies].mcp` in `pyproject.toml`.
- In `server.py`'s `main()`, iterate `reg.tools` and register each with the framework. Enforce `allowed_callers` before invoking `handler`.
- Bind to the URL from `workspaces/_shared/mcp.json`.

### 6.2 Teammate spawn — `orchestrator/launch.py`, function `_spawn_teammates`

The function already has the call shape in a docstring. Replace the `print` with:

```python
from openharness.swarm import SubprocessBackend, TeammateSpawnConfig, TeammateIdentity

backend = SubprocessBackend(...)
for a in cfg.teammates():
    backend.spawn(
        TeammateSpawnConfig(
            identity=TeammateIdentity(id=a.teammate_id, display_name=a.name),
            workspace=a.workspace,
            extra_prompt=cfg.shared_prompt_path.read_text(),
            extra_skill_dirs=[cfg.shared_skills_dir],
            settings_override=_effective_settings(cfg, a),
        )
    )
```

Confirm argument names against the pinned OpenHarness version — the shape above reflects the current upstream, not a guess.

### 6.3 Router session — `orchestrator/launch.py`, function `_run_router`

Replace the `print` with `ohmo.runtime.run_ohmo_backend(...)`, passing the same `extra_prompt`, `extra_skill_dirs`, and merged settings for the router workspace.

Once 6.1–6.3 are in, the command in §4 boots the whole system.

---

## 7. Troubleshooting

### 7.1 `preflight failed; missing: ...`

`orchestrator.launch` checks that every workspace has `identity.md`, `soul.md`, `BOOTSTRAP.md`, and that `state/roadmap.md` exists. Missing files are listed. Usually means someone deleted a stub; restore from git.

### 7.2 `python3 -m orchestrator.launch --describe` shows fewer than four agents

`config.load_config()` globs `workspaces/*/`. If a teammate directory was renamed or the `router/` folder moved, fix the directory layout — everything in the orchestrator assumes `workspaces/router`, `workspaces/product`, `workspaces/marketing`, `workspaces/finance`.

### 7.3 `pip install -e ".[dev]"` fails on `openharness-ai`

Likely the package name on PyPI has changed, or the version range is wrong. Check the upstream README. Update `pyproject.toml` → `dependencies`. Don't bypass it with a local clone unless you have a specific reason (see [`dev-concepts/implementation.md`](dev-concepts/implementation.md) §5 on forking).

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
