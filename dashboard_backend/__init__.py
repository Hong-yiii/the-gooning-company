"""Dashboard HTTP backend for the-gooning-company.

Serves the React SPA (built from ``dashboard/``) together with a JSON API
and SSE stream that surface live views of:

* the shared roadmap (parsed from ``state/roadmap.md``),
* each agent's private ``god.md`` living doc,
* the cascade trace (JSONL emitted by the mock MCP server on every tool
  call),
* chat-with-the-router, implemented by spawning a short-lived
  ``ohmo --print`` subprocess per message and streaming stdout back.

Why Starlette and not FastAPI?
    Starlette is already transitively installed via ``mcp`` and is all we
    need for a tiny JSON + SSE surface. Keeping the dep floor small.
"""
