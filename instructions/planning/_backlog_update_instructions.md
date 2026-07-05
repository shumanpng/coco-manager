# Planning update instructions (from state + a range of worklogs)

This repo uses atomic planning items under `{PLANNING_DIR}/items/` as the canonical source of truth.

Use this process to update planning items based on:

- the current canonical state in `{STATE_DIR}/`, and
- a specified range of worklogs under `{WORKLOGS_DIR}/` (e.g., “2026-01-05 to 2026-01-12” or an explicit list of worklog files).

The goal: keep planning items canonical and actionable, and regenerate dashboards:

- `{PLANNING_DIR}/INDEX.md`
- `{PLANNING_DIR}/horizons.md`

## Inputs (provide these up front)

1. Worklog range:
   - Start date (inclusive) and end date (inclusive), OR
   - Explicit list of worklog file paths under `{WORKLOGS_DIR}/`
2. Scope focus (optional but recommended):
   - What to prioritize (e.g., “auth-flow refactor”, “flaky-test triage”, “API migration”)
3. Backlog policy knobs (optional):
   - Max number of `Ready` items (default: 5–10)
   - Whether to auto-create “maintenance” items (default: no)

If the range is ambiguous, list what you found and ask for confirmation before updating the backlog.

## Files involved

- Canonical items: `{PLANNING_DIR}/items/*.md`
- Template: `./_template_item.md`
- Generated outputs: `{PLANNING_DIR}/INDEX.md`, `{PLANNING_DIR}/horizons.md`
- Primary sources:
  - `{STATE_DIR}/*` (assumptions, decisions, findings, hypotheses, open questions)
  - `{WORKLOGS_DIR}/*.md` (recent work and newly discovered follow-ups)

## What belongs in planning items (and what doesn’t)

Include:

- Concrete follow-up work implied by `{STATE_DIR}/open_questions.md` (with a smallest disambiguating test)
- Hypothesis tests and experiments implied by `{STATE_DIR}/hypotheses.md`
- Engineering tasks required to operationalize/validate state claims (scripts, eval expansion, cleanup)
- Blockers that need targeted resolution (with a dependency list and a next step)
- Worklog TODOs that are still relevant and not already tracked elsewhere

Do not include:

- Narrative session notes (keep those in worklogs)
- Vague ideas without a “next smallest step” (convert them into a well-scoped item or keep them out)
- Duplicates (merge and preserve evidence pointers)
- Prose-only “Now/Next/Later” lists (use `horizon` on items instead)

## Evidence requirements (minimum bar)

Every backlog item must have pointers in “Evidence / pointers”:

- Related state items (IDs like `Q001`, `H002`, `F003`, etc.) when applicable
- Worklog paths that motivated the item
- Artifact paths under `results/` or `evaluation/` when applicable
- Code/scripts entrypoints when applicable

If evidence is missing, include a brief “unknown” note in the item’s evidence section (do not invent).

## Step-by-step process

### 1) Load context from state (canonical)

Read the per-type state index files first — do not read individual item files at this stage:

- `{STATE_DIR}/open_questions.md`
- `{STATE_DIR}/hypotheses.md`
- `{STATE_DIR}/findings.md`
- `{STATE_DIR}/decisions.md`
- `{STATE_DIR}/assumptions.md`

Each file is a generated table with id, title, status, priority, related, and last_verified — enough to identify which items imply follow-up work. Only read the full `{STATE_DIR}/items/X###.md` file for a specific item if its title/tags suggest a backlog implication that requires deeper context (e.g., the `## Next step` or `## Evidence` section).

Extract candidate backlog items from what you find:

- **Open questions** → backlog items whose “Next smallest step” is the disambiguating test
- **Hypotheses** → backlog items whose “Next smallest step” is a minimal experiment
- **Findings** → backlog items when findings imply follow-up (e.g., “expand test coverage”, “confirm a fix”)
- **Decisions/assumptions** → backlog items only when implementation is incomplete or risk is high (e.g., “add guardrails”, “document runbook”)

### 2) Collect worklogs in range

- Identify worklog files in the requested range under `{WORKLOGS_DIR}/`.
- Extract unfinished tasks, bugs, inconsistencies, and “next session” bullets that are still relevant.
- Prefer durable items; ignore one-off debugging unless it still blocks progress.

### 3) Derive/shape candidate planning items

For each candidate, ensure it is actionable and rankable:

- Use the structure from `./_template_item.md`
- Require:
  - `Problem / Goal`
  - `Next smallest step` (single command/change/measurement)
  - `Success looks like` (measurable outcome or acceptance criteria)
  - `Dependencies / blockers` (if any)

If the item is primarily research/diagnosis, write the next step as the smallest experiment that reduces uncertainty.

### 4) Reconcile with existing items (dedupe + lifecycle)

**4a — Index scan first (one read):** Read `{PLANNING_DIR}/INDEX.md`. This file lists all existing items with id, title, status, horizon, kind, tags, and related — sufficient for preliminary duplicate screening. Do not open any `{PLANNING_DIR}/items/*.md` file yet.

**4b — Selective deep read:** For each candidate from steps 1–3, scan the index for potential matches: title keyword overlap, matching tags, or shared related IDs. Only read the full `{PLANNING_DIR}/items/B###.md` file for IDs flagged as potential matches. Do not read items whose titles and tags have no plausible topical overlap with the candidate.

**4c — Reconcile:** Using the index and the selectively-read item content:

- If an item already exists: update it in place; do not duplicate.
- If the scope changed: update the title and “Proposed approach”, preserving prior evidence pointers.
- If it’s resolved in the worklog range: move to `Done / Obsolete` and add the resolving evidence.
- If it is not actionable yet: set `status: icebox` and explain what must change to make it actionable.

### 5) Set `status` and `horizon` consistently

Use item properties instead of monolithic sections:

- `status`: `todo | in_progress | done | archived`
- `horizon`: `now | next | later | unscheduled`

Rank/scan via the generated dashboards (`{PLANNING_DIR}/INDEX.md`, `{PLANNING_DIR}/horizons.md`).

### 6) Set metadata consistently

For each updated/created item:

- `created_on`: date of earliest motivating state/worklog entry (if known; else use the oldest in-range worklog date)
- `updated_on`: date of newest supporting worklog in the range
- `priority/impact/effort/risk`: set conservatively; if unknown, set `P2/medium/medium/medium` and add a note
- `owner`: optional; leave blank if unknown
- `due_by`: only set if explicitly discussed; do not guess

### 7) Post-update consistency check

Before finishing:

- Every `todo` item has a concrete “Next smallest step” and “Success looks like”.
- Every item has at least one evidence pointer (state/worklog/code/artifact).
- No duplicates; no “orphan” IDs referenced but missing.

Then regenerate dashboards:

- `make planning-index` (from your notes-dir)

## Expected output (what “done” looks like)

- Canonical planning items live in `{PLANNING_DIR}/items/*.md` and include evidence pointers.
- `{PLANNING_DIR}/INDEX.md` and `{PLANNING_DIR}/horizons.md` reflect the current items after regeneration.
