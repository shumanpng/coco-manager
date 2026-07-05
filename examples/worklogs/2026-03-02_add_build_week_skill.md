---
created_on: 2026-03-02
tags: [skills, workflow, planning]
---

<!-- Sanitized example from the context-manager project's own development. Some details have been redacted. -->

# 2026-03-02: Add /build-week and /end-week skills [B001, B007]

### Related work logs
-

## Goal/Outcome
Turn `planning/_weekly_planner_agent.md` into a working `/build-week` Claude skill with INDEX-first speed, meeting integration, and user confirmation checkpoints.

## Tasks
- [x] Design the skill's step-by-step process [B001]
  - How it reads `planning/INDEX.md` to pull `now`/`next` items
  - How it handles an existing weekly plan (update vs. new version)
  - What the output format looks like
- [x] Implement `/build-week` skill [B001]
  - Created `.claude/skills/build-week/SKILL.md`
- [x] Add plan diff sub-step (Step 8b) for re-runs [B001]
  - Compares previous plan's top priorities against newly confirmed ones
- [x] Move constraints from `constraints.md` to weekly plan's `## Constraints` section [B001]
  - Updated `_weekly_plan_template.md` with dedicated `## Constraints` section
  - Skill reads constraints from prior weekly plans, carries forward standing constraints
  - If no prior constraints exist, asks user whether to specify now or defer
- [x] Test: running `/build-week context-manager` creates or updates this week's plan file [B001]
- [ ] Test: re-running after a constraint change reflects the update without losing the original plan [B001]
  - Status: not started
- [x] Design `/end-week` skill — walk through design decisions [B007]
  - Single-phase (vs two-phase like build-week): retrospective, no intermediate confirmation needed
  - Fills existing `## Review notes` section (not a new `## Summary`)
  - Data sources: weekly plan, worklogs (summaries only), INDEX.md, top-priority B###.md files, meeting notes
  - Lightweight planning item reconciliation pass (safety net for missed /end-session updates)
  - No carry-forward suggestions (that's /build-week's job), no constraint actuals
  - Closed marker: presence of non-empty Review notes = closed (no frontmatter needed)
  - Idempotent: detects existing review notes, asks before overwriting
- [x] Implement `/end-week` skill [B007]
  - Created `.claude/skills/end-week/SKILL.md`
- [x] Update B007 planning item — status `in_progress` → `done`, updated approach/success criteria [B007]
- [x] Test: running `/end-week` against a project with an existing weekly plan [B007]
- [x] Clean up superseded files [B001, B007]
  - Deleted `planning/constraints.md` (constraints now in weekly plan `## Constraints` section)
  - Archived `planning/_weekly_planner_agent.md` → `.archived` (superseded by `/build-week` + `/end-week`)
  - Archived `agents/update_state_and_planning_from_meeting_minutes.md` → `.archived` (superseded by `/process-meeting`)
  - Updated references in `manual.md` and `index.md`

---
## Distilled information corner

### Guidelines
[Guidelines file](../knowledge_base/guidelines.md)

### Useful info

**What changed this session:**
- Implemented `/build-week` skill (two-phase: INDEX-first → top-3 items; meeting integration; two confirmation checkpoints; plan diff on re-runs)
- Implemented `/end-week` skill (single-phase retrospective; fills `## Review notes`; worklog summaries only; lightweight reconciliation safety net)
- Consolidated constraints: deleted `planning/constraints.md` — constraints now live in weekly plan `## Constraints` section
- Archived superseded docs: `_weekly_planner_agent.md`, `update_state_and_planning_from_meeting_minutes.md`
- Updated B007 planning item status → `done`

### Design decisions
- **[/build-week]** Constraints consolidated into the weekly plan file (`## Constraints` section) — no separate `constraints.md`. Standing constraints carry forward from the previous week's plan. → [D008](../state/items/D008.md)
- **[/build-week]** Plan diff (Step 8b) shows what changed on re-runs rather than maintaining a revision log — git handles version history.
- **[/build-week]** Two-phase architecture: Phase 1 reads indices only (fast), Phase 2 reads individual item files only for the top 3 confirmed priorities.
- **[/build-week]** Meeting notes: current-week meetings prioritized, supplemented by 1–2 prior-week meetings if needed (capped at 3 total).
- **[/end-week]** Single-phase (retrospective, no intermediate confirmation needed). Fills existing `## Review notes` section.
- **[/end-week]** Worklog reading depth: summaries only (`## Summary` + `## Tasks`), fall back to `## Distilled information corner` if no Summary.
- **[/end-week]** Lightweight planning item reconciliation as safety net — presents "possible missed updates", never auto-applies. Clean separation: end-week closes, build-week opens → [D010](../state/items/D010.md)
- **[/end-week]** Closed marker = non-empty `## Review notes` (no frontmatter). Idempotent: detects existing content, asks before overwriting. → [D009](../state/items/D009.md)

### Instructions to keep track of

**Skill invocation:**
- `/build-week [project]` — create or update current week's focused plan (`.claude/skills/build-week/SKILL.md`)
- `/end-week [project]` — end-of-week retrospective; fills `## Review notes` in current week's plan file (`.claude/skills/end-week/SKILL.md`)

### Risks/Unknowns
- ~~The standalone `constraints.md` still exists but is no longer referenced by `/build-week` — can be deleted when ready.~~ Deleted 2026-03-02.

### Links/Refs
- Skill file: `.claude/skills/build-week/SKILL.md`
- Skill file: `.claude/skills/end-week/SKILL.md`
- Weekly plan template: `planning/_weekly_plan_template.md`
- Original agent doc: `planning/_weekly_planner_agent.md`
- Backlog items: `planning/items/B001.md`, `planning/items/B007.md`


---
## Work log

### Design and implement `/build-week` skill [B001]

#### Chain of thought

Turned `planning/_weekly_planner_agent.md` into a Claude skill at `.claude/skills/build-week/SKILL.md`.

**Key design decisions:**

- **Two-phase architecture** for speed: Phase 1 reads only `PLANNING_DIR/INDEX.md` and `STATE_DIR/INDEX.md` (no individual `B###.md` files). Phase 2 reads at most 3 individual item files for the confirmed top priorities — only after user confirmation.
- **Meeting integration (Step 4):** Current-week meetings prioritized first; supplements with 1–2 prior-week meetings if needed (capped at 3). Surfaces decisions, unchecked action items, and `## Weekly plan delta`. Flags meetings where `weekly_plan_updated: false`.
- **Two confirmation checkpoints:**
  1. After Phase 1 (Step 7): compact dashboard of candidates + meeting signals + research context. Asks user to confirm/adjust priorities before generating the full plan.
  2. After Phase 2 (Step 9): full ranked plan, proposed item edits, and draft file. Confirms before writing anything.
- Follows all existing skill patterns: Step 0 project resolution, `_shared_rules.md` compliance, canonical process for any new backlog items created from meeting action items.

**Follow-up: re-run safety analysis**

Analyzed whether re-running `/build-week` after a constraint change preserves the original plan. Identified three gaps: (1) no diffing against previous plan, (2) no version history, (3) only `## Review notes` explicitly preserved. Decided:
- **Added Step 8b (plan diff):** shows a compact table of what priorities changed and why on re-runs. Essential for mid-week replanning.
- **Skipped revision log:** git already handles this; adding it to the file duplicates version control.
- **Skipped expanded preservation:** plan sections (`## Top priorities`, `## Planned work`, etc.) *should* be overwritten on re-runs; user annotations belong in `## Review notes`.

**Follow-up: constraints consolidation**

`constraints.md` and the weekly plan's `## Context` section duplicated constraint info. Decided to consolidate into a dedicated `## Constraints` section in the weekly plan template. The skill carries forward standing constraints from prior weekly plans. If no prior plan exists, it asks the user whether to specify constraints now or defer.



### Design and implement `/end-week` skill [B007]

#### Chain of thought

Designed and implemented an `/end-week` skill at `.claude/skills/end-week/SKILL.md`, modeled on `/end-session` (reflection flow) and `/build-week` (project resolution, index-first reading).

**Key design decisions:**

- **Single-phase architecture** (unlike build-week's two-phase): end-week is retrospective — it summarizes what happened rather than soliciting user input to shape a plan. Reads everything, drafts the review, confirms with user, then writes.
- **Target section: `## Review notes`** — the weekly plan template already has `## Review notes (end of week)` with placeholder prompts. Reuses that section instead of adding a new `## Summary` (as B007 originally proposed). Keeps the template clean.
- **Data sources and reading depth:**
  - Weekly plan file (priorities, success criteria, risks)
  - Worklogs from the week — **summaries only** (`## Summary` + `## Tasks`). Falls back to `## Distilled information corner` if no Summary exists. Avoids reading full `## Work log` for speed.
  - `INDEX.md` for current status of referenced planning items
  - Individual `B###.md` files — only for top priorities (max 3), read after INDEX
  - Meeting notes from the week (decisions, action items, weekly plan delta)
- **Lightweight planning item reconciliation (Step 9):** safety net for status updates missed by `/end-session`. Cross-references INDEX.md status against worklog evidence and success criteria. Presents discrepancies as "possible missed updates" — never auto-applies. Follows `_shared_rules.md` confirmation flow.
- **No carry-forward suggestions** — that's `/build-week`'s responsibility. Clean separation of concerns: end-week closes; build-week opens.
- **No constraint actuals** tracking — avoided scope creep.
- **Closed marker: presence of non-empty `## Review notes`** — no YAML frontmatter or explicit status field needed. Weekly plans don't currently use frontmatter; adding it would be a bigger structural change for minimal benefit.
- **Idempotency (Step 2):** if `## Review notes` already has substantive content, shows it and offers three choices: replace, append, or abort. Prevents accidental overwrites on re-runs.

---
## Summary

### Start here next session
- Files: [`.claude/skills/build-week/SKILL.md`](../../.claude/skills/build-week/SKILL.md), current week's plan file (`planning/weekly/`)
- Commands: `/build-week context-manager` (after modifying a constraint in the current week's plan, to test re-run + diff behavior)

### In-progress tasks (ordered)

**Test: re-running `/build-week` after a constraint change [B001]**
- Goal: Verify Step 8b (plan diff) reflects constraint changes without losing the original plan
- Current state: Not started
- Next smallest step: Temporarily modify a constraint in the current week's plan, then re-run `/build-week context-manager` and inspect the diff output
- Blocked by / open questions: None
- Relevant files / commands: `.claude/skills/build-week/SKILL.md`, `planning/weekly/`

### Blockers / waiting
None

### Next actions
1. Test `/build-week context-manager` re-run after a constraint change [B001]
