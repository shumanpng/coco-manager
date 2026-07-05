#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _read_frontmatter(md_text: str) -> tuple[list[str], list[str]] | None:
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1 :]
    return None


def _parse_frontmatter(fm_lines: list[str]) -> dict[str, Any]:
    fm_text = "\n".join(fm_lines)
    data = yaml.safe_load(fm_text) or {}
    return data if isinstance(data, dict) else {}


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        v = value.strip()
        return [v] if v else []
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            if isinstance(v, str) and v.strip():
                out.append(v.strip())
        return out
    return []


def _format_list(values: list[str]) -> str:
    if not values:
        return "[]"
    return "[" + ", ".join(values) + "]"


def _replace_blocking_line(fm_lines: list[str], blocking_values: list[str]) -> list[str]:
    key_idx = None
    for i, line in enumerate(fm_lines):
        if line.strip().startswith("blocking:"):
            key_idx = i
            break

    new_line = f"blocking: {_format_list(blocking_values)}"

    if key_idx is not None:
        # Drop any YAML list items that followed a block-style "blocking:".
        end_idx = key_idx + 1
        while end_idx < len(fm_lines):
            next_line = fm_lines[end_idx]
            if next_line.startswith(" ") or next_line.startswith("\t") or next_line.lstrip().startswith("- "):
                end_idx += 1
                continue
            if ":" in next_line:
                break
            end_idx += 1
        return fm_lines[:key_idx] + [new_line] + fm_lines[end_idx:]

    insert_at = None
    for i, line in enumerate(fm_lines):
        if line.strip().startswith("blocked_by:"):
            insert_at = i + 1
            break
    if insert_at is None:
        for i, line in enumerate(fm_lines):
            if line.strip().startswith("related:"):
                insert_at = i
                break
    if insert_at is None:
        insert_at = len(fm_lines)
    return fm_lines[:insert_at] + [new_line] + fm_lines[insert_at:]


@dataclass
class Item:
    id: str
    path: Path
    blocked_by: list[str]
    blocking: list[str]
    fm_lines: list[str]
    body_lines: list[str]


def _load_items(items_dir: Path) -> list[Item]:
    items: list[Item] = []
    for path in sorted(items_dir.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        fm = _read_frontmatter(text)
        if fm is None:
            continue
        fm_lines, body_lines = fm
        fm_data = _parse_frontmatter(fm_lines)
        item_id = str(fm_data.get("id") or path.stem).strip()
        items.append(
            Item(
                id=item_id,
                path=path,
                blocked_by=_coerce_str_list(fm_data.get("blocked_by")),
                blocking=_coerce_str_list(fm_data.get("blocking")),
                fm_lines=fm_lines,
                body_lines=body_lines,
            )
        )
    return items


def derive_blocking(items: list[Item]) -> dict[str, list[str]]:
    blocking_by_id: dict[str, list[str]] = {item.id: [] for item in items}
    for item in items:
        for blocker_id in item.blocked_by:
            if blocker_id == item.id or blocker_id not in blocking_by_id:
                continue
            if item.id not in blocking_by_id[blocker_id]:
                blocking_by_id[blocker_id].append(item.id)
    for item_id, values in blocking_by_id.items():
        deduped: list[str] = []
        seen: set[str] = set()
        for v in values:
            if v not in seen:
                deduped.append(v)
                seen.add(v)
        blocking_by_id[item_id] = deduped
    return blocking_by_id


def write_updates(items: list[Item], blocking_by_id: dict[str, list[str]]) -> int:
    updated = 0
    for item in items:
        desired = blocking_by_id.get(item.id, [])
        if desired == item.blocking and any(line.strip().startswith("blocking:") for line in item.fm_lines):
            continue
        new_fm_lines = _replace_blocking_line(item.fm_lines, desired)
        new_text = "\n".join(["---", *new_fm_lines, "---", *item.body_lines])
        if item.path.read_text(encoding="utf-8").endswith("\n"):
            new_text += "\n"
        item.path.write_text(new_text, encoding="utf-8")
        updated += 1
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive blocking lists from blocked_by across state/items and planning/items (relative to --repo-root)."
    )
    parser.add_argument("--repo-root", default=".", help="Path to repo root (default: .).")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    state_dir = repo_root / "state" / "items"
    planning_dir = repo_root / "planning" / "items"

    items = _load_items(state_dir) + _load_items(planning_dir)
    blocking_by_id = derive_blocking(items)
    updated = write_updates(items, blocking_by_id)
    print(f"Updated {updated} item files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
