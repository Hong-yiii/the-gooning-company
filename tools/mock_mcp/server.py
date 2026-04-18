"""Mock MCP server entry point.

TODO(glue): pick the MCP/HTTP stack and wire the registered specs to it.
This module currently collects specs and exposes a simple ``main()`` that
prints the spec table — enough to validate registration before the transport
lands.

Usage (once wired):
    python -m tools.mock_mcp.server
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .spec import ToolRegistry
from .tools import all_tools


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gooning Company mock MCP server")
    parser.add_argument("--list", action="store_true", help="Print registered tools and exit.")
    parser.add_argument("--smoke", action="store_true", help="Run every handler with {} args.")
    parser.add_argument("--dump-schema", action="store_true", help="Print tool schema JSON.")
    args = parser.parse_args(argv)

    reg = build_registry()

    if args.dump_schema:
        print(
            json.dumps(
                [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in reg.tools],
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

    # TODO(glue): serve the registry over the chosen MCP transport.
    # Suggested flow:
    #   1. Pick framework (e.g. fastmcp) and add to pyproject.toml [project.optional-dependencies].mcp
    #   2. Instantiate it, iterate reg.tools, register each with name/description/input_schema/handler.
    #   3. Before invoking handler, enforce allowed_callers using the MCP client identity.
    #   4. Bind to the URL named in workspaces/_shared/mcp.json (default http://127.0.0.1:8765/mcp).
    print("TODO(glue): transport not wired. Run with --list or --smoke for now.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
