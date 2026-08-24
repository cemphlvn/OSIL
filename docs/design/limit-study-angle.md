# Capability pricing IS a limit study — checked without waiting for line G

Written 2026-08-24. U15's novelty verdict was flagged self-limited ("search
budget constrained, not a confident 'novel'"). This is the check done from the
project's own side, with each claim marked by how it is grounded.

## The genre exists, and my instrument is an instance of it

A **limit study** progressively relaxes constraints and measures the resulting
ceiling. The canonical form is David Wall, *"Limits of Instruction-Level
Parallelism"* (DEC WRL Research Report 93/6; ASPLOS '91), which measured
available parallelism under progressively idealized assumptions — perfect
branch prediction, perfect alias analysis, unbounded registers — alone and in
combination.

`tools/capability_ceiling.py --what-if <feature>` is structurally identical:
relax one declared refusal, recompute the ceiling. **The method is not new. It
is 1991.**

`VERIFIED 2026-08-24` from the PDF itself (73 pages, supplied by the maintainer):
**David W. Wall, "Limits of Instruction-Level Parallelism", WRL Research Report
93/6, November 1993.** Figure 11 is titled *"Seven increasingly ambitious
models"* — Stupid / Poor / Fair / Good / Great / Superb / Perfect — each fixing
a level for branch prediction, alias analysis, register renaming and jump
prediction. Progressive constraint relaxation, confirmed.

## The masking effect IS Wall's. The supermodularity measurement is not.

I claimed, from memory, that Wall reports combinations exceeding the sum of
individual relaxations. **Reading the paper, he does not run that experiment.**
His models are ordered ladders (all-Fair, all-Good, all-Superb), not a factorial
design over individual relaxations, so there is no sum-of-marginals to compare
against.

What he DOES document, verbatim, is the underlying masking effect:

> *"Its performance, however, is disappointing; we had hoped for more of an
> improvement. The parallelism of the Superb model is less than half that of the
> Perfect model, **mainly because of the imperfection of its branch
> prediction.**"*

Superb is excellent at everything except branch prediction, and that single
weak dimension halves the result. One bottleneck masks the benefit of relaxing
the others — which is the mechanism that produces this project's measured
supermodularity.

**Corrected verdict:** the *phenomenon* is documented in 1993. The *factorial
measurement* of it — pricing every subset and comparing joint gain to the sum of
marginals — is not something Wall did. That is a smaller claim than "novel" and
a larger one than "rediscovery", and it is the accurate one.

## Wall independently states two cautions this project had already recorded

From the same sentence:

> *"A study using the Perfect model alone would lead us down a dangerous garden
> path, as would a study that included only fpppp and tomcatv."*

1. **Do not report the all-idealized ceiling as if achievable.** This project's
   `96.0% if all four capabilities land` is exactly a Perfect-model number, and
   was already flagged as an upper bound on ATTEMPTS rather than outcomes.
   Wall puts it more sharply: reporting it alone is a garden path.
2. **Do not trust a narrow benchmark.** Wall used eighteen programs and warns
   that two would mislead. Every price in this project is measured on TSVC2
   alone — already recorded as the missing held-out corpus, and now with a
   1993 precedent for why it matters.

## The domain precedent is the author of our own benchmark

`VERIFIED` (from this repo's own U7 and U12): the 151-loop C TSVC used all
session — `UoB-HPC/TSVC_2`, and the corpus behind arXiv:2502.11906 — descends
from **Maleki, Gao, Garzarán, Wong, Padua, "An Evaluation of Vectorizing
Compilers," PACT '11**, which ported and extended Callahan/Dongarra/Levine's
1988 suite to 151 loops.

`RECALLED, UNVERIFIED`: that paper's methodology was to run several production
compilers over TSVC and then **manually analyse and vectorize the loops the
compilers missed**, establishing how many were vectorizable in principle. If
that is right it is a vectorization limit study on *exactly this benchmark*, and
it is the nearest prior art to the capability model by a wide margin.

**ACTION, and it is cheap:** get that paper. It plausibly contains the empirical
true cap for TSVC — the number `docs/design/theoretical-cap.md` currently
estimates at ~75-80% by extrapolating a 20.7% recurrence rate from a biased
sample. A measured figure from the benchmark's own authors would replace a
guess, and would settle whether the 96% all-four figure is an upper bound on
attempts or nonsense.

## What is left that might actually be new

Stated narrowly, because the two above are not:

1. **The capability set as a declared, versioned artifact inside the running
   system** — `conformance/corpus/026`, with the system checking that its
   self-model still corresponds to its machinery (G21 lie-detection, G22
   vocabulary reachability). In the literature a limit study is a paper's
   methodology; here it is a gated component that fails the build when the
   model and the machinery diverge.
2. **The predicted-vs-realized calibration loop.** A limit study establishes
   headroom and stops. This project priced `subscript.wraparound` at +3, built
   it, measured +2, and traced the 33% gap to a specific classification defect
   (a forward alias lumped in with genuine wrap-arounds). Closing that loop —
   using realized gain to falsify the price — is the part I would defend.

Neither is a large claim. Both are smaller than "capability pricing is novel",
which is what U15 declined to assert and which should not be asserted here.

## The reframe this suggests for the whole optimizer track

If limit studies are the genre, then the interesting output was never beating
GCC's 56%. It is **characterizing the headroom mechanically** — which is what
Maleki et al. appear to have done by hand, and what this project's capability
model does as an executable, gated artifact.

That reframing also retires the disappointment recorded in
`docs/design/record-attempt.md`. The record attempt failing is not the result.
The measured ceiling, its decomposition by blocker, and the calibration of a
prediction against a realized outcome are the result.
