"""``router.*`` — optional router-only helpers.

The router's primary tool is ``SendMessage`` (provided by OpenHarness swarm).
Only add router.* tools here if the router genuinely needs tool-backed ops
beyond messaging — e.g. a structured cascade-trace writer.

TODO(router-owner): decide whether to keep this module at all.
"""

from __future__ import annotations

from ..spec import ToolSpec

TOOLS: list[ToolSpec] = []
