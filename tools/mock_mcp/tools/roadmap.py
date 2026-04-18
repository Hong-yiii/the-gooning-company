"""``roadmap.*`` — the shared roadmap. Read by everyone; mutated only by product.

Persists to ``state/roadmap.md`` (markdown kanban tables). Parser/serializer is
aligned with ``dashboard_backend/roadmap.py`` so the dashboard and MCP agree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ..spec import ToolSpec

# repo_root = tools/mock_mcp/tools -> ../../../
ROADMAP_PATH = Path(__file__).resolve().parents[3] / "state" / "roadmap.md"

_STATUS_ORDER = ("backlog", "next", "in-progress", "blocked", "done")

_HEADING_TO_STATUS: dict[str, str] = {
    "backlog": "backlog",
    "next": "next",
    "in progress": "in-progress",
    "in-progress": "in-progress",
    "blocked": "blocked",
    "done": "done",
}

_TABLE_HEADER_LINE = {
    "backlog": "| id | title | domain | owner | notes |",
    "next": "| id | title | domain | owner | notes |",
    "in-progress": "| id | title | domain | owner | notes |",
    "blocked": "| id | title | domain | owner | blocker |",
    "done": "| id | title | domain | owner | shipped |",
}

_SEP_LINE = "|----|-------|--------|-------|-------|"

_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")


@dataclass(frozen=True)
class RoadmapRow:
    """Fifth column is always stored in ``notes`` internally (notes/blocker/shipped)."""

    id: str
    title: str
    domain: str
    owner: str
    notes: str
    status: str


def _is_separator_row(cells: list[str]) -> bool:
    return all(set(c) <= set("-:") and c for c in cells)


def _parse_row_cells(header_fields: list[str], cells: list[str]) -> RoadmapRow | None:
    if len(cells) < len(header_fields):
        cells = cells + [""] * (len(header_fields) - len(cells))
    data = dict(zip(header_fields, cells))

    raw_id = (data.get("id") or "").strip()
    if not raw_id or raw_id.startswith("<!--") or raw_id in {"", "—", "-", "–"}:
        return None

    fifth = (
        (data.get("notes") or data.get("blocker") or data.get("shipped") or "").strip()
    )
    return RoadmapRow(
        id=raw_id,
        title=(data.get("title") or "").strip(),
        domain=(data.get("domain") or "").strip().lower(),
        owner=(data.get("owner") or "").strip().lower(),
        notes=fifth,
        status="",  # filled by caller
    )


def parse_roadmap_markdown(text: str) -> tuple[str, dict[str, list[RoadmapRow]], str]:
    """Split file into head (before first kanban table), rows by status, changelog tail."""
    lines = text.splitlines()
    try:
        backlog_idx = next(i for i, ln in enumerate(lines) if ln.strip() == "## Backlog")
    except StopIteration:
        return text, {s: [] for s in _STATUS_ORDER}, ""

    head_lines = lines[:backlog_idx]
    head = "\n".join(head_lines).rstrip() + "\n\n"

    try:
        changelog_idx = next(i for i, ln in enumerate(lines) if ln.strip() == "## Change log")
    except StopIteration:
        changelog_idx = len(lines)
        changelog = ""
    else:
        changelog = "\n".join(lines[changelog_idx:]).rstrip() + "\n"

    body_lines = lines[backlog_idx:changelog_idx]

    rows_by: dict[str, list[RoadmapRow]] = {s: [] for s in _STATUS_ORDER}
    current: str | None = None
    header_fields: list[str] | None = None
    in_table = False

    heading_re = re.compile(r"^##\s+(.+?)\s*$")

    for raw_line in body_lines:
        hm = heading_re.match(raw_line)
        if hm:
            name = hm.group(1).strip().lower()
            current = _HEADING_TO_STATUS.get(name)
            header_fields = None
            in_table = False
            continue

        if current is None:
            continue

        rm = _ROW_RE.match(raw_line)
        if not rm:
            in_table = False
            header_fields = None
            continue

        cells = [c.strip() for c in rm.group(1).split("|")]
        if not header_fields:
            header_fields = [c.lower() for c in cells]
            continue
        if _is_separator_row(cells):
            in_table = True
            continue
        if not in_table:
            in_table = True

        item = _parse_row_cells(header_fields, cells)
        if item is None:
            continue
        rows_by[current].append(replace(item, status=current))

    return head, rows_by, changelog


def _escape_cell(s: str) -> str:
    return (s or "").replace("\n", " ").strip()


def _serialize_tables(rows_by: dict[str, list[RoadmapRow]]) -> str:
    chunks: list[str] = []
    for status in _STATUS_ORDER:
        title = {
            "backlog": "Backlog",
            "next": "Next",
            "in-progress": "In progress",
            "blocked": "Blocked",
            "done": "Done",
        }[status]
        chunks.append(f"## {title}\n")
        chunks.append("\n")
        chunks.append(_TABLE_HEADER_LINE[status] + "\n")
        chunks.append(_SEP_LINE + "\n")
        for row in rows_by[status]:
            if status == "blocked":
                col5 = _escape_cell(row.notes)
                line = (
                    f"| {_escape_cell(row.id)} | {_escape_cell(row.title)} | "
                    f"{_escape_cell(row.domain)} | {_escape_cell(row.owner)} | {col5} |"
                )
            elif status == "done":
                col5 = _escape_cell(row.notes)
                line = (
                    f"| {_escape_cell(row.id)} | {_escape_cell(row.title)} | "
                    f"{_escape_cell(row.domain)} | {_escape_cell(row.owner)} | {col5} |"
                )
            else:
                col5 = _escape_cell(row.notes)
                line = (
                    f"| {_escape_cell(row.id)} | {_escape_cell(row.title)} | "
                    f"{_escape_cell(row.domain)} | {_escape_cell(row.owner)} | {col5} |"
                )
            chunks.append(line + "\n")
        chunks.append("\n")

    return "".join(chunks).rstrip() + "\n\n"


def _append_changelog_line(changelog: str, line: str) -> str:
    block = changelog.rstrip()
    if not block.endswith("\n"):
        block += "\n"
    return block + line + "\n"


def _write_roadmap(head: str, rows_by: dict[str, list[RoadmapRow]], changelog: str) -> None:
    body = _serialize_tables(rows_by)
    # Ensure head ends with blank line before tables
    full = head.rstrip() + "\n" + body + changelog.rstrip() + "\n"
    ROADMAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = ROADMAP_PATH.with_suffix(".tmp")
    tmp.write_text(full, encoding="utf-8")
    tmp.replace(ROADMAP_PATH)


def _load_or_default() -> tuple[str, dict[str, list[RoadmapRow]], str]:
    if not ROADMAP_PATH.is_file():
        return "", {s: [] for s in _STATUS_ORDER}, "## Change log\n\n"
    text = ROADMAP_PATH.read_text(encoding="utf-8")
    return parse_roadmap_markdown(text)


def _all_rows(rows_by: dict[str, list[RoadmapRow]]) -> list[RoadmapRow]:
    out: list[RoadmapRow] = []
    for st in _STATUS_ORDER:
        out.extend(rows_by[st])
    return out


def _find_row(rows_by: dict[str, list[RoadmapRow]], item_id: str) -> tuple[str, int] | None:
    for st in _STATUS_ORDER:
        for idx, row in enumerate(rows_by[st]):
            if row.id == item_id:
                return st, idx
    return None


def _next_id(rows_by: dict[str, list[RoadmapRow]], domain: str) -> str:
    prefix = {"product": "P-", "marketing": "M-", "finance": "F-"}.get(domain, "P-")
    max_n = 0
    for row in _all_rows(rows_by):
        if row.id.upper().startswith(prefix.upper()) and len(row.id) > 2:
            tail = row.id[2:]
            if tail.isdigit():
                max_n = max(max_n, int(tail))
    return f"{prefix}{max_n + 1:03d}"


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def _read_all(args: Mapping[str, Any]) -> dict[str, Any]:
    if not ROADMAP_PATH.exists():
        return {"markdown": "", "items": [], "note": "roadmap not initialised"}
    text = ROADMAP_PATH.read_text(encoding="utf-8")
    _head, rows_by, _cl = parse_roadmap_markdown(text)
    items: list[dict[str, Any]] = []
    for st in _STATUS_ORDER:
        for r in rows_by[st]:
            items.append(
                {
                    "id": r.id,
                    "title": r.title,
                    "domain": r.domain,
                    "owner": r.owner,
                    "notes": r.notes,
                    "status": st,
                }
            )
    nonempty = sum(1 for st in _STATUS_ORDER for r in rows_by[st])
    return {
        "markdown": text,
        "items": items,
        "note": f"{nonempty} items across {len(_STATUS_ORDER)} columns",
    }


async def _read_item(args: Mapping[str, Any]) -> dict[str, Any]:
    rid = (args.get("id") or "").strip()
    if not rid:
        return {"ok": False, "note": "missing id"}
    if not ROADMAP_PATH.is_file():
        return {"ok": False, "note": "roadmap not initialised"}
    text = ROADMAP_PATH.read_text(encoding="utf-8")
    _head, rows_by, _cl = parse_roadmap_markdown(text)
    hit = _find_row(rows_by, rid)
    if hit is None:
        return {"ok": False, "note": f"not found: {rid}"}
    st, idx = hit
    r = rows_by[st][idx]
    return {
        "ok": True,
        "item": {
            "id": r.id,
            "title": r.title,
            "domain": r.domain,
            "owner": r.owner,
            "notes": r.notes,
            "status": st,
        },
        "note": f"read {rid} from {st}",
    }


async def _add_item(args: Mapping[str, Any]) -> dict[str, Any]:
    title = (args.get("title") or "").strip()
    domain = (args.get("domain") or "").strip().lower()
    owner = (args.get("owner") or "").strip().lower()
    notes = (args.get("notes") or "").strip()
    if not title or domain not in ("product", "marketing", "finance"):
        return {"ok": False, "note": "missing title or invalid domain (product|marketing|finance)"}
    if not owner:
        owner = domain

    head, rows_by, changelog = _load_or_default()
    new_id = _next_id(rows_by, domain)
    row = RoadmapRow(
        id=new_id,
        title=title,
        domain=domain,
        owner=owner,
        notes=notes,
        status="backlog",
    )
    rows_by["backlog"].append(row)

    log_line = f"- {_today()} — {domain} — {new_id} — added — {title}"
    changelog = _append_changelog_line(changelog, log_line)
    _write_roadmap(head, rows_by, changelog)

    return {
        "ok": True,
        "id": new_id,
        "status": "backlog",
        "event": "roadmap.changed",
        "from_status": "",
        "to_status": "backlog",
        "title": title,
        "domain": domain,
        "note": f"added {new_id} to Backlog",
    }


async def _move_item(args: Mapping[str, Any]) -> dict[str, Any]:
    rid = (args.get("id") or "").strip()
    to_status = (args.get("status") or "").strip().lower()
    reason = (args.get("reason") or "").strip()

    if not rid:
        return {"ok": False, "note": "missing id"}
    allowed = {"backlog", "next", "in-progress", "blocked", "done", "dropped"}
    if to_status not in allowed:
        return {"ok": False, "note": f"invalid status {to_status!r}"}

    head, rows_by, changelog = _load_or_default()
    hit = _find_row(rows_by, rid)
    if hit is None:
        return {"ok": False, "note": f"not found: {rid}"}
    from_st, idx = hit
    row = rows_by[from_st].pop(idx)

    target = to_status
    shipped_value = row.notes
    if to_status == "dropped":
        target = "done"
        shipped_value = f"dropped — {reason or 'no reason'}"
    elif target == "done":
        shipped_value = reason or row.notes or _today()
    elif target == "blocked":
        shipped_value = reason or row.notes

    new_row = RoadmapRow(
        id=row.id,
        title=row.title,
        domain=row.domain,
        owner=row.owner,
        notes=shipped_value,
        status=target,
    )
    rows_by[target].append(new_row)

    if to_status == "dropped":
        action = "dropped"
    elif target == "done" and shipped_value.lower().startswith("dropped"):
        action = "dropped"
    elif target == "done" and (reason or "").lower().startswith("shipped"):
        action = "shipped"
    else:
        action = "moved"
    log_line = (
        f"- {_today()} — {row.domain} — {rid} — {action} — "
        f"{from_st}→{target}: {reason or title_short(row.title)}"
    )
    changelog = _append_changelog_line(changelog, log_line)
    _write_roadmap(head, rows_by, changelog)

    return {
        "ok": True,
        "id": rid,
        "event": "roadmap.changed",
        "from_status": from_st,
        "to_status": target if to_status != "dropped" else "dropped",
        "title": row.title,
        "domain": row.domain,
        "note": f"moved {rid} {from_st} → {target}" + (" (dropped)" if to_status == "dropped" else ""),
    }


def title_short(title: str) -> str:
    t = title.strip()
    return t if len(t) <= 60 else t[:59] + "…"


async def _drop_item(args: Mapping[str, Any]) -> dict[str, Any]:
    rid = (args.get("id") or "").strip()
    reason = (args.get("reason") or "").strip()
    if not rid:
        return {"ok": False, "note": "missing id"}
    if not reason:
        return {"ok": False, "note": "missing reason"}

    low = reason.lower()
    if low.startswith("shipped") or low == "done":
        shipped = reason
    else:
        shipped = f"dropped — {reason}"

    return await _move_item({"id": rid, "status": "done", "reason": shipped})


_READ_CALLERS = ("product", "marketing", "finance", "the-gooning-company")
_WRITE_CALLERS = ("product",)


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="roadmap.read_all",
        description="Return the full roadmap markdown plus parsed items for convenience.",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_read_all,
        allowed_callers=_READ_CALLERS,
    ),
    ToolSpec(
        name="roadmap.read_item",
        description="Return a single roadmap item by id.",
        input_schema={
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "additionalProperties": False,
        },
        handler=_read_item,
        allowed_callers=_READ_CALLERS,
    ),
    ToolSpec(
        name="roadmap.add_item",
        description="Add a new roadmap item to the backlog. Product only.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "domain": {"type": "string", "enum": ["product", "marketing", "finance"]},
                "owner": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["title", "domain"],
            "additionalProperties": False,
        },
        handler=_add_item,
        allowed_callers=_WRITE_CALLERS,
    ),
    ToolSpec(
        name="roadmap.move_item",
        description="Move an item between status columns. Product only. Use status=dropped to archive with dropped provenance.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["backlog", "next", "in-progress", "blocked", "done", "dropped"],
                },
                "reason": {"type": "string"},
            },
            "additionalProperties": False,
        },
        handler=_move_item,
        allowed_callers=_WRITE_CALLERS,
    ),
    ToolSpec(
        name="roadmap.drop_item",
        description="Drop or ship an item: moves to Done with shipped text, or dropped — reason. Product only.",
        input_schema={
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "additionalProperties": False,
        },
        handler=_drop_item,
        allowed_callers=_WRITE_CALLERS,
    ),
]
