"""Domain tool modules. Each exposes a module-level ``TOOLS: list[ToolSpec]``."""

from . import finance, marketing, product, roadmap, router

__all__ = ["finance", "marketing", "product", "roadmap", "router"]


def all_tools() -> list:
    """Flat list of every tool spec across every domain."""
    return [*product.TOOLS, *marketing.TOOLS, *finance.TOOLS, *roadmap.TOOLS, *router.TOOLS]
