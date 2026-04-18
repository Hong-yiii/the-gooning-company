"""Orchestrator for the-gooning-company.

Responsible for:
  * Computing the shared system prompt (``workspaces/_shared/base-system.md``)
    and passing it as ``extra_prompt`` to each agent.
  * Computing ``extra_skill_dirs`` (``workspaces/_shared/skills``).
  * Merging ``workspaces/_shared/mcp.json`` into each per-workspace
    ``settings.json`` so every agent talks to the same mock MCP server.
  * Spawning the three domain teammates under the router via
    :class:`openharness.swarm.SubprocessBackend` (TODO once wired).

Everything defined here is transport-neutral; the OpenHarness import happens
lazily inside :func:`launch` so the package can be imported for inspection
without the heavy dep installed.
"""

from .config import AgentConfig, OrchestratorConfig, load_config

__all__ = ["AgentConfig", "OrchestratorConfig", "load_config"]
