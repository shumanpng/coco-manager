---
name: setup
description: First-time configuration skill. Sets the worklogs directory path in meta.md so all other skills know where to find worklogs. Use when the user invokes /setup or when another skill says configuration is missing.
allowed-tools: Read, Edit, Write
---

You are configuring the skills for this workspace. The configuration lives in `.claude/skills/meta.md` under a `PROJECTS:` block. Each project is a nested block with named directory keys (e.g., `worklogs`, `weekly-planning`, `planning`, `state`, `meetings`, `instructions`) mapping to absolute paths.

## Step 1: Read current config

Read `.claude/skills/meta.md` and `.claude/skills/_shared_rules.md`. Show the user the current `PROJECTS:` block from meta.md. If the file doesn't exist or is empty, note that no projects are configured yet.

## Step 2: Ask what the user wants to do

Present the options:
1. **Add a project** — register a new project name with one or more named directories
2. **Remove a project** — delete a project entry entirely
3. **Edit a project** — add, remove, or change a named directory within an existing project

## Step 3: Collect the details

For **add**:
- Ask for a project name (short identifier, e.g. `my-project`)
- Ask for the directories to register. At minimum prompt for `worklogs`. Then ask if they want to add other named directories (e.g. `weekly-planning`, `planning`, `state`, `meetings`, `instructions`). For each, ask for the path.
- **Required for every project — prompt for `instructions`:** the directory holding repo-owned templates and instruction files (the `_*-prefixed` files) that `init.sh` installed — this is `<notes-dir>/.coco-manager/instructions`. Default to that path. Skills resolve templates from `INSTRUCTIONS_DIR/<sub>/`.

For **remove**:
- Show existing project names and ask which to remove

For **edit**:
- Show existing project names, ask which to edit
- Show the current directory keys for that project and ask whether to: add a new key, remove a key, or change a key's path

## Step 4: Update meta.md

Use Edit (or Write if creating from scratch) to update `.claude/skills/meta.md`.

The file format must be:
```
# Skills Configuration

PROJECTS:
  project-name:
    worklogs: /path/to/notes/worklogs
    weekly-planning: /path/to/notes/planning/weekly
    instructions: /path/to/notes/.coco-manager/instructions
  another-project:
    worklogs: /path/to/other/worklogs
```

Rules:
- Each project name is indented with two spaces
- Each directory key under a project is indented with four spaces
- No trailing slashes on paths
- If the user provides an absolute path, accept it but note that relative paths are preferred for portability
- Every project block must include an `instructions:` key (the repo-owned templates/instruction dir). Skills resolve templates from `INSTRUCTIONS_DIR/<sub>/`.
- Do not add or remove the `# Skills Configuration` header or the `PROJECTS:` key

## Step 5: Confirm

Show the user the updated `PROJECTS:` block and tell them:
> "Done. You can re-run `/setup` at any time to add, remove, or edit projects and directories. You can also edit `.claude/skills/meta.md` directly."

## Important rules
- Do not modify any content outside the `PROJECTS:` block
- A project name or directory key may contain hyphens, underscores, and alphanumeric characters
- If adding a project whose name already exists, ask the user to confirm they want to overwrite it
