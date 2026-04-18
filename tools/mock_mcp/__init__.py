"""Mock MCP server for the-gooning-company.

Tool specs are defined per domain in :mod:`tools.mock_mcp.tools` and registered
by the server entry point. Keep this package import-light so the specs can be
introspected without booting a web server.
"""

from .spec import ToolSpec, ToolRegistry

__all__ = ["ToolSpec", "ToolRegistry"]
