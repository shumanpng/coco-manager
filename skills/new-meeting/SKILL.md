---
name: new-meeting
description: Creates a new meeting note from the template. Use when the user invokes /new-meeting or asks to create a new meeting note.
argument-hint: "[title]"
allowed-tools: Read, Write, Glob
---

You are helping the user create a new meeting note. Follow these steps exactly:

## Step 0: Resolve project and load configuration

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Parse the `PROJECTS:` block in meta.md. Each project is a nested block: the project name is the outer key, and it contains named directory keys (e.g., `meetings`, `worklogs`) mapping to absolute paths.

- If the file doesn't exist or contains no projects, stop and tell the user:
  > "No projects configured. Run `/setup` to get started."

**Resolve which project to use:**

- Count the number of projects in the map.
- If there is exactly **one** project: use it automatically, regardless of `$ARGUMENTS`.
- If there are **multiple** projects:
  - Check if the first word of `$ARGUMENTS` matches a project name (case-sensitive).
  - If it matches: use that project. Treat the remainder of `$ARGUMENTS` (after the first word) as the title for Step 1.
  - If it does not match or `$ARGUMENTS` is empty: stop and tell the user:
    > "Multiple projects found. Please specify one: `project-a`, `project-b` (list actual names). Example: `/new-meeting project-a`"

Once the project is resolved, extract `MEETINGS_DIR` = the `meetings` path for the project. Also extract `INSTRUCTIONS_DIR` = the `instructions` path for the project (required — `init.sh` sets it and `/setup` validates it).

- If `meetings` is not configured for the resolved project, stop and tell the user:
  > "No `meetings` directory configured for project **[project-name]**. Add a `meetings` key to `.claude/skills/meta.md` or run `/setup`."

**Print a confirmation line immediately — before doing any other work:**
> Using project: **[project-name]** (meetings: `[MEETINGS_DIR]`)

Use `MEETINGS_DIR` in all steps below.

## Step 1: Gather information

You already know today's date from your system context. You need:

1. **meeting-title**: A short, descriptive title for the meeting.
   - If `$ARGUMENTS` is non-empty (after stripping any matched project name), treat it as the title and confirm with the user.
   - Otherwise, ask the user for a title.

2. **meeting-date**: The date of the meeting.
   - Default to today's date. Confirm this with the user and allow them to specify a different date if the meeting is in the past or future.

3. **attendees**: Who attended (optional).
   - Ask the user for a comma-separated list of names, or leave blank if not known yet.

## Step 2: Create the meeting note file

- File location: `MEETINGS_DIR`
- File name format: `YYYY-MM-DD_short_title.md` where `short_title` is a lowercase, hyphen-separated abbreviation of the title (e.g., `2026-02-22_weekly-sync.md`)
- Read the template from `INSTRUCTIONS_DIR/meeting/_template_meeting_note.md`
- Populate the frontmatter fields:
  - `date`: the meeting date as `YYYY-MM-DD`
  - `title`: the meeting title in double quotes
  - `attendees`: a YAML list, e.g. `[Alice, Bob]`, or `[]` if none provided
  - Leave `processed_on` and `worklog` as `null`
- Preserve all section headings and comment blocks from the template exactly as-is.
- Write the file with the populated frontmatter and the empty template body.

## Step 3: Confirm

Show the user the created file path and a one-line summary of the frontmatter that was populated. Ask if they want any adjustments.

## Important rules

- Never fabricate meeting details — only use what the user provides.
- Do NOT fill in `## Discussion`, `## Decisions`, `## Action items`, `## Open questions`, or `## Notes` — leave them for the user to complete.
- Today's date is available in your system context.
- Do NOT modify planning or state items — this skill only creates the meeting note file.
