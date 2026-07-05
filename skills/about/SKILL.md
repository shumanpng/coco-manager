---
name: about
description: Lists installed context-manager skills and points new users to the tutorial. Triggers when the user types `/about`, asks "what skills are available", "what can I do with this", or "tell me about this system".
---

# About

Print the following text verbatim.

---

**The context-manager system in one line:** keeps your project's memory alive across sessions so you don't spend an hour re-onboarding every time you switch contexts.

## Installed skills

| Skill | What it does | When to use |
|-------|--------------|-------------|
| `/setup` | Configures `meta.md` paths for your project | First-time setup, or whenever you change directory layout |
| `/new-worklog` | Creates today's worklog (resumes from a previous one if you choose) | Start of every work session |
| `/end-session` | Distills today's worklog into state items + planning items | End of every work session |
| `/catchup` | Briefs you on recent worklogs and surfaces open tasks | Picking back up after 2+ days away |
| `/status` | Prioritization dashboard from planning + state + today's worklog | Mid-session "what should I be doing" |
| `/new-meeting` | Creates a meeting note from the template | Before any meeting that produces decisions/actions |
| `/process-meeting` | Extracts decisions, actions, and state updates from a meeting note | After every meeting (review transcript first) |
| `/build-week` | Produces a weekly plan from planning + state + recent meetings | Start of each week (or when you want to reset focus) |
| `/end-week` | Reviews the week's actual work against the plan | End of each week |
| `/audit` | Wraps a write-heavy skill with independent proposer + reviewer subagents that draft and audit the work before any writes | When you want a high-confidence pass for a complex skill (e.g. `/audit end-session`) |
| `/co-work` | Adopts the collaborative co-working workflow for the rest of the session (Research Engineer Collaborator: propose → dispatch subagents → review → verify → document) | Start of a focused collaborative session where you want quality gates and per-session documentation |
| `/about` | This message | Whenever you forget what skills exist |

## If you're new — start here

Day-one minimum loop (interview Q7 layering order):

1. `/setup` (one-time)
2. `/new-worklog` → work in the worklog → `/end-session`

That's it. Add the others as you get comfortable. The full layering order is in the tutorial (linked below).

## Where to find more

- Tutorial (online): https://shumanpng.github.io/coco-manager/
- Tutorial (local install copy, always present): `<notes-dir>/.coco-manager/site/index.html`
- Co-working defaults (optional `CLAUDE.md` snippets, opt-in): `<notes-dir>/.coco-manager/co-working-setup.md` (local install copy) or `co-working-setup.md` in the repo
- Issues / discussions: GitHub.
