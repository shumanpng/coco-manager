# Shared rules for all skills

Every skill under `.claude/skills/` reads this file in Step 0. These rules are non-negotiable.

---

## Path resolution: INSTRUCTIONS_DIR

Templates and instruction files (`_*-prefixed`) are always resolved via `INSTRUCTIONS_DIR`, the `instructions:` path bound from the resolved project's `meta.md` block. Skills read `INSTRUCTIONS_DIR/<sub>/_*` (where `<sub>` is `worklogs`, `planning`, `state`, or `meeting`). If `INSTRUCTIONS_DIR` is unset for a project, stop and tell the user to run `/setup` to configure it.

---

## Rule 1: Planning item changes must follow the canonical process

Any skill that creates or modifies items in `PLANNING_DIR/items/*.md` **MUST**:

1. **Read `INSTRUCTIONS_DIR/planning/_backlog_update_instructions.md` in full** before proposing any changes.
2. **Follow the step-by-step process defined there** — do not invent a separate extraction, reconciliation, or write process.
3. **Present all proposed changes to the user and wait for explicit confirmation** before writing any file.
4. **Regenerate dashboards** after confirmed writes (the Makefile lives in the parent of `PLANNING_DIR`):
   - First try: `cd {PLANNING_DIR}/.. && make planning-index`
   - If that fails: `python {PLANNING_DIR}/../scripts/generate_planning_index.py --repo-root {PLANNING_DIR}/.. --items-dir planning/items --out-index planning/INDEX.md --out-horizons planning/horizons.md`

Key requirements from that file:
- Every item needs a concrete "Next smallest step" and "Success looks like"
- Every item needs at least one evidence pointer (state ID, worklog path, artifact, or code)
- Dedupe against existing items — update in place rather than creating duplicates
- Use `INSTRUCTIONS_DIR/planning/_template_item.md` for new items; find the next available `B###` ID

---

## Rule 2: State item changes must follow the canonical process

Any skill that creates or modifies items in `STATE_DIR/items/*.md` **MUST**:

1. **Read `INSTRUCTIONS_DIR/state/_state_update_instructions.md` in full** before proposing any changes.
2. **Follow the step-by-step process defined there** — do not invent a separate extraction, reconciliation, or write process.
3. **Present proposed changes to the user separately by category** (new items / field updates / status flips) and wait for explicit confirmation before writing any file.
4. **Regenerate indices** after confirmed writes (the Makefile lives in the parent of `STATE_DIR`):
   - First try: `cd {STATE_DIR}/.. && make state-index`
   - If that fails: `python {STATE_DIR}/../scripts/generate_state_index.py --repo-root {STATE_DIR}/.. --items-dir state/items --out state/INDEX.md`

Key requirements from that file:
- Every item needs worklog/artifact evidence pointers
- Dedupe against existing items — update rather than duplicate
- Do NOT flip status to terminal values (`refuted`, `superseded`, `invalidated`) without explicit user confirmation
- Use `INSTRUCTIONS_DIR/state/_template_item.md` for new items

---

## Rule 3: Confirmation before any write

No skill may write, create, or edit a planning or state item file without first presenting the full proposed change set to the user and receiving explicit confirmation. Confirmation of one item does not imply confirmation of others.
