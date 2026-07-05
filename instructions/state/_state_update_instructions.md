# State update instructions (from a range of worklogs)

This repo uses **atomic state items**: one Markdown file per state item under `{STATE_DIR}/items/`. The scannable tables under `{STATE_DIR}/` are **generated** (do not edit them by hand).

Reference: [`state_workflow.md`](../../state_workflow.md) (at the public repo root) for the conceptual overview.

After editing items, regenerate the scannable tables (from your notes-dir):

- `make state-index`

The index outputs:

- `{STATE_DIR}/INDEX.md` (all items)
- `{STATE_DIR}/hypotheses.md`, `{STATE_DIR}/open_questions.md`, `{STATE_DIR}/assumptions.md`, `{STATE_DIR}/findings.md`, `{STATE_DIR}/decisions.md` (per-type tables)

Use this process to update `{STATE_DIR}/` based on a specified range of worklogs (e.g., “2026-01-05 to 2026-01-12” or an explicit list of `{WORKLOGS_DIR}/*.md` files).

The goal: distill *durable* knowledge and keep `{STATE_DIR}/` as the canonical current understanding, with clear history when things change.

## Inputs (provide these up front)

1. Worklog range:
   - Start date (inclusive) and end date (inclusive), OR
   - Explicit list of worklog file paths under `{WORKLOGS_DIR}/`
2. Scope focus (optional but recommended):
   - What topics to prioritize (e.g., “payment retries”, “cache invalidation”, “error-rate spike”)
3. Repo context (optional):
   - Relevant branches/commits if needed to interpret results

## Files to update (typical)

- Canonical source-of-truth items: `{STATE_DIR}/items/*.md` (e.g., `{STATE_DIR}/items/Q004.md`, `{STATE_DIR}/items/D009.md`)
- Template for new items: `./_template_item.md`
- Generated outputs (do not edit manually): `{STATE_DIR}/INDEX.md`, `{STATE_DIR}/{hypotheses,open_questions,assumptions,findings,decisions}.md`

Use `./_template_item.md` for new entries or when you need a consistent structure.

## What belongs in state (and what doesn’t)

Include in `{STATE_DIR}/items/`:

- Distilled findings/results that remain useful beyond the day they were discovered
- Assumptions currently being relied on, and assumptions that were invalidated (with evidence)
- Hypotheses with explicit status (to_test/supported/refuted/unclear)
- Open questions + the smallest disambiguating test
- Design decisions + rationale + consequences (and superseding links when changed)

Do not include in `{STATE_DIR}/items/`:

- Long narrative/debug logs (keep in worklogs)
- Unverified hunches without a path to verification (convert to an “open question” with a test)
- Duplicate entries that say the same thing (merge and link)

## Evidence requirements (minimum bar)

Every state update driven by worklogs should include pointers:

- Worklog file path(s) (the evidence trail)
- Commands/scripts used (if present)
- Artifact paths under `results/` (if present)
- Code/script pointers (paths and key function/module names if relevant)

If any of these are missing in the worklogs, add a note under the entry’s “Evidence” section indicating what is unknown.

## Step-by-step process

### 1) Collect the worklogs in range

- Identify all files under `{WORKLOGS_DIR}/` that fall in the requested range.
- If the range is ambiguous (multiple worklogs on same date, gaps, etc.), list what you found and ask for confirmation.

### 2) Extract candidate updates

As you read each worklog, maintain a scratch list of candidate items:

- Findings (numbers, comparisons, qualitative outcomes)
- Assumptions (explicit or implicit “we assume X”)
- Hypotheses (statements that could be supported/refuted)
- Open questions / unclear results (and proposed disambiguation)
- Design decisions (choices made + rationale)

Only promote an item to `{STATE_DIR}/items/` if it’s durable and has an evidence pointer.

### 3) Reconcile with existing state (dedupe + lifecycle)

For each candidate, build a proposed change list — do not edit any files yet:

**3a — Index scan first (one read):** Read `{STATE_DIR}/INDEX.md` (or the relevant per-type file: `{STATE_DIR}/open_questions.md`, `{STATE_DIR}/hypotheses.md`, `{STATE_DIR}/assumptions.md`, `{STATE_DIR}/findings.md`, `{STATE_DIR}/decisions.md`). These generated tables provide id, title, status, priority, related, and last_verified for all items — sufficient for preliminary duplicate detection. Do not open any `{STATE_DIR}/items/*.md` file yet.

**3b — Selective deep read:** For each candidate, scan the index/per-type table for title keyword overlap or shared related IDs. Only read the full `{STATE_DIR}/items/X###.md` for IDs flagged as potential matches. Do not read items whose titles have no plausible topical overlap with the candidate.

**3c — Reconcile:** Using the index and the selectively-read item content:

- Check whether the claim already exists as an item.
  - If yes: propose updating the existing item (don’t create a duplicate).
  - If no: propose a new item file using `./_template_item.md` (pick the next ID; don’t reuse IDs).
- If a worklog contradicts existing “current” state:
  - Propose flipping the old entry to `invalidated/refuted/superseded` (don’t delete it).
  - Note the reason + evidence pointer, and identify the replacement entry.
  - Do not apply this change until confirmed by the user in step 3b.
- If evidence is mixed or the contradiction is ambiguous (both sides have plausible evidence, recency is unclear, or the conflict is partial):
  - Propose `status: uncertain/unclear` and draft a “What Would Change My Mind” note.
  - Do not flip to a terminal status (`refuted`, `superseded`, `invalidated`) without explicit user confirmation.

### 3b) Confirm proposed changes with user

Before creating or modifying any item file, present the full change list:

- **New items to add**: proposed type, ID, title, and one-line claim
- **Existing items to update** (non-status changes): ID and what fields will change (e.g., adding evidence pointer, updating `last_verified`)
- **Status changes**: for each proposed status flip (e.g., `current` → `superseded`, `to_test` → `refuted`), state explicitly: current status, proposed new status, and the evidence driving the change

Ask the user to confirm, reject, or adjust each proposed change before proceeding. If the user is uncertain about a conflict, default to `status: uncertain` with a disambiguation note rather than leaving it unresolved.

### 4) Update metadata for changed items

For each updated or newly added entry:

- Update `updated_on: YYYY-MM-DD` (use the date of the newest supporting worklog in the range).
- If the item is “current/supported/accepted” and got reaffirmed:
  - Update `last_verified: YYYY-MM-DD` and set a `review_by` date if appropriate.
- If the item is “invalidated/refuted/superseded/resolved”:
  - Keep the prior text, mark status accordingly, and add pointers to the newer evidence.

### 5) Keep item bodies scannable

Item files should be small and durable:

- Prefer one claim/question/decision per item.
- Keep the body short and link out to worklogs for narrative/debug detail.
- Put statuses/priority/etc. in frontmatter so the generated tables stay useful.

### 6) Post-update consistency check

Before finishing:

- Ensure every “current” assumption/hypothesis has either `last_verified` or `review_by`.
- Ensure every status change has an evidence pointer.
- Ensure question items (type `question`) include a “What would disambiguate this?" in the item body.
- Ensure decisions that changed are marked `superseded` with a link to the newer decision.
- If any `blocked_by` changed, run `python scripts/derive_blocking.py` (from your notes-dir) to refresh `blocking`.
- Regenerate indexes: `make state-index`.

## Expected output (what “done” looks like)

- `{STATE_DIR}/items/*.md` reflects the canonical current understanding after considering the specified worklog range.
- Any outdated claims are preserved but clearly marked as not current.
- Every meaningful entry has a worklog pointer (and artifact/command pointers when available).
- Generated tables have been regenerated so `{STATE_DIR}/INDEX.md` and the per-type index pages reflect the changes.