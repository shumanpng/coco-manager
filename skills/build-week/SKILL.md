---
name: build-week
description: Creates or updates this week's focused plan. Reads the planning and state indices (not individual items) for speed, incorporates recent meeting signals, confirms priorities with the user, then writes the weekly plan file. Use when the user invokes /build-week or /build-weekly-plan.
argument-hint: "[project-name if multiple projects configured]"
allowed-tools: Read, Glob, Write, Edit, Bash
---

You are helping the user build a focused weekly plan. Work in **two phases**:
- **Phase 1 (fast):** Read indices and summaries only — no individual `B###.md` files yet. Surface candidates and meeting signals, then confirm priorities with the user.
- **Phase 2 (detailed):** After user confirmation, drill into the top 3 individual planning item files and produce the full plan.

Follow every step in order.

---

## Step 0: Resolve project and load configuration

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Parse the `PROJECTS:` block in meta.md. Each project is a nested block: the project name is the outer key, and it contains named directory keys mapping to absolute paths.

- If the file doesn't exist or contains no projects, stop and tell the user:
  > "No projects configured. Run `/setup` to get started."

**Resolve which project to use:**

- If exactly **one** project: use it automatically, regardless of `$ARGUMENTS`.
- If **multiple** projects:
  - Check if the first word of `$ARGUMENTS` matches a project name (case-sensitive).
  - If it matches: use that project.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/build-week project-a`"

Extract from the resolved project:
- `PLANNING_DIR` = the `planning` path
- `STATE_DIR` = the `state` path
- `WORKLOGS_DIR` = the `worklogs` path
- `WEEKLY_PLANNING_DIR` = the `weekly-planning` path
- `MEETINGS_DIR` = the `meetings` path (may be absent — treat as `null` if not configured)
- `INSTRUCTIONS_DIR` = the `instructions` path for the project (required — `init.sh` sets it and `/setup` validates it)

**Print a confirmation line immediately — before any other work:**
> Using project: **[project-name]**

---

## ── PHASE 1: LIGHTWEIGHT SCAN ──

### Step 1: Read the planning index

Read `{PLANNING_DIR}/INDEX.md`. This is the **only** planning source for Phase 1 — do NOT read any individual `items/B###.md` files yet.

If the file does not exist: note "Planning index not found — skipping candidate extraction" and continue.

Parse every data row in the markdown table, skipping the header and separator rows. Extract per row: `id`, `title`, `status`, `horizon`, `priority`, `impact`, `effort`, `risk`, `kind`, `tags`, `blocked_by`, `due_by`.

Build three groups:

**A. Active** — `status = in_progress` (any horizon)

**B. Ready** — ALL of the following:
  - `status = todo`
  - `horizon = now` or `next`
  - `blocked_by` column is empty

Within group B, sort by: P0 before P1 before P2, then high impact before medium/low. Mark any item with a non-empty `due_by` as deadline-sensitive.

**C. Blocked** — `status` is not `done` AND `blocked_by` is non-empty

### Step 2: Read the state index

Read `{STATE_DIR}/INDEX.md`. If the file does not exist: note "State index not found" and skip to Step 3.

Locate the `## Attention` section. Each entry has the format:
```
- [ID](items/ID.md): title (`status`, `priority`)
```

Group attention items by ID prefix:
- `Q` prefix → **Open questions**
- `H` prefix → **Hypotheses to test**
- `A` prefix → **Uncertain assumptions**
- `D` prefix → **Recent decisions**

Only surface items that appear in `## Attention` — do not read individual state item files in Phase 1.

### Step 3: Read constraints

Constraints live in the weekly plan file's `## Constraints` section — there is no separate `constraints.md` file.

- If an existing weekly plan was found in Step 5: extract the `## Constraints` section to get time budget, compute budget, deadlines, non-goals, and preferences. These are the **standing constraints** carried forward from the previous run.
- If no existing plan was found for this week: check the previous week's plan. Glob `{WEEKLY_PLANNING_DIR}/` for the most recent `YYYY-W##.md` file before this week. If found, read its `## Constraints` section to carry forward standing constraints.
- If no prior plan exists at all: **stop and ask the user:**
  > No prior constraints found. Would you like to specify constraints now (time budget, compute budget, deadlines, non-goals, preferences) before planning begins, or defer and add them after the plan is drafted?

  If the user provides constraints now: record them and use them for prioritization in all subsequent steps.
  If the user defers: proceed without constraints and include the user-provided values (or blanks) in the draft weekly plan's `## Constraints` section at Step 9C.

If `{PLANNING_DIR}/horizons.md` exists: read it for any "now" horizon definition that affects scope.

### Step 4: Read recent meeting notes

If `MEETINGS_DIR` is `null` or not configured: skip this step.

**Determine the current ISO week** (YYYY-Www, e.g. `2026-W09`).

Glob all `.md` files in `MEETINGS_DIR` that do NOT start with `_`. Sort by filename (date prefix descending).

**Priority order:**
1. Meetings from the current week (filename starts with the current week's Monday date or matches `YYYY-Www` in frontmatter `date` field falling within this week).
2. If fewer than 2 current-week meetings exist, supplement with the most recent 1–2 prior-week meetings.

Cap total at **3 meeting notes** to read.

For each selected meeting note, read it and extract:
- Frontmatter: `date`, `title`, `processed_on`, `weekly_plan_updated`
- `## Decisions` section (full text)
- `## Action items` section (all `- [ ]` and `- [x]` lines)
- `## Weekly plan delta` section (if present)

**Flag meetings where `weekly_plan_updated: false`** — these contain priority shifts not yet reflected in the weekly plan file.

### Step 5: Read the existing weekly plan (if any)

Compute current ISO week: `YYYY-Www`.

Glob `{WEEKLY_PLANNING_DIR}/YYYY-W##.md` (zero-padded). If not found, try `YYYY-W#.md` (non-padded). If found: read it and note the existing top priorities, planned work, and any review notes already written.

### Step 6: Read recent worklogs (freshness signal)

Glob `.md` files in `{WORKLOGS_DIR}/` that do NOT start with `_`. Sort by filename descending. Take the most recent **2**. For each: extract open tasks (`- [ ]` in `## Tasks`) and breadcrumbs from `## Summary`.

---

## Step 7: Present candidate shortlist and confirm priorities

This is the **Phase 1 confirmation checkpoint**. Do not produce the full plan yet.

Format and display:

---

### Build-week · [project-name] · Week [YYYY-Www]

#### Constraints recap
[2–3 bullet points from Step 3: time budget, compute budget, deadlines. If no prior constraints were found: "⚠ No constraints set yet — you'll be prompted to provide them when the plan is written."]

#### Recent meeting signals
[For each meeting note read in Step 4, show:]

**[date] — [title]** *(processed: [yes/no], delta applied: [yes/no])*
- Decisions: [bullet list from `## Decisions`, or "none"]
- Action items: [bullet list of unchecked `- [ ]` items from `## Action items`, or "none"]
- Weekly plan delta: [contents of `## Weekly plan delta` if present, or "—"]
- ⚠ *Delta not yet applied to weekly plan* [show only if `weekly_plan_updated: false`]

[If no meetings found: "No recent meeting notes found in `{MEETINGS_DIR}`."]

#### Candidate planning items

**Active (in-progress)**
| id | title | priority | kind | effort |
|----|-------|----------|------|--------|
[rows from Step 1A; if none: omit this sub-section]

**Ready (now/next · unblocked)**
| id | title | priority | horizon | impact | effort | due_by |
|----|-------|----------|---------|--------|--------|--------|
[rows from Step 1B sorted by priority/impact; mark deadline-sensitive items with ⚑]

**Blocked**
| id | title | priority | blocked by |
|----|-------|----------|------------|
[rows from Step 1C; if none: omit]

#### Research context (attention items)
[From Step 2 — only items in the `## Attention` section of the state index:]

**Open questions:** [list Q items, or omit if none]
**Hypotheses to test:** [list H items, or omit if none]
**Uncertain assumptions:** [list A items, or omit if none]
**Recent decisions:** [list D items, or omit if none]

#### Open worklog tasks (not yet in planning)
[Open `- [ ]` tasks from Step 6 that have no `[Bxxx]` reference in their description. If none: omit this section.]

---

> **Before I generate the full plan, please confirm:**
> 1. Do the **Ready** items above reflect the right priorities this week? (Mark any that are no longer relevant, blocked, or should be deprioritized.)
> 2. Do the **meeting signals** above change anything? (Any action items or decisions that should bump something up or push something out?)
> 3. Should any **open worklog tasks** be added to planning this week?
> 4. Any **time/compute constraints** to add or correct?
>
> Reply with your changes, or say **"looks good"** / **"proceed"** to continue.

**Stop here and wait for the user's response before proceeding.**

---

## ── PHASE 2: DETAILED PLAN ──

### Step 8: Resolve the confirmed candidate set

Apply the user's changes from Step 7:
- Remove deprioritized items from the candidate list.
- Note new items the user wants to add (flag for Step 9c — these require planning item creation).
- Confirm which items are the **top 3 priorities** for this week.

For each of the top 3 confirmed priorities: read `{PLANNING_DIR}/items/{id}.md` to get the full detail:
- Problem / goal
- Proposed approach
- Next smallest step
- Success looks like
- Evidence / pointers

Do not read files for items outside the top 3 unless the user explicitly requested it.

### Step 8b: Plan diff (re-run only)

If an existing weekly plan was found in Step 5, compare the previous plan's top priorities against the newly confirmed top 3 from Step 8. Present a compact diff:

---

**Changes from current plan ([YYYY-Www].md):**

| | previous | proposed | reason |
|---|---|---|---|
| Priority #1 | [id — title] | [id — title] | *(unchanged)* or [reason for change] |
| Priority #2 | … | … | … |
| Priority #3 | … | … | … |
| Dropped | — | [id — title] | [reason deferred] |
| Added | [id — title] | — | [reason added] |

Only show rows where something changed. If all 3 priorities are identical: "No priority changes from the existing plan."

---

If no existing plan was found (first run of the week): skip this step — there is nothing to diff against.

### Step 9: Produce the detailed weekly plan

Using the full detail from Step 8, produce the following output sections:

---

### A) Proposed weekly plan

**Week:** [YYYY-Www] · **Dates:** [Mon DD – Sun DD, YYYY]
**Constraints:** [recap from Step 3]

**Top [N] priorities (ranked)**

For each priority:
- **[id] — [title]**
  - *Why now:* [tie to evidence: state attention items, meeting decisions, worklog breadcrumbs, deadline pressure]
  - *Expected impact:* [high/med/low — what concretely improves]
  - *Effort estimate:* [small/medium/large]
  - *Risks/unknowns:* [key risks or open questions]
  - *Dependencies/blockers:* [any, or "none"]
  - *Next smallest step:* [exact text from the planning item — one concrete action]
  - *Success criteria:* [exact text from "Success looks like" in the planning item]
  - *Evidence pointers:* [links to state items, worklog files, meeting notes, artifacts]

---

### B) Proposed planning item edits

List any `horizon` or `status` changes implied by this week's plan:

| id | field | current value | proposed value | reason |
|----|-------|--------------|----------------|--------|

If no changes are needed: "No planning item edits proposed."

---

### C) Draft weekly plan file

Provide the full content for `{WEEKLY_PLANNING_DIR}/YYYY-Www.md` using the structure from `{INSTRUCTIONS_DIR}/planning/_weekly_plan_template.md`. Fill in all sections; leave `## Review notes` blank (for end-of-week use).

---

> **Please confirm:**
> 1. Does the plan look right? Any adjustments before I write it?
> 2. Should I apply the planning item edits from section B above?
> 3. Should I write (or update) `{WEEKLY_PLANNING_DIR}/YYYY-Www.md`?
>    - If the file already exists: I will update `## Top priorities`, `## Planned work`, `## Success criteria`, and `## Risks / unknowns`. I will **preserve** `## Review notes` and update `## Constraints` only if you confirmed changes.
>    - If no file exists: I will create it.

**Stop here and wait for the user's response before writing any files.**

---

## Step 10: Apply confirmed changes

Apply **only** what the user explicitly confirmed.

### 10a. Write or update the weekly plan file

If confirmed:
- If the file already exists: read it, then use Edit to update the plan sections. Preserve `## Review notes` and `## Constraints` (unless the user confirmed constraint changes).
- If the file does not exist: use Write to create it with the full draft from Step 9C.

### 10b. Apply planning item edits

If the user confirmed any edits from Step 9B:
- For each item: read `{PLANNING_DIR}/items/{id}.md`, apply only the confirmed field changes using Edit.
- After all edits: regenerate the planning index.
  - First try: `make planning-index` (from the project root, using Bash).
  - If that fails: `python {PLANNING_DIR}/../scripts/generate_planning_index.py`.
  - If both fail: inform the user that `{PLANNING_DIR}/INDEX.md` needs manual regeneration.

### 10c. Handle new items flagged by the user

If the user asked to add new backlog items (from meeting action items or unlinked worklog tasks):
- **Read `{INSTRUCTIONS_DIR}/planning/_backlog_update_instructions.md`** as required by `_shared_rules.md` before proposing anything.
- Follow the canonical process: check for duplicates against existing `items/*.md`, assign the next available `B###` ID, use `{INSTRUCTIONS_DIR}/planning/_template_item.md` for structure.
- Present the full proposed item to the user and wait for confirmation before writing.
- After confirmed writes: regenerate the planning index.

---

## Step 11: Summary

Print a brief summary:

> **Weekly plan built — Week [YYYY-Www]**
> - Plan file: [created at path / updated at path / skipped]
> - Planning item edits: [N items updated / none]
> - New backlog items: [N items created / none]
>
> Tip: Run `/catchup` to start your next session, or `/end-session` to wrap up today's work.

---

## Important rules

- **Phase 1 reads indices only** — do not read individual `B###.md` files until Step 8 (after user confirmation).
- Do not invent results, metrics, priorities, or evidence — if something is unknown, say so.
- Prefer items that unblock others, test key hypotheses, or reduce the biggest uncertainty; respect constraints.
- Keep scope small: at most **3 top priorities**; everything else stays "Next" or "Later".
- Tie every priority to evidence (state/worklog/meeting pointers).
- Follow `_shared_rules.md` for all planning item writes: present changes, wait for confirmation, then write.
- If no prior constraints exist, ask the user whether to specify them now or defer — do not silently skip constraints.
- If `MEETINGS_DIR` is not configured, skip meeting steps entirely and note it in the output.
