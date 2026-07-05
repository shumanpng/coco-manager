---
name: process-meeting
description: Processes a meeting note by extracting decisions, action items, and open questions into planning backlog items and state items. Links the meeting note to the worklog matching the meeting date (not necessarily today). Use when the user invokes /process-meeting or wants to sync a meeting note into the planning/state system.
allowed-tools: Read, Edit, Glob, Write, Bash
---

You are processing a meeting note to extract durable knowledge into the planning and state systems, and to link the note to the appropriate worklog (defaulting to the meeting's date, not today's date). Follow these steps:

## Step 0: Resolve project and load configuration

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Parse the `PROJECTS:` block in meta.md.

- If the file doesn't exist or contains no projects, stop and tell the user:
  > "No projects configured. Run `/setup` to get started."

**Resolve which project to use:**

- If exactly **one** project: use it automatically.
- If **multiple** projects:
  - Check if the first word of `$ARGUMENTS` matches a project name (case-sensitive).
  - If it matches: use that project. Treat the remainder of `$ARGUMENTS` as the file argument.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b`. Example: `/process-meeting project-a 2026-02-22-standup.md`"

Once the project is resolved, extract:
- `WORKLOGS_DIR` = the `worklogs` path for the project
- `MEETINGS_DIR` = the `meetings` path for the project
- `PLANNING_DIR` = the `planning` path for the project (if present)
- `STATE_DIR` = the `state` path for the project (if present)
- `INSTRUCTIONS_DIR` = the `instructions` path for the project (required — `init.sh` sets it and `/setup` validates it)

If `MEETINGS_DIR` is not configured, stop and tell the user:
> "No `meetings` directory configured for this project. Run `/setup` to add one."

**Print a confirmation line immediately:**
> Using project: **[project-name]** | meetings: `[MEETINGS_DIR]` | worklogs: `[WORKLOGS_DIR]`

## Step 1: Identify the meeting note

**From `$ARGUMENTS`** (after project name is stripped, if applicable):
- If a `.md` filename or path is provided: resolve it relative to `MEETINGS_DIR` if not absolute. Read it to confirm it exists.
- If a date string (YYYY-MM-DD) is provided: glob `MEETINGS_DIR/[date]*.md` (excluding `_` prefix files).

**If no argument or no match:**
- Glob `MEETINGS_DIR/[today's date]*.md` (excluding `_` prefix files) for unprocessed candidates (`processed_on: null` or absent).
- If one candidate: confirm with user ("Found today's unprocessed meeting: [filename]. Use this one?")
- If multiple: list them and ask the user to pick.
- If none: ask the user to specify the file path explicitly.

## Step 2: Read the meeting note

Read the full file. Extract:
- Front matter: `date`, `title`, `attendees`, `processed_on`, `worklog`
- Sections: `## Decisions`, `## Action items`, `## Open questions`, `## Notes`

If `processed_on` is already set, warn the user:
> "This note was already processed on [processed_on]. Re-processing will propose additional items but will not duplicate those already created. Continue?"

Wait for confirmation before proceeding.

## Step 3: Check worklog status

Use the **meeting date** (the `date` field from front matter, extracted in Step 2) as the default worklog date — not today's date.

**If meeting date ≠ today's date:**
- Glob `WORKLOGS_DIR/[meeting-date]*.md` (excluding `_` prefix files).
- If exactly one worklog found: confirm with the user in a lightweight way:
  > "Meeting was on [meeting-date]. Link to worklog `[filename]`? (y / different date / skip)"
  - If confirmed: set `WORKLOG_PATH` to its absolute path.
  - If "different date": ask which date, then glob for that date's worklog.
  - If "skip": set `WORKLOG_PATH = "pending"`.
- If multiple: show list, ask user which one.
- If none: set `WORKLOG_PATH = "pending"` and inform the user:
  > "No worklog found for meeting date [meeting-date]. The meeting note will be marked `worklog: pending` and linked automatically when you run `/end-session` or `/new-worklog`."

**If meeting date = today's date:**
- Glob `WORKLOGS_DIR/[today's date]*.md` (excluding `_` prefix files).
- If exactly one worklog found: set `WORKLOG_PATH` to its absolute path.
- If multiple: show list, ask user which one.
- If none: set `WORKLOG_PATH = "pending"` and inform the user:
  > "No worklog found for today. The meeting note will be marked `worklog: pending` and linked automatically when you run `/end-session` or `/new-worklog`."

## Step 4: Identify candidates from meeting note sections

The meeting note sections map to item types as follows — use these as the **source framing**:

| Meeting note section | Target system | Item type |
|---|---|---|
| `## Decisions` | State | `type: decision` |
| `## Action items` | Planning | backlog item |
| `## Open questions` | State | `type: question` |
| `## Notes` | State | `type: finding` — **only** if a concrete, durable insight; skip narrative |

If a section is empty or absent, skip that category entirely.

**For state item candidates:** Apply the criteria and evidence requirements from `INSTRUCTIONS_DIR/state/_state_update_instructions.md` (sections "What belongs in state" and "Evidence requirements") to decide what qualifies. The meeting note path counts as the evidence pointer (`## Evidence → Meeting minutes:`).

**For planning item candidates:** Apply the criteria and evidence requirements from `INSTRUCTIONS_DIR/planning/_backlog_update_instructions.md` (sections "What belongs in planning items" and "Evidence requirements") to decide what qualifies. The meeting note path counts as the evidence pointer.

## Step 5: Reconcile, confirm, and write — follow canonical processes

**For state item candidates:** Follow `INSTRUCTIONS_DIR/state/_state_update_instructions.md` steps 3, 3b, 4, 5, and 6 exactly:
- Step 3: Reconcile against existing `STATE_DIR/items/*.md` — update existing items rather than creating duplicates
- Step 3b: Present all proposed changes to the user (new items / field updates / status flips) and wait for explicit confirmation before writing anything
- Steps 4–6: Write confirmed items, update metadata, run the post-update consistency check, regenerate indices (`cd {STATE_DIR}/.. && make state-index`; if that fails: `python {STATE_DIR}/../scripts/generate_state_index.py --repo-root {STATE_DIR}/.. --items-dir state/items --out state/INDEX.md`)

**For planning item candidates:** Follow `INSTRUCTIONS_DIR/planning/_backlog_update_instructions.md` steps 3–7 exactly:
- Step 3: Shape each candidate (ensure "Next smallest step" and "Success looks like" are present)
- Step 4: Reconcile against existing `PLANNING_DIR/items/*.md` — update in place rather than duplicating
- Steps 5–7: Set status/horizon, set metadata, run consistency check, regenerate dashboards (`cd {PLANNING_DIR}/.. && make planning-index`; if that fails: `python {PLANNING_DIR}/../scripts/generate_planning_index.py --repo-root {PLANNING_DIR}/.. --items-dir planning/items --out-index planning/INDEX.md --out-horizons planning/horizons.md`)

**Meeting note as evidence:** When writing any item, use the meeting note's absolute path as the evidence pointer. For state items, put it under `## Evidence → Meeting minutes:`. For planning items, put it under `### Evidence / pointers → Worklogs:`.

## Step 6: Apply meeting-specific linkage

After confirmed items are written (or if there were no items to write), handle the meeting-note-specific housekeeping:

### A) Link to worklog

If `WORKLOG_PATH` is a real path (not `"pending"`):
- Read the worklog file.
- If the meeting note is not already listed as a task in `## Tasks`, add:
  `- [x] Meeting: [title](relative/path/to/meeting/note.md)`
  Use a relative path from the worklog file to the meeting note.

### B) Update meeting note front matter

Use Edit to update only the front matter fields in the meeting note:
- `processed_on`: today's date (YYYY-MM-DD)
- `worklog`: absolute path to worklog, or `"pending"` if no worklog exists

(`weekly_plan_updated` is set in step 6D below, after the weekly plan is updated.)

### C) Capture presentation & workflow tips

Scan `## Discussion` and `## Notes` for any collaborator suggestions about how to present, visualize, or evaluate (e.g., "make a plot showing X", "use retrieval instead of classification"). For each, append a bullet to `knowledge_base/presentation_and_workflow_tips.md` under the appropriate section, with attribution and a back-link to this meeting note. Skip if none found.

### D) Update weekly plan (required — do not skip)

1. **Fill in `## Weekly plan delta`** in the meeting note, if that section exists:
   - "New items added to this week": planning items newly set to `horizon: now` as a result of this meeting
   - "Items deferred / removed": items demoted or deferred from this week
   - "Priority or scope changes": any horizon/priority shifts
   - "Key decisions to note in Review notes": 1-line summaries of key decisions

   If the section does not exist (older note), skip this sub-step.

2. **Update the current week's plan file**: resolve the current ISO week (YYYY-Www), then glob `PLANNING_DIR/weekly/[current-week].md`.
   - If the file exists: read it, then apply the delta:
     - Add newly urgent items under "Top priorities" or "Planned work (scoped)".
     - Annotate deferred items (e.g. `~~B026~~ — deferred, pending B019`).
     - Append a one-line meeting outcome to `## Review notes`.
   - If no file exists for the current week and the meeting is setting direction for next week: draft `PLANNING_DIR/weekly/YYYY-W(ww+1).md` using `INSTRUCTIONS_DIR/planning/_weekly_plan_template.md`.

   **Direction changes only.** The weekly plan records what shifted in priorities or scope — not activity records (those go in the worklog) or detailed discussion (that stays in the meeting note).

3. **Flip `weekly_plan_updated: true`** in the meeting note's frontmatter using Edit.

## Step 7: Summary

Print a brief summary of what was done:
> Processed: **[meeting title]** ([date])
> - Created/updated [N] planning items: [list IDs]
> - Created/updated [N] state items: [list IDs]
> - Worklog link: [linked to path / set to pending]
>
> Tip: Run `/end-session` to complete today's worklog wrap-up, or `/process-meeting [other-note]` for another meeting.

## Important rules
- Only create or modify items the user explicitly confirms — see `_shared_rules.md`
- The canonical processes in `_state_update_instructions.md` and `_backlog_update_instructions.md` take precedence over anything in this skill — if there is a conflict, defer to those files
- Use Edit for targeted front matter changes in the meeting note, not full file rewrites
- Do not modify `## Discussion` or `## Notes` sections of the meeting note — those are read-only records
