---
name: end-week
description: End-of-week review skill. Summarizes the week's work against the weekly plan, fills the Review notes section, and catches missed planning item updates. Use when the user invokes /end-week or says they want to wrap up the week.
argument-hint: "[project-name if multiple projects configured]"
allowed-tools: Read, Edit, Glob, Write, Bash
---

You are helping the user wrap up the week by reviewing progress against the weekly plan and filling in the `## Review notes` section. This is a single-phase skill: read everything, draft the review, confirm with the user, then write.

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
  - If it matches: use that project. Treat the remainder of `$ARGUMENTS` as arguments for the steps below.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/end-week project-a`"

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

## Step 1: Find the current weekly plan

Compute the current ISO week: `YYYY-Www`.

Glob `{WEEKLY_PLANNING_DIR}/YYYY-W##.md` (zero-padded). If not found, try `YYYY-W#.md` (non-padded).

- If found: proceed.
- If not found: stop and tell the user:
  > "No weekly plan found for [YYYY-Www] in `{WEEKLY_PLANNING_DIR}`. Run `/build-week` to create one first."

---

## Step 2: Read the weekly plan

Read the weekly plan file. Extract:
- **Top priorities**: item IDs, titles, success criteria
- **Planned work**: deliverables, experiments, engineering tasks
- **Success criteria** table
- **Risks / unknowns**
- **Existing Review notes content**

### Idempotency gate

Inspect the `## Review notes` section (or `## Review notes (end of week)`). Determine whether it contains **non-placeholder content** — i.e., content beyond the template prompts like `_(Fill in at end of week)_` or empty bullet points.

- If `## Review notes` has substantive content already: show the existing content to the user and ask:
  > "Review notes already exist for this week. Would you like to:"
  > 1. **Replace** the existing review notes with a fresh review
  > 2. **Append** new notes below the existing ones
  > 3. **Abort** — keep the existing review notes unchanged

  Wait for the user's choice before proceeding. If they choose abort, skip to Step 9 (planning item reconciliation).

- If `## Review notes` is empty or placeholder-only: proceed normally.

---

## Step 3: Read worklogs from this week

Determine the date range for the current ISO week (Monday through Sunday).

Glob `.md` files in `{WORKLOGS_DIR}/` that do NOT start with `_`. Filter to files whose date prefix (YYYY-MM-DD) falls within this week's Monday–Sunday range.

For each matching worklog, read selectively:
1. Read `## Summary` and `## Tasks` sections.
2. If no `## Summary` section exists: fall back to reading `## Distilled information corner`.
3. If neither exists: note the file as "no summary available" and skip it.

From each worklog, extract:
- Completed tasks (`- [x]` in `## Tasks`)
- Open tasks (`- [ ]` in `## Tasks`)
- Blockers mentioned
- Next actions listed
- Key outcomes from `## Summary`

If no worklogs are found for this week: note "No worklogs found for this week" and continue — the review will be based on the plan and INDEX.md alone.

---

## Step 4: Read planning INDEX.md

Read `{PLANNING_DIR}/INDEX.md`. Parse the markdown table.

For each item ID referenced in the weekly plan's top priorities and planned work:
- Note the current `status`, `priority`, `horizon`

Also note any items whose status changed to `done` or `in_progress` during this week (if `updated_on` is available in the table).

---

## Step 5: Read individual B###.md for top priorities

For each top-priority item ID from the weekly plan (max 3): read `{PLANNING_DIR}/items/{id}.md` to get:
- Current `status` (from frontmatter)
- Problem / goal
- Next smallest step
- Success looks like
- Evidence / pointers

Do not read files for items outside the top priorities unless the user explicitly requests it.

---

## Step 6: Read meeting notes from this week

If `MEETINGS_DIR` is `null` or not configured: skip this step.

Glob `.md` files in `{MEETINGS_DIR}/` that do NOT start with `_`. Filter to files whose date prefix falls within this week's date range.

For each matching meeting note, read and extract:
- Frontmatter: `date`, `title`, `processed_on`
- `## Decisions` section
- `## Action items` section (checked and unchecked)
- `## Weekly plan delta` section (if present)

If no meeting notes are found: note "No meeting notes found for this week" and continue.

---

## Step 7: Draft the review

Using all gathered data, produce a draft for the `## Review notes` section. Use this structure:

```markdown
## Review notes (end of week)

### Priorities outcome

For each top priority from the plan:

- **[id] — [title]**: [Completed | Partially completed | Not started | Blocked]
  - Success criteria: [met | partially met | not met] — [evidence from worklogs]
  - Key result: [one-line summary of what was achieved]
  - [If incomplete]: What remains: [brief description]

### Planned work recap

- **Deliverables**: [which were delivered, which weren't]
- **Experiments**: [which ran, key results if available]
- **Engineering tasks**: [completed vs remaining]

### Unplanned work

[Items worked on this week that were NOT in the weekly plan — extracted from worklog tasks that don't reference any planned item ID. If none: "None identified."]

### Risks that materialized

[For each risk listed in the plan's ## Risks / unknowns: did it happen? How was it handled? If no risks materialized: "None of the identified risks materialized."]

### Key learnings

[Distilled from worklog summaries — decisions made, findings, surprises. Keep to 3–5 bullet points. If meeting notes contained relevant decisions, include them here.]
```

**Formatting rules:**
- Do not invent results or metrics — if something is unknown, say "unknown" or "no data in worklogs"
- Prefer pointers (file paths, item IDs, commands) over vague summaries
- Keep it concise — the review should fit on one screen

**Present the full draft to the user and ask for confirmation:**
> Here is the draft review for Week [YYYY-Www]. Please review and let me know:
> 1. Any corrections or additions?
> 2. Confirm to write, or abort?

**Wait for the user's response before proceeding.**

---

## Step 8: Write the review

After the user confirms (with any requested edits applied):

- If the user chose **replace** in Step 2 (idempotency gate): use Edit to replace the entire `## Review notes` section content.
- If the user chose **append** in Step 2: use Edit to append the new content below the existing review notes.
- If this is a fresh write (no existing content): use Edit to replace the placeholder content under `## Review notes` with the confirmed draft.

Do not modify any other section of the weekly plan file.

---

## Step 9: Planning item reconciliation (lightweight)

This step catches planning item status updates that `/end-session` may have missed. It is a **safety net**, not a full reconciliation.

**A) Read `{INSTRUCTIONS_DIR}/planning/_backlog_update_instructions.md`** in full (required by `_shared_rules.md`).

**B) Cross-reference evidence:**

For each top-priority item from the weekly plan:
- Compare the item's current `status` in INDEX.md (from Step 4) against the evidence from worklogs (Step 3) and the item's success criteria (Step 5).
- Flag items where a status change seems warranted but hasn't been applied. Common cases:
  - Item still `in_progress` or `todo` but success criteria appear met → suggest `done`
  - Item still `todo` but work was started this week → suggest `in_progress`

**C) Present proposed changes:**

If any status changes are flagged:
> **Possible missed planning item updates:**
>
> | id | current status | proposed status | evidence |
> |----|---------------|----------------|----------|
> | [id] | [current] | [proposed] | [worklog reference or success criteria match] |
>
> These were not caught by `/end-session`. Should I apply any of these? (Confirm each, or say "skip all".)

If no changes are flagged: "No missed planning item updates detected."

**Wait for explicit confirmation before writing any file.**

**D) Apply confirmed changes:**

For each confirmed update:
- Read `{PLANNING_DIR}/items/{id}.md`
- Use Edit to update only the `status` field (and `updated_on` to today's date)
- After all edits: regenerate the planning index:
  ```bash
  # prefer make when available
  make planning-index
  ```
  If that fails:
  ```bash
  python {PLANNING_DIR}/../scripts/generate_planning_index.py
  ```
  If both fail: inform the user that `{PLANNING_DIR}/INDEX.md` needs manual regeneration.

---

## Step 10: Summary

Print a brief summary:

> **Week [YYYY-Www] review complete**
> - Review notes: [written to `{path}` | skipped (user chose abort)]
> - Planning item updates: [N items updated | none]
>
> Tip: Run `/build-week` to plan next week, or `/catchup` to start your next session.

---

## Important rules

- Do not invent results, metrics, or evidence — if something is unknown, say so.
- Use Edit for targeted changes — do not rewrite the entire weekly plan file.
- Never remove or overwrite existing content without the user's explicit choice (see idempotency gate in Step 2).
- Follow `_shared_rules.md` for all planning item writes: present changes, wait for confirmation, then write.
- Keep the review concise — prioritize durable knowledge and pointers over narrative.
- If `MEETINGS_DIR` is not configured, skip meeting steps entirely and note it in the output.
