# Mock MCP server

A single MCP server exposing **mocked** tools in four domain namespaces:

- `product.*`
- `marketing.*`
- `finance.*`
- `roadmap.*` (owned by Product; readable by everyone)

Optional:

- `router.*` — only if the router genuinely needs tool-backed operations beyond `SendMessage`.

## Status

Scaffold only. Transport is intentionally **not** picked yet — that is a "glue" decision. Each domain module exports tool **specs** (name, description, JSON-schema-ish input, mock handler). Wire them to the chosen MCP stack in `server.py` once decided.

> TODO(glue): pick transport + MCP framework. OpenHarness v0.1.5+ prefers HTTP. Candidates: `fastmcp`, `aiohttp`, plain `starlette`.

## Adding a tool

1. Open the right domain file in `tools/`.
2. Append a `ToolSpec(...)` entry to the module-level `TOOLS` list.
3. Implement the `handler` as an `async def` that returns a JSON-serialisable dict. Mocked payloads are fine.
4. Restart the server.

## Namespaces and ownership

| Namespace | Who may call | Mutates `state/roadmap.md`? |
|-----------|--------------|------------------------------|
| `product.*` | product agent | no (uses `roadmap.*` for that) |
| `marketing.*` | marketing agent | no |
| `finance.*` | finance agent | no |
| `roadmap.read_*` | product, marketing, finance, router | no |
| `roadmap.add / move / reprioritize / drop` | **product only** | yes |
| `router.*` (optional) | router only | no |

Enforcement is per-workspace via `settings.json` `tools` and `permissions`; the server should *also* check, defence-in-depth.
