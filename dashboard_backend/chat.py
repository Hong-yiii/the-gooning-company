"""Spawn ``ohmo --print`` subprocesses for founder chat.

Each message from the dashboard's chat panel becomes one fresh ``ohmo``
subprocess scoped to the router workspace. We stream the child's stdout
line-by-line over SSE so the browser sees the router thinking, calling
tools, and delegating to teammates in near-real-time.

Why one process per message?
    ``ohmo --print`` is designed for non-interactive runs: it emits the
    final answer (plus tool transcripts in most modes) and exits. That
    matches a chat-turn cleanly and means we never have to reconcile
    session state across tabs or restarts. It does cost a cold-start
    per message; acceptable for the hackathon.

Env expectations (set by the orchestrator before this module is used):
    * ``OPENHARNESS_CONFIG_DIR`` — points at our composed config dir so
      ``ohmo`` picks up the mock MCP server + agent registry.
    * ``GOONING_PERMISSION_MODE=full_auto`` — non-interactive mode
      cannot surface tool-approval prompts to a human, so we opt in
      to automatic approval for mutating tools on the dashboard path.
"""

from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ChatConfig:
    repo_root: Path
    router_workspace: Path
    model: str
    profile: str = "gooning-openai"

    def ohmo_binary(self) -> Path:
        """Prefer the ``ohmo`` installed alongside the active interpreter."""
        candidate = Path(sys.executable).parent / "ohmo"
        return candidate if candidate.is_file() else Path("ohmo")


async def stream_router_reply(
    cfg: ChatConfig,
    prompt: str,
) -> "asyncio.Queue[tuple[str, str]]":
    """Spawn ``ohmo --print`` and return a queue of ``(kind, text)`` chunks.

    Kinds:
        ``stdout`` — normal model output
        ``stderr`` — error/log lines from ohmo (useful for debugging)
        ``exit``   — final sentinel with the exit-code string
    """
    queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    cmd = [
        str(cfg.ohmo_binary()),
        "--workspace",
        str(cfg.router_workspace),
        "--profile",
        cfg.profile,
        "--model",
        cfg.model,
        "--print",
        prompt,
    ]

    # Force full_auto for non-interactive mode so mutating tools don't
    # block waiting for a human to press "y". The orchestrator sets this
    # before boot, but we defensively reinforce it here for any caller
    # that imports this module directly.
    env = os.environ.copy()
    env.setdefault("GOONING_PERMISSION_MODE", "full_auto")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cfg.repo_root),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _pump(stream: asyncio.StreamReader | None, kind: str) -> None:
        if stream is None:
            return
        while True:
            chunk = await stream.readline()
            if not chunk:
                return
            await queue.put((kind, chunk.decode("utf-8", errors="replace")))

    async def _run() -> None:
        await asyncio.gather(
            _pump(proc.stdout, "stdout"),
            _pump(proc.stderr, "stderr"),
        )
        code = await proc.wait()
        await queue.put(("exit", str(code)))

    asyncio.create_task(_run())
    return queue
