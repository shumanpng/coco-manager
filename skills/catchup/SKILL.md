---
name: catchup
description: Start-of-session briefing skill. Summarizes recent worklog sessions, surfaces incomplete tasks, and helps the user plan their day. Use when the user invokes /catchup or asks for an overview of recent work.
allowed-tools: Read, Glob
---

You are giving the user a start-of-session briefing based on their recent worklogs. Follow these steps:

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
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/catchup project-a`"

Once the project is resolved, extract:
- `WORKLOGS_DIR` = the `worklogs` path for the project
- `WEEKLY_PLANNING_DIR` = the `weekly-planning` path for the project (may be absent — treat as `null` if not configured)

**Print a confirmation line immediately — before doing any other work:**
> Using project: **[project-name]** (worklogs: `[WORKLOGS_DIR]`)

## Step 1: Find recent worklogs

Use Glob to list all `.md` files in `WORKLOGS_DIR` that do NOT start with `_`. Sort by filename (which is date-prefixed), and take the most recent **3** (or fewer if less exist).

## Step 1.5: Load the weekly plan (if it exists)

You know today's date from your system context. Compute the current ISO week number and year.

If `WEEKLY_PLANNING_DIR` is configured:
- Try Glob for `YYYY-W##.md` (zero-padded week, e.g. `2026-W08.md`) in `WEEKLY_PLANNING_DIR`.
- If not found, try `YYYY-W#.md` (non-padded, e.g. `2026-W8.md`).
- If a file is found: read it and store its contents as `WEEKLY_PLAN`. Extract the date range from the file header (e.g. the line starting with `` `Date`: ``) to display to the user.
- If no file is found: set `WEEKLY_PLAN` to `null`.

If `WEEKLY_PLANNING_DIR` is not configured:
- Set `WEEKLY_PLAN` to `null`.

## Step 2: Read and extract

For each recent worklog (most recent first), read the file and extract:
- **Date and session name** (from the `# title` line)
- **Goal/Outcome** summary (from `## Goal/Outcome`)
- **Completed tasks**: checked items (`- [x]`) from `## Tasks`
- **Incomplete tasks**: unchecked items (`- [ ]`) from `## Tasks`
- **Breadcrumbs / Next actions** from `## Summary`

## Step 3: Present the briefing

Format the output as a clean briefing:

---

### Recent sessions
For each session: one-line summary of goal, list of what was done.

### Open items
All unchecked tasks across the recent worklogs, grouped by worklog, linked to the source file.

### Suggested focus for today
Based on the open items and next actions from the most recent worklog's `## Summary`, suggest a short prioritized list for today. Label these as suggestions — the user decides.

- If `WEEKLY_PLAN` is available: open with a note like *"Week YYYY-W## (Mon DD – Sun DD)"* showing the week date range extracted from the file. Then cross-reference the plan with the open items and next actions to align suggestions with the week's stated priorities. Mention which suggested items are directly tied to the weekly plan.
- If `WEEKLY_PLAN` is `null` because the file wasn't found: include a brief note — *"No weekly plan found for week YYYY-W## in `[WEEKLY_PLANNING_DIR]`, so recommendations are based solely on your worklogs."*
- If `WEEKLY_PLAN` is `null` because `weekly-planning` is not configured in meta.md: include a brief note — *"`weekly-planning` directory not configured — run `/setup` to add it. Recommendations are based solely on your worklogs."*

---

## Step 4: Offer to create today's worklog

Ask: "Would you like to create today's worklog now?" If yes, invoke the `/new-worklog` skill or guide the user to do so.

## Important rules
- Be concise — this is a briefing, not a transcript
- Do not invent or infer tasks not present in the files
- Always link to source worklogs using relative Markdown links
