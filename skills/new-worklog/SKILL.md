---
name: new-worklog
description: Creates a new worklog for today's session. Use when the user invokes /new-worklog or asks to start a new worklog/work log.
argument-hint: "[task name]"
allowed-tools: Read, Write, Glob
---

You are helping the user create a new worklog entry. Follow these steps exactly:

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
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/new-worklog project-a`"

Once the project is resolved, extract `WORKLOGS_DIR` = the `worklogs` path for the project. Also extract `INSTRUCTIONS_DIR` = the `instructions` path for the project (required — `init.sh` sets it and `/setup` validates it).

**Print a confirmation line immediately — before doing any other work:**
> Using project: **[project-name]** (worklogs: `[WORKLOGS_DIR]`)

Use `WORKLOGS_DIR` in all steps below.

## Step 1: Gather information

You already know today's date from your system context. You need:

1. **task-name**: The name of today's task/session.
   - If `$ARGUMENTS` is non-empty, use that as the task name (confirm with user).
   - Otherwise, ask the user for the task name.

2. **resume-worklog-from-date**: Which previous worklog to resume from (carry over incomplete tasks and summary).
   - Use Glob to list all `.md` files in `WORKLOGS_DIR` that do NOT start with `_`.
   - Show the user the list and ask which one (if any) they want to resume from.
   - If there are none, skip this step.

## Step 2: Create the worklog file

- File location: `WORKLOGS_DIR`
- File name format: `YYYY-MM-DD_short_task_name.md` where short_task_name is a lowercase, underscore-separated abbreviation of the task name
- Copy the structure from `INSTRUCTIONS_DIR/worklogs/_starter_template.md`
- Set `created_on` in frontmatter to today's date
- Set the title to `# YYYY-MM-DD: [Full Task Name]`

## Step 3: Populate from resume worklog (if selected)

If the user selected a worklog to resume from:
- Read that worklog file
- Copy the `## Goal/Outcome` section content into the new file
- Copy any unchecked tasks (`- [ ]`) from the `## Tasks` section
- **Condense** the `## Summary` content into the new file's `## Goal/Outcome` as carried-over context (see style rules below)
- Populate `### Related work logs` with:
  1. The resumed worklog (linked)
  2. All worklogs listed under `### Related work logs` of that file (if any)

### Style rules for the carried-over context block

Do NOT paste the resumed worklog's Summary verbatim. Condense it into a compact block that preserves signal while cutting bulk. Target: ~10 lines, not ~45.

**Keep** (every one of these matters for resuming):
- Whatever task label convention the resumed worklog uses (it varies by user — could be `(T5)`, `#5`, `[task-5]`, or just the title). Preserve it verbatim; don't normalize.
- **Backlog IDs** (e.g. `B019`, `B072`) whenever the task references one — always surface these, they're the stable cross-doc identifier.
- Short titles and priority flags (e.g. *top priority, meeting*).
- The **next smallest step** per task (often the only actionable line).
- Open questions and blockers per task, but inline — not a separate labeled field.
- Concrete paths, commands, file refs, and key numbers (e.g. partition sizes, job IDs).
- A single "Start here" line collapsing "Files to open first" + "Commands to run first" into one paragraph.
- Top-level `**Blockers:**` line.

**Strip** (noise that re-reading the prior worklog covers better):
- Per-task labeled fields: `Goal:`, `Current state:`, `Blocked by / open questions:`, `Relevant files / commands:`. Fold these into one bullet per task.
- Redundant "(from YYYY-MM-DD Summary)" preambles on subsections.
- Full "Next actions" numbered list — the per-task bullets already cover this.
- Wordy transitions ("now unblocked", "not yet started") — use terser phrasing.

**Format:** one bullet per task, each following the shape:
> **[task-label, verbatim from source] [backlog ID if any] [Short title]** — *flag, if any*. One-sentence state. **Next:** next smallest step. **Open Q:** any blockers/questions.

Example: `**(T5) [B072] Benchmark partition + eval** — *top priority, meeting*. …`

Confirm the condensed block makes sense before writing (user may want more or less detail).

## Step 4: Confirm

Show the user the created file path and a brief summary of what was populated. Ask if they want any adjustments.

## Important rules
- Never fabricate task details — only use what the user provides
- Always use relative Markdown links when referencing files
- Today's date is available in your system context
