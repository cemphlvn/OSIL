# CGO 2027 R2 — paper outline (C1–C4 measurement/experience paper)

Companion to `docs/design/cgo-2027-round2.md` (claim/evidence map, submission
logistics, DECISION). This file is the section-by-section skeleton to write
into. Target: 11 pages of text excluding bibliography (ACM sigconf template,
two-column), submission 2026-09-10.

**Working title (pick one before drafting):**
- "Measured, Not Assumed: Four Ways an Optimizer's Own Evidence Misleads It"
- "What a Loop Optimizer Learns When It Leaves Its Own Benchmark"
- "Genus, Species, and the Cost of Believing Your Own Cost Model"

Working title should foreground C1 (the doc already flags it as "the
contribution most likely to be novel") without promising a speed result.

---

## 1. Introduction — ~1 page

Frame, do not apologize: this is not a speed paper (say so in paragraph one,
per `## What this is not` in the round-2 doc — pre-empt the reviewer's first
question rather than let them find it). The actual claim: a loop-vectorization
optimizer's own evaluation apparatus — the benchmark it was built against, the
cost model that prices its capabilities, the timing rig that judges a
transformation, the tool that checks its own correctness claim — is exactly
the wrong witness to trust, and this paper reports four independent instances
where trusting it would have produced a wrong or wildly overstated number.

State the four findings as one sentence each (C1–C4, see §4 table below),
then one unifying sentence: each is a different failure of **self-measurement**
— pricing, discovery, profiling, verification — caught only because something
*external* to the producing code path was consulted. Close with contributions
list (standard CGO form): (1) a prospective calibration showing genus-level
capability pricing overstates species-level delivery by 43x, (2) a
generalization probe (10 repos, 10,777 loops) that surfaces defects invisible
to the home benchmark, (3) a demonstration that a performance gate can invert
an accept/reject decision under machine-load or profile mismatch, not just
misestimate it, (4) an independent-witness validation layer that finds a
correctness bug the producing harness structurally cannot see.

## 2. Background and related work — ~1.25 pages

Two threads, kept explicit rather than blended:

- **Loop vectorization + capability-based selection.** TSVC/TSVC_2 (Callahan,
  Dongarra, Levine '88; UoB-HPC's C2 port), the ARM-vs-x86 vectorization-rate
  paper (arXiv:2502.11906) as the direct baseline this project's TSVC2 numbers
  are measured against (cite, disclose non-comparability: different hardware,
  A64FX/SVE-512 vs. M4/NEON-128). Diospyros (ASPLOS'21) for
  translation-validation-style correctness methodology — cite as a design
  precedent for §6's witness/validator split, not as a competing number.
- **Evaluation-methodology critiques this paper extends.** Kalibera & Jones
  (rigorous benchmarking methodology — repeated independent runs over a fixed
  margin, cited already in `docs/research/U15-harness-expertise.md`), SV-COMP's
  witness/validator discipline (independent checker, no shared code — the
  direct design source for C4/G25), C-Reduce's "test-case validity problem"
  (Regehr et al., PLDI 2012 — cited in G22's own gate text as prior art the
  project's own H1-H4 harness rules rediscovered 14 years later). Position
  this paper as adding two more items to that lineage: genus/species pricing
  (C1) and profile-dependent verdict inversion (C3), neither of which the
  above directly covers.

Do not survey ML-guided compilation (MLGO, Ansor, TenSet) at length — U9
already established these are a different decision surface; one sentence
citing them as adjacent-but-distinct is enough, not a subsection.

## 3. System and experimental setup — ~1.5 pages

Enough to make C1–C4 legible without re-deriving the whole architecture:

- The pipeline, one paragraph: lift (libclang) -> classify dependence
  structure -> choose a transformation -> verify correctness (differential
  harness) -> verify profitability (stopwatch) -> accept/reject. Cite G17–G22.
- TSVC2 headline table (from README "Results" section): 64/151 = 42.4% clang
  alone -> 74/151 = 49.0% with the pipeline, 10 kernels recovered at
  1.3x–4.5x, ceiling 52.3%. State plainly: below the published 56.0% record,
  different hardware, no record claimed.
- The repo-scale probe, one paragraph: ten repositories not authored by this
  project (opus, vorbis, speexdsp, libsamplerate, darknet, genann, PolyBench/C,
  NPB, milc_qcd, GSL), 10,777 distinct loops, **zero applicable candidates**.
  This negative result is the setup for C1 and C2, not a separate claim —
  frame it as the instrument the rest of the paper's findings were measured
  with, not as its own contribution.
- Machine/measurement disclosure up front (per `docs/design/measurement-contention.md`):
  Apple M4, and the explicit acknowledgment that early timing numbers were
  contaminated by background load and were corrected — this belongs in setup,
  not buried, because C3's whole point is measurement discipline.

## 4. C1 — Genus-level prices do not forecast species-level delivery — ~2 pages

The strongest section; give it the most room.

- The instrument: `capability_decl` (admits/refuses named features),
  `just price` derives a ceiling contribution *before* a capability is built —
  a zero-cost structural proxy. Cite G21.
- The prospective test: priced on the TSVC-only in-repo corpus first
  (`body.control_flow` +18), then re-derived on the held-out 5,147-loop corpus
  from the ten repositories (+599, the top-ranked refusal, blocking 2,108
  loops).
- What was actually built: predicated execution (ADR-0015), a *species* of
  `body.control_flow` — normalizes `if (P) lhs = rhs;` rather than refusing
  it. Delivered **+14** on the same corpus.
- The number: **599 / 14 ≈ 43x overstatement.** State the mechanism plainly:
  prices are quoted for a genus, capabilities get built for a species, and
  most of the priced genus (`body.nested_loop`, +2,888) was not even the same
  kind of refusal as the one built. This is a **prospective** calibration —
  the price was recorded before the build, not fit after — and that ordering
  is what makes it evidence rather than a post-hoc rationalization; say this
  explicitly, since a reviewer's first instinct will be "of course a cost
  model looks bad in hindsight."
- One paragraph of generalizable lesson: any capability-priced or
  cost-modeled optimizer that reports "this refusal is worth N" should
  disclose whether N was priced at the same granularity the fix will be built
  at — genus prices systematically overstate species delivery when the genus
  is heterogeneous.

## 5. C2 — Leaving the benchmark finds what the benchmark cannot — ~1.5 pages

- Reframe the repo-scale probe's *defect-discovery* half (§3 introduced the
  zero-applicable-candidates half).
- Table: eight wrong-code classes, split by discovery method (per the
  README's own split, which should carry into the paper unchanged since it
  was written for exactly this reason): five in already-shipped tools, each
  hiding behind a coincidence uniform across the ten probe loops (step=1,
  ascending, dead store written last, plain identifier array names, stays
  inside the differential harness's own buffer bounds); two surfaced while
  building predicated execution (a pointer-validity guard the correctness
  gate structurally cannot catch, since the harness only ever passes valid
  pointers; a trapping guarded expression); one found by the independent
  validator (G25/C4 — cross-reference forward, do not duplicate detail here).
- The worst one gets its own paragraph: the differential harness **indexed
  past its own buffers**, scoring wrong code EXACT over undefined behavior —
  name this as the safety property of the whole track being quietly weaker
  than advertised, not a minor bug.
- Lesson: a benchmark's own uniformities are invisible from inside the
  benchmark; each of the five coincidences was true of every TSVC2 probe loop
  simultaneously, which is exactly why nothing inside the benchmark could
  have surfaced them.

## 6. C3 — A performance gate can invert a decision, not just misestimate it — ~1.5 pages

- The bug, precisely: the timing loop reset ONCE per trial, then ran 200
  repetitions over what the previous repetition left behind — a converging
  kernel was timed on degenerate data, and the rig reported the *same* 2.2x
  regardless of whether a guard held 5% or 50% of the time.
- The consequence, precisely: fixture `p004` was published at **ACCEPT
  1.56x** and is a **5.9x regression** under fresh inputs, confirmed
  independently outside the rig. State the distinction the paper is actually
  about: this is not a bigger error bar on a correct verdict, it is the
  *sign* of the verdict flipping.
- The fix: fresh input per measurement, reset outside the timed region, two
  input regimes with the worst reported, `UNDECIDED-profile` /
  `UNSTABLE-margin` verdicts when regimes disagree or are inert,
  `PROFILE_DEPENDENCE` declared per family. Profitability stays advisory by
  design — a speedup is machine-dependent, but a claim that quietly stops
  holding is what the declaration is for.
- The robustness check: all ten "none60" decisions survive the stricter
  measurement (cite the specific worst-of-two-regimes numbers from
  ADR-0016), both prior rejections still reject. This matters for the
  paper's own credibility — the fix did not just change one embarrassing
  fixture, it was checked against everything already claimed.
- Fold in the machine-contention finding here or as a subsection: `s221` was
  used in this project's own earlier write-ups as the flagship example of the
  stopwatch gate working correctly (REJECTED ~1.0x) and was later found to be
  a background-load artifact (1.27x, ACCEPTED, on a quiet machine) — an
  uncomfortable but load-bearing admission that strengthens C3 rather than
  undercutting it: the paper is explicitly about not trusting your own rig,
  including when it happens to agree with your prior narrative.

## 7. C4 — Independent witness validation finds what the producer cannot — ~1 page

- SV-COMP's discipline stated plainly: not the benchmark suite, but that the
  tool emits a witness and a *separate* validator, sharing no code, decides.
  `tools/witness_check.py` imports nothing from the chooser.
- The probe surface: five input regimes (zeros, wide signed, denormals, exact
  integers, alternating extremes), trip-count edges n ∈ {0,1,2,3,5,7,8,63,
  64,65,1000} against a chooser that only ever measures n=32000, out-of-bounds
  canaries on both sides of every buffer.
- Scoring: SV-COMP's own asymmetry, CONFIRMED-EXACT +2, CLOSE +1, REFUTED −32
  — asymmetric on purpose, a single false confirmation costs far more than a
  missed one.
- The result: found dead-store wrong at n=0 (`int i = n - 1` writes index −1)
  on its **first run** — 4 refuted, score −86. After the fix: 25 witnesses,
  0 refuted, **+50**. State plainly: this is the first result in the project
  produced by a lineage that did not also produce the thing it checked —
  independence realized in code, not merely claimed by authorship.

## 8. Discussion — what this implies for optimizer evaluation generally — ~1 page

Synthesize, do not repeat. One paragraph per generalizable prescription, each
traceable to exactly one of C1–C4:
1. Disclose the granularity a price was computed at, and check it prospectively
   against the granularity anything gets built at (C1).
2. Run the tool somewhere it was not tuned before trusting a coverage or
   defect-rate number from its home benchmark (C2).
3. A performance gate needs its own correctness discipline — reset input
   state, use more than one input regime, report profile-dependence rather
   than a single number (C3).
4. Build the validator so it cannot import the thing it checks (C4).

Close with the relationship between these four and the project's stated
non-goal: none of this beats a baseline, and that is the point — the paper's
subject is what evaluation methodology cost the project before these four
fixes, not what the optimizer earns after them.

## 9. Threats to validity / limitations — ~0.5 page

State without hedging: single machine (Apple M4, NEON-128, no results on
SVE/AVX hardware); TSVC2-centric tuning with only PolyBench/GSL-class repos as
generalization evidence, not a second tuning corpus; several probes are N=1
(one predication family, one witness layer); the analysis ceiling (52.3%)
sits below the published record on incomparable hardware and no record is
claimed; three partitions (static-fact preservation, hotness sampling,
in-situ transfer) remain open and are explicitly why this is a
measurement/experience paper rather than a tool paper this round.

## 10. Conclusion — ~0.25 page

Restate the four findings in one sentence each, restate the unifying claim
(self-measurement is the wrong witness; each fix required something external
to the producing code path), and end on the artifact: `just test` is the
reproducible entry point for all four, an available (not yet AE-badged)
artifact any reviewer can run today.

---

## Page budget check

1 + 1.25 + 1.5 + 2 + 1.5 + 1.5 + 1 + 1 + 0.5 + 0.25 = **11.5 pages** — half a
page over. Trim candidates, in order: fold the `s221` machine-contention
aside in §6 into a single sentence with a footnote instead of a subsection
(-0.25); tighten §2's related-work citations to one sentence each rather than
a paragraph (-0.25). Re-check once real prose replaces these bullet budgets —
bullet-point line counts under-predict prose length, so budget for this
outline to run long and cut at the sentence level once drafted, not by
dropping a whole claim.

## What each section still needs before it can be drafted

- **Figures/tables to build:** (1) the pipeline diagram (§3 — likely reuse
  `conformance/golden-render/views/projection-map` styling if it fits, or a
  new one, since the existing view is OSIL-vocabulary-shaped, not
  pipeline-stage-shaped); (2) the TSVC2 headline table (§3, data already in
  README); (3) the genus/species price-vs-delivery table (§4, data in
  ADR-0015/docs/design/repo-scale-probe.md); (4) the eight-wrong-code-class
  table (§5, data in README's "What happened when it left the benchmark");
  (5) the p004 before/after table (§6, ADR-0016); (6) the witness scoring
  table (§7, G25 gate text has the exact numbers).
- **Anonymization pass** before submission: double-blind requires removing
  repo name/URL if it identifies the author, rephrasing "this project" framing
  consistently, and citing this project's own prior related decisions
  (ADR-0009 egglog binding, etc.) in third person per CGO's own guidance.
- **Not yet decided:** working title (three options above, pick one before
  the abstract is written, since the abstract should echo it).
