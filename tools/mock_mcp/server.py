"""Mock MCP server entry point.

Serves the transport-neutral :class:`ToolRegistry` over **Streamable HTTP**
using the official `mcp` SDK's lowlevel :class:`Server`, wrapped in a
:class:`StreamableHTTPSessionManager`, mounted on a tiny Starlette app at
``/mcp`` (the default path OpenHarness's MCP client expects).

Three operating modes via CLI:

* ``--list``         — print registered tools and exit (no transport).
* ``--smoke``        — run every handler with ``{}`` args (no transport).
* ``--dump-schema``  — dump the JSON-schema-ish tool definitions and exit.
* (no flag)          — bind HTTP server at ``$GOONING_MCP_HOST:$GOONING_MCP_PORT``
                       (defaults ``127.0.0.1:8765``) and serve Streamable HTTP.

Caller identity (x-agent header):
 OpenHarness's MCP client is configured per-workspace with a static
 ``x-agent`` header via ``McpHttpServerConfig.headers``. This server reads
 that header on every tool call and logs it to stderr as the attributed
 caller. Enforcement of :attr:`ToolSpec.allowed_callers` is **off by default**
 and enabled by ``GOONING_STRICT_CALLERS=1``. Rationale: OpenHarness loads
 ``settings.json`` once per process, so all four agents that share a
 ``~/.openharness/settings.json`` send the same header. Primary tool-gating
 is done client-side via each ``AgentDefinition.tools`` list; the header is
 informational + defence-in-depth once per-agent header injection is wired.
 Requests without an ``x-agent`` header are attributed to ``unknown`` and
 always allowed (smoke tests, curl).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mcp.types as types
import uvicorn
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount

from .spec import ToolRegistry, ToolSpec
from .tools import all_tools

logger = logging.getLogger("gooning.mock_mcp")


# ---------------------------------------------------------------------------
# Cascade trace JSONL
# ---------------------------------------------------------------------------
#
# Every tool call and its result is appended to a JSONL file so the dashboard
# can show a live feed of cross-agent activity. The file path is controlled
# by ``$GOONING_CASCADE_TRACE`` and defaults to
# ``<repo_root>/state/cascade-trace.jsonl``. The writer is process-local
# (threading.Lock) — we only run one MCP process at a time.

_trace_lock = threading.Lock()


def _cascade_trace_path() -> Path | None:
    override = os.environ.get("GOONING_CASCADE_TRACE", "").strip()
    if override:
        return Path(override)
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "state" / "cascade-trace.jsonl"


def _append_trace(event: dict[str, Any]) -> None:
    path = _cascade_trace_path()
    if path is None:
        return
    event.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="milliseconds"))
    line = json.dumps(event, ensure_ascii=False)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with _trace_lock:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except OSError as exc:
        logger.warning("failed to write cascade trace: %s", exc)


# ---------------------------------------------------------------------------
# Registry construction
# ---------------------------------------------------------------------------


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(*all_tools())
    return reg


def _print_spec_table(reg: ToolRegistry) -> None:
    print(f"Registered tools: {len(reg.tools)}")
    for t in reg.tools:
        callers = ",".join(t.allowed_callers) or "ANY"
        print(f"  - {t.name:32s}  callers={callers}")


async def _smoke_check(reg: ToolRegistry) -> None:
    """Call every handler with empty args to catch crashes early."""
    for t in reg.tools:
        try:
            result = await t.handler({})
            assert isinstance(result, dict), f"{t.name} returned non-dict"
        except Exception as exc:  # noqa: BLE001 — hackathon scaffold
            print(f"  ! {t.name}: {exc!r}", file=sys.stderr)


# ---------------------------------------------------------------------------
# MCP server wiring — lowlevel Server + Streamable HTTP transport.
# ---------------------------------------------------------------------------


def _caller_from_request_context(mcp_server: Server) -> str:
    """Extract the attributed caller id from the current request context.

    Reads the ``x-agent`` HTTP header that OpenHarness's MCP HTTP client
    sends on every call (per-workspace configuration in
    ``McpHttpServerConfig.headers``). Falls back to ``"unknown"`` when there
    is no HTTP request in scope (stdio, smoke, curl without the header).
    """
    try:
        ctx = mcp_server.request_context
    except (LookupError, AttributeError):
        return "unknown"
    request = getattr(ctx, "request", None)
    if request is None:
        return "unknown"
    headers = getattr(request, "headers", None)
    if headers is None:
        return "unknown"
    try:
        value = headers.get("x-agent")
    except Exception:  # pragma: no cover — defensive for non-stdlib header maps
        return "unknown"
    return (value or "unknown").strip() or "unknown"


def _build_mcp_server(reg: ToolRegistry) -> Server:
    """Register list_tools + call_tool against a lowlevel MCP Server."""
    mcp_server: Server = Server("gooning-mock")

    tool_index: dict[str, ToolSpec] = {t.name: t for t in reg.tools}

    @mcp_server.list_tools()
    async def _list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=t.name,
                description=t.description,
                inputSchema=dict(t.input_schema),
            )
            for t in reg.tools
        ]

    @mcp_server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = tool_index.get(name)
        if spec is None:
            raise ValueError(f"unknown tool: {name}")

        caller = _caller_from_request_context(mcp_server)
        strict = os.environ.get("GOONING_STRICT_CALLERS", "0") == "1"
        allowed = spec.allowed_callers
        if strict and allowed and caller not in allowed and caller != "unknown":
            raise PermissionError(
                f"caller {caller!r} not allowed for tool {name!r}; "
                f"allowed={list(allowed)}"
            )
        if allowed and caller not in allowed and caller != "unknown":
            logger.warning(
                "caller %r not in allowed_callers=%s for %s (soft mode)",
                caller,
                list(allowed),
                name,
            )

        logger.info("call_tool name=%s caller=%s args=%s", name, caller, arguments)
        call_id = uuid.uuid4().hex[:8]
        started = time.monotonic()
        _append_trace({
            "event": "tool_call",
            "call_id": call_id,
            "tool": name,
            "caller": caller,
            "args": arguments or {},
        })
        try:
            result = await spec.handler(arguments or {})
        except Exception as exc:  # noqa: BLE001 — surface every failure to the feed
            _append_trace({
                "event": "tool_error",
                "call_id": call_id,
                "tool": name,
                "caller": caller,
                "error": repr(exc),
                "elapsed_ms": int((time.monotonic() - started) * 1000),
            })
            raise
        if not isinstance(result, dict):
            raise TypeError(f"tool {name!r} handler returned non-dict: {type(result).__name__}")
        _append_trace({
            "event": "tool_result",
            "call_id": call_id,
            "tool": name,
            "caller": caller,
            "ok": bool(result.get("ok", True)),
            "result": result,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        })
        return result

    return mcp_server


def _build_starlette_app(mcp_server: Server) -> Starlette:
    """Wrap the MCP server in a Starlette app that mounts Streamable HTTP at /mcp."""
    session_manager = StreamableHTTPSessionManager(mcp_server, stateless=True)

    async def handle_streamable_http(scope, receive, send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette):
        async with session_manager.run():
            yield

    return Starlette(
        routes=[Mount("/mcp", app=handle_streamable_http)],
        lifespan=lifespan,
    )


def _serve_http(reg: ToolRegistry, *, host: str, port: int) -> int:
    """Bind the Streamable HTTP transport. Blocks until SIGINT/SIGTERM."""
    mcp_server = _build_mcp_server(reg)
    app = _build_starlette_app(mcp_server)
    logging.basicConfig(
        level=os.environ.get("GOONING_MCP_LOG", "INFO").upper(),
        format="[mock-mcp] %(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info("serving %d tools at http://%s:%d/mcp", len(reg.tools), host, port)
    _print_spec_table(reg)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level=os.environ.get("GOONING_MCP_UVICORN_LOG", "warning").lower(),
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gooning Company mock MCP server")
    parser.add_argument("--list", action="store_true", help="Print registered tools and exit.")
    parser.add_argument("--smoke", action="store_true", help="Run every handler with {} args.")
    parser.add_argument("--dump-schema", action="store_true", help="Print tool schema JSON.")
    parser.add_argument(
        "--host",
        default=os.environ.get("GOONING_MCP_HOST", "127.0.0.1"),
        help="HTTP bind host (default from $GOONING_MCP_HOST or 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("GOONING_MCP_PORT", "8765")),
        help="HTTP bind port (default from $GOONING_MCP_PORT or 8765).",
    )
    args = parser.parse_args(argv)

    reg = build_registry()

    if args.dump_schema:
        print(
            json.dumps(
                [
                    {
                        "name": t.name,
                        "description": t.description,
                        "input_schema": t.input_schema,
                        "allowed_callers": list(t.allowed_callers),
                    }
                    for t in reg.tools
                ],
                indent=2,
            )
        )
        return 0

    if args.list:
        _print_spec_table(reg)
        return 0

    if args.smoke:
        asyncio.run(_smoke_check(reg))
        _print_spec_table(reg)
        return 0

    return _serve_http(reg, host=args.host, port=args.port)


if __name__ == "__main__":
    raise SystemExit(main())
