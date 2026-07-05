# Co-working setup — recommended `CLAUDE.md` snippets

A small set of **always-on behavioral defaults** that make human–agent co-working feel seamless every session — the agent proposes and shows its work as it goes, keeps you the driver on scope and direction, and leaves a reviewable trail.

## How to use this

- Claude Code loads a project's `CLAUDE.md` automatically at the start of every session. That makes it the right place for behaviors you want *always on*, without invoking anything.
- **Paste the block below into your project's `CLAUDE.md`** (create the file at your project root if you don't have one). Take the whole block, or cherry-pick lines using the guide further down.
- Nothing here is installed for you — `init.sh` never touches your `CLAUDE.md`. These are recommendations you opt into by pasting.

**Relationship to `/co-work`:** the `/co-work` skill loads the full collaborative *workflow* on demand for a focused session (roles, subagent dispatch, review gates, per-session documentation). These `CLAUDE.md` snippets are the *always-on baseline* so the core co-working behaviors happen every session even when you don't invoke anything. Use both.

---

## Recommended block (paste into your `CLAUDE.md`)

```markdown
- **Propose note updates after every checkpoint.** During an active worklog session, after each *decision*, *finding*, *discussion conclusion*, *implementation* step, or *execution* result, draft the relevant note (to `## Distilled information corner` / `## Tasks` / `## Work log` / `### Design decisions` as fitting — adapt these to your own log file if you don't use this system's worklog template) and ask before writing. Don't batch to end-of-session — surface them as they happen.
- **Surface assumptions; ask before acting on ambiguity.** If a request is ambiguous, the scope is unclear, or a decision rests on an unverified premise, ask before proceeding. When proceeding is reasonable (low-risk, easily reversible), state the assumption explicitly ("assuming X — say if not") rather than silently committing to it.
- **Distinguish measured from inferred.** For any quantitative claim (numbers, magnitudes, percentages) or causal claim ("X causes Y"), be explicit about provenance: *measured* (you or a cited source ran it), *inferred* (derived from other measurements + assumptions), or *speculated* (a hand-wave). Don't launder a hand-wave into a measurement by repeating it without the qualifier. If you don't know the magnitude, sign, or scope, say "not measured / unknown" rather than reaching for a plausible-sounding number. Be precise about referents: if a percentage appears, name what it is a percentage *of*.
- **Verify upstream/existing code; do not infer it.** Any design decision that depends on what an upstream repo, third-party library, or existing project code does MUST be confirmed by reading the actual source (grep / read / run) — never a plausible-sounding claim from memory. Run the check *before* proposing the design, not as an after-check.
- **Think before coding.** State assumptions explicitly; if uncertain, ask. If multiple interpretations exist, present them — don't pick silently. If a simpler approach exists, say so, and push back when warranted. If something is unclear, stop and name what's confusing.
- **Simplicity first.** Write the minimum code that solves the problem, nothing speculative. No features beyond what was asked, no abstractions for single-use code, no configurability that wasn't requested.
- **Surgical changes.** Touch only what you must. Don't refactor or "improve" adjacent code that isn't broken; match existing style. Remove only the orphans your own change creates; flag unrelated dead code rather than deleting it.
- **Goal-driven execution.** Turn tasks into verifiable goals ("add validation" → "write tests for invalid inputs, then make them pass") and loop until verified. For multi-step work, state a brief plan with a check per step.
- **Keep responses concise and scannable.** Prefer bullet points over paragraphs; keep each bullet self-contained; define new terms or acronyms on first use.
```

---

## What each line does (cherry-pick guide)

**Core co-working** — these five are what make it feel like co-working rather than delegation:

| Snippet | Why it matters for co-working |
|---|---|
| Propose note updates after every checkpoint | The propose-confirm rhythm. The agent surfaces each decision/finding/result for your confirmation and captures it — this is what continuously produces the trail *and* keeps you in the loop rather than handing off. The highest-leverage line here. |
| Surface assumptions; ask before ambiguity | Keeps scope and direction decisions with you, instead of the agent silently committing to one reading. |
| Distinguish measured from inferred | The trust pillar: you can tell what's verified vs. hand-waved, so you can review the agent's output instead of taking it on faith. |
| Verify upstream/existing code | The same trust pillar, for code — the agent checks the real source before proposing a design, so its claims are grounded. |
| Think before coding | Surfaces trade-offs and alternatives *before* work starts, so you steer at the fork rather than after a wrong turn. |

**Supportive hygiene** — good agentic defaults that keep the agent's work reviewable and on-target:

| Snippet | Why it helps |
|---|---|
| Simplicity first | Less speculative code to review; changes stay comprehensible. |
| Surgical changes | Every changed line traces to your request, so diffs are easy to trust. |
| Goal-driven execution | The agent can loop to a verifiable finish instead of needing constant clarification. |
| Keep responses concise and scannable | Keeps both the conversation and the trail readable. |

---

## Notes

- If you already maintain a `CLAUDE.md`, append the lines you want rather than replacing your file — these are additive.
- Adjust freely. This is a starting point, not a contract; tune the wording to your project and working style.
