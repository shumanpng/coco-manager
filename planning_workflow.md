# Planning workflow (atomic items + generated dashboards)

This repo uses **one Markdown file per planning item** (e.g. backlog item `B007`), and **generated dashboard pages** for scannable tables.

The single source of truth is the individual item file in `planning/items/`. Dashboard pages are derived outputs.

## Folder layout

- Canonical items: `planning/items/`
  - Examples: `planning/items/B007.md`, `planning/items/B001.md`
- Generated dashboards:
  - Full index: `planning/INDEX.md`
  - Horizon view: `planning/horizons.md`
- Scripts (under `scripts/` at your notes-dir root, copied there by `init.sh`):
  - Generate dashboards: `scripts/generate_planning_index.py` (or `make planning-index`)
  - Derive `blocking` lists from `blocked_by`: `scripts/derive_blocking.py`

## Item file format (source of truth)

Each item is a normal `.md` file with YAML frontmatter at the top (Obsidian “Properties”).

Required frontmatter fields:

- `id`: stable ID like `B007`
- `title`: short, scannable title
- `status`: `todo | in_progress | done | archived`
- `horizon`: `now | next | later | unscheduled`

Recommended fields used in tables:

- `priority`: `P0 | P1 | P2 | P3` (optional)
- `kind`: `experiment | engineering | analysis | docs | maintenance | reading | writing` (optional)
- `tags`: list of strings (optional)
- `blocked_by`: list of IDs (optional), e.g. `[B008, Q003]`
- `blocking`: list of IDs (optional), e.g. `[B002, B004]`
- `related`: list of IDs (optional), e.g. `[H001, F003]`
- `created_on`: `YYYY-MM-DD` (optional)
- `due_by`: `YYYY-MM-DD` (optional)

Template: `instructions/planning/_template_item.md`

## Regenerating dashboards

Run (from your notes-dir):

```
make planning-index
```

If `blocked_by` changed, run `python scripts/derive_blocking.py` first to refresh `blocking` lists, then `make planning-index`.

This rewrites:

- `planning/INDEX.md`
- `planning/horizons.md`

## Adding a new item

1. Pick the next ID (keep IDs stable; don’t reuse).
2. Create `planning/items/<ID>.md` (e.g., `B011.md`).
3. Fill in frontmatter + a short body with goal/next-step/evidence.
4. Regenerate dashboards: `make planning-index`.
