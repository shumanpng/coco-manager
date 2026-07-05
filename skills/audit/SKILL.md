---
name: audit
description: Wrap any write-heavy skill with two independent subagents (proposer + reviewer) that draft and audit the work end-to-end before any writes happen. Single user-approval moment at the end with summary, must-fix-already-applied, user-decision questions, and a pointer to the full proposal. Use when you want a high-confidence pass for a complex skill (e.g., `/audit end-session`, `/audit process-meeting`, `/audit build-week`) without mid-flow interruptions. Default proposer model is sonnet, reviewer model is opus; override with `--proposer-model` / `--reviewer-model` (or `--subagent-model` for both).
argument-hint: <skill-name> [--proposer-model opus|sonnet|haiku] [--reviewer-model opus|sonnet|haiku] [--subagent-model opus|sonnet|haiku] [skill args...]
allowed-tools: Read, Edit, Write, Glob, Grep, Bash, Agent
---

You are wrapping another skill with a proposer/reviewer audit pass. **You do not execute the target skill** — instead you read its instructions, hand them to two independent subagents (one drafts a complete proposal, one audits it), then execute the writes yourself per the audited proposal.

The pattern's value comes from its discipline: **no mid-flow questions to the user**, single approval at the end with everything surfaced at once.

## Step 0: Resolve target skill and parse args

Parse `$ARGUMENTS`:
- First positional token = `<skill-name>` (required).
- `--proposer-model <opus|sonnet|haiku>` (optional; default `sonnet`).
- `--reviewer-model <opus|sonnet|haiku>` (optional; default `opus`).
- `--subagent-model <opus|sonnet|haiku>` (optional; both-agents override alias — applied to *both* proposer and reviewer only if neither per-agent flag is set).
- All remaining tokens = `<skill-args>` to forward to the proposer (whatever the target skill expects).

Resolve the target skill's `SKILL.md`:
- Look in this skill's sibling directory: `<this-SKILL.md-parent>/../<skill-name>/SKILL.md` (i.e., `.../.claude/skills/<skill-name>/SKILL.md`).
- If not found, stop and tell the user: `Skill '<skill-name>' not found at <expected-path>. Available siblings: <ls of .claude/skills/>`.

**Soft check (audit-friendliness):**
- Read the target's frontmatter `allowed-tools`. If neither `Edit` nor `Write` appears, warn:
  > "Target skill '<skill-name>' is read-only (no Edit/Write in allowed-tools) — `/audit` adds little value here. Continue anyway? (y/n)"
- Otherwise proceed without prompting.

## Step 1: Resolve current date and print the run header

Resolve the current date from the user's system (do **not** hard-code a timezone — different users have different defaults):

```bash
date +%Y-%m-%d
date +%Z
```

Print on two lines so the user can interrupt if anything is wrong:

> Auditing skill: **<skill-name>** | proposer: <proposer-model> | reviewer: <reviewer-model>
> Detected date: **<YYYY-MM-DD>** (system timezone: **<TZ>**) — is this the date/timezone you want? (y / `<YYYY-MM-DD>` to override / `tz=<IANA-zone>` to recompute in another timezone)

If the user replies `y` (or empty), proceed with the detected date.
If they supply a date string, use that verbatim.
If they supply `tz=<zone>`, re-run `TZ=<zone> date +%Y-%m-%d` and use the result.

Bind the confirmed date to `<TODAY>` for use in the proposer + reviewer briefs below. The proposer uses `<proposer-model>` (default `sonnet`); the reviewer uses `<reviewer-model>` (default `opus`).

## Step 2: Spawn the Proposer (Agent tool, in foreground)

Spawn a `general-purpose` subagent with `model: <proposer-model>`. Brief it with:

1. **The target skill's `SKILL.md` verbatim** — this is the spec it must follow.
2. **The forwarded `<skill-args>`** — what the user invoked.
3. **Today's date: `<TODAY>`** (the date the user confirmed in Step 1; do not re-derive in the agent).
4. **Override directive (verbatim):**

   > "Follow the steps in the target SKILL.md to **plan** the work, but **do NOT write or edit any project files**. Read freely with Read/Glob/Grep/Bash, but produce a complete *proposal* instead of writes. The proposal must be at *executable fidelity*: every Edit/Write the target skill would do must be specified to the level a downstream executor could apply mechanically without re-deciding anything.
   >
   > Output format — a single markdown document titled `# PROPOSED <SKILL-NAME>`, with one numbered top-level section per category of write the target skill performs (e.g., `1. New state items`, `2. Planning item updates`, `3. Worklog summary`, `4. Frontmatter changes`, `5. Index regeneration commands`). For each item include: target file path, exact new content (or `old_string` / `new_string` for Edits), and a one-line rationale citing the source-of-truth (worklog line, meeting bullet, etc.).
   >
   > After the proposal, add `## NOTES TO REVIEWER` listing: judgment calls and why; anything you couldn't pin down; items considered and rejected (with the canonical-instruction reason); the provenance audit for any quantitative claim (measured / inferred / speculated).
   >
   > Do not write anything to project files. Read-only."

Capture the proposer's full output. If it exceeds the inline read limit, save to `/tmp/audit_<skill-name>_proposer_<timestamp>.md` and reference by path.

## Step 3: Spawn the Reviewer (Agent tool, in foreground)

Spawn a second `general-purpose` subagent with `model: <reviewer-model>`. Brief it with:

1. **The target skill's `SKILL.md` verbatim** (same as proposer).
2. **The proposer's proposal** (inline if small enough, else by `/tmp/...` path).
3. **Today's date: `<TODAY>`** (the date confirmed in Step 1).
4. **Audit directive (verbatim):**

   > "Audit the proposer's draft against the target SKILL.md and the canonical instructions it references. Read sources independently — do not trust the proposer's claims without verification. **Read-only.** No Edit/Write calls.
   >
   > For each proposed item, check: (a) faithful to source evidence; (b) follows the canonical update instructions; (c) frontmatter and ID conventions match the project's existing items; (d) cross-references and IDs are valid (no fabrications); (e) provenance correctly tagged (measured / inferred / speculated).
   >
   > Output format — these top-level sections, in order:
   >
   > - `# AUDIT VERDICT` — one of `APPROVE` / `APPROVE WITH MINOR EDITS` / `REVISE` / `BLOCKED — needs user decision`. One-paragraph justification.
   > - `# MUST-FIX ISSUES` — numbered list. For each: (section affected, what's wrong, source-of-truth evidence, exact proposed rewrite).
   > - `# NICE-TO-HAVE EDITS` — same shape, lower priority.
   > - `# QUESTIONS THAT NEED USER DECISION` — items the agent cannot resolve from sources (e.g., supersede vs. refine, atomic vs. combined). Be specific.
   > - `# PROVENANCE / ID CONSISTENCY CHECK` — confirm every cross-reference exists and quantitative claims trace to measured sources.
   > - `# CONFIRMED OK` — briefly list which proposal sections you read and agree with as-is."

Capture the reviewer's output (same /tmp fallback rule).

## Step 4: Auto-iterate once if reviewer said `REVISE`

If the reviewer's `# AUDIT VERDICT` is `REVISE` (not `APPROVE` / `APPROVE WITH MINOR EDITS`):

1. Spawn the proposer **once more** with the same brief plus the reviewer's `MUST-FIX ISSUES` section appended as: "The reviewer flagged these issues with your previous draft — produce a revised proposal addressing them." Do not include `NICE-TO-HAVE` (those become orchestrator polish, not proposer work).
2. Re-spawn the reviewer on the revised proposal.
3. If the second reviewer pass is still `REVISE`, **stop and surface to the user** (skip Step 5–9 below; report both rounds' verdicts and the persistent disagreements; ask how to proceed).

If reviewer said `BLOCKED — needs user decision`, do not iterate; surface to user (the user-decisions are the unblocker).

## Step 5: Synthesize and persist the proposal

Silently fold the reviewer's `MUST-FIX ISSUES` into the proposer's draft (the proposer's ground truth + the reviewer's corrections = the final proposal you'll execute).

Persist the final proposal to `/tmp/audit_<skill-name>_<YYYY-MM-DDTHHMMSS>.md`. Do **not** auto-symlink to a `latest`. The file persists for the session and is wiped on reboot by the OS.

## Step 6: Surface a single user message

This is the **only** user-facing prompt in the entire run. Format:

```
Reviewer verdict: <APPROVE | APPROVE WITH MINOR EDITS>

Would change:
- <one-line summary per category, e.g., "Worklog Summary: 1 section drafted (~140 words)">
- <"Tasks: 4 → done, 1 → carry">
- <"State items: N new (IDs), M updated (IDs)">
- <"Planning items: N updated, M new (IDs)">
Full proposal: /tmp/audit_<skill-name>_<timestamp>.md

NEEDS YOUR CALL:
1. <specific user-decision question, with options>
2. ...

Approve as-is / answer the calls / want to read the full proposal first?
```

If the reviewer's `# QUESTIONS THAT NEED USER DECISION` is empty, the `NEEDS YOUR CALL` block is omitted and you just ask `Approve as-is?`.

## Step 7: Wait for sign-off

The user will either:
- Approve → proceed to Step 8.
- Answer the user-decisions → fold their answers into the proposal (these may further modify state items / planning items), then proceed to Step 8.
- Ask to read the proposal first → wait, then re-prompt.
- Reject → stop. Do not write. Leave the `/tmp/...` file for inspection.

## Step 8: Execute the writes (fail loud on errors)

Walk the final proposal section by section. For each item:

- Use `Write` for new files; use `Edit` for in-place changes per the proposal's `old_string` / `new_string` blocks.
- Run any housekeeping commands the target SKILL specifies (regenerate indexes via `make state-index` / `make planning-index`, run `derive_blocking.py`, etc.).

**Failure mode: abort and surface.** If any housekeeping command fails (e.g., `make state-index` errors), stop immediately, report the error, and **do not proceed to the next housekeeping step or the commit prompt**. Items already written stay written; the user can decide whether to fix manually or revert. Do not paper over the error with a fallback path unless the SKILL.md explicitly defines one.

## Step 9: Always offer to commit

After successful execution, ask:

> "Audit run complete. Commit the changes? (y/n)"

If yes, follow the git commit guidance from the system prompt (stage related files, draft a commit message, create the commit). If no, exit cleanly and tell the user the changes are unstaged for them to handle manually.

## Cost note

Each `/audit` run spawns two subagents. By default the proposer is Sonnet and the reviewer is Opus (good balance of cost vs. catch-rate). Override either via `--proposer-model` / `--reviewer-model`, or both via `--subagent-model`. If you find a target skill is expensive to wrap, try `--proposer-model haiku` or `--reviewer-model sonnet` first.

## Important rules

- **No mid-flow user prompts** between Step 1 and Step 6 except: (a) the audit-friendliness warning in Step 0 (only fires for read-only target skills); (b) the date/timezone confirmation in Step 1 (one-line setup check). Everything else runs end-to-end.
- **Do not hard-code a timezone.** Use the user's system default `date +%Y-%m-%d` and double-check with the user in Step 1 — different users have different default timezones. The skill must not assume.
- **Do not invoke the target skill.** You read its `SKILL.md` and execute the writes yourself per the audited proposal. The target skill is the spec, not the executor.
- **Both subagents read sources independently.** The reviewer is not just checking the proposer's claims; it is verifying against the canonical instructions and the project's existing items. This is what catches duplicate IDs, dangling cross-refs, and stale dates.
- **Proposer must produce executable-fidelity output.** If the proposer hand-waves ("...and update the relevant planning item"), the reviewer should flag it as `MUST-FIX` and the executor (you) cannot apply it.
- **Persist the proposal to /tmp** so the user can inspect even after the chat moves on. Filename includes the skill name and a timestamp; no auto-cleanup.
