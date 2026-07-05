# CoCo Manager

*Short for **Co**-working **Co**ntext Manager.*

**Shared memory for human–agent co-working, inside [Claude Code](https://docs.anthropic.com/en/docs/claude-code).**

You just spent an hour reconstructing where you left off — which question you were chasing, what you decided and threw away, why the half-written test was the right one. Every project switch costs that hour, for you *and* for the agents you work with. CoCo Manager keeps a small, disciplined trail of notes — worklogs, decisions, open questions, a backlog — in a layout you and your agents can both scan, so picking back up takes five minutes instead of an hour.

## What this is

- A **skills + markdown system** that runs inside Claude Code.
- Keeps your project's memory alive across sessions: worklogs, decisions, hypotheses, open questions, and a backlog — all linked, all plain markdown.
- Built for people who **switch contexts** and work *with* agents (often several at once), not just delegate to them.

## Who it's for

- Researchers and solo knowledge workers juggling 1+ projects with long-running context.
- **Not for** projects you'll finish in a couple of days — the overhead isn't worth it without a context-switching problem to solve.

## Quickstart

```bash
git clone https://github.com/shumanpng/coco-manager.git
cd <your-project>                                  # the project you want memory for
bash /path/to/coco-manager/init.sh                 # sets up .claude/skills/ + a notes dir
# open Claude Code in your project, then:
/setup                                             # writes your paths into meta.md
```

Then start your first session:

```
/new-worklog
```

That's it. See the **[tutorial](https://shumanpng.github.io/coco-manager/tutorial.html)** for what to do next, or the [full site](https://shumanpng.github.io/coco-manager/) for the overview and [how it works](https://shumanpng.github.io/coco-manager/how-it-works.html).

## Your first session

The whole system on day one is three commands: `/new-worklog` to open a session, *work in the worklog* as you go, `/end-session` to close it. Everything else — meetings, planning, weekly cycles, co-working — layers on later.

Full first-week guide: **[the tutorial](https://shumanpng.github.io/coco-manager/tutorial.html)**, part of the [full site](https://shumanpng.github.io/coco-manager/). It's also installed offline by `init.sh` at `<notes-dir>/.coco-manager/site/index.html`.

## Examples

The [`examples/`](./examples/) directory holds real, lightly-redacted artifacts from this system's own development — worklogs, planning items, and state items with their generated index views — so you can see what a populated notes dir actually looks like.

## What's included

| Skill | What it does |
|-------|--------------|
| `/setup` | Configures `meta.md` paths for your project (run once). |
| `/new-worklog` | Creates today's worklog, optionally resuming from a previous one. |
| `/end-session` | Distills today's worklog (and any co-working sublogs) into a summary + state/planning updates. |
| `/catchup` | Briefs you on recent worklogs and surfaces open tasks. |
| `/status` | Prioritization dashboard from planning + state + today's worklog. |
| `/new-meeting` | Creates a meeting note from the template. |
| `/process-meeting` | Extracts decisions, action items, and state updates from a meeting note. |
| `/build-week` | Produces a weekly plan from planning + state + recent meetings. |
| `/end-week` | Reviews the week's actual work against the plan. |
| `/co-work` | Adopts the collaborative co-working workflow (propose → dispatch subagents → review → verify → document) for the rest of the session. |
| `/audit` | Wraps a write-heavy skill with independent proposer + reviewer subagents that draft and audit before any writes. |
| `/about` | Lists the installed skills and points to this tutorial. |

For always-on co-working defaults (so the propose-confirm rhythm applies every session without invoking `/co-work`), paste the snippets from [`co-working-setup.md`](./co-working-setup.md) into your project's `CLAUDE.md`.

## FAQ

**How do I update?** v1 is a snapshot — re-clone if you want a newer version. A safe update flow is planned for a future release.

**Does this work without Claude Code?** No. The skills are markdown instructions Claude Code reads. But your *data* is plain markdown — worklogs, planning items, and state items stay readable (and editable) in any tool, including as an Obsidian vault.

**Can I customize the templates?** The templates under `<notes-dir>/.coco-manager/instructions/` are **repo-owned** — re-running `init.sh` overwrites them. For custom flows, fork the repo or open an issue. Your *data* dirs (`worklogs/`, `planning/items/`, `state/items/`, `meeting/`) are never touched by `init.sh`.

**Will `init.sh` clobber my own files?** No. It installs repo-owned files under `.claude/skills/`, plus a `.coco-manager/` folder, a `Makefile`, and a `scripts/` dir in your notes dir. It **aborts rather than overwrite** a pre-existing `.coco-manager/`, `Makefile`, or `scripts/` it didn't create, and it preserves any skills you already have in `.claude/skills/`.

## Acknowledgments

CoCo Manager has been in development since January 2026. A big thank-you to **nio** ([niopeng](https://github.com/niopeng)) — the first person besides me to use it, and its earliest contributor — who put a rough early version to real use in February 2026 and helped shape the session and note-summary workflows the system is built on. See [CONTRIBUTORS.md](./CONTRIBUTORS.md).

## License

MIT — see [LICENSE](./LICENSE).
