"""Parse ``state/roadmap.md`` into the shape the React kanban expects.

The roadmap uses GitHub-style pipe tables, one per status column. This
module is deliberately forgiving — placeholder rows (``<!-- TODO -->``)
and malformed lines are skipped, not fatal. The hackathon scaffold keeps
the roadmap in markdown (see ``Product-requirement-doc/``) so that humans
and the Product agent can both edit it without losing a schema war.

Output shape (matches ``dashboard/src/api/index.js``):

    {
      "backlog": [{id, title, domain, owner, notes}, ...],
      "next": [...],
      "in-progress": [...],
      "blocked": [...],
      "done": [...],
    }
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Column keys the frontend expects. We normalise markdown headings
# ("In progress", "In Progress", "In-Progress") to the hyphenated form
# used by the React kanban panel.
COLUMN_KEYS: dict[str, str] = {
    "backlog": "backlog",
    "next": "next",
    "in progress": "in-progress",
    "in-progress": "in-progress",
    "blocked": "blocked",
    "done": "done",
}

_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
_TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")


@dataclass
class RoadmapItem:
    id: str
    title: str
    domain: str
    owner: str
    notes: str

    def as_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "title": self.title,
            "domain": self.domain,
            "owner": self.owner,
            "notes": self.notes,
        }


def parse_roadmap(path: Path) -> dict[str, list[dict[str, str]]]:
    """Parse ``path`` into {column: [items]}.

    Missing columns come back as empty lists so the frontend never has
    to defensively check for undefined keys.
    """
    columns: dict[str, list[dict[str, str]]] = {v: [] for v in set(COLUMN_KEYS.values())}
    if not path.is_file():
        return columns

    text = path.read_text(encoding="utf-8")
    current_col: str | None = None
    in_table = False
    header_fields: list[str] | None = None

    for raw_line in text.splitlines():
        heading_match = _HEADING_RE.match(raw_line)
        if heading_match:
            name = heading_match.group(1).strip().lower()
            current_col = COLUMN_KEYS.get(name)
            in_table = False
            header_fields = None
            continue

        if current_col is None:
            continue

        row_match = _TABLE_ROW_RE.match(raw_line)
        if not row_match:
            in_table = False
            header_fields = None
            continue

        cells = [c.strip() for c in row_match.group(1).split("|")]
        if not header_fields:
            # First matching row is the table header.
            header_fields = [c.lower() for c in cells]
            continue
        if _is_separator_row(cells):
            in_table = True
            continue
        if not in_table:
            # Unusual — body row without a separator. Keep going anyway.
            in_table = True

        item = _cells_to_item(header_fields, cells)
        if item is not None:
            columns[current_col].append(item.as_dict())

    return columns


def _is_separator_row(cells: list[str]) -> bool:
    return all(set(c) <= set("-:") and c for c in cells)


def _cells_to_item(headers: list[str], cells: list[str]) -> RoadmapItem | None:
    """Map header-labelled cells → :class:`RoadmapItem`, skipping placeholders."""
    if len(cells) < len(headers):
        cells = cells + [""] * (len(headers) - len(cells))
    data = dict(zip(headers, cells))

    raw_id = data.get("id", "").strip()
    if not raw_id or raw_id.startswith("<!--") or raw_id in {"", "—", "-"}:
        return None

    # Some columns use ``blocker`` or ``shipped`` in place of ``notes``.
    notes = data.get("notes") or data.get("blocker") or data.get("shipped") or ""

    return RoadmapItem(
        id=raw_id,
        title=data.get("title", "").strip(),
        domain=(data.get("domain", "") or "").strip().lower(),
        owner=(data.get("owner", "") or "").strip().lower(),
        notes=notes.strip(),
    )
