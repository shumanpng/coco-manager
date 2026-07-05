---
name: end-session
description: End-of-session skill. Helps the user fill out the Summary section of today's worklog, update planning backlog items, and suggest new state items. Use when the user invokes /end-session or says they are done for the day.
allowed-tools: Read, Edit, Glob, Write, Bash
---

You are helping the user wrap up their work session by completing the `## Summary` section of today's worklog. Follow these steps:

## Step 0: Resolve project and load configuration

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Parse the `PROJECTS:` block in meta.md. Each project is a nested block: the project name is the outer key, and it contains named directory keys (e.g., `worklogs`, `weekly-planning`) mapping to absolute paths.

- If the file doesn't exist or contains no projects, stop and tell the user:
  > "No projects configured. Run `/setup` to get started."

**Resolve which project to use:**

- Count the number of projects in the map.
- If there is exactly **one** project: use it automatically, regardless of `$ARGUMENTS`.
- If there are **multiple** projects:
  - Check if the first word of `$ARGUMENTS` matches a project name (case-sensitive).
  - If it matches: use that project. Treat the remainder of `$ARGUMENTS` (after the first word) as the arguments for the steps below.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/end-session project-a`"

Once the project is resolved, extract:
- `WORKLOGS_DIR` = the `worklogs` path for the project
- `PLANNING_DIR` = the `planning` path for the project (if present in meta.md)
- `STATE_DIR` = the `state` path for the project (if present in meta.md)
- `MEETINGS_DIR` = the `meetings` path for the project (if present in meta.md)
- `INSTRUCTIONS_DIR` = the `instructions` path for the project (required — `init.sh` sets it and `/setup` validates it)

**Print a confirmation line immediately — before doing any other work:**
> Using project: **[project-name]** | worklogs: `[WORKLOGS_DIR]` | planning: `[PLANNING_DIR]` | state: `[STATE_DIR]` | meetings: `[MEETINGS_DIR or "not configured"]`

Use these paths in all steps below.

## Step 1: Find today's main worklog

Use Glob to list `.md` files in `WORKLOGS_DIR` that start with today's date (YYYY-MM-DD, available in your system context) and do NOT start with `_`.

**Exclude sublogs from this list.** A file is a sublog if its name contains `_sublog_` **or** its YAML front matter has a `parent_worklog` field. Sublogs are per-task session records created by `/co-work`; they are gathered in Step 1.6, not here. What remains after excluding sublogs is the candidate main worklog.

- If exactly one main worklog matches: use it.
- If multiple match: show the list and ask the user which one.
- If none match: tell the user no worklog was found for today, and ask if they want to create one with `/new-worklog`.

## Step 1.5: Scan for today's meeting notes

Only run this step if `MEETINGS_DIR` is configured.

Use Glob to list `.md` files in `MEETINGS_DIR` that start with today's date (YYYY-MM-DD) and do NOT start with `_`.

For each file found, read its YAML front matter and classify it:
- **Unprocessed**: `processed_on` is null or absent — `/process-meeting` has never been run on it
- **Pending link**: `processed_on` is set but `worklog` is `"pending"` — extracted but not yet linked to a worklog
- **Already linked**: `worklog` contains a file path — nothing to do

Report to the user before continuing:
> Found [N] meeting note(s) for today: [list filenames]
> - Unprocessed (run `/process-meeting` to extract): [list or "none"]
> - Pending worklog link (will be linked in Step 4): [list or "none"]
> - Already linked: [list or "none"]

If there are **unprocessed** notes, tell the user:
> These notes were not processed with `/process-meeting`. Decisions and action items inside them will **not** be proposed as planning or state items in this session. Consider running `/process-meeting [filename]` after this session, or now before continuing.

Do NOT block the rest of end-session on unprocessed notes — continue regardless.

## Step 1.6: Gather today's sublogs (co-working sessions)

`/co-work` sessions record their work in **sublogs** — per-task files named `YYYY-MM-DD_sublog_<task>.md`, each with a `parent_worklog` front-matter field pointing at the main worklog. A single day may have several.

Use Glob to list today-dated `.md` files in `WORKLOGS_DIR` whose name contains `_sublog_` **or** whose front matter has a `parent_worklog` field. Keep those whose `parent_worklog` points at the main worklog from Step 1 (also include a `_sublog_`-named file that has no `parent_worklog`). Read **all** kept sublogs in full.

Report (if none are found, say so and continue — the rest of the skill just uses the main worklog):
> Found [N] sublog(s) for today: [list filenames, or "none"] → linked to [main worklog].

Treat every sublog as **first-class source material** for the rest of this skill. The main worklog often only links to its sublogs, so the actual decisions, findings, outputs, and design notes usually live in the sublogs. **Wherever a step below says "the worklog," read it as "the main worklog *and* all of today's sublogs."**

**Read-only:** end-session **never writes to a sublog.** Every write lands in the main worklog (`## Summary`, `## Distilled information corner`, `## Tasks`) or in planning/state items. Sublogs are consumed as input only.

## Step 2: Read the worklog and its sublogs

Read the main worklog and every sublog from Step 1.6, and identify (across all of them):
- Current state of `## Tasks` (checked vs unchecked) — in the main worklog
- Anything already written in `## Summary` — in the main worklog
- Content in `## Work log` (chain-of-thought entries), plus `## Design decisions` and any outputs manifests — in the main worklog **and each sublog** (the sublogs usually carry the bulk of the session's reasoning and results)

## Step 2.5: Draft and confirm Distilled information corner

**A) Gather repo state**

Run the following commands in the worklog's project directory. If the directory is not a git repo, note that and skip:
```bash
git branch --show-current
git log -1 --format="%H %s"
git status
```
Show the output to the user and ask them to confirm it looks correct before proceeding.

**B) Draft the update**

From the main worklog **and all of today's sublogs** (`## Work log`, `## Tasks`, `## Design decisions`, outputs manifests, and any already-written `## Summary`), extract and draft updates for `## Distilled information corner`. Derive this directly from the worklog — do not ask open-ended questions. Use only the headings below that have content (omit empty ones):

- **What changed**: high-level summary of what was worked on this session
- **Decisions + rationale**: choices made and why (include trade-offs considered)
- **Key findings/results**: results useful beyond this session; include numbers/metrics when present; do not invent — mark "unknown" if missing
- **Risks/unknowns**: open questions or things that could go wrong
- **Commands & entrypoints**: key commands run this session; derive env vars from worklog text
- **Scripts (usage)**: for scripts developed or modified — capture location, purpose, inputs/outputs, flags, dependencies, expected runtime, 1–2 known-good invocations, required env vars, expected artifacts, one-line "success looks like", common failure modes
- **Glossary**: new or redefined terminology introduced this session
- **Cleanup/rollback notes**: temporary hacks, debug flags, or local-only steps that need reverting

**C) Show preview and confirm**

Present the full drafted content as a preview. Ask the user to confirm or request edits — do not ask open-ended reflection questions. Only write to `## Distilled information corner` after the user confirms.

Use Edit to append under each heading **in the main worklog**. Do not overwrite existing content unless the user explicitly requests it.

## Step 3: Ask the user to reflect

Ask the user the following (you can ask all at once):
1. What's blocked or unresolved?
2. What are the top 2–3 next actions for the next session?

Also ask: should any task statuses be updated (e.g. mark things as done)?

## Step 4: Update the worklog

Using the user's answers:
- Update task checkboxes and status labels in `## Tasks` where applicable
- Fill in the sections below inside `## Summary`. If a section heading does not exist in the worklog, create it.
- Fill in `### Start here next session` with a structured handoff:
  - 1–3 files to open first (derived from the main worklog, today's sublogs, and the user's answers)
  - 1–3 commands to run first (derived from the main worklog, today's sublogs, and the user's answers)
- Fill in `### In-progress tasks (ordered)` for each unfinished task using this mini-template, pulling current state / next step / blockers / file pointers from the main worklog **and today's sublogs**:
  - Goal:
  - Current state:
  - Next smallest step (the very first thing to do next session):
  - Blocked by / open questions:
  - Relevant files / commands:
- Fill in `### Blockers / waiting` with any blockers the user named
- Fill in `### Next actions` with the numbered list the user provided
- Do NOT modify `## Work log` or `## Goal/Outcome` unless the user explicitly asks
- Do NOT modify `## Distilled information corner` in this step — that was handled in Step 2.5
- Do NOT modify any sublog — all writes go to the **main** worklog (sublogs are read-only input to end-session)

**Meeting note linkage (if MEETINGS_DIR is configured):** For any **pending-link** meeting notes identified in Step 1.5, do the following for each:
1. Add a completed task entry to `## Tasks` in the worklog (if one doesn't already exist):
   `- [x] Meeting: [title from front matter](relative/path/to/meeting/note.md)`
2. Use Edit to update the meeting note's front matter: change `worklog: "pending"` to `worklog: "[absolute path to this worklog file]"`

Do this automatically without asking — it is non-destructive housekeeping.

## Step 5: Confirm

Show the user the updated `## Summary` section and ask if they want any changes.

## Step 6: Backlog management

Only run this step if `PLANNING_DIR` is configured. Read `INSTRUCTIONS_DIR/planning/_backlog_update_instructions.md` in full and follow its step-by-step process. The source for this session is today's worklog **and its sublogs** (not a range of days). In brief:

**A) Extract candidates**: From the main worklog **and today's sublogs** (`## Tasks`, `## Work log`, `## Design decisions`, `## Summary`), identify new tasks/TODOs, completed items, and changed scope. Apply the "What belongs in planning" criteria from the instructions file.

**B) Reconcile**: Read `PLANNING_DIR/INDEX.md` first (one file) to get a full list of existing items with id, title, tags, and status — use this to screen for potential matches before opening any individual item file. Only read `PLANNING_DIR/items/B###.md` for IDs flagged as potential matches. Then follow the instructions file's reconciliation step — update existing items in place rather than duplicating; mark completed items `status: done`; mark irrelevant items `status: archived`.

**C) Confirm with user first**: Follow the instructions file's confirmation step — present all proposed creates and updates before writing any file. Wait for explicit confirmation.

**D) Write and regenerate**: After confirmed changes, write items using `INSTRUCTIONS_DIR/planning/_template_item.md`. Regenerate dashboards:
- First try: `cd {PLANNING_DIR}/.. && make planning-index`
- If that fails: `python {PLANNING_DIR}/../scripts/generate_planning_index.py --repo-root {PLANNING_DIR}/.. --items-dir planning/items --out-index planning/INDEX.md --out-horizons planning/horizons.md`

**E) Mirror in_progress items into Summary**: If any newly created/updated items have `status: in_progress` and are absent from `## Summary → In-progress tasks`, add them using the mini-template (Goal / Current state / Next smallest step / Blocked by / Relevant files).

## Step 7: State item suggestions

Only run this step if `STATE_DIR` is configured. Read the detailed instructions from `INSTRUCTIONS_DIR/state/_state_update_instructions.md` and scan `STATE_DIR/INDEX.md` for existing items. This is a light single-pass scan of today's worklog and its sublogs.

**A) Extract candidates**: From the main worklog **and today's sublogs**, identify durable, evidence-backed items:
- **Findings** (results useful beyond this session; include numbers when present)
- **Decisions** (choice + rationale + consequences)
- **Hypotheses** (testable claims with an explicit status)
- **Assumptions** (things being relied on, or assumptions invalidated this session)
- **Open questions** (unresolved questions + smallest disambiguating test)

Skip: unverified hunches, narrative/debug logs, items already captured as planning items.

**B) Check for duplicates**: Compare candidates against `STATE_DIR/INDEX.md`. Note the existing ID if a candidate updates an existing item.

**C) Propose to user**: For each candidate, show:
- Proposed type, ID, and title
- One-line rationale
- Evidence pointer (worklog section or file path)
- New or update to existing item (include existing ID if so)
- Flag any conflicts with existing items explicitly

**Wait for explicit confirmation before creating or modifying any state file.**

**D) Add confirmed items**: Use Write to create files in `STATE_DIR/items/` following `INSTRUCTIONS_DIR/state/_template_item.md`. For updates to existing items, use Edit to change only the fields that changed (add evidence pointer, update `last_verified`). Do not flip status to `superseded/refuted/invalidated` — leave that for the periodic batch update.

**E) Reflect in Distilled information corner**: If any confirmed state items are missing or only partially captured in `## Distilled information corner`, add them under the appropriate heading with a link to the item ID (e.g., `[F007](../state/items/F007.md)`).

## Important rules
- Never write to a sublog — end-session's only write targets are the main worklog, planning items, and state items. Sublogs are read-only session input.
- Only update what the user confirms — do not auto-fill anything based on guesses
- Use Edit tool to make targeted changes, not rewrite the whole file
- Never remove or overwrite existing content without asking
- Don't guess: if details, metrics, or script usage are missing from the worklog, mark as "unknown" rather than inventing; ask only when critical for the handoff
- Don't include long raw logs or stack traces — keep only key error signatures and their context
- Exclude transient chat and repeated debug outputs; prioritize durable knowledge and resumption steps
- Prefer pointers (file paths, symbol names, commands) over vague "we did X" phrasing
