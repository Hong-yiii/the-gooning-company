"""Allow ``python -m tools.mock_mcp --list|--smoke|...`` (see server.py)."""

from __future__ import annotations

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
