---
name: skill-improver
description: Improve any skill in improvable/ from a concrete feedback signal, under the constitution/legislation rule
scope: [improvable/]
verbs: [edit-body, propose-frontmatter]
cadence: feedback
invariants: [evals-pass, changelog-logged, frontmatter-constitutional, never-self-frontmatter]
evals: evals/
---

# skill-improver

Improve a skill when — and only when — there is a concrete feedback signal:
a gate failure, an agent that misapplied the skill, a human correction, or an eval
regression. "It could be better" without a signal is not a trigger.

## Procedure

1. **Capture the signal.** Write one sentence: what happened, which skill, which
   step of its body failed or misled. If you cannot name the step, the fix belongs
   elsewhere (maybe GOVERNANCE, maybe a README card) — stop and report instead.
2. **Classify: body or constitution?**
   - Fix expressible by editing procedure text → body edit (proceed).
   - Fix requires touching `scope`, `verbs`, or `invariants` → constitutional:
     write a proposal into the skill's CHANGELOG.md under `## Proposed`, tag a
     human, STOP. Never apply frontmatter changes yourself.
3. **Edit the body.** Smallest change that addresses the signal. Keep the body
   harness-neutral: any file-reading agent must be able to execute it; put
   tool-specific guidance only under `## Harness notes`.
4. **Run the skill's evals** (`<skill>/evals/`). Every fixture states a situation
   and the behavior class the skill must produce; check the edited body still
   yields each. A failing fixture = revert or iterate; never delete a fixture to
   make it pass (deletion is constitutional).
5. **Grow the evals.** Add one fixture derived from the triggering signal, so this
   failure class is caught next time. Mark it `held-out: false`. Roughly every
   third new fixture should be marked `held-out: true` — held-out fixtures are for
   measuring, not for optimizing; do not read them while editing bodies.
6. **Log it.** CHANGELOG.md entry: date, signal, change summary, eval result.
   The ledger is what lets a fresh agent resume this loop — agents are stateless,
   the loop is not.

## Self-application limits

- This skill may edit other skills' bodies. For its OWN body, apply steps 1–6 with
  the full eval set of ALL skills as the regression bar.
- This skill may NEVER edit its own frontmatter, under any procedure.

## Harness notes

Claude Code: prefer the Edit tool for body changes so diffs stay minimal; evals are
plain-markdown fixtures — evaluate them by reading, they are not executable yet.
