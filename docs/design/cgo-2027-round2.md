# CGO 2027 Round 2 — claim/evidence map and what is missing

Target: **paper submission 10 September 2026** (rebuttal 20–22 Oct, notification
2 Nov; conference 20–24 Mar 2027, Salt Lake City). Tool-paper track exists and
makes artifact evaluation **mandatory**; artifacts are badged Available /
Functional / Reusable / Results Reproduced, with up to 10% Distinguished Papers
and up to 10% Distinguished Artifacts.

`ASSUMPTION:` the artifact-evaluation cycle listed on the CGO 2027 site
(submission 31 Aug, notification 15 Oct) aligns with **Round 1** acceptances.
The Round 2 AE schedule is not stated there and must be confirmed with the
chairs before committing to the tool-paper track.

## What this is not

It is not a speed paper. No tuned baseline has been beaten; the derived analysis
ceiling (52.3%) sits **below** the published TSVC figure (56.0%), which is on
different hardware and is not comparable anyway; and across 10,777 loops in ten
repositories the transformation catalogue matched **zero**. Submitting this as a
performance result would fail on the first reviewer question.

There is also no leaderboard to enter. CompilerGym — the only submission-based
compiler-optimization leaderboard — was archived 27 May 2026, and TSVC has never
been a competition.

## What it is: four claims, each with gated evidence

| # | claim | evidence | gate |
|---|---|---|---|
| C1 | **Measurement priced its own gaps at +599; the buildable species delivered +14.** Capability prices computed at **genus** level do not forecast what building a capability delivers, because capabilities are built at **species** level — a measured overstatement of **43x**. | `docs/design/repo-scale-probe.md`, ADR-0015 | `just ceiling`, `just choose` |
| C2 | Pointing a loop optimizer at code it did not author finds defects a home benchmark structurally cannot. **Five**, each traced to a coincidence uniform across the probe set (step, replay distance, member naming, iteration direction, harness bounds). | `conformance/lift/repo-pins/` | `just choose` |
| C3 | A performance gate that destroys its input distribution can **invert** decisions, not merely mis-estimate them. Fixture `p004` was published at ACCEPT 1.56x and is a 5.9x regression. | ADR-0016 | `just choose` |
| C4 | Preservation claims validated by an **independent** checker find bugs the producing harness cannot. Found dead-store wrong at n = 0 on first run. | ADR-0017 | `just witness` |

C1 is the contribution most likely to be novel: it is a **prospective**
calibration of a capability-pricing instrument, and the genus/species rule falls
out of it. C3 and C4 are methodological results about how optimizer evaluation
goes wrong, which is squarely CGO's subject matter.

## The artifact is the strong half

Single reproducible entry point (`just test`), every claim carrying a witness or
a pin, refusals named by species, negative fixtures at each boundary, and now
mutant pins for the validator itself. That maps directly onto *Functional* →
*Reusable* → *Results Reproduced*.

## What is missing, in dependency order

- **C (static facts).** The lifter is type-blind and the emitter types every
  array `float`; most of opus is Q14 `int32`. *Gate:* a constant-bound loop's
  emitted `orig` and its in-file original get the same `-Rpass=loop-vectorize`
  verdict.
- **D (hotness).** *Gate:* sample one repository's own test suite; `min_curve`,
  called once per stream, must drop out of the candidate list.
- **E (in-situ transfer).** *Gate:* one patched loop, built in the real
  repository, measured on that repository's own benchmark, agreeing with the rig
  within a stated tolerance.

**E is the gate that decides the track.** Without it the honest submission is a
measurement/experience paper on C1–C4. With it, the tool paper becomes available
and the mandatory artifact requirement turns the gate discipline from overhead
into the strongest part of the submission.

## Schedule reality

15 days from 26 Aug. C1–C4 are already evidenced and gated; the writing is the
work, not the research. E is not plausible in that window at the standard the
rest of the repo is held to. Recommended: write C1–C4 as the measurement paper,
and hold the tool paper for a round where E has passed.

A journal is the lower-risk home for C1–C4 — ACM TACO has published exactly this
genre (*"Evaluating Auto-Vectorizing Compilers through Objective Withdrawal of
Useful Information"*), with no deadline pressure. `ASSUMPTION:` TACO's current
submission process has not been checked.
