---
name: status
description: Shows a concise prioritization dashboard reading from planning and state indices, with today's worklog as a secondary source. Use when the user invokes /status or asks what tasks are open or in progress.
argument-hint: "[project-name if multiple projects configured]"
allowed-tools: Read, Glob
---

You are showing the user a prioritization dashboard. The primary sources are the planning index (for backlog tasks) and the state index (for research context). Today's worklog is a secondary source for tasks not yet promoted to planning.

## Step 0: Resolve project and load configuration

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Parse the `PROJECTS:` block in meta.md. Each project is a nested block: the project name is the outer key, and it contains named directory keys (e.g., `worklogs`, `planning`, `state`) mapping to absolute paths.

- If the file doesn't exist or contains no projects, stop and tell the user:
  > "No projects configured. Run `/setup` to get started."

**Resolve which project to use:**

- If there is exactly **one** project: use it automatically, regardless of `$ARGUMENTS`.
- If there are **multiple** projects:
  - Check if the first word of `$ARGUMENTS` matches a project name (case-sensitive).
  - If it matches: use that project.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/status project-a`"

Extract from the resolved project:
- `PLANNING_DIR` = the `planning` path
- `STATE_DIR` = the `state` path
- `WORKLOGS_DIR` = the `worklogs` path

**Print a confirmation line immediately — before doing any other work:**
> Using project: **[project-name]**

## Step 1: Read the planning index

Read `{PLANNING_DIR}/INDEX.md`. If the file does not exist, note "Planning index not found at {PLANNING_DIR}/INDEX.md" and skip to Step 2.

This file contains a markdown table with columns including: `id`, `title`, `status`, `horizon`, `priority`, `kind`, `impact`, `effort`, `blocked_by`, `last_updated`.

Parse every data row (skip the header and separator rows) and extract four groups:

**A. Active** — rows where `status = in_progress` (any horizon, any priority)

**B. Up next** — rows where ALL of the following are true:
  - `status = todo`
  - `horizon = now`
  - `priority` is P0 or P1
  - `blocked_by` column is empty (no blocking dependencies)

**C. Blocked** — rows where `blocked_by` is non-empty AND `status` is not `done`

**D. Completed today** — rows where `status = done` AND `last_updated` equals today's date in `YYYY-MM-DD` format

Note: today's date can be read from the current date context or inferred from the worklog filename in Step 3.

## Step 2: Read the state index

Read `{STATE_DIR}/INDEX.md`. If the file does not exist, note "State index not found at {STATE_DIR}/INDEX.md" and skip to Step 3.

Locate the `## Attention` section near the top of the file. Each line in this section has the format:
```
- [ID](items/ID.md): title (`status`, `priority`)
```

Group the attention items by ID prefix:
- Lines where the ID starts with `Q` → **Open questions**
- Lines where the ID starts with `H` → **Hypotheses to test**
- Lines where the ID starts with `A` → **Uncertain assumptions**

When constructing links for output, prepend `{STATE_DIR}/` to the relative path, e.g. `{STATE_DIR}/items/Q005.md`.

## Step 3: Read today's worklog

Use Glob to find a `.md` file in `{WORKLOGS_DIR}/` whose filename starts with today's date (`YYYY-MM-DD` prefix). If no file exists for today, skip this step entirely.

Read the file. Extract all task lines from the `## Tasks` section:
- `- [x]` lines → completed today (worklog)
- `- [ ]` lines → open in today's worklog

For open `- [ ]` tasks: a task is **unlinked** if its description contains no reference matching the pattern `[Bxxx]` (a backlog item ID). Unlinked tasks have not yet been promoted to the planning index.

## Step 4: Display the dashboard

Output the following sections in order. Omit any section that has no content — do not show empty section headers.

---

### Status — [project-name] · [today's date]

#### Active
| id | title | priority | kind |
|----|-------|----------|------|
| [B018]({PLANNING_DIR}/items/B018.md) | … | P0 | experiment |

List all **Active** items from Step 1A. Link each `id` to `{PLANNING_DIR}/items/{id}.md`.

#### Up next · now · P0/P1
| id | title | priority | kind | impact | effort |
|----|-------|----------|------|--------|--------|
| [B017]({PLANNING_DIR}/items/B017.md) | … | P0 | experiment | high | medium |

List all **Up next** items from Step 1B, sorted by priority (P0 before P1). Link each `id`.

#### Blocked
| id | title | priority | blocked by |
|----|-------|----------|------------|
| [B001]({PLANNING_DIR}/items/B001.md) | … | P1 | [B002]({PLANNING_DIR}/items/B002.md) |

List all **Blocked** items from Step 1C. In the "blocked by" column, render each blocking ID as a link to its planning item file. Omit this section entirely if there are no blocked items.

#### Research context

**Open questions (P0/P1)**
- [Q005]({STATE_DIR}/items/Q005.md): … *(title elided in example)*

**Hypotheses to test (P0/P1)**
- [H009]({STATE_DIR}/items/H009.md): … *(title elided in example)*

**Uncertain assumptions (P0/P1)**
- [A001]({STATE_DIR}/items/A001.md): … *(title elided in example)*

Render the grouped attention items from Step 2. Omit any sub-group that has no items.

#### Completed today
- [B013]({PLANNING_DIR}/items/B013.md): … *(planning)*
- … *(worklog task description)*

List planning items from Step 1D followed by worklog `[x]` tasks from Step 3, each labeled with its source in italics. Omit this section if nothing was completed today.

#### Unlinked tasks · today's worklog
- … *(task description from today's worklog with no `[Bxxx]` reference)*

List open worklog tasks from Step 3 that have no `[Bxxx]` reference. Add a brief note beneath the list: *"These haven't been added to planning yet. Consider promoting them with `/end-session`."* Omit this section if there are none, or if there is no worklog for today.

---

## Important rules
- Read only — do not modify any files
- Only report items actually present in the files — never infer or guess
- Keep output compact — this is a dashboard, not a detailed report
- Link every planning item ID to its source file at `{PLANNING_DIR}/items/{id}.md`
- Link every state item ID to its source file at `{STATE_DIR}/items/{id}.md`
- If a section is empty, omit it entirely (no empty headers)
