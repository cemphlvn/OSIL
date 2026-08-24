# U14 — Recurrence scan: is admitting `dep.true_carried` the cheapest of the three theoretical-cap capabilities?

**Date:** 2026-08-24
**Researcher:** research-agent
**Question:** `docs/design/theoretical-cap.md` prices admitting `dep.true_carried` (a true
loop-carried recurrence) at **+9 kernels, 51.0% -> 57.0%**, above the published
56.0% record, and observes that `numeric_semantics = reassociable` — the guard
that would license it — already exists and is gated in this repo. Is that framing
right? How many of the 9 are actually parallelizable scans, what declaration
vocabulary would a scan need beyond what already exists, and is a NEON-128
realization honestly profitable, given this project has already measured two
"correct but not faster" results on directly comparable loop shapes (s116 at
0.33x before a fix, s221 at 1.08x — an Amdahl-capped near-wash)?

## Method

The user's six numbered investigation lines are close to MECE already (algorithm
complexity; compiler prior art; recurrence taxonomy; numeric cost; declaration
vocabulary; NEON profitability), so this document follows them directly rather
than re-decomposing. One gap the six lines leave implicit: **neither
`theoretical-cap.md` nor `optimizer/probe/none60/README.md` names which 9
kernels compose the +9** — the number is asserted, not shown. Treating an
un-shown number as ground truth would violate this project's own evidence
hierarchy (measured, not estimated — `theoretical-cap.md`'s own opening line).
So a seventh, self-added line: **mechanically re-derive the 9 by name**, using
the project's own G21 tooling (`tools/capability_ceiling.py`, ratified
2026-08-24, same day as the theoretical-cap measurement) against a freshly
vendored TSVC_2 source tree. That re-derivation is Section 1 and it is the
load-bearing finding of this document — the other sections (external literature
on scan algorithms, LLVM/GCC capability, numeric error, NEON estimate) are
in service of interpreting what was found there.

**Primary sources used, ranked:** (1) this repo's own source and tooling, run
directly — `tools/c_lift.py`, `tools/capability_ceiling.py`,
`conformance/corpus/026-capability-analysis.osil`,
`optimizer/probe/none60/README.md`, `optimizer/README.md`,
`profiles/domain/numeric/numeric.osil`, `conformance/interop/c/{cases,refusals}/*.osil`
— all read or executed, not paraphrased from memory; (2) TSVC_2's own source
comments (`src/tsvc.c`, Argonne/UTK benchmark, vendored to scratch for this
investigation) — the benchmark authors' own classification of each loop
("first order linear recurrence", "second order linear recurrence", "coupled
recurrence" — a primary, authoritative taxonomy, not inferred); (3) LLVM's own
patch review (D16197) and docs (`llvm.org/docs/Vectorizers.html`) for compiler
capability; (4) peer-reviewed/technical literature for scan complexity and
floating-point error; (5) one blog post (Lemire, 2026-03, Apple M4 NEON prefix
sum) — flagged as blog-tier evidence but unusually strong because it is **the
same CPU family this project benchmarks on**, dated, with source code and raw
throughput numbers, not just claims.

---

## TL;DR — answers to the four deliverables

**(a) How many of the +9 are genuinely scans vs unparallelizable recurrences.**
Of the 9, **3 are not recurrences needing a scan at all** (`s211`, `s1213`,
`s261` — false positives in the conservative `dep.true_carried` classifier;
already recovered in this repo by hand via loop distribution/restructuring,
bit-identical, **zero numeric licence**). **5 are genuine scan-shaped
recurrences**: 3 are plain associative prefix-sums (`s221`, `s242`, and `s323`
after a coupled-recurrence substitution) — exactly `reassociable`-shaped — and
2 (`s321`, `s322`) are linear recurrences with a *varying multiplicative
coefficient*, which need a materially different combine operator than plain
associative `+`. **1 (`s222`) is a genuinely nonlinear (squaring) recurrence
with no known general parallel-scan algorithm** — a permanent refusal, not a
future capability.

**(b) Minimum declaration vocabulary.** For the cheapest 3 (`s221`, `s242`,
`s323`): reuse `numeric_semantics = reassociable` verbatim, plus one thing that
does **not** exist yet anywhere in this repo — a **declared identity element**
per combining operator (the gap `RC002-unknown-operator.osil` already
demonstrates by refusing `maxof` for exactly this reason) — and a new SIR
*shape* distinguishing "produces an array of partial results" from `reduce`'s
"produces one scalar" (there is no `purpose: scan` today, and `purpose: reduce`
itself is not yet grammar-legal — see Section 6). For `s321`/`s322`: a second,
genuinely new guard is needed — an affine-pair (order-1) or matrix (order-2)
composition monoid is not the same algebraic object as scalar `+`
reassociation, so `reassociable` alone underspecifies what licenses their
parallel algorithm.

**(c) NEON-128 profitability verdict.** Honest and hedged, but the best
available primary data point — an Apple-M4, 128-bit-NEON, hand-tuned integer
prefix-sum benchmark from 2026-03 — shows a **naive** SIMD scan implementation
measured **slower than scalar** (3.6 vs 3.9 billion values/s, ~0.92x) on this
exact chip family, and only a heroically-tuned version (4-way deinterleaved
ILP, ~8 instructions per 16 elements) reaches 2.3x. A mechanically-generated
OSIL realization is architecturally closer to the "naive" case than the
hand-tuned one. **ASSUMPTION:** a mechanical Hillis-Steele-on-NEON-128
realization for the 3 pure-scan TSVC kernels most plausibly lands in the
0.9x-1.5x range — i.e. a *third* "correct but not clearly faster" result,
continuing the pattern of `s116` (0.33x before a fix) and `s221` (1.08x,
Amdahl-capped) rather than breaking it.

**(d) Is this the cheapest of the three?** Cheapest **by guard reuse**, yes —
uniquely among the three theoretical-cap blockers, this one already has a
ratified, gated guard (`reassociable`) with prior working code
(`optimizer/cases/s312.osil`, `s317.osil`); the other two blockers
(`body.control_flow`, `subscript.indirect`) both require vocabulary that
`theoretical-cap.md` itself says does not exist yet. But "cheapest" collapses
from +9 to a true addressable set of **3 kernels** (not 5, if NEON-128
profitability for the 2 harder linear-recurrence cases is set aside pending
evidence), the realization-side engineering (a new `Kind::Scan` in
`optimizer/src/main.rs`, alongside existing `Chain`/`Lanes`/`PowI`) is not
free just because the guard is reused, and the profitability case on this
specific hardware is unproven and trending negative from the one comparable
data point found. Recommend: **scope to the 3 pure-associative kernels only,
and gate the build on a standalone NEON-128 scan microbenchmark before writing
any optimizer rule** — cheap to check, expensive to discover after the fact a
third time.

---

## 1. The +9, named and reclassified (mechanically reproduced)

Ran `tools/capability_ceiling.py` against a freshly vendored TSVC_2 (`tsvc.c`,
`LEN_1D = 32000`) via `uv run --with libclang python3
tools/capability_ceiling.py <tsvc.c> -I<dir>`, exactly as
`theoretical-cap.md` describes its own method. Output reproduced the
published numbers exactly:

```
kernels                      : 151
clang -O3 already vectorizes : 64  (42.4%)
analysable under these caps  : 41
DERIVED CEILING              : 77/151 = 51.0%
    +9   kernels  if `dep.true_carried` were admitted  -> 57.0%
```

A small script (`byfn` diff between `refused` and `refused - {dep.true_carried}`,
mirroring `capability_ceiling.py`'s own internals) named the 9:

```
s1213  s211  s221  s222  s242  s261  s321  s322  s323
```

Cross-referencing each against its TSVC_2 source (`src/tsvc.c`) and this
repo's own `optimizer/probe/none60/README.md` (which already hand-attacked
several of these):

| kernel | TSVC's own label | loop body (abridged) | class | already solved here? |
|---|---|---|---|---|
| `s211` | statement reordering | `a[i]=b[i-1]+c[i]*d[i]; b[i]=b[i+1]-e[i]*d[i]` | **not a recurrence** | YES — 2.31x, BIT-IDENTICAL, restructuring only |
| `s1213` | statement reordering, dependency needing temporary | `a[i]=b[i-1]+c[i]; b[i]=a[i+1]*d[i]` | **not a recurrence** | YES — 1.70x, BIT-IDENTICAL, loop distribution |
| `s261` | wrap-around scalar | `t=a[i]+b[i]; a[i]=t+c[i-1]; t=c[i]*d[i]; c[i]=t` | **not a recurrence** | YES — 1.63x, rel<1e-5, array expansion |
| `s221` | loop that is partially recursive | `a[i]+=c[i]*d[i]; b[i]=b[i-1]+a[i]+d[i]` | (a) associative scan | PARTIAL — a-part vectorizes at 1.08x, b-part explicitly "cannot" per project's own words |
| `s242` | node splitting | `a[i]=a[i-1]+s1+s2+b[i]+c[i]+d[i]` | (a) associative scan | no |
| `s323` | coupled recurrence | `a[i]=b[i-1]+c[i]*d[i]; b[i]=a[i]+c[i]*e[i]` | (a) after substitution | no |
| `s321` | first order linear recurrence | `a[i]+=a[i-1]*b[i]` | (b) linear recurrence, order 1 | no |
| `s322` | second order linear recurrence | `a[i]=a[i]+a[i-1]*b[i]+a[i-2]*c[i]` | (b) linear recurrence, order 2 | no |
| `s222` | recurrence in middle | `e[i]=e[i-1]*e[i-1]` (embedded) | (c) nonlinear | no, and cannot be |

**The classifier undercounts in the direction its own guard note admits.**
`tools/ceiling_check.py` already carries this exact caveat in its own source:
*"the model is deliberately CONSERVATIVE. `dep.true_carried` disqualifies a
loop here, but distribution can PARTIALLY recover such loops by isolating the
recurrence... s1213 (1.67x) and s211 (1.66x) were both recovered despite
carrying a true dependence... the derived ceiling UNDERSTATES what is
reachable."* This document's finding sharpens that: it is not merely an
understatement, it means **3 of the 9 kernels attributed to "admit
`dep.true_carried`" do not need that capability admitted at all** — they need
a different, cheaper analysis (single-hop dependence testing extended to
recognize when a flow dependence is *algebraically eliminable by substitution
of pre-loop values*, which is what `s211`/`s1213`/`s261` all turn out to be on
inspection). That is closer to `s244`'s dead-store-elimination fix (already in
the "breakable" bucket) than to a numeric-licence question, and it was done by
hand in this repo, not by any existing OSIL machinery
(`optimizer/probe/none60/README.md`: *"no OSIL machinery is involved -- the
term language cannot express maps, stores, or multi-array loops yet"*).

**Also worth flagging:** 11 further TSVC kernels carry a `dep.true_carried`
feature but are not in the +9, because they *also* carry
`body.control_flow`/`subscript.indirect`/`access.multi_dimensional` (e.g.
`s112`, `s119`, `s132`, `s161`, `s232`, `s233`, `s256`, `s257`, `s277`,
`s2111`, `s3251`) — admitting the recurrence capability alone would not
unlock them; this matches `theoretical-cap.md`'s own note that "25 kernels
have all three [blockers] simultaneously," and is consistent with, not
contradictory to, the +9 figure.

**Minor inconsistency, disclosed rather than silently resolved:**
`theoretical-cap.md` states *"12 among 58 analysable loop nests (20.7%)"* are
true recurrences — a different pair of numbers than this section's 9-of-77 (or
20-of-151 counting the overlapping cases above). The discrepancy likely comes
from a narrower "analysable" denominator used when that document's prose was
written versus the G21 tool's current, more precise per-feature accounting
(dated the same day). This document treats the freshly re-run
`capability_ceiling.py` output as authoritative for the +9 breakdown, since it
is the same tool `theoretical-cap.md` itself cites as its method, re-executed
directly rather than paraphrased — but the inconsistency across the project's
own docs is real and should be reconciled (`ASSUMPTION:` not resolved here,
flagged for a maintainer pass on `theoretical-cap.md`).

---

## 2. Parallel prefix / scan algorithms — work, depth, and SIMD width 4

**Hillis-Steele:** O(n log n) total work, O(log n) depth/span. Step-efficient
(maximally parallel), work-*in*efficient — it does strictly more total additions
than the O(n) sequential algorithm. Well suited to architectures with as many
processors as elements (its origin, the Connection Machine); on a narrow SIMD
lane count this "excess work" is exactly what a 4-wide NEON register pays for
every local prefix it computes.

**Blelloch (work-efficient scan):** O(n) work — asymptotically no more
operations than the sequential version — but O(log n) depth with roughly
**2x** the number of sequential steps of Hillis-Steele (an up-sweep reduction
pass, O(log n) steps, then a down-sweep pass, another O(log n) steps), and a
larger constant per step (branching/indexing overhead in the classic
formulation). Trade-off, stated plainly by the sources found: *Hillis-Steele
is more step-efficient (parallel); Blelloch is more work-efficient.*

**What this means at width 4 (NEON-128, f32):** for a single 4-lane vector,
computing a local Hillis-Steele prefix takes `log2(4) = 2` dependent
shift-and-add steps (`vext` + `vadd`, twice) — i.e. **more instructions per
element than sequential accumulation**, not fewer, before any cross-vector
carry propagation is added. This is the mechanism behind deliverable (c)'s
verdict: a scan is not "the same work, parallelized" the way a reduction is —
it does strictly more total arithmetic (Hillis-Steele) or comparable
arithmetic with real control/bookkeeping overhead (Blelloch), and the payoff
only shows up once instruction-level parallelism from processing *several*
vectors' worth of local prefixes concurrently outweighs that overhead. At
4 lanes, that crossover is architecture-sensitive, not automatic — Section 7
gives the concrete estimate.

**Crossover array length:** for TSVC's own arrays (`LEN_1D = 32000`), length
is not the binding constraint — 32,000 elements is far past any reasonable
amortization threshold; a handful of loop iterations pays for one-time setup
overhead. What is *not* amortized away is the **per-element steady-state
overhead** of the shuffle/carry chain versus a single scalar add — this is
exactly the throughput regime the Section 7 estimate addresses, not a
short-array warm-up cost. `ASSUMPTION:` no source found gave a specific
crossover-length number for a narrow (4-wide) SIMD scan versus scalar; the
Algorithmica reference (below) discusses breakeven only qualitatively for
wider (AVX2, 8-wide) registers.

**Sources:** [Prefix Sum with SIMD — Algorithmica](https://en.algorithmica.org/hpc/algorithms/prefix/) (measured on 8-wide AVX2: scalar baseline 1.2-1.6 GFLOPS; naive-vectorized ~2x scalar; fully tuned interleaved+prefetched version 2.8x for small arrays down to 1.75x for large arrays — i.e. even on a *wider*, more mature SIMD ISA than NEON-128, a tuned scan tops out under 3x, and speedup *falls* as arrays grow, the opposite of what a purely compute-bound win would show, consistent with this being partly bandwidth-bound); [GeeksforGeeks — Hillis-Steele Scan](https://www.geeksforgeeks.org/cpp/hillis-steele-scan-parallel-prefix-scan-algorithm/); [NVIDIA GPU Gems 3 Ch.39 — Parallel Prefix Sum (Scan) with CUDA, Harris](https://developer.nvidia.com/gpugems/gpugems3/part-vi-gpu-computing/chapter-39-parallel-prefix-sum-scan-cuda) (canonical Blelloch/Hillis-Steele work-depth statement, GPU-oriented but the complexity analysis transfers).

---

## 3. What compilers already do

**Reductions:** confirmed directly from `llvm.org/docs/Vectorizers.html` —
*"LLVM supports vectorizing floating point reductions only when at least the
`-fassociative-math -fno-signed-zeros -fno-trapping-math` subset of
`-ffast-math` is used on most targets"* (AArch64 and RISC-V can additionally
generate *ordered* reductions that preserve the exact scalar result, at a
throughput cost). Supported operators: addition, multiplication, XOR, AND, OR
— a **fixed, hardcoded list**, not a general "any associative operator"
mechanism. This matches, independently, what this repo's own
`RC002-unknown-operator.osil` refusal fixture demonstrates on the OSIL side:
*"`maxof` is not a reduction operator the projection supports. There is no
identity element declared for it, so emitting a fold would require the
projector to INVENT one."* Both LLVM and this project's own C projection hit
the identical wall — reduction/scan support is enumerated per-operator, gated
on a declared or hardcoded identity element, not derived from a general
associativity fact alone.

**LLVM does have a feature literally named "first-order recurrence"
vectorization** (patch [D16197](https://reviews.llvm.org/D16197), landed
~2016, still documented in current `VPlan` infrastructure with a dedicated
`FIRST-ORDER-RECURRENCE-PHI` / "first-order splice" VPlan node). Verified its
exact scope directly from the patch description: it handles patterns like
`for (i=0;i<n;++i) b[i] = a[i] - a[i-1];` where **`a` is an independently
computed array being shifted, not accumulated** — the patch's own definition:
*"a non-reduction recurrence relation in which the value of the recurrence in
the current loop iteration equals a value defined in the previous
iteration."* **This explicitly excludes self-referential accumulation
(`x[i] = x[i-1] + f(i)`)** — a true scan/prefix-sum is, by LLVM's own
taxonomy, a different thing entirely, handled by neither this feature nor the
reduction path. This is a materially important finding: **LLVM's
"first-order recurrence" is exactly the shift-only false-dependence pattern
this repo already recovers by hand for `s211`/`s254`/`s255`-shaped loops
(Section 1's 3 non-scan kernels), not the scan capability this document is
about.** That LLVM has this feature and clang -O3 still refused all of
`s211`/`s1213`/`s261` in practice (per `optimizer/probe/none60/README.md`'s
own measurement — clang's own diagnostic on these loops: *"Backward loop
carried data dependence"*) means either LLVM's pattern-matcher is narrower
than the general shift-substitution reasoning this repo's hand fix used
(likely — TSVC's multi-statement bodies with cross-array coupling are more
complex than the patch's single-statement example), or the specific compound
patterns here simply fall outside what the legality check accepts. Either
way: **no evidence found, in LLVM docs, GCC docs, or the literature searched,
that any mainstream compiler auto-vectorizes a genuine accumulating scan**,
`-ffast-math`-gated or otherwise. This is consistent with, not contradicted
by, this repo's own `s221` result (b-loop explicitly stated as un-vectorizable
by the current pipeline).

**First-order linear recurrences (`x[i] = a[i]*x[i-1] + b[i]`) do have known
parallel algorithms**, confirmed from multiple independent sources: Blelloch
(1990) shows such recurrences parallelize via the scan primitive when the
combining operator is associative — here the operator is not scalar `+` but
**pair composition**, `(α₁,β₁) ∘ (α₂,β₂) = (α₁α₂, α₂β₁+β₂)`, which *is*
associative, forming a genuine monoid, and a scan over these pairs recovers
the full sequence with the standard O(n) work / O(log n) depth trade-off.
Independent confirmation from Sameh & Brent's classical result ("A Parallel
First-Order Linear Recurrence Solver," 1977) and Kwong et al.'s SMP-targeted
transform ("Parallel Processing of First Order Linear Recurrence on SMP
Machines," *J. Supercomputing*) — recursive doubling on the (α,β) pairs is the
common method across all sources found. **This is the key structural fact for
Section 1's class (b):** `s321` needs this pair-composition monoid, not plain
`reassociable` addition; `s322` (second order) needs the equivalent
generalization to 2x2 companion-matrix composition, a strictly heavier
combine operator again.

**Sources:** [LLVM Auto-Vectorization docs](https://llvm.org/docs/Vectorizers.html); [D16197 — Vectorize first-order recurrences](https://reviews.llvm.org/D16197); [LLVM VectorizationPlan docs](https://llvm.org/docs/VectorizationPlan.html); Blelloch, *Prefix Sums and Their Applications*, CMU-CS-90-190 (1990) (via secondary citation in searched neural-net-recurrence literature, not independently re-verified against the original PDF — `ASSUMPTION:` the 1990 attribution and content summary is as reported by citing sources, not re-derived from Blelloch's own text in this pass); ["A Parallel First-Order Linear Recurrence Solver" (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/0743731587900013); ["Parallel Processing of First Order Linear Recurrence on SMP Machines" (Springer, J. Supercomputing)](https://link.springer.com/article/10.1023/B:SUPE.0000011389.69863.dc).

---

## 4. The classification that matters — class (a)/(b)/(c) applied beyond the +9

The 9 kernels of Section 1 are TSVC's `s2xx` and `s3xx` "%2.2" and "%3.2"
families; reading the full `s2xx`/`s3xx` range directly from `src/tsvc.c`
(all loops with TSVC's own "recurrences" or dependence-labeled comments)
confirms the taxonomy generalizes:

- **(a) Associative-operator scans — parallelizable, cheapest.** Pure
  `x[i] = x[i-1] OP f(i)` with associative `OP` (here always `+`). Besides
  `s221`/`s242`/`s323`: also `s231` (`aa[j][i]=aa[j-1][i]+bb[j][i]`, a
  2D-embedded prefix sum, blocked from the +9 today only by
  `access.multi_dimensional`, not by the recurrence itself) and `s235`
  (structurally identical, loop-invariant multiplier inside the j-loop).
- **(b) Linear recurrences — parallelizable via a different, heavier
  algorithm.** `s321` (order 1, varying coefficient), `s322` (order 2). Also
  `s256`/`s257` (`a[j] = 1 - a[j-1]`, `a[i] = aa[j][i] - a[i-1]`) — first-order
  with a *constant* coefficient of -1, the simplest possible member of this
  class, currently blocked by `access.multi_dimensional`/`body.control_flow`
  rather than by the recurrence.
- **(c) General nonlinear recurrences — not parallelizable by any scan
  technique found.** `s222` (`e[i]=e[i-1]²`). Checked directly whether a
  closed form escapes this: `e[i] = e[0]^(2^i)` is exact algebraically, but
  computing the *array* of intermediate values via `log`/`exp` substitution
  (rather than repeated squaring) is numerically catastrophic for anything
  past small `i` (the exponent `2^i` overflows or destroys all precision in
  `2^i · ln(e[0])` well before `i=30`), and is undefined for `e[0] <= 0`. No
  general, numerically sound parallel algorithm exists for this loop; it is
  correctly a permanent refusal, structurally analogous to the existing
  `R001`-`R008` rejection fixtures in `conformance/rejections/`.

Several other loops the theoretical-cap `s2xx` family flags as "recurrences"
in TSVC's own comments are, on inspection, **not recurrences at all** — false
dependences from statement order or wraparound scalars, resolvable without
any numeric licence: `s211`, `s1213`, `s261` (Section 1); also `s241`, `s244`
(both already hand-recovered per `none60/README.md`, node-splitting /
dead-store, no licence); `s251`, `s2251`, `s252`, `s254`, `s255`, `s3251` (all
"scalar/array expansion" family — a value carried one iteration is a *shift*
of an independently-computed quantity, not an accumulation). **The single
largest practical lesson from reading this whole family end-to-end: TSVC's
own English label "recurrence" is not a reliable signal for "needs a scan."**
Roughly two-thirds of the loops TSVC's comments call recurrence-shaped, in
the `s2xx`/`s3xx` ranges surveyed, turn out to be restructurable false
dependences; only a minority are genuine scan/linear-recurrence candidates.

---

## 5. The numeric cost — is a parallel scan as accurate as sequential accumulation?

**The reassociation fact itself is uncontested and well-sourced:** floating-point
addition is not associative — `fl(fl(a+b)+c) != fl(a+fl(b+c))` in general,
because each operation rounds independently. Confirmed directly from a 2026
technical post on exactly this failure mode
([xania.org — "When SIMD Fails: Floating Point Associativity"](https://xania.org/202512/21-vectorising-floats)):
*"Operations are not associative... after each operation, rounding occurs."*
Vectorized code restructures the summation order (partial sums per lane,
combined at the end) — a genuinely different rounding-error path than
sequential left-to-right accumulation, not an approximation of it.

**Whether that different path is systematically *worse* is a separate,
harder claim, and the evidence found does not support a strong general
answer either way.** The literature on summation accuracy (probabilistic
error bounds, compensated/Kahan summation, "twofold" summation) treats
sequential summation's own error growth as a well-studied but *not
special-cased-as-best* baseline — compensated methods beat plain sequential
accumulation too, and tree-structured (reassociated) summation is a standard
technique specifically *because* it can reduce worst-case error growth from
O(n) (sequential, error can accumulate linearly with array length in
adversarial orderings) to O(log n) (balanced tree) in the classical rounding-error
bound literature — the reduced *depth* of the accumulation chain is itself
sometimes an accuracy argument in the tree's favor, not just a performance
one. No source found gave a head-to-head empirical accuracy comparison of a
*scan's* running-partial-sums specifically (as opposed to a single final
reduction's tree-sum) against sequential accumulation.

**This project's own finding — that vectorized reduction was not more
accurate than sequential, "roughly a coin flip" — is the most directly
relevant data point available, and no external source found either confirms
or refutes that it extends to scans.** The reasoning for why it plausibly
*does* extend, stated as reasoning rather than measurement: a scan's `i`-th
output element is itself a partial reduction over the first `i` elements,
computed via the *same* lane-interleaved partial-sum-then-combine structure a
vectorized reduction uses internally at each prefix point — so each element
of a vectorized scan's output inherits the same "different-not-better"
rounding-order characteristic this project already measured for the
single-element reduction case. **`ASSUMPTION:`** by extension, a vectorized
scan's error is *plausibly no worse, and no better, than sequential* on
average across kernels — consistent with the project's own "coin flip"
framing — but this is an inference from the reduction case, not an
independent measurement of a scan, and should be treated as unverified until
this project runs the equivalent accuracy harness (`bench/accuracy` per
`optimizer/README.md`'s existing convention) against an actual scan
realization. **This matters concretely for `s221`/`s242`/`s323`:** the
none60 table already records `s261`'s hand fix at `rel < 1e-5` rather than
bit-identical (Section 1) — a scan realization for the same family should be
expected, going in, to land in that same non-bit-identical-but-small-relative-error
regime, not the bit-identical regime this project has otherwise favored for
its strongest, least-disputable results.

**Sources:** [xania.org — floating-point associativity and SIMD](https://xania.org/202512/21-vectorising-floats); [Probabilistic Error Analysis For Sequential Summation of Real Floating Point Numbers](https://arxiv.org/pdf/2101.11738); [An Efficient Summation Algorithm for Accuracy, Convergence and Reproducibility of Parallel Numerical Methods](https://arxiv.org/pdf/2205.05339); this project's own `optimizer/` energy/accuracy measurements (`optimizer/README.md`, in-repo).

---

## 6. The declaration angle — minimum vocabulary

Read directly, the current architecture already has more machinery here than
a first glance suggests, and one confirmed gap:

**What exists today (`profiles/domain/numeric/numeric.osil`, `spec/TERMS.md`):**
`regime = <Concept>` is the *canonical* guard form (ADR-0007); `numeric_semantics
= <value>` is a declared, transcript-faithful synonym. Two concepts are
formally declared with genus/differentia (`ExactArithmetic`,
`IntegerArithmetic`) — **but `reassociable` itself, despite being used
live in five working `.osil` files
(`optimizer/cases/s312.osil`, `s317.osil`, `s317-noclosed.osil`, `s352.osil`,
`conformance/interop/c/cases/c001`, `c002`), has no corresponding `concept
Reassociable { ... }` block in `profiles/domain/numeric/numeric.osil`.** It is
used as a bare guard *value*, not a defined *concept*, unlike `exact` and
`integer`. This is itself a small, pre-existing gap independent of scan — the
"already have this" framing in `theoretical-cap.md` is accurate for the
*working mechanism* (the guard gates real rewrites, measurably, in
`optimizer/`) but slightly overstates the *formal* state (it is not yet a
first-class ontology entry alongside its two siblings).

**What a scan needs beyond that, confirmed from `RC002-unknown-operator.osil`
and `optimizer/src/main.rs`:** the existing `purpose: reduce` machinery
already requires — per RC002's own refusal text — a **declared identity
element** per operator before a fold/reduction can be emitted; today this is
implicit/hardcoded to `mul`/`add` in `optimizer/src/main.rs::rules()`, not a
declared fact in the SIR. A scan needs the same identity-element requirement
(seeding block-boundary partial sums), so this is not new *conceptually*, but
it is not yet *expressed* anywhere as a declaration rather than as compiler
code — closing that gap benefits both `reduce` and any future `scan`
uniformly.

**What is genuinely new, not a reuse of anything in this repo:**
1. **A SIR shape that outputs an array, not a scalar.** `(reduce mul (range a
   32000))` is, by construction, scalar-producing; there is no `purpose:
   scan` (or `reduce`-with-an-"emit-all-partials" flag) anywhere in the
   grammar, the optimizer, or any case file. This is an *ontological* gap,
   not a guard gap — `reduce`'s SIR shape cannot express "keep every prefix,"
   only "keep the last one." This needs a new construct, and per this
   project's own `docs/design/theoretical-cap.md`/`GOVERNANCE.md` triple-representation
   rule (grammar production + >=1 corpus example in the same change), it
   cannot be added cheaply as a side effect of the guard work.
2. **A recurrence-order/kind classification for class (b).** `reassociable`
   alone licenses associative-`+` reassociation; it does not, and should not,
   license reassociating an affine-pair composition or a companion-matrix
   product — those need their own declared associative operator and identity
   (the pair `(1,0)` for the order-1 monoid; the 2x2 identity matrix for
   order-2). The minimum honest vocabulary is something like `recurrence_kind
   = linear` with a declared `order` — genuinely new, not an extension of
   `reassociable` by relabeling.
3. **Nothing for class (c).** No declaration should exist for `s222`-shaped
   loops; the correct artifact is a permanent refusal fixture, mirroring the
   existing `R001`-`R008`/`RS001`-`RS006` pattern this project already uses
   for other permanently-rejected cases.

**Also worth stating plainly:** `optimizer/README.md`'s own "Known gaps"
section says `sir { (reduce mul a 32000) }` "is not grammar-legal" under
grammar v0.6 today — `reduce` itself is a probe construct, not yet promoted.
A `scan` construct inherits that same not-yet-grammar-legal status at minimum,
and arguably a larger burden, since it needs a new production the grammar has
*never* had (an array-producing recurrence), where `reduce` at least has a
plausible existing production shape (`factor` application) it is squatting on
informally.

---

## 7. Honest NEON-128 profitability — an estimate, clearly flagged

**The strongest available evidence is Daniel Lemire's 2026-03 ARM NEON prefix-sum
benchmark**, chosen because it is dated, code-linked, and — unusually for this
kind of search — run on the **same CPU family this project already benchmarks
on** (Apple M4, 4.5 GHz). Its algorithm: `vld4q_u32` loads 16 values
deinterleaved into 4 lanes-of-4 vectors; 3 lanewise `vaddq_u32` steps compute
within-group local prefixes; ~4 more `vextq_u32`/`vaddq_u32` steps combine
across the 4 groups; a final broadcast carries the running total into the
next block — roughly **8 instructions total per 16-value block** (0.5
instructions/element) in the tuned version. Measured throughput:

| method | throughput (M4, uint32) |
|---|---|
| scalar sequential | 3.9 billion values/s |
| naive SIMD | **3.6 billion values/s — slower than scalar** |
| tuned/"fast" SIMD | 8.9 billion values/s — **2.3x scalar** |

Two things follow directly from this, both load-bearing for the verdict:

1. **A naive vectorization of a scan can and does lose to a well-optimized
   scalar dependent-add chain on an out-of-order Apple core** — confirmed
   measured, not theoretical, on the closest available hardware analog. This
   is precisely the failure mode this project has already hit twice, on
   different (non-scan) loops: `s116` at **0.33x** before a fix (a
   speculative preload cost 3x what vectorizing saved) and `s221` at
   **1.08x** (Amdahl-capped by the irreducibly scalar b-loop — which, per
   Section 1, is exactly one of the 3 genuine scan candidates in the +9).
2. **Only a heroically-tuned realization wins, and only by 2.3x**, on an
   *integer* (exact-arithmetic, no rounding-error complication), large-array,
   almost certainly memory-bandwidth-adjacent kernel ("tens of gigabytes per
   second" — this is streaming through the array, not compute-bound in the
   TSVC sense). TSVC's `s221`/`s242`/`s323` are **floating-point**, embedded
   inside loop bodies with *other, independent, non-recurrent work in the
   same iteration* (e.g. `s221`'s `a[i] += c[i]*d[i]`) that an out-of-order
   core can already interleave with the scalar recurrence's latency chain
   today, for free, without any vectorization at all — exactly the mechanism
   Lemire's post itself names for why the scalar baseline is already fast:
   *"the scalar approach has inherent dependency... to compute the current
   value, you must have computed the previous one"* — true, but an OOO core
   still retires other independent instructions during that latency, and
   TSVC's loop bodies hand it plenty to retire.

**Reasoned estimate for a Hillis-Steele-on-NEON-128 (4-wide f32) realization,
explicitly flagged as an estimate, not a measurement:**

- Local in-register prefix for 4 lanes: `log2(4) = 2` dependent steps, each
  one `vext` (shuffle, low latency) + `vadd`/`vaddq` (using this project's own
  calibrated `mul_latency` ≈ 3.2 cycles on this exact M4 as a stand-in for
  add latency, per `optimizer/calibration/constants.toml` fitted in prior
  work in this repo) — roughly 2 x ~3-4 cycles ≈ 6-8 cycles for the local
  prefix, plus shuffle latency that partially overlaps.
- Cross-vector carry: one more dependent broadcast-add per vector, another
  ~3-4 cycles, strictly serial across vectors (this is the part that cannot
  be hidden — it is the scan's own irreducible sequential spine, now running
  at *vector* granularity instead of scalar granularity).
- Net: roughly 10-14 cycles per 4-element block ≈ 2.5-3.5 cycles/element,
  against a scalar chain bound by the same ~3-4 cycle add latency per
  *single* element when the recurrence is the sole bottleneck — i.e. **a
  plausible 1.1x-1.5x win in complete isolation**, before accounting for (i)
  the extra shuffle instruction pressure Lemire's "naive" result shows is
  enough to erase the win entirely in practice, and (ii) TSVC's actual loop
  bodies giving the OOO scalar core other work to hide the recurrence's
  latency behind, which a naive microbenchmark does not.

**`ASSUMPTION:`** given both effects point the same direction (real
instruction overhead this estimate under-counts, and a scalar baseline this
estimate over-penalizes relative to TSVC's actual loop shapes), the honest
range to state is **0.9x-1.5x for a mechanically-generated realization**,
i.e. genuinely uncertain whether it wins at all, and even a "win" is likely
modest — nothing resembling the 32x/6164x results this project's `optimizer/`
has demonstrated for reductions with closed forms (`s317`) or wide lane
interleaving (`s312`). This is not a reason not to build it — `s221`'s
existing 1.08x is already published in this repo as an honest result, not
hidden — but it is a reason to **measure before engineering the realization
rule**, exactly as the project's own `just price` tool exists to do for
capability admission before code is written.

**Sources:** [Lemire — "Prefix sums at tens of gigabytes per second with ARM NEON" (2026-03-08)](https://lemire.me/blog/2026/03/08/prefix-sums-at-tens-of-gigabytes-per-second-with-arm-neon/); this repo's own `optimizer/calibration/constants.toml` / `optimizer/README.md` (fitted NEON fp-mul latency ≈3.2 cycles, `lanes_per_cycle` ≈18 on this exact M4 — cited as the closest in-repo calibrated analog to an add-latency figure, not as a direct measurement of add latency, which was not separately fitted in this repo — `ASSUMPTION:` NEON f32 add latency is comparable to the fitted mul latency on this microarchitecture, a common but not universal property across ARM cores); `optimizer/probe/none60/README.md` (s116, s221 results, in-repo).

---

## 8. Recommendation

**Yes, admitting the recurrence-scan capability is the cheapest of the three
theoretical-cap blockers to *start* — but the honest addressable win is
smaller than +9, and profitability on this project's own hardware is
unproven and trending negative from the closest available evidence.**

The "cheapest" framing survives on structural grounds independent of this
document's findings: `theoretical-cap.md`'s own bridge table shows the other
two blockers need vocabulary that **does not exist yet** —
`body.control_flow` needs a side-effect-freedom declaration for branch
speculation (not started), `subscript.indirect` needs an
index-injectivity invariant explicitly stated to be something **C's
`restrict` cannot express** (not started, and `restrict` was separately
measured in this repo to recover 0/151 loops on its own). `reassociable`, by
contrast, is ratified, gated, and has three working `optimizer/cases/*.osil`
files already exercising it end-to-end with measured speedups. That
asymmetry is real and this document does not undercut it.

What this document adds is a downward correction on *how much* that
head-start is worth, and a concrete pre-condition before spending it:

1. **Scope the first cut to 3 kernels, not 9 or 5**: `s221`, `s242`, `s323`
   (the pure-associative-`+` scans). These alone reuse `reassociable`
   verbatim — no new guard concept needed, only the identity-element and
   array-output-shape gaps in Section 6, both of which are general
   improvements to `purpose: reduce` too, not scan-specific cost.
2. **Defer `s321`/`s322`** (linear recurrences, class b) to a follow-on. They
   need a genuinely new guard (pair/matrix composition monoid), a different
   and heavier realization algorithm, and were not shown to be cheap by
   anything found in this investigation — bundling them into the same
   proposal as the 3 pure-scan cases would misrepresent the "just reuse
   `reassociable`" pitch.
3. **Formally refuse `s222`** as a permanent rejection fixture rather than
   leaving it implicitly "not yet supported" — the nonlinear case has no
   parallel algorithm in the literature searched, and TSVC's own comment
   ("recurrence in middle") makes it an easy trap to conflate with the
   genuinely parallelizable cases if the vocabulary work doesn't name the
   distinction explicitly.
4. **Measure before building the realization rule.** Write the NEON-128
   Hillis-Steele scan as a standalone microbenchmark against this repo's own
   scalar `s221`/`s242` baselines *before* investing in a new `Kind::Scan`
   variant in `optimizer/src/main.rs` — Section 7's estimate is honestly
   uncertain in the 0.9x-1.5x range, and Lemire's naive-vs-tuned NEON
   result on the same CPU family shows the naive case can lose outright.
   This project already has the harness pattern for exactly this
   (`optimizer/bench/run.py`, the `just price` capability-pricing tool) — use
   it before, not after, committing engineering time.

---

## Validity & limitations

**Valid as of:** 2026-08-24. **Re-evaluate if:** the G21 capability-ceiling
tooling or `theoretical-cap.md` are revised (this document's Section 1
numbers should be re-run against `tools/capability_ceiling.py` if either
changes); TSVC_2 is updated upstream (loop bodies could change); Apple
releases a new M-series core with different NEON add/shuffle latencies
(Section 7's estimate is chip-specific by construction).

**Limitations:** the NEON-128 estimate in Section 7 is explicitly an
estimate, built from one blog-tier (though unusually well-sourced and
same-hardware) benchmark plus this project's own previously-fitted
calibration constants used analogically, not a direct measurement of scan
performance — it should not be cited as a measured result. The numeric-error
extension in Section 5 is reasoning from this project's own reduction-accuracy
finding, not an independent scan-accuracy measurement. The
`theoretical-cap.md` "12 of 58" vs this document's "9 of 77 / 20 total"
discrepancy (Section 1) is disclosed, not resolved — a maintainer should
reconcile which denominator the theoretical-cap document intends before this
document's numbers are cited as a correction rather than a companion.

---

**Epistemological note.** This document's central quantitative claims — the
exact identity of the 9 kernels and their (a)/(b)/(c) split — are mechanically
reproduced, not estimated: `tools/capability_ceiling.py` was executed against
a freshly vendored TSVC_2 source tree and reproduced the published 51.0%/57.0%/+9
figures exactly before the per-kernel breakdown was derived. The NEON-128
profitability verdict is explicitly the opposite kind of claim — a reasoned,
flagged estimate from adjacent evidence, not a measurement — and is presented
with that distinction preserved rather than smoothed over, per this project's
own stated preference for "it depends" over manufactured certainty.
