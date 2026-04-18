"""Tail the cascade-trace JSONL written by the mock MCP server.

The MCP server appends one JSON object per line to
``state/cascade-trace.jsonl`` on every tool call and result (see
``tools/mock_mcp/server.py::_append_trace``). This module reads the tail
of that file for REST polling, and exposes a simple ``follow()`` generator
for the SSE stream to push new events as they're written.
"""

from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Iterator


def read_tail(path: Path, *, limit: int = 200) -> list[dict]:
    """Return the last ``limit`` parsed events from the trace file."""
    if not path.is_file():
        return []
    # Trace files are small (one line per tool call) so a full read is
    # fine. Switch to a seek-based tail if they grow past ~10 MB.
    lines = deque(maxlen=limit)
    with path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if raw:
                lines.append(raw)
    out: list[dict] = []
    for raw in lines:
        try:
            out.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return out


def follow(path: Path, *, from_start: bool = False, poll_s: float = 0.5) -> Iterator[dict]:
    """Yield new events appended to ``path`` as they appear.

    A tiny, robust poll-based tailer. Resets cleanly if the file is
    rotated (inode change) or truncated.
    """
    last_inode = None
    position = 0

    def _seek_end(fh) -> int:
        fh.seek(0, 2)
        return fh.tell()

    while True:
        if not path.is_file():
            time.sleep(poll_s)
            continue

        try:
            stat = path.stat()
        except FileNotFoundError:
            time.sleep(poll_s)
            continue

        inode = stat.st_ino
        if last_inode is None:
            with path.open("r", encoding="utf-8") as fh:
                if from_start:
                    position = 0
                else:
                    position = _seek_end(fh)
            last_inode = inode

        if inode != last_inode or stat.st_size < position:
            # Rotated or truncated — reset.
            position = 0
            last_inode = inode

        with path.open("r", encoding="utf-8") as fh:
            fh.seek(position)
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
            position = fh.tell()
        time.sleep(poll_s)
