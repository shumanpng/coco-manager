# State workflow (atomic items + generated indexes)

This repo uses **one Markdown file per state item** (hypothesis / question / assumption / finding / decision), and **generated index pages** for “at-a-glance” tables.

The single source of truth is the individual item file in `state/items/`. Index pages are derived outputs.

## Why

Long, monolithic `state/*.md` files were hard to scan and maintain. Atomic items make updates easy, and generated tables make prioritization fast without hand-maintaining indexes.

## Folder layout

- Canonical items: `state/items/`
  - Examples: `state/items/H001.md`, `state/items/Q004.md`, `state/items/A002.md`, `state/items/F003.md`
- Generated “tables”:
  - Full index: `state/INDEX.md`
  - Per-type indexes: `state/hypotheses.md`, `state/open_questions.md`, `state/assumptions.md`, `state/findings.md`, `state/decisions.md`
- Scripts (under `scripts/` at your notes-dir root, copied there by `init.sh`):
  - Generate indexes: `scripts/generate_state_index.py` (or `make state-index`)
  - Derive `blocking` lists from `blocked_by`: `scripts/derive_blocking.py`

## Item file format (source of truth)

Each item is a normal `.md` file with YAML frontmatter at the top (Obsidian calls these “Properties”).

Required frontmatter fields:

- `id`: stable ID like `H001`, `Q004`, …
- `type`: `hypothesis | question | assumption | finding | decision`
- `title`: short, scannable title
- `status`: per-type status value (see below)

Recommended fields used in tables:

- `priority`: `P0 | P1 | P2 | P3` (optional)
- `review_by`: `YYYY-MM-DD` (optional; acts like a revisit “deadline”)
- `impact`: `low | medium | high` (optional)
- `blocked_by`: list of IDs (optional), e.g. `[Q004]`
- `blocking`: list of IDs (optional), e.g. `[H002]`
- `related`: list of IDs (optional), e.g. `[H002, F003]`
- `created_on`: `YYYY-MM-DD` (optional)
- `last_verified`: `YYYY-MM-DD` (optional)

Status conventions:

- hypotheses: `to_test | supported | refuted | unclear`
- questions: `open | resolved`
- assumptions: `current | invalidated | uncertain`
- findings: `current | outdated`
- decisions: `accepted | superseded`

Template: `instructions/state/_template_item.md`

## Editing workflow (Obsidian-friendly, git-first)

1. Open your notes-dir as an Obsidian vault.
2. Open an item file under `state/items/`.
3. Edit its Properties (frontmatter) via Obsidian UI (or edit YAML directly).
4. Commit normally; diffs are just changes to `.md` files in your git repo.

Important: The index pages do **not** update live. They are generated.

## Regenerating the index pages

Run (from your notes-dir):

```
make state-index
```

If `blocked_by` changed, run `python scripts/derive_blocking.py` first to refresh `blocking` lists, then `make state-index`.

This rewrites:

- `state/INDEX.md`
- `state/hypotheses.md`
- `state/open_questions.md`
- `state/assumptions.md`
- `state/findings.md`
- `state/decisions.md`

When to regenerate:

- after a batch of item edits
- before/after meetings
- before pushing if you want the dashboards to reflect your latest changes

## Adding a new item

1. Pick the next ID (keep IDs stable; don’t reuse).
2. Create `state/items/<ID>.md` (e.g., `Q006.md`).
3. Fill in frontmatter + a short body with evidence/next-step.
4. Regenerate indexes: `make state-index`.

## Linking “blocked by”, “blocking”, and “related”

- Use IDs in `blocked_by` / `blocking` / `related` lists (e.g., `blocked_by: [Q004]`).
- The generator links to those items if they exist; otherwise it renders the ID as code.

## Notes on “last updated”

The generated tables include `last_updated` based on git history when available, with a filesystem timestamp fallback for new/untracked files. You don’t need to manually maintain a “last updated” property.

