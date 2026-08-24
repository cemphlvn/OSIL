# The theoretical cap, and the bridge to it

Measured 2026-08-24 with `tools/c_lift.py` over all 151 TSVC2 kernels. Every
number below is computed, not estimated.

## Partition of the suite

| kernels | class |
|---|---|
| 41 | straight-line, affine, 1-D, **no irreducible recurrence** — parallelizable |
| 12 | analysable but a **true recurrence** — never vectorizable without a scan algorithm |
| 98 | **unanalysable** by an affine straight-line model |

## Ceiling of the CURRENT architecture

```
clang -O3 already vectorizes                     64/151
straight-line affine 1-D, no recurrence             41
   of which clang already gets                      28
   remaining headroom for our chooser               13   <- the entire cap
   we actually recovered                             6

CEILING (clang + a perfect chooser of this kind)  77/151 = 51.0%
we are at                                         70/151 = 46.4%
published record (GCC, A64FX SVE-512)             85/151 = 56.0%
```

**The current architecture cannot reach the record.** Even at 100% of its own
ceiling it falls 5 points short of GCC. Only **7 kernels** of headroom remain
inside it. Grinding on more transformation families is provably not the path —
this is why `record-attempt.md`'s kill condition was the right call, and now
there is a structural reason rather than a disappointing measurement.

## The true cap

- **Empirical floor: 60.3%** — the union of GCC + ACFL + Clang on A64FX
  vectorizes 91/151, so at least that much is achievable in practice.
- **Estimated cap: ~75-80%.** Irreducible recurrences are the only hard limit.
  We measure 12 among 58 analysable loop nests (20.7%). If that rate holds
  across the unanalysable 98, ~32 kernels are genuinely non-vectorizable,
  putting the cap near 119/151 = 78.8%. `ASSUMPTION:` the extrapolation is from
  a biased sample — the analysable loops are the simpler ones.

So roughly **20-25 points of headroom exist that no compiler captures.**

## What blocks the 98, measured

| kernels | blocker | bridge required |
|---|---|---|
| 58 | control flow in the body | **if-conversion / predication** |
| 59 | non-affine subscript (`a[idx[i]]`, wrap-around scalars) | **runtime versioning**, or pattern recognition |
| 31 | 2-D array access | **multi-dimensional dependence test** (GCD / Banerjee / polyhedral) |
| 12 | true recurrence | **scan recognition** — and a numeric licence, since it reassociates |

Heavily overlapping: 25 kernels have all three of control flow, non-affine
subscripts, and 2-D access simultaneously.

## The bridge, and why it is an OSIL-shaped problem

Each blocker is an **analysis** capability the compiler lacks. Each also has a
corresponding **declaration** that would discharge it without the analysis:

| blocker | what analysis must PROVE | what a declaration would STATE |
|---|---|---|
| control flow | both arms are safe to speculate | side-effect freedom of the branch |
| non-affine subscript | `idx[]` never collides | an index-injectivity invariant — precisely what `restrict` **cannot** express |
| 2-D access | the multi-index dependence test | **indexing maps + iterator types** — the MLIR `linalg` vocabulary U8 recommended |
| recurrence | the operator is associative | `numeric_semantics = reassociable` — **we already have this** |

This is the OSIL thesis, now sized with real numbers instead of asserted. The
route from 51% to the cap is **not** better analysis; it is moving the burden
from proof to declaration. Three of the four vocabularies do not exist yet; the
fourth already ships and is gated.

## Consequence for the C ecosystem profile

`profiles/ecosystem/c/CONTRACT.osil` currently declares
`may_lose { declared_licence }` — C cannot carry the guards. That is exactly why
the bridge cannot be built *in C*: `restrict` is the only invariant C offers and
it is inter-array only (measured: 0 of 151 loops recovered).

So the bridge has to live **above** C, in the declaration layer, with C as the
lowering target it already is. The C profile is the right shape; what is missing
is the vocabulary the declarations would be written in.

## Honest reading

The cheapest true statement here: **the ceiling of what we built is 51%, and
that number was knowable before the record attempt started.** Computing it took
one afternoon with tooling that already existed. Next time, compute the ceiling
of the architecture before committing to a target that sits above it.


---

# Capabilities are COMPLEMENTARY — marginal pricing is the wrong instrument

Measured 2026-08-24 after building `just price`, and it inverted the intuition
that motivated building it.

The expectation was **sub**additive: blockers overlap (25 kernels carry control
flow AND non-affine subscripts AND 2-D access), so a joint gain should be less
than the sum of marginals. The measurement says the opposite.

| capability set | ceiling | gain | sum of marginals |
|---|---|---|---|
| `multi_dimensional` | 51.7% | +1 | 1 |
| `true_carried` | 57.0% | +9 | 9 |
| `indirect` | 60.9% | +15 | 15 |
| `control_flow` | 62.9% | +18 | 18 |
| `control_flow + indirect` | 74.8% | **+36** | 33 |
| `multi_dim + control_flow + indirect` | 85.4% | **+52** | 34 |
| all four | 96.0% | **+68** | 43 |

**A kernel blocked by two features is unlocked by NEITHER alone.** The
triple-blocked kernels contribute zero to every marginal price and contribute
fully to the joint. The set function is supermodular, not submodular.

## Why this matters as a decision paradigm

Marginal pricing says **never build `multi_dimensional`** — it is worth +1.
Joint pricing says it is worth +18 in the right company (`+52` vs `+34` for the
triple). A decision procedure reading marginal prices would have discarded
exactly the capability that unlocks the largest combination.

`tools/capability_ceiling.py` now reports both and labels the marginal table
MISLEADING ON ITS OWN. Build ORDER must be chosen from the joint table.

## Two gaps this analysis still has

1. **No held-out corpus.** Every price here is measured on TSVC2 — a suite
   *designed* to reward vectorization. Real-code coverage was measured far
   lower (kissfft lifted at 0%). A capability priced +18 here could be +0 in
   the field. This is the same overfitting hazard `calibration/` was built to
   prevent at G19, reintroduced one gate later in a new place. Prices need a
   fit/held-out split of their own.
2. **Price has no risk term.** Admitting control flow is precisely what let the
   chooser emit INCORRECT code (s277/s278/s279). A capability that raises the
   ceiling while opening an unsoundness class is not comparable to one that does
   not, and the instrument currently reports only the upside.

## Caution on the 96%

The all-four figure EXCEEDS this document's own estimated cap of ~79%. That is
not a contradiction; it means the capability model measures **analysability**,
not **vectorizability**. Admitting `dep.true_carried` counts recurrences as
recoverable when many need scan algorithms that may not exist or may not pay on
4 lanes. Treat 96% as an upper bound on what could be ATTEMPTED.


---

# U14 correction: part of the gap to the record was a MODELING error

`dep.true_carried` tested "has a true carried dependence" and treated that as
"is an irreducible recurrence." Those are different things. A carried flow
dependence BETWEEN statements is separable by distribution — this repo had
already recovered `s211` (1.66x) and `s1213` (1.67x) exactly that way,
bit-identical, with no scan and no licence — while only a dependence CYCLE is
irreducible.

The feature is now `dep.recurrence_cycle`, computed from the chooser's own SCC
analysis (a multi-statement SCC, or a self-edge). Consequences:

| | before | after |
|---|---|---|
| baseline ceiling | 77/151 = 51.0% | **79/151 = 52.3%** |
| `dep.*` marginal price | +9 | **+7** |
| gap to the 56.0% record | 8 kernels | **6 kernels** |

**Two kernels of the "gap to the record" were self-inflicted.** The ceiling was
never 51.0%; the model said so because a declaration was wrong. The machinery
had already beaten its own stated ceiling and the instrument could not see it.

This also means the old price DOUBLE-COUNTED: it charged the (unbuilt) scan
capability for kernels the (shipped) distribution capability had already won.
Conservative would have been safe. This was not conservative — it inflated the
price of work not yet done, which is the more dangerous direction.

## Corrected prices

```
baseline                                        79/151 = 52.3%
+1   access.multi_dimensional                          53.0%
+7   dep.recurrence_cycle                              57.0%
+15  subscript.indirect                                62.3%
+19  body.control_flow                                 64.9%
+37  control_flow + indirect                           76.8%   <- the pair
+53  multi_dim + control_flow + indirect                87.4%
                                     record          = 56.0%
```

## `dep.recurrence_cycle` is close to worthless — retire it as a target

U14 decomposed the 7. Only **3** are pure associative scans reachable with the
`reassociable` guard this repo already ships (`s221`, `s242`, `s323`). Two
(`s321`, `s322`) are linear recurrences with varying coefficients needing an
affine-pair/matrix-composition monoid — a genuinely different algebraic
structure, not `reassociable`. One (`s222`) is a nonlinear squaring recurrence
with no known parallel-scan algorithm: a permanent refusal.

And profitability is against it. U14 found Lemire's **2026-03 Apple-M4** NEON
prefix-sum benchmark: a naive SIMD scan measured **0.92x — SLOWER than scalar**,
with heroic tuning reaching 2.3x only on an easier bandwidth-bound integer
kernel. Estimate for a mechanical realization: **0.9x-1.5x**, i.e. a likely
third correct-but-slower result after `s116` (0.33x) and `s221` (1.08x).

**Decision: do not build scan.** ~3 addressable kernels at ~1x. The guard reuse
that made it look cheap does not survive contact with the profitability data.
