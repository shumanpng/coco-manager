#!/usr/bin/env python3

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


STATUS_ORDER: dict[str, dict[str, int]] = {
    "question": {"open": 0, "resolved": 1},
    "hypothesis": {"to_test": 0, "unclear": 1, "supported": 2, "refuted": 3},
    "assumption": {"current": 0, "uncertain": 1, "invalidated": 2},
    "finding": {"current": 0, "outdated": 1},
    "decision": {"accepted": 0, "superseded": 1},
}

TYPE_TITLES: dict[str, str] = {
    "question": "Open questions",
    "hypothesis": "Hypotheses",
    "assumption": "Assumptions",
    "finding": "Findings",
    "decision": "Decisions",
}

TYPE_INDEX_OUTPUTS: dict[str, str] = {
    "hypothesis": "state/hypotheses.md",
    "question": "state/open_questions.md",
    "assumption": "state/assumptions.md",
    "finding": "state/findings.md",
    "decision": "state/decisions.md",
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
    # Untracked / no git history yet: fall back to filesystem mtime so the column is still useful.
    try:
        return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()
    except OSError:
        return None


@dataclass(frozen=True)
class Item:
    id: str
    type: str
    title: str
    status: str
    priority: str | None
    review_by: dt.date | None
    impact: str | None
    blocked_by: tuple[str, ...]
    blocking: tuple[str, ...]
    related: tuple[str, ...]
    created_on: dt.date | None
    last_verified: dt.date | None
    git_updated_on: str | None
    path: Path


def _normalize_type(type_value: str) -> str:
    t = (type_value or "").strip().lower()
    if t in {"hypothesis", "assumption", "question", "finding", "decision"}:
        return t
    if t in {"q", "questions"}:
        return "question"
    if t in {"h", "hypotheses"}:
        return "hypothesis"
    if t in {"a", "assumptions"}:
        return "assumption"
    if t in {"f", "findings"}:
        return "finding"
    if t in {"d", "decisions"}:
        return "decision"
    return t


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


def load_items(repo_root: Path, items_dir: Path) -> list[Item]:
    items: list[Item] = []
    for path in sorted(items_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = _read_frontmatter(text)

        inferred_id = path.stem.strip()
        item_id = str(frontmatter.get("id") or inferred_id).strip()
        item_type = _normalize_type(str(frontmatter.get("type") or "").strip())
        title = str(frontmatter.get("title") or "").strip() or (_first_heading(body) or item_id)
        status = str(frontmatter.get("status") or "").strip().lower()

        items.append(
            Item(
                id=item_id,
                type=item_type,
                title=title,
                status=status,
                priority=(str(frontmatter.get("priority")).strip() if frontmatter.get("priority") is not None else None),
                review_by=_parse_date(frontmatter.get("review_by") or frontmatter.get("deadline")),
                impact=(str(frontmatter.get("impact")).strip().lower() if frontmatter.get("impact") is not None else None),
                blocked_by=_coerce_str_list(frontmatter.get("blocked_by")),
                blocking=_coerce_str_list(frontmatter.get("blocking")),
                related=_coerce_str_list(frontmatter.get("related")),
                created_on=_parse_date(frontmatter.get("created_on")),
                last_verified=_parse_date(frontmatter.get("last_verified")),
                git_updated_on=_git_last_updated_iso(repo_root=repo_root, path=path),
                path=path,
            )
        )
    return items


def _md_link(label: str, target_relpath: str) -> str:
    return f"[{label}]({target_relpath})"


def _render_table(items: list[Item], out_dir: Path, id_to_item: dict[str, Item]) -> list[str]:
    def rel_link_for(item: Item) -> str:
        rel = item.path.relative_to(out_dir)
        return _md_link(item.id, rel.as_posix())

    def links_for_ids(ids: tuple[str, ...]) -> str:
        if not ids:
            return ""
        parts: list[str] = []
        for _id in ids:
            if _id in id_to_item:
                parts.append(rel_link_for(id_to_item[_id]))
            else:
                parts.append(f"`{_id}`")
        return ", ".join(parts)

    lines: list[str] = []
    lines.append("| id | title | status | priority | review_by | impact | blocked_by | blocking | related | created | last_verified | last_updated |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    rel_link_for(item),
                    item.title.replace("|", "\\|"),
                    (item.status or ""),
                    (item.priority or ""),
                    (item.review_by.isoformat() if item.review_by else ""),
                    (item.impact or ""),
                    links_for_ids(item.blocked_by),
                    links_for_ids(item.blocking),
                    links_for_ids(item.related),
                    (item.created_on.isoformat() if item.created_on else ""),
                    (item.last_verified.isoformat() if item.last_verified else ""),
                    (item.git_updated_on or ""),
                ]
            )
            + " |"
        )
    return lines


def _sort_items(items: list[Item]) -> list[Item]:
    def sort_key(item: Item) -> tuple[int, tuple[int, str], dt.date, str]:
        status_rank = STATUS_ORDER.get(item.type, {}).get(item.status, 99)
        prio = _priority_key(item.priority)
        # Handle None review_by by sorting items without it last
        review_date = item.review_by if item.review_by else dt.date(9999, 12, 31)
        return (status_rank, prio, review_date, item.id)

    return sorted(items, key=sort_key)


def render_index(items: list[Item], out_path: Path) -> str:
    out_dir = out_path.parent
    id_to_item: dict[str, Item] = {item.id: item for item in items}

    by_type: dict[str, list[Item]] = {}
    for item in items:
        by_type.setdefault(item.type, []).append(item)
    for t in by_type:
        by_type[t] = _sort_items(by_type[t])

    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat(sep=" ", timespec="minutes")
    lines: list[str] = []
    lines.append("# State index")
    lines.append("")
    lines.append(f"_Generated by `scripts/generate_state_index.py` on {now}._")
    lines.append("")
    lines.append("Canonical items live in `state/items/` (one file per item).")
    lines.append("")

    # Quick “attention” list first.
    attention = [
        item
        for item in items
        if (item.type in {"question", "hypothesis"})
        and item.status in {"open", "to_test", "unclear"}
        and _priority_key(item.priority)[0] <= 1
    ]
    if attention:
        lines.append("## Attention (P0/P1 open or unvalidated)")
        lines.append("")
        for item in _sort_items(attention)[:25]:
            rel = item.path.relative_to(out_dir).as_posix()
            lines.append(f"- [{item.id}]({rel}): {item.title} (`{item.status}`, `{item.priority or 'P?'}`)")
        lines.append("")

    for type_name in ["question", "hypothesis", "assumption", "finding", "decision"]:
        items_for_type = by_type.get(type_name, [])
        if not items_for_type:
            continue
        lines.append(f"## {TYPE_TITLES.get(type_name, type_name)} ({len(items_for_type)})")
        lines.append("")
        lines.extend(_render_table(items_for_type, out_dir=out_dir, id_to_item=id_to_item))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_type_index(type_name: str, items: list[Item], out_path: Path) -> str:
    out_dir = out_path.parent
    id_to_item: dict[str, Item] = {item.id: item for item in items}
    items_for_type = _sort_items([item for item in items if item.type == type_name])
    now = dt.datetime.now().astimezone().replace(microsecond=0).isoformat(sep=" ", timespec="minutes")

    lines: list[str] = []
    lines.append(f"# {TYPE_TITLES.get(type_name, type_name)}")
    lines.append("")
    lines.append(f"_Generated by `scripts/generate_state_index.py` on {now}._")
    lines.append("")
    lines.append("Canonical items live in `state/items/`.")
    lines.append("")
    if not items_for_type:
        lines.append("_No items._")
        lines.append("")
        return "\n".join(lines)

    lines.extend(_render_table(items_for_type, out_dir=out_dir, id_to_item=id_to_item))
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate scannable state tables from state/items/*.md.")
    parser.add_argument("--repo-root", default=".", help="Path to repo root (default: .).")
    parser.add_argument("--items-dir", default="state/items", help="Directory containing state item markdown files.")
    parser.add_argument("--out", default="state/INDEX.md", help="Output markdown path for the full index.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    items_dir = (repo_root / args.items_dir).resolve()
    out_path = (repo_root / args.out).resolve()

    if not items_dir.exists():
        raise SystemExit(f"Items dir not found: {items_dir}")

    items = load_items(repo_root=repo_root, items_dir=items_dir)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_index(items=items, out_path=out_path), encoding="utf-8")

    for type_name, rel_out in TYPE_INDEX_OUTPUTS.items():
        type_path = (repo_root / rel_out).resolve()
        type_path.write_text(render_type_index(type_name=type_name, items=items, out_path=type_path), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
