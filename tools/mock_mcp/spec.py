"""Transport-neutral tool spec + registry.

Domain modules (``product.py``, ``marketing.py`` etc.) append :class:`ToolSpec`
instances to their module-level ``TOOLS`` list. ``server.py`` collects them all
and hands them to whichever MCP/HTTP stack we end up picking.

Keeping this file dependency-free is intentional: it lets the team iterate on
tool contracts before the transport decision is made, and it makes the specs
trivially testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping

# Handler takes the validated arguments dict and returns a JSON-serialisable
# result. Mocked payloads are fine during the hackathon.
ToolHandler = Callable[[Mapping[str, Any]], Awaitable[Mapping[str, Any]]]


@dataclass(frozen=True)
class ToolSpec:
    """Everything needed to expose a single namespaced mock tool."""

    name: str  # e.g. "roadmap.add_item"
    description: str  # shown to the model; keep tight and action-oriented.
    input_schema: Mapping[str, Any]  # JSON-schema-ish; mocked ok.
    handler: ToolHandler
    allowed_callers: tuple[str, ...] = ()  # teammate ids; empty == allow all.


@dataclass
class ToolRegistry:
    """Aggregates specs from every domain module."""

    tools: list[ToolSpec] = field(default_factory=list)

    def register(self, *specs: ToolSpec) -> None:
        for spec in specs:
            if any(existing.name == spec.name for existing in self.tools):
                raise ValueError(f"duplicate tool name: {spec.name}")
            self.tools.append(spec)

    def namespace(self, prefix: str) -> list[ToolSpec]:
        return [t for t in self.tools if t.name.startswith(f"{prefix}.")]

    def by_name(self, name: str) -> ToolSpec | None:
        return next((t for t in self.tools if t.name == name), None)
