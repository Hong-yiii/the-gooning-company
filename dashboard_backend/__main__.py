"""Entry point for ``python -m dashboard_backend``.

Boots the complete application in a single process tree:

1. Runs the orchestrator bootstrap (writes ``state/.openharness/``).
2. Starts the mock MCP server as a child subprocess (same lifecycle as
   ``orchestrator.launch``).
3. Starts the Starlette dashboard on ``$GOONING_DASHBOARD_HOST:$GOONING_DASHBOARD_PORT``
   (default ``127.0.0.1:8000`` — matches the Vite dev proxy target).

Usage
-----
Production / single-URL mode (serves built SPA from ``dashboard/dist/``):

    python -m dashboard_backend

Development mode (backend on :8000, Vite on :3000 proxies ``/api``):

    # terminal 1
    python -m dashboard_backend
    # terminal 2
    cd dashboard && npm run dev
"""

from __future__ import annotations

import argparse
import os
import subprocess

import uvicorn

from orchestrator.bootstrap import run_bootstrap
from orchestrator.config import load_config
from orchestrator.launch import _install_signal_handlers, _start_mock_mcp

from .app import DashboardPaths, build_app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve the gooning company dashboard + MCP.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("GOONING_DASHBOARD_HOST", "127.0.0.1"),
        help="HTTP bind host for the dashboard (default 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("GOONING_DASHBOARD_PORT", "8000")),
        help="HTTP bind port for the dashboard (default 8000).",
    )
    parser.add_argument(
        "--no-mcp",
        action="store_true",
        help="Don't start the mock MCP subprocess. Useful if one is already running.",
    )
    args = parser.parse_args(argv)

    # Dashboard chat runs ohmo non-interactively; every chat turn needs
    # full_auto so mutating tools don't block on approval. Same guard
    # the orchestrator applies to ``--print``.
    os.environ.setdefault("GOONING_PERMISSION_MODE", "full_auto")

    cfg = load_config()
    bootstrap = run_bootstrap(cfg, verbose=True)

    mcp_proc_ref: list[subprocess.Popen[bytes] | None] = [None]
    _install_signal_handlers(mcp_proc_ref)

    if not args.no_mcp:
        mcp_proc_ref[0] = _start_mock_mcp(cfg)

    paths = DashboardPaths.from_repo(cfg.repo_root, model=bootstrap.model)
    app = build_app(paths)

    print(f"[dashboard] http://{args.host}:{args.port}")
    print(f"[dashboard] MCP: http://{os.environ.get('GOONING_MCP_HOST', '127.0.0.1')}:{os.environ.get('GOONING_MCP_PORT', '8765')}/mcp/")
    print(f"[dashboard] model: {bootstrap.model}")
    if not paths.spa_dist_dir.is_dir():
        print(
            "[dashboard] NOTE: dashboard/dist/ missing — SPA not built yet.\n"
            "            Run `cd dashboard && npm install && npm run build`\n"
            "            or `npm run dev` for the Vite dev server on :3000."
        )

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=os.environ.get("GOONING_DASHBOARD_LOG", "info").lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
