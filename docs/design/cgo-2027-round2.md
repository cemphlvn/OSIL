# CGO 2027 Round 2 — claim/evidence map and what is missing

Target: **paper submission 10 September 2026** (rebuttal 20–22 Oct, notification
2 Nov; conference 20–24 Mar 2027, Salt Lake City). Tool-paper track exists and
makes artifact evaluation **mandatory**; artifacts are badged Available /
Functional / Reusable / Results Reproduced, with up to 10% Distinguished Papers
and up to 10% Distinguished Artifacts.

**Verified 2026-08-29** against `2027.cgo.org/track/cgo-2027-papers`
(cross-checked `conf.researchr.org/track/cgo-2027/cgo-2027-papers`): Round 2
has a distinct "new R2 submissions" category, separate from "R1-revision
submissions" — a paper that never went through Round 1 may submit fresh on
10 September 2026, 11:59pm AoE. Format is ACM, 11 pages of text excluding
bibliography, unlimited references, and supplementary material without page
limit (reviewers not obliged to read it). Double-blind: anonymize, discuss own
prior work in third person. **Artifact evaluation is optional for standard
research papers** — the mandatory-AE requirement binds only the tool-paper
track. The earlier `ASSUMPTION:` here (that the Round 2 AE schedule needed
chair confirmation) is resolved: it does not apply, because this submission is
not entering the tool-paper track at all (see DECISION below).

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
Useful Information"*), with no deadline pressure.

**Verified 2026-08-29** (ACM's own author-guidelines and APC pricing pages,
via search — `dl.acm.org/journal/taco` blocks direct fetch with 403, so this
is search-summary sourced, not a primary-document fetch; re-verify by reading
the guidelines page directly before a real submission). TACO's own scope
statement is a near-exact genre match: *"Articles that appear in TACO present
new techniques and concepts OR report on experiences and experiments with
actual systems"* — the "experiences and experiments" half is C1–C4 with no
reframing needed. Continuous submission (no deadline), 20 pages initial
(text+figures, excluding references, strict), double-anonymous review,
ACM template required. **New cost factor found, not in scope when this doc was
first written:** ACM became a fully Open-Access publisher 2026-01-01 — every
journal article now carries an APC unless the corresponding author's
institution is one of 1,800+ ACM Open participants (or in a World Bank
low-income country). A solo/unaffiliated author pays the **2026 subsidized
rate: $250 (ACM/SIG member) or $350 (non-member)** — but that subsidy is
**temporary and journal-specific**: 2027 onward, journal APCs revert to list
price ($700 member / $1,000 non-member; conference proceedings keep a
subsidized rate longer, journals do not). Since TACO is the *fallback*
(pursued only if CGO is rejected, with notification 2 Nov 2026), a TACO
submission would likely fall in early-to-mid 2027 — check which APC rate
applies **at actual submission time**, not against this note's 2026 figures.

---

## DECISION (2026-08-29)

Accepted this document's own recommendation: **skip the tool-paper track,
submit C1–C4 as a "new R2 submission" to CGO 2027's regular research track**,
deadline 10 September 2026, 11:59pm AoE. E remains open and unattempted (no
code exists toward C, D, or E as of this date) and is not required for this
track — optional AE, if pursued, can rest on the already-closed C1–C4 evidence
without waiting on E. Hold the tool-paper track for a future round where E has
passed once, per this doc's original condition. TACO submission process is now
checked (see above) and confirmed a genre and page-budget fit; not needed
unless the CGO submission is rejected, at which point re-verify the APC rate
in effect at that time before submitting.
