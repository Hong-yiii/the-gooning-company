"""Starlette app: REST + SSE + static SPA.

Endpoints (all under ``/api``):

* ``GET  /api/status``               — coordinator + per-agent health
* ``GET  /api/roadmap``              — parsed kanban columns
* ``GET  /api/god/{agent}``          — {agent, content, updatedAt}
* ``GET  /api/cascade``              — last N trace entries
* ``GET  /api/events``               — SSE: live roadmap/god/cascade deltas
* ``POST /api/chat``                 — run one router turn, stream the reply
                                       back as SSE (``delta`` / ``done`` / ``error``)

Static:
* ``GET /``                          — served from ``dashboard/dist/index.html``
* ``GET /assets/*``                  — Vite build artefacts

The SPA uses Vite proxy in dev; in production the SPA is served by this
process so the dashboard is one URL and one port.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response, StreamingResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import cascade, gods
from .chat import ChatConfig, stream_router_reply
from .roadmap import parse_roadmap

logger = logging.getLogger("gooning.dashboard")


# ---------------------------------------------------------------------------
# App-wide config container
# ---------------------------------------------------------------------------


@dataclass
class DashboardPaths:
    repo_root: Path
    workspaces_dir: Path
    roadmap_path: Path
    cascade_path: Path
    router_workspace: Path
    spa_dist_dir: Path
    model: str

    @classmethod
    def from_repo(cls, repo_root: Path, *, model: str) -> "DashboardPaths":
        return cls(
            repo_root=repo_root,
            workspaces_dir=repo_root / "workspaces",
            roadmap_path=repo_root / "state" / "roadmap.md",
            cascade_path=Path(
                os.environ.get("GOONING_CASCADE_TRACE", "")
                or (repo_root / "state" / "cascade-trace.jsonl")
            ),
            router_workspace=repo_root / "workspaces" / "router",
            spa_dist_dir=repo_root / "dashboard" / "dist",
            model=model,
        )


# ---------------------------------------------------------------------------
# SSE plumbing
# ---------------------------------------------------------------------------


def _sse_format(event: str, data: Any) -> bytes:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


class FileMtimeWatcher:
    """Poll a set of files and emit an event when one mutates."""

    def __init__(self, paths: dict[str, Path], *, poll_s: float = 0.75) -> None:
        self._paths = paths
        self._poll = poll_s
        self._mtimes: dict[str, float] = {k: self._stat(p) for k, p in paths.items()}

    @staticmethod
    def _stat(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except FileNotFoundError:
            return 0.0

    async def stream(self) -> AsyncIterator[tuple[str, Path]]:
        while True:
            await asyncio.sleep(self._poll)
            for key, path in self._paths.items():
                cur = self._stat(path)
                if cur != self._mtimes[key]:
                    self._mtimes[key] = cur
                    yield key, path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


def build_app(paths: DashboardPaths) -> Starlette:
    async def api_status(_: Request) -> JSONResponse:
        agents_ok = all((paths.workspaces_dir / a / "memory" / "god.md").is_file() for a in gods.AGENTS)
        return JSONResponse(
            {
                "coordinator": "online",
                "agents": {a: ("online" if agents_ok else "offline") for a in gods.AGENTS},
                "model": paths.model,
                "mcp": {
                    "host": os.environ.get("GOONING_MCP_HOST", "127.0.0.1"),
                    "port": int(os.environ.get("GOONING_MCP_PORT", "8765")),
                },
            }
        )

    async def api_roadmap(_: Request) -> JSONResponse:
        data = parse_roadmap(paths.roadmap_path)
        total = sum(len(v) for v in data.values())
        return JSONResponse({"columns": data, "total": total, "path": str(paths.roadmap_path)})

    async def api_god(request: Request) -> Response:
        agent = request.path_params["agent"]
        if agent not in gods.AGENTS:
            return JSONResponse({"error": f"unknown agent: {agent}"}, status_code=404)
        return JSONResponse(gods.read_god_file(paths.workspaces_dir, agent).as_dict())

    async def api_cascade(request: Request) -> JSONResponse:
        limit = int(request.query_params.get("limit", "200"))
        events = cascade.read_tail(paths.cascade_path, limit=limit)
        return JSONResponse({"events": events, "path": str(paths.cascade_path)})

    async def api_events(_: Request) -> StreamingResponse:
        # Single SSE stream multiplexes roadmap/god.md/cascade updates.
        watcher = FileMtimeWatcher(
            {
                "roadmap": paths.roadmap_path,
                "god:product": gods.god_path(paths.workspaces_dir, "product"),
                "god:marketing": gods.god_path(paths.workspaces_dir, "marketing"),
                "god:finance": gods.god_path(paths.workspaces_dir, "finance"),
                "cascade": paths.cascade_path,
            },
            poll_s=0.5,
        )

        async def gen() -> AsyncIterator[bytes]:
            yield _sse_format("ready", {"ok": True})
            async for key, _p in watcher.stream():
                if key == "roadmap":
                    yield _sse_format("roadmap", parse_roadmap(paths.roadmap_path))
                elif key.startswith("god:"):
                    agent = key.split(":", 1)[1]
                    yield _sse_format(
                        "god",
                        gods.read_god_file(paths.workspaces_dir, agent).as_dict(),
                    )
                elif key == "cascade":
                    yield _sse_format("cascade", cascade.read_tail(paths.cascade_path, limit=50))

        return StreamingResponse(gen(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        })

    async def api_chat(request: Request) -> StreamingResponse:
        body = await request.json()
        message = (body.get("message") or "").strip()
        if not message:
            return JSONResponse({"error": "missing message"}, status_code=400)

        chat_cfg = ChatConfig(
            repo_root=paths.repo_root,
            router_workspace=paths.router_workspace,
            model=paths.model,
        )

        async def gen() -> AsyncIterator[bytes]:
            yield _sse_format("start", {"message": message})
            try:
                queue = await stream_router_reply(chat_cfg, message)
            except Exception as exc:  # noqa: BLE001
                yield _sse_format("error", {"error": repr(exc)})
                return

            while True:
                kind, chunk = await queue.get()
                if kind == "exit":
                    yield _sse_format("done", {"exit_code": chunk})
                    return
                if kind == "stderr":
                    yield _sse_format("log", chunk)
                    continue
                yield _sse_format("delta", chunk)

        return StreamingResponse(gen(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        })

    # ---- static SPA (built by vite into dashboard/dist/) -------------------

    async def index(_: Request) -> Response:
        index_file = paths.spa_dist_dir / "index.html"
        if not index_file.is_file():
            return Response(
                content=_build_missing_spa_html(paths),
                status_code=200,
                media_type="text/html",
            )
        return FileResponse(index_file)

    routes = [
        Route("/api/status", api_status),
        Route("/api/roadmap", api_roadmap),
        Route("/api/god/{agent}", api_god),
        Route("/api/cascade", api_cascade),
        Route("/api/events", api_events),
        Route("/api/chat", api_chat, methods=["POST"]),
        Route("/", index),
    ]

    if paths.spa_dist_dir.is_dir():
        routes.append(Mount("/assets", app=StaticFiles(directory=paths.spa_dist_dir / "assets")))
        # Favicon + other root-level static files, if present.
        routes.append(Mount("/static", app=StaticFiles(directory=paths.spa_dist_dir)))

    return Starlette(debug=False, routes=routes)


def _build_missing_spa_html(paths: DashboardPaths) -> str:
    """Helpful stub shown when the React SPA hasn't been built yet."""
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>the gooning company — dashboard</title>
<style>
body{{font-family:ui-sans-serif,system-ui;padding:3rem;max-width:680px;margin:0 auto;color:#1f2937}}
code{{background:#f3f4f6;padding:2px 6px;border-radius:4px}}
pre{{background:#f3f4f6;padding:1rem;border-radius:6px;overflow:auto}}
</style></head>
<body>
<h1>Dashboard is running, UI not built.</h1>
<p>The Python backend is up on this URL. The React SPA lives in
<code>dashboard/</code> but hasn't been compiled yet.</p>
<p>Run once:</p>
<pre>cd dashboard
npm install
npm run build</pre>
<p>Then refresh this page. For iterative frontend work, use
<code>npm run dev</code> from <code>dashboard/</code> (port 3000, proxies
<code>/api</code> to this process).</p>
<p>In the meantime the API is live:</p>
<ul>
  <li><a href="/api/status">/api/status</a></li>
  <li><a href="/api/roadmap">/api/roadmap</a></li>
  <li><a href="/api/god/product">/api/god/product</a></li>
  <li><a href="/api/cascade">/api/cascade</a></li>
</ul>
<p>Expected SPA dist dir: <code>{paths.spa_dist_dir}</code></p>
</body></html>
"""
