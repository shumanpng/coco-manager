#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path
import os
from typing import Any

import yaml


STATUS_ORDER: dict[str, int] = {
    "in_progress": 0,
    "todo": 1,
    "done": 2,
    "archived": 3,
}

HORIZON_ORDER: dict[str, int] = {
    "now": 0,
    "next": 1,
    "later": 2,
    "unscheduled": 3,
}


def _priority_key(priority: str | None) -> tuple[int, str]:
    if not priority:
        return (99, "")
    p = priority.strip().upper()
    if p.startswith("P") and p[1:].isdigit():
        return (int(p[1:]), p)
    return (98, p)


def _parse_date(value: Any) -> dt.date | None:
    if value is None:
        return None
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def _read_frontmatter(md_text: str) -> tuple[dict[str, Any], str]:
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, md_text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_text = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :]).lstrip("\n")
            data = yaml.safe_load(fm_text) or {}
            if not isinstance(data, dict):
                return {}, md_text
            return data, body
    return {}, md_text


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _git_last_updated_iso(repo_root: Path, path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            cwd=str(repo_root),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        result = None
    out = (result.stdout or "").strip()
    if out:
        return out
    try:
        return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return None


def _coerce_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        v = value.strip()
        return (v,) if v else ()
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
        return tuple(out)
    return ()


def _normalize_status(value: Any) -> str:
    v = str(value or "").strip().lower()
    if not v:
        return "todo"
    if v in {"todo", "in_progress", "done", "archived"}:
        return v
    if v in {"in progress", "in-progress"}:
        return "in_progress"
    return v


def _normalize_horizon(value: Any) -> str:
    v = str(value or "").strip().lower()
    if not v or v == "none":
        return "unscheduled"
    if v in {"now", "next", "later", "unscheduled"}:
        return v
    return v


def _normalize_kind(value: Any) -> str | None:
    v = str(value or "").strip().lower()
    if not v:
        return None
    allowed = {"experiment", "engineering", "analysis", "docs", "maintenance", "reading", "writing"}
    return v if v in allowed else v


@dataclass(frozen=True)
class Item:
    id: str
    title: str
    status: str
    horizon: str
    priority: str | None
    impact: str | None
    effort: str | None
    risk: str | None
    owner: str | None
    kind: str | None
    tags: tuple[str, ...]
    blocked_by: tuple[str, ...]
    blocking: tuple[str, ...]
    related: tuple[str, ...]
    created_on: dt.date | None
    updated_on: dt.date | None
    due_by: dt.date | None
    git_updated_on: str | None
    path: Path


def load_items(repo_root: Path, items_dir: Path) -> list[Item]:
    items: list[Item] = []
    for path in sorted(items_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _read_frontmatter(text)

        inferred_id = path.stem.strip()
        item_id = str(frontmatter.get("id") or inferred_id).strip()
        title = str(frontmatter.get("title") or "").strip() or (_first_heading(body) or item_id)

        items.append(
            Item(
                id=item_id,
                title=title,
                status=_normalize_status(frontmatter.get("status")),
                horizon=_normalize_horizon(frontmatter.get("horizon")),
                priority=(str(frontmatter.get("priority")).strip() if frontmatter.get("priority") is not None else None),
                impact=(str(frontmatter.get("impact")).strip().lower() if frontmatter.get("impact") is not None else None),
                effort=(str(frontmatter.get("effort")).strip().lower() if frontmatter.get("effort") is not None else None),
                risk=(str(frontmatter.get("risk")).strip().lower() if frontmatter.get("risk") is not None else None),
                owner=(str(frontmatter.get("owner")).strip() if frontmatter.get("owner") is not None else None),
                kind=_normalize_kind(frontmatter.get("kind")),
                tags=_coerce_str_list(frontmatter.get("tags")),
                blocked_by=_coerce_str_list(frontmatter.get("blocked_by")),
                blocking=_coerce_str_list(frontmatter.get("blocking")),
                related=_coerce_str_list(frontmatter.get("related")),
                created_on=_parse_date(frontmatter.get("created_on")),
                updated_on=_parse_date(frontmatter.get("updated_on")),
                due_by=_parse_date(frontmatter.get("due_by")),
                git_updated_on=_git_last_updated_iso(repo_root=repo_root, path=path),
                path=path,
            )
        )
    return items


def _md_link(label: str, target_relpath: str) -> str:
    return f"[{label}]({target_relpath})"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _relpath_from(out_dir: Path, target: Path) -> str:
    try:
        rel = target.relative_to(out_dir)
        return rel.as_posix()
    except ValueError:
        return os.path.relpath(target, out_dir).replace(os.path.sep, "/")


def _resolve_id_link(repo_root: Path, out_dir: Path, planning_by_id: dict[str, Item], item_id: str) -> str:
    if item_id in planning_by_id:
        rel = _relpath_from(out_dir, planning_by_id[item_id].path)
        return _md_link(item_id, rel)
    state_path = repo_root / "docs" / "state" / "items" / f"{item_id}.md"
    if state_path.exists():
        rel = _relpath_from(out_dir, state_path)
        return _md_link(item_id, rel)
    return f"`{item_id}`"


def _links_for_ids(repo_root: Path, out_dir: Path, planning_by_id: dict[str, Item], ids: tuple[str, ...]) -> str:
    if not ids:
        return ""
    return ", ".join(_resolve_id_link(repo_root, out_dir, planning_by_id, _id) for _id in ids)


def _render_table(repo_root: Path, items: list[Item], out_dir: Path, planning_by_id: dict[str, Item]) -> list[str]:
    def rel_link_for(item: Item) -> str:
        rel = _relpath_from(out_dir, item.path)
        return _md_link(item.id, rel)

    lines: list[str] = []
    lines.append(
        "| id | title | status | horizon | priority | kind | tags | impact | effort | risk | owner | blocked_by | blocking | related | created | due_by | last_updated |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    rel_link_for(item),
                    _escape_cell(item.title),
                    (item.status or ""),
                    (item.horizon or ""),
                    (item.priority or ""),
                    (item.kind or ""),
                    _escape_cell(", ".join(item.tags) if item.tags else ""),
                    (item.impact or ""),
                    (item.effort or ""),
                    (item.risk or ""),
                    _escape_cell(item.owner or ""),
                    _links_for_ids(repo_root, out_dir, planning_by_id, item.blocked_by),
                    _links_for_ids(repo_root, out_dir, planning_by_id, item.blocking),
                    _links_for_ids(repo_root, out_dir, planning_by_id, item.related),
                    (item.created_on.isoformat() if item.created_on else ""),
                    (item.due_by.isoformat() if item.due_by else ""),
                    (item.git_updated_on or ""),
                ]
            )
            + " |"
        )
    return lines


def _sort_items(items: list[Item]) -> list[Item]:
    def sort_key(item: Item) -> tuple[int, int, tuple[int, str], dt.date | None, str]:
        horizon_rank = HORIZON_ORDER.get(item.horizon, 99)
        status_rank = STATUS_ORDER.get(item.status, 99)
        prio = _priority_key(item.priority)
        return (horizon_rank, status_rank, prio, item.due_by, item.id)

    return sorted(items, key=sort_key)


def render_index(repo_root: Path, items: list[Item], out_path: Path) -> str:
    out_dir = out_path.parent
    planning_by_id: dict[str, Item] = {item.id: item for item in items}
    items_sorted = _sort_items(items)
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat(sep=" ", timespec="minutes")

    lines: list[str] = []
    lines.append("# Planning index")
    lines.append("")
    lines.append(f"_Generated by `scripts/generate_planning_index.py` on {now}._")
    lines.append("")
    lines.append("Canonical items live in `planning/items/` (one file per item).")
    lines.append("")
    lines.extend(_render_table(repo_root, items_sorted, out_dir=out_dir, planning_by_id=planning_by_id))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_horizons(repo_root: Path, items: list[Item], out_path: Path) -> str:
    out_dir = out_path.parent
    planning_by_id: dict[str, Item] = {item.id: item for item in items}
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat(sep=" ", timespec="minutes")

    by_horizon: dict[str, list[Item]] = {h: [] for h in ["now", "next", "later", "unscheduled"]}
    for item in items:
        by_horizon.setdefault(item.horizon, []).append(item)

    lines: list[str] = []
    lines.append("# Planning horizons")
    lines.append("")
    lines.append(f"_Generated by `scripts/generate_planning_index.py` on {now}._")
    lines.append("")
    lines.append("Canonical items live in `planning/items/`.")
    lines.append("")

    for horizon in ["now", "next", "later", "unscheduled"]:
        items_for_horizon = _sort_items(by_horizon.get(horizon, []))
        title = horizon.capitalize()
        lines.append(f"## {title} ({len(items_for_horizon)})")
        lines.append("")
        if items_for_horizon:
            lines.extend(_render_table(repo_root, items_for_horizon, out_dir=out_dir, planning_by_id=planning_by_id))
        else:
            lines.append("_No items._")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate scannable planning dashboards from planning/items/*.md.")
    parser.add_argument("--repo-root", default=".", help="Path to repo root (default: .).")
    parser.add_argument("--items-dir", default="planning/items", help="Directory containing planning item markdown files.")
    parser.add_argument("--out-index", default="planning/INDEX.md", help="Output markdown path for the full index.")
    parser.add_argument("--out-horizons", default="planning/horizons.md", help="Output markdown path for the horizons view.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    items_dir = (repo_root / args.items_dir).resolve()
    out_index = (repo_root / args.out_index).resolve()
    out_horizons = (repo_root / args.out_horizons).resolve()

    if not items_dir.exists():
        raise SystemExit(f"Items dir not found: {items_dir}")

    items = load_items(repo_root=repo_root, items_dir=items_dir)

    out_index.parent.mkdir(parents=True, exist_ok=True)
    out_horizons.parent.mkdir(parents=True, exist_ok=True)
    out_index.write_text(render_index(repo_root=repo_root, items=items, out_path=out_index), encoding="utf-8")
    out_horizons.write_text(render_horizons(repo_root=repo_root, items=items, out_path=out_horizons), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
