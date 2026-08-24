# Research: U13 — Non-affine subscripts (indirect addressing vs wrap-around scalars)

**Date:** 2026-08-24
**Researcher:** research-agent
**Question:** Our C loop-vectorization pipeline (`tools/c_lift.py` ->
`tools/c_choose.py`) refuses all non-affine subscripts. Pricing
(`tools/capability_ceiling.py`) says admitting `subscript.indirect` is worth
+15 kernels alone, +36 jointly with control flow, +52 jointly with control
flow + multi-dimensional access (60.9% / 74.8% / 85.4% of TSVC2's 151
kernels, against a published ceiling of 56.0% on A64FX/SVE-512 and our
current 51.0%/46.4%). Two structurally different sub-cases hide inside that
one capability label: (a) genuine indirect/gather addressing `a[idx[i]]`,
and (b) wrap-around scalars (`im1 = i` at the end of the body, read as
`b[im1]`). This asks whether they deserve the same verdict, what
declaration would discharge each, whether NEON-128 can ever profit from
gather-style code, whether polyhedral analysis subsumes the problem, and
what correctness risk admitting either one opens.

## Philosophical framing

**Ontological.** "Non-affine subscript" is not one thing. `a[idx[i]]` is a
composition of two maps — the loop index `i` and an opaque array lookup
`idx` — whose composite the affine dependence test cannot represent because
`idx` is a runtime *value*, not a *syntactic* affine function of `i`. A
wrap-around scalar like `im1` is different in kind: it IS an affine function
of `i` (`im1(i) = i - 1`, with a boundary case at `i=0`), but the affine
subscript test as built only pattern-matches expressions written directly as
`arr[i + c]` in source text — a scalar whose value happens to equal `i - 1`
after an assignment chain is invisible to a syntactic pattern-matcher even
though it is exactly the kind of fact an affine test is built to accept once
substituted. The two cases are asked "are you affine?" but only one fails
the question on the merits; the other fails because the *recognizer*, not
the *property*, is too weak.

**Epistemological.** Section 4 below is answered first with a reproducible
artifact from this repo's own tooling, then cross-checked against external
literature. Primary sources used externally: the ARM Architecture Reference
Manual family and an official ARM whitepaper (`102131`) for the NEON/SVE
instruction-set question; LLVM source (`LoopAccessAnalysis`,
`VectorizerParams`) and a merged LLVM pull request for the compiler-internals
questions; the OpenMP, OpenACC, and C99 specification texts (where
fetchable) or their well-corroborated secondary paraphrase (marked
`ASSUMPTION:` where I could not retrieve primary text directly) for the
declaration-semantics questions; a peer-reviewed-venue-track arXiv paper
(Sakib et al. 2025) that directly measures TSVC2 gather/scatter vectorization
on real A64FX (SVE-512) and Skylake (AVX-512) hardware — this is the closest
available empirical analogue to the NEON-128 profitability question, used to
extrapolate rather than to directly answer it (flagged accordingly).

**Ethical/risk framing.** The record-attempt history in this repo already
demonstrates the failure mode point 6 asks about: admitting `body.control_flow`
into the dependence model let the chooser reorder statements around
`goto`/label pairs and it took a differential test — not the dependence
model, not a type system — to catch silently-incorrect outputs before they
were reported as "recovered." A capability that raises the ceiling while
opening a correctness hole is not free, and this report treats "can it be
checked statically" as a first-class question, not an afterthought.

---

## 1. Indirect addressing / gather-scatter — NEON status and profitability

### 1.1 Does NEON have gather/scatter? (primary-source verified)

**No.** ARM's own document *"SVE and Neon coding compared"* (Arm document
102131, Issue 01, 14 September 2020 — a primary vendor source, not a
secondary blog) gives, in §4.1 "Instruction sets", a table of the
*"Categorization of new instructions"* each extension provides:

- **Neon:** promotion and demotion; pair-wise operations; load and store
  operations; logical operators; multiplication operation.
- **SVE:** load/store/prefetch instructions; integer operations; **vector
  address calculation**; bitwise operations; floating-point operations;
  predicate operations; move operations; reduction operations.

"Vector address calculation" is the category gather/scatter belongs to —
computing N independent addresses per instruction and loading/storing at
each — and it is listed only under SVE. Neon's category list contains
nothing equivalent. The document is explicit elsewhere that Neon "operates
on a separate register file of 128-bit registers," fixed at 128 bits, with
no per-lane predicated addressing mechanism.

This is corroborated by every secondary technical source found (NVIDIA's
Grace CPU benchmarking guide, an ARM SVE tutorial (Stony Brook/Ookami),
and multiple independent vectorization surveys): *"SVE offers native
gather/scatter... Neon lacks a general-purpose solution for random access
patterns."* The AArch64 Architecture Reference Manual itself places
gather/scatter load/store encodings exclusively under the SVE/SVE2
instruction chapters (`ld1w`/`ldff1w`/`st1w` etc. with vector-plus-scalar or
scalar-plus-vector addressing) — I could not fetch that manual page's exact
text directly (Cloudflare-gated redirect; both `developer.arm.com` and
`support.arm.com` blocked automated fetch), so the manual-chapter-placement
claim rests on the ARM whitepaper above plus consistent secondary
corroboration rather than a directly quoted manual excerpt.
`ASSUMPTION:` none of the sources found describe any Neon/AdvSIMD
instruction, in any AArch64 revision through the one this repo's Apple M4
implements, that performs a hardware gather or scatter. This is a negative
claim (an absence), which is harder to fully close than a positive one, but
the convergence across a vendor whitepaper's instruction taxonomy and
every secondary technical source is strong.

**Apple M4** is NEON-128 only, no SVE (stated as already-verified in the
task and consistent with all public Apple Silicon documentation — Apple's
AArch64 cores have not shipped SVE as of this writing).

### 1.2 If NEON lacks gather, what does "vectorizing" `a[idx[i]]` degenerate to?

A compiler targeting NEON that still wants to vectorize a loop containing
`a[idx[i]]` has no hardware gather to emit. The only path is a **software
gather**: read `idx[i+0..3]` (themselves loaded contiguously, cheaply,
since `idx` access IS affine), then perform four independent *scalar*
loads from `a[]` at those four addresses, then assemble the four scalar
values into one NEON vector register via lane-insert instructions
(`LD1 {Vd.S}[lane], [Xn]`-style sequences, or a `vld1`+shuffle idiom), then
continue the vectorized computation, then — if the destination is also
indirect (a scatter, e.g. `a[idx[i]] = ...`) — extract each lane back out
and perform four independent scalar stores. This is exactly what GCC's own
vectorizer internals distinguish as "emulated gather": GCC ships a target
hook (`TARGET_VECTORIZE_BUILTIN_GATHER`-family) that reports whether native
gather is *cheaper than a sequence of elementwise loads*, and a documented
fallback (GCC PR91033, "Make scatter/gather vectorization failures
non-fatal") that degrades gracefully to this elementwise/emulated form when
the target cannot do it natively.

Whether this ever pays: it can only pay if the *arithmetic* performed on
the gathered vector is wide/heavy enough to amortize the lane
insert/extract overhead against doing the same arithmetic scalar, four
times, with no lane shuffling at all. NEON's 128-bit width gives only 4
float32 lanes to amortize that overhead over — a much smaller amortization
surface than SVE-512's 16 lanes or AVX-512's 16 lanes.

### 1.3 Direct empirical evidence, from wider (real gather) hardware

Sakib, Prabhu, Santhi, Shalf, Badawy, *"Comparison of Vectorization
Capabilities of Different Compilers for X86 and ARM CPUs"* (arXiv:2502.11906,
Feb 2025) — this is the same paper this repo's `theoretical-cap.md` and
`record-attempt.md` already cite for the "GCC 56.0% A64FX" published record
— directly measures TSVC2's indirect-memory-access kernels on hardware that
DOES have native gather/scatter (Skylake AVX-512 for x86; A64FX SVE-512 for
ARM):

> "There are 8 loops in TSVC2 with indirect memory accesses. Both x86 and
> ARM provide vector gather/scatter instructions. Neither GCC nor Clang
> were able to utilize them to vectorize these 8 loops on x86. However, ICX
> was able to vectorize 2 loops. On ARM, GCC and ACFL were able to
> vectorize the same 2 loops but Clang was not able to vectorize any."

That is: even with hardware gather/scatter available, only 2 of 8 (25%)
indirect-access kernels get vectorized at all by any tested compiler, on
either platform. And where it IS used, the paper's own measurements show it
frequently does **not** pay off:

- `s2102` (identity-matrix scatter): "Both Clang and ICX used vector
  **scatter** instructions which did not provide any performance
  improvement over non-vectorized stores."
- `s3111` (indirect reduction, gather): "The vectorized code... did not
  yield any performance improvement over the code produced by GCC and
  ICX" — masked gather/compare/add sequences were no faster than scalar.
- `s4115` (indirect dot product, gather): Clang unrolled by 8 instead of
  vectorizing; ACFL used SVE `ld1w {z1.s}, p0/z, [x19, x8, lsl #2]` (a real
  SVE gather) but the paper notes "it is not clear why the vector gather
  instructions were not profitable" for the Clang-generated masked-gather
  alternative it examined.

**This is the strongest evidence available for the profitability
question, and it comes from hardware strictly more favorable to
gather/scatter than the M4's NEON-128** — wider vectors (512-bit vs
128-bit) and, critically, hardware gather/scatter that NEON does not have
at all. If gather/scatter measurably fails to pay off on the majority of
TSVC2's indirect kernels on 512-bit SVE/AVX-512 silicon, the software-gather
emulation NEON-128 would require (scalar loads + lane-insert, on a 4-lane
register) has a strictly worse cost structure and a strictly smaller
amortization surface, and would be *at least as unlikely, probably more
unlikely*, to pay off.

`ASSUMPTION:` I found no paper or benchmark that directly measures TSVC2's
indirect-addressing kernels on NEON-128/Apple Silicon specifically — the
above is a documented, physically-grounded extrapolation from measured
wider-hardware data plus the verified instruction-set gap, not a direct
measurement. The direction of the extrapolation (worse, not better, on
NEON-128) is high confidence; a precise "X% of kernels would pay off"
number is not obtainable from what I found.

### Verdict (deliverable c)

**Analysable-but-usually-not-profitable is the correct verdict for
NEON-128 gather-style access**, and it is not a hedge — it is the qualitative
reading the best available (adjacent-hardware) data supports. Building the
analysis (recognizing `a[idx[i]]` as legal-if-`idx`-is-injective, or gating
it behind a runtime distinctness check) is a well-defined, tractable
software-engineering task. Whatever the chooser does with that analysis on
this machine would need its OWN stopwatch gate (exactly like
`tools/c_choose.py`'s gate 3) to reject the software-gather transformation
in the (likely common) case where it is correct but not faster — mirroring
what already happened with `s221` at 1.0x. Expect a similar or worse hit
rate: some kernels will clear gate 3, most on NEON-128 probably will not.

---

## 2. Runtime dependence checking / loop versioning (LLVM `LoopAccessAnalysis`)

**Mechanism** (from LLVM source: `llvm/Analysis/LoopAccessAnalysis.h/.cpp`,
`llvm/Transforms/Utils/LoopVersioning.cpp`): when static dependence analysis
cannot prove two pointers don't alias, `RuntimePointerChecking` partitions
the may-alias pointers into `RuntimeCheckingPtrGroup`s (pointers that are
provably disjoint from each other stay in one group; comparisons are only
needed *between* groups). `LoopVersioning` then clones the loop body into
two versions — a fast path guarded by "no group overlaps" bounds checks at
entry, and a scalar/conservative fallback — and branches to the fast path
only if every emitted check passes.

**Cost model / threshold, verified from LLVM source (`VectorizerParams`):**

- `RuntimeMemoryCheckThreshold` — default **8**. "When performing memory
  disambiguation checks at runtime do not generate more than this number of
  comparisons." Above this, the loop is not vectorized via runtime checks at
  all (LLVM gives up on this path rather than emit unbounded compile-time or
  runtime check cost).
- `PragmaDistributeSCEVCheckThreshold` — default **128**, but only applies
  when the programmer explicitly opts in with
  `#pragma clang loop distribute(enable)` — an order of magnitude more
  checks are tolerated once a human has asserted the loop is worth it.
- `MemoryCheckMergeThreshold` bounds the compile-time cost of the grouping
  algorithm itself (how many groups get compared pairwise while merging).

**What "amortizes the check" means here, and what I could not find:** the
gate above is a **threshold cutoff**, not a smoothly-amortized cost model —
LLVM either emits ≤8 (or ≤128 under the pragma) runtime comparisons and
vectorizes, or it doesn't attempt this path at all. The cost of the checks
themselves is O(1) per loop entry (a handful of pointer-bounds compares),
so for any loop whose trip count is not known to be tiny at compile time,
the checks are effectively always "worth it" in isolation — the real
gating question LLVM asks is not "does this pay for itself" but "is the
*number* of checks bounded enough to be worth generating two loop bodies
and a branch at all," which is a code-size/compile-time proxy, not a direct
runtime cost/benefit calculation.

`ASSUMPTION:` I was not able to find a published empirical study
quantifying *how often*, across a real benchmark corpus, LLVM's or GCC's
runtime-versioning actually measures faster than the scalar fallback (as
opposed to how often it is *attempted*). This is a genuine gap in what I
could verify — I would flag it explicitly rather than manufacture a number.
What IS directly relevant and already measured *in this repo*: this
project's own chooser applies exactly this "gate 3" stopwatch discipline
(`conformance/lift/CHOOSER.md`) and found roughly a 50% hit rate (6/12
legal-and-correct candidates were also faster) on straight-line affine
loops — a plausible, though not directly transferable, reference point for
what fraction of *any* speculative vectorization (runtime-checked or not)
actually pays off on this class of code.

---

## 3. Index injectivity as a declared property

### 3.1 The exact precedent exists, and is decades old

Cray's Compiling Environment ships precisely the vocabulary this repo's
`theoretical-cap.md` proposes inventing:

```
C:       #pragma _CRI permutation symbol[, symbol]...
Fortran: !DIR$ PERMUTATION (ia [, ia]...)
```

Per the HPE Cray Programming Environment manual page (`permutation(7)`),
this directive "specifies that an integer array has no repeated values,"
applied to an integer array used as a vector-valued subscript for indirect
addressing, and it licenses the compiler to "safely generate an unordered
scatter for the write" — i.e., exactly the index-injectivity fact that
would discharge `a[idx[i]] = ...` without needing a dependence test at all.
The documentation states that "many-to-one assignment occurs if any
repeated elements exist in the subscripting array" if the declaration is
false, but describes **no runtime check and no detection mechanism** — like
`restrict`, it is a trusted assertion, silently wrong if false.

This confirms, with a concrete citation, what `theoretical-cap.md` already
asserted: `restrict` genuinely cannot express this (it declares
non-aliasing between *pointers*, not distinctness of the *values inside* one
array — confirmed against the C99 restrict semantics below), but the
missing vocabulary is not novel — it is a 1980s/90s-vintage Cray vendor
pragma that has apparently never been standardized or adopted outside Cray
tooling.

### 3.2 What each related mechanism actually licenses (and what happens if false)

| mechanism | spec text (paraphrased where primary text was unfetchable) | what it licenses | on violation |
|---|---|---|---|
| C99 `restrict` (§6.7.3) | "if an object accessed through a restrict pointer is also accessed through another pointer not derived from it, behavior is undefined" | non-aliasing between the *pointers themselves* — nothing about the *values* an array holds | undefined behavior; no runtime check (verified via cppreference + C99 text) |
| `#pragma ivdep` (Intel/Cray/`#pragma GCC ivdep`) | Intel's own docs: "the compiler treats an assumed dependence as a proven dependence... ivdep overrides that," but "proven dependencies... are not ignored" | overriding only *assumed, unproven* dependences — narrower than an unconditional override | silently wrong if the assumed dependence was actually real; compiler does not attempt to verify |
| Cray `permutation` | see 3.1 | index-array injectivity, licensing unordered scatter | silently wrong (many-to-one write), no check described |
| Fortran `DO CONCURRENT` | LLVM Flang's own docs (`flang.llvm.org/docs/DoConcurrent.md`, title literally *"DO CONCURRENT isn't necessarily concurrent"`): compilers are explicitly **not required** to detect all violations in "ambiguous" localization cases | serial-semantics-but-parallelizable loop, with automatic localization of ambiguous temporaries | compiler-dependent; standard explicitly permits non-detection |
| OpenMP `order(concurrent)` (5.1+) | Per spec-derived secondary summary (I could not fetch openmp.org directly — Cloudflare-blocked both `www.openmp.org/spec-html/5.1` and `/5.2`; treat wording below as `ASSUMPTION:` paraphrase, not verbatim): iterations "may execute in any order, including concurrently"; code "must not assume that any cross-iteration data dependences would be preserved" | whole-loop-body reordering freedom, not a *specific array's* injectivity — coarser instrument | programmer responsibility; unspecified behavior if violated |
| OpenMP `simd`/`safelen` | bounds the assumed-safe cross-iteration distance | a *distance* bound, not a *reason* the distance is safe | silently wrong if violated |
| OpenACC `independent` | per OpenACC best-practices guide (secondary-sourced): "asserts... iterations are independent... safe to parallelize"; if results are wrong under `parallel` (as opposed to `kernels`, where a wrong assertion is treated as a compiler bug), that is explicitly characterized as a **programmer** bug | loop-level parallel-safety assertion | explicitly programmer's fault if false; unspecified/incorrect results, no check |

**Pattern across every mechanism found, without exception: these are all
unchecked assertions.** None of the prior art — not `restrict`, not
`ivdep`, not Cray's own `permutation`, not Fortran's locality rules, not
OpenMP's `order`/`safelen`, not OpenACC's `independent` — pairs the
declaration with a runtime or static proof obligation. Every one trusts the
programmer and produces silent corruption if the trust is misplaced.

### Verdict (deliverable b, indirect-addressing half)

The declaration form that would discharge `a[idx[i]]` is real, has direct
40-year-old precedent (Cray `permutation`), and is exactly what
`theoretical-cap.md` already named ("an index-injectivity invariant"). But
**every piece of prior art found ships it as an unchecked assertion**, and
this project has already been burned once by trusting an unchecked
assumption (the control-flow incident). If OSIL adopts an
index-injectivity vocabulary, the honest options — given the
already-demonstrated cost of getting this wrong — are: (i) require the
declaration be *discharged by construction* (e.g., `idx` is provably the
output of a known-bijective builder, not an arbitrary runtime array), or
(ii) pair it with an explicit runtime distinctness check (an O(n) or
O(n log n) pass over `idx[]`, amortized the same way LLVM amortizes its
`RuntimePointerChecking` bounds checks) before trusting it for a
transformation the differential test might not exercise. Shipping it as a
bare, unchecked assertion — the industry-standard model — would be
repeating the exact mistake this project's own record attempt already made
once, this time with a category of bug (aliasing/memory corruption) that is
strictly harder to catch by differential testing on one input distribution
than the control-flow reordering bug was.

---

## 4. Wrap-around scalars

### 4.1 Internal finding: the "+0 in isolation" price is a measurement artifact, not a fact about the feature

**Established by direct experiment on this repo's own tooling (this
session, 2026-08-24), reproducible by anyone with the repo checked out and
TSVC2's lifted JSON on hand:**

`tools/capability_ceiling.py` declares (via
`conformance/corpus/026-capability-analysis.osil`) two DISTINCT refused
features on the `affine_subscript` capability: `subscript.indirect` and
`subscript.wraparound`. But its `features()` extractor
(`tools/capability_ceiling.py` lines 81-94) collapses both into one token:

```python
for u in lp["unhandled"]:
    if "control flow" in u:
        f.add("body.control_flow")
    elif "non-affine" in u:
        f.add("subscript.indirect")      # the only branch reached; wraparound never produced
```

Every `unhandled` diagnostic string containing `"non-affine subscript ..."`
matches this branch — whether the lifter emitted it for `a[idx[i]]`
(genuine indirect addressing) or for `b[im1]` (a wrap-around scalar). I
confirmed this directly against the already-lifted TSVC2 JSON (176 loops,
produced by `c_lift.py --json` earlier in this session) by importing
`capability_ceiling` and running its own `features()` function over every
kernel:

```
s291 features: {'subscript.indirect'}      # b[im1]        -- NOT tagged subscript.wraparound
s292 features: {'subscript.indirect'}      # b[im1], b[im2] -- same
all feature tokens EVER produced by features() over the whole 176-loop corpus:
    {'subscript.indirect', 'dep.true_carried', 'access.multi_dimensional'}
```

`subscript.wraparound` is never in that set — not for s291, s292, or any
other kernel in the suite. Consequently, replaying the marginal-pricing
logic (`ceil_with(admit)` in `capability_ceiling.py`) with
`admit = {'subscript.wraparound'}` alone is **guaranteed by construction**
to return `+0`, independent of whether wrap-around recognition has real
value, because no lifted loop's feature set ever contains that token to
begin with:

```
baseline analysable (nothing admitted)          : 67
admit subscript.indirect alone                  : 99   (delta +32)
admit subscript.wraparound alone                : 67   (delta  +0)   <- structurally forced, not measured
admit subscript.indirect + subscript.wraparound : 99   (delta +32, identical to indirect alone)
```

(These per-function deltas over the 176-loop lifted set, computed live in
this session, are not identical in scale to the headline +15/60.9% number
in `theoretical-cap.md` — that number is computed per-kernel over the
151-kernel TSVC2 set with the compiler-vectorized baseline unioned in — but
the qualitative structure, including the forced-zero result for
`subscript.wraparound`, is identical and reproduces on the same tooling
either way.)

**Verdict: the "+0 in isolation" pricing finding is an artifact of the
classifier, not a fact about the feature's value.** s291/s292 were
*already* folded into the `subscript.indirect` price the moment the
lifter's diagnostic string matched `"non-affine"` without recording *why*
the subscript is non-affine. The pricing tool cannot currently ask "what is
wrap-around recognition worth *instead of* full indirect-addressing
support" because it has no separate feature channel for that question — the
corpus declaration (`026-capability-analysis.osil`) promises a distinction
(`subscript.indirect` vs `subscript.wraparound` as separate `refuses`
entries) that the extractor (`capability_ceiling.py::features()`) does not
implement (it needs a branch that inspects the lifter's per-statement
`deps[].why` field — the lifter already emits `"scalar \`im1\` links S0 -> S1"`
for exactly this case, distinct from an opaque `idx[]` array read — but
`features()` never reads that field). This is a bug/gap in the pricing
instrument, not evidence about the true isolated worth of wrap-around
recognition.

### 4.2 What production compilers actually do (external, primary-source verified)

**LLVM merged support for exactly this pattern less than a year before
this research** (verified via GitHub PR page): **[LoopPeel] Peel to make
Phis loop inductions**, `llvm/llvm-project#121104`, **merged 2025-08-20**
into `llvm/main`. The PR's own motivating example is essentially
byte-for-byte the TSVC s291 pattern:

```c
int im = N-1;
for (int i=0; i<N; i++) {
  a[i] = b[i] + b[im];
  im = i;
}
```

Peeling the loop by one iteration turns `im` into a genuine loop induction
variable (`im(i) = i-1` after the peel), which then flows through the
existing ScalarEvolution/affine machinery like any ordinary affine
subscript. This is, precisely, **induction-variable recognition via
peeling** — a classical scalar-evolution technique, not a new
soundness-relevant capability at all. Measured speedup on Neoverse-V2
(`-O3 -ffast-math -mcpu=neoverse-v2`): reported "more than 60%."

Caveats, also verified from the PR: it is **disabled by default** behind
`-enable-peeling-for-iv`, "pending resolution of undesired peeling cases";
it is currently restricted to single-block loops with constant-increment
operations and requires `nsw`/`nuw` overflow flags on the relevant
arithmetic; cast operations can defeat the analysis and cause unnecessary
peeling. So as of this writing (per the two TSVC2-measurement papers found,
both dated Feb/June 2025 — Sakib et al. arXiv:2502.11906 and the VecTrans
paper arXiv:2503.19449 — both predating or contemporaneous with the LLVM
PR's merge), **mainstream Clang/GCC releases do not recognize s291/s292 by
default today**, and the fix that would make them do so is real, recent,
upstream, and off-by-default.

The VecTrans paper (arXiv:2503.19449) is cited by a search-derived summary
as stating ICC (Intel's classic, now-legacy compiler) could already
vectorize s291/s292 automatically while GCC and Clang could not.
`ASSUMPTION:` this ICC claim is carried only via the search engine's
paraphrase of that paper/an LLVM Discourse thread, not a directly quoted
primary passage I verified myself — flagged accordingly, though it is
consistent with ICC's historical reputation for aggressive scalar-recurrence
recognition.

### Verdict (deliverable a, wrap-around half)

Production compilers **do** recognize this pattern via a well-understood,
purely-static technique (loop peeling to expose a hidden induction
variable, feeding the existing SCEV/affine machinery) — LLVM shipped it
(gated) in August 2025, and Intel's classic compiler apparently did it
years earlier by some other route. **The mechanically-trivial appearance
noted in the prompt is correct**: this is not a new class of analysis at
all, it is a gap in *recognition*, not a gap in *what the affine model can
express*. Once `im1`'s closed form is derived, the resulting access is
literally an affine subscript — the SAME capability (`affine_subscript`)
this project already trusts and gates, not a new one.

**This project's "+0 in isolation" pricing result is genuinely wrong as a
statement about value, and right only as an artifact of how the classifier
was built.** The correct verdict is that wrap-around-scalar recognition is
a small (bounded by the 2/176 TSVC2 kernels — s291, s292 — it targets on
this specific suite) but essentially free and low-risk win: it needs a
lifter-side induction-variable-substitution pass (à la LLVM's peel-for-IV,
or the simpler special case of just recognizing `scalar = i` assigned at
loop-body-end and substituting its prior value as `i - step`), NOT a new
admits/refuses vocabulary entry, NOT a runtime check, and NOT a new
soundness obligation — see §6 for why this differs categorically from
indirect addressing.

---

## 5. The polyhedral alternative (isl/Polly)

### 5.1 What Polly actually requires and refuses

Polly's SCoP (Static Control Part) detection requires **affine loop
bounds** — every natural loop's iteration count must be describable as an
affine function of surrounding loop iterators/parameters — and, *by
default*, only multidimensional **affine** array accesses (verified via
`polly.llvm.org` documentation and the `ScopDetection` source/doxygen).
This is exactly the "famously still requires affine bounds" characterization
in the prompt, confirmed.

Polly does have a documented escape hatch for non-affine code, introduced
around February 2015 per Polly's own changelog: **non-affine subregions**,
enabled via `-polly-allow-nonaffine`. This lets Polly admit a region
containing a data-dependent or non-affine access into a SCoP by
**overapproximating** it as an opaque black box with conservative
(whole-object, MAY-alias) read/write summaries, rather than a precise
index set. Practically: Polly can build a SCoP *around* a loop containing
`a[idx[i]]`, but it does so by giving `idx`/`a` conservative "something in
this object may be touched" semantics for that one statement — which
typically defeats parallelization/vectorization of *that specific
statement* while still letting Polly optimize everything else in the loop
nest. This is functionally similar in spirit to what this project's
analyser already does (refuse the specific access, not the whole file) —
Polly just does it inside a larger, general transformation pipeline instead
of a targeted per-loop refusal.

### 5.2 Maintenance status (verified live against the mainline repo)

Queried directly via the GitHub API against `llvm/llvm-project` during this
research (2026-08-24): the 5 most recent commits touching the `polly/`
subtree span **2026-07-23 to 2026-08-13**, including active internal work
(`[Polly] Narrow IV to lower type when possible`, `[Polly] Fix memory leak
in DependenceAnalysis::Result::abandonDepende...`, both merged PRs). Polly
is **actively maintained** as part of the mainline LLVM monorepo as of this
writing — contrary to its reputation (traceable to a 2017 "[RFC] Polly
Status and Integration" mailing-list thread that discussed reduced
staffing at the time) of being a stalled side project. Confidence: HIGH
that it still receives commits; MEDIUM on adoption/production-usage rate,
which I found no data on either way.

### 5.3 Integration cost, for this project specifically

Polly is an LLVM-IR-level pass family built on `isl` polyhedra, not a
source-level, libclang-AST tool. Adopting it for this project's pipeline
would mean either (a) shelling out to `clang -mllvm -polly ...` and parsing
Polly's remarks/generated IR — a much heavier, less directly-inspectable
integration than the current AST-walking `tools/c_lift.py`, and one that
loses the direct C-source-to-declared-facts traceability this project's
lifter currently has — or (b) linking Polly's own C++/isl APIs directly, a
substantially larger dependency and skillset shift than the current
from-scratch Python dependence test. `ASSUMPTION:` I found no
engineer-days-scale estimate for either integration path; this is inferred
from Polly's documented architecture, not measured against this specific
codebase.

### Verdict (deliverable d)

Polly would subsume the **2-D / multi-dimensional-affine** blocker (31
kernels per `theoretical-cap.md`'s table) in essentially one move — this is
its exact design center (affine multidimensional array access analysis,
tiling, fusion, GEMM pattern recognition), and it remains actively
maintained. It would **not** meaningfully subsume indirect addressing
(it black-boxes the non-affine access, giving up precision exactly where
this project's own analyser already refuses — same outcome, bigger
pipeline) nor wrap-around scalars (Polly's SCoP model doesn't perform the
induction-variable substitution that problem needs either; that
preprocessing would still be required, Polly or not). Net: adopting Polly
cleanly answers **one of the four blockers** named in `theoretical-cap.md`
(2-D access), is a nontrivial, IR-level integration lift relative to the
project's current source-level architecture, and does not reduce the work
needed for the other three (control flow, indirect addressing, true
recurrence).

---

## 6. Risk / unsoundness assessment

### 6.1 What this project has already learned, the hard way, about admitting a new capability

`docs/design/record-attempt.md` documents that admitting `body.control_flow`
(TSVC kernels with `if (...) goto L20; ... L20: ;` patterns — I confirmed
directly against the lifted TSVC2 corpus in this session that **s277, s278,
s279 are exactly these goto/label kernels** referenced in the task) first
produced **three kernels that measured as "recovered" but were silently
INCORRECT** in an uncorrected run (10 recovered / 49.0%, before the fix),
caught only by the differential test comparing transformed output against
the original on concrete inputs — the dependence model itself had "no
notion of branching" and could not have caught it. The fix was to refuse
any body containing control flow outright (10 -> 6 recovered, 49.0% ->
46.4%).

Independently, `conformance/lift/CHOOSER.md` documents a second, structurally
different unsoundness that a *static* check did catch, once the lifter was
fixed to track it: the chooser originally tracked only array dependences,
so a scalar (`t` in `s261`) linking two statements iteration-to-iteration
was invisible, and the chooser proposed splitting statements that shared a
scalar — silently wrong (the reader would see the *last* iteration's value
of `t`, not its own). Only an incidental undeclared-variable compile error
stopped it from shipping; had the scalar been in scope, it would have
compiled and run incorrectly. This is directly relevant here: `im1`/`im2`
are exactly this "scalar links statements across iterations" shape, and the
lifter's fix (track scalar reads/writes as dependences, force scalar edges
bidirectional) is precisely why s291/s292 land in `refuse` today rather
than a silently-wrong `distribute`.

### 6.2 External confirmation this is a real, not hypothetical, risk class

Even in LLVM — a mature, heavily fuzz-tested, production vectorizer —
alias-analysis-driven vectorization miscompilations have shipped and been
reported: `llvm/llvm-project#69744`, "LoopVectorize Miscompilation with
Aliases in clang 15+" (the vectorizer treated a value as safe to vectorize
despite it aliasing an object from a previous iteration), and
`llvm/llvm-project#98978`, "[BasicAA] Incorrect alias analysis causing
miscompile in slp-vectorizer" (an assumption-based alias result was
incorrectly treated as definitive in the presence of a dependency cycle).
These confirm the risk class this project's own control-flow incident
belongs to — aliasing/dependence-analysis errors silently corrupting
vectorized output — is one that escapes to production even in the
best-resourced open-source compiler, not a risk unique to a smaller
research pipeline.

### 6.3 The two sub-capabilities carry categorically different risk, which is the central finding of this section

**Indirect addressing (`a[idx[i]]`) is a genuine new soundness-obligation
class.** Whether two accesses through `idx[]` alias — within one iteration
or across iterations — is, in general, undecidable statically without an
extra fact about `idx`'s values (injectivity, or a bound on its range). A
false "provably not aliased" conclusion silently reorders or vectorizes
memory operations that actually collide — the exact bug class §6.2's LLVM
issues exhibit. Per §3, this is checkable **statically only** if `idx[]`
is provably constructed to be injective by dataflow (rare, and not
something this project's lifter currently attempts), and otherwise is
checkable **only at runtime** — either an explicit O(n)-or-worse
distinctness pass over `idx[]`, or an LLVM-`RuntimePointerChecking`-style
bounds/no-overlap check if the access pattern permits one. Neither
machinery exists in this project's pipeline today; admitting
`subscript.indirect` without building one would be repeating the exact
"admit, trust the pattern match, hope the differential test catches it"
mistake the control-flow incident already made — this time for a bug class
(silent memory corruption from a false non-aliasing conclusion) that is, if
anything, *harder* to catch by differential testing on a single input
distribution than a control-flow reordering bug is, because it is
data-dependent on the specific values `idx[]` happens to hold in whatever
inputs the differential test exercises.

**Wrap-around scalars carry a materially lower, narrower risk.** This is
not a memory-aliasing question at all — it is scalar-evolution/induction-
variable recognition. Once the recurrence is proven closed-form (as LLVM's
SCEV plus its August-2025 peel-for-IV pass does, entirely statically, no
runtime check involved), the resulting access, after substitution, *is*
literally an affine subscript — it is handed to the exact same
`affine_subscript` capability this project already trusts and gates, not a
new one. The only failure mode is a *missed* optimization (failing to
recognize a recognizable pattern, as GCC/Clang do today by default) or, if
implemented carelessly, a *wrong* substitution (e.g. mishandling the
boundary iteration where `im1` starts at `LEN-1` rather than `i-1`) — a
correctness bug that is bounded, local, and directly differential-testable
per-kernel, not the open-ended aliasing risk indirect addressing carries.
It does not need a new declaration, a new runtime check, or a new gate; it
needs a correctly-implemented recognizer, tested the same way every other
transformation in `tools/c_choose.py` already is.

### Verdict (deliverable e)

**Do not treat the two sub-capabilities as one price or one risk tier.**
Admitting `subscript.indirect` should be treated as HIGH risk requiring new
machinery this project does not have (a checked injectivity declaration
per §3, or a runtime-versioning gate per §2, or both) before it is admitted
at all — an index-injectivity vocabulary with the *unchecked-assertion*
semantics every piece of prior art in §3 uses would specifically reproduce
the failure mode this project's own history already flags as
unacceptable. Admitting wrap-around-scalar recognition should be treated as
LOW risk: it is a self-contained lifter-side recognizer fix that degrades,
once correct, into analysis this project already trusts — closer in kind to
fixing a bug in the existing affine pattern-matcher than to admitting a new
capability with new failure modes.

---

## Summary — the five deliverables

**(a) Separate verdicts.** Indirect addressing: HIGH risk, genuinely new
soundness obligation (aliasing undecidable without an extra fact), and —
per §1.3's extrapolation from measured SVE-512/AVX-512 data — likely
low/marginal payoff on NEON-128 even where it is legal to vectorize.
Treat as its own gated capability, built only alongside the checking
machinery it requires. Wrap-around scalars: LOW risk, mechanically distinct
(induction-variable/closed-form substitution, not indirection), reduces to
already-trusted affine analysis once recognized by a lifter-side pass;
production precedent exists (LLVM peel-for-IV, merged Aug 2025, still
off-by-default) targeting this exact TSVC pattern. This project's own "+0
in isolation" pricing result for it is a measurement artifact (§4.1) — the
classifier never emits a `subscript.wraparound` token to price in the first
place — not evidence the feature is worthless.

**(b) Precise declaration forms.** Indirect addressing needs a
Cray-`permutation`-style index-injectivity invariant ("this integer array,
over this iteration domain, takes each value at most once") — but unlike
every prior-art instance found (Cray `permutation`, `ivdep`, `restrict`,
Fortran locality rules, OpenMP `order`/`safelen`, OpenACC `independent`,
all of which are unchecked assertions), it should be discharged either by
construction (provable bijective origin) or by an explicit runtime
distinctness/versioning check, given this project's own history with
trusting unchecked assumptions. Wrap-around scalars need no injectivity
declaration at all — the "declaration" that discharges them is really a
*recognizer capability* (induction-variable substitution turning `im1`
into `i - 1`), a lifter-time transformation feeding the existing
`affine_subscript` admits path, not a new vocabulary entry in the
capability corpus.

**(c) NEON-128 profitability verdict.** Analysable-but-usually-not-profitable.
ARM's own instruction-taxonomy documentation (§1.1) confirms NEON has no
gather/scatter category at all; the closest available empirical proxy
(§1.3, measured directly on 512-bit SVE/AVX-512 hardware that DOES have
native gather/scatter) shows the majority of TSVC2's indirect-access
kernels either fail to vectorize at all or show zero/negative measured
speedup even there. NEON-128's forced software-gather emulation, on a
4-lane (vs 16-lane) register, has a structurally worse cost profile and
smaller amortization surface than the hardware already shown to
underperform. Confidence: medium-high on direction, low on a precise
quantitative threshold — no direct NEON-128/TSVC2 gather benchmark was
found; this is a physically-grounded extrapolation, flagged as such.

**(d) Polyhedral adoption verdict.** Polly (actively maintained, verified
live against mainline LLVM through August 2026) would subsume the
multi-dimensional/affine-bounds blocker (31 kernels) in one move — its
exact design center — but would not meaningfully subsume indirect
addressing (it black-boxes non-affine accesses, same effective refusal,
bigger pipeline) or wrap-around scalars (needs the same IV-substitution
preprocessing regardless). Integration cost is real: Polly is an LLVM-IR/isl
pass family, a different integration shape than this project's current
source-level, libclang-AST architecture. It answers one of
`theoretical-cap.md`'s four blockers cleanly and leaves the other three's
work largely undiminished.

**(e) Risk/unsoundness assessment.** The two sub-capabilities are not
comparable risks and should not be priced or gated together. Indirect
addressing opens a new, general aliasing-soundness hole with no existing
mitigation in this pipeline, of the same class that has caused real
production miscompilations even in LLVM (§6.2) and that this project's own
differential test is less likely to catch reliably than it caught the
control-flow incident, because the failure is data-dependent rather than
structural. Wrap-around-scalar recognition carries a narrow, local,
differential-testable risk (boundary-condition correctness in a
substitution pass) and, once correct, produces output indistinguishable
from — and gated exactly like — the affine analysis already trusted in
this project.

---

## Sources

**Primary — this repository (grounding, read/queried directly in this session):**
1. `docs/design/theoretical-cap.md`
2. `conformance/lift/README.md`
3. `conformance/lift/CHOOSER.md`
4. `conformance/lift/GROUND-TRUTH.md`
5. `conformance/corpus/026-capability-analysis.osil`
6. `tools/capability_ceiling.py` (read in full; its `features()` classifier
   instrumented live against the TSVC2 lifted JSON to produce the §4.1
   finding)
7. `docs/design/record-attempt.md`
8. `docs/decisions/ADR-0014-c-ecosystem-profile.md`
9. `/private/tmp/tsvc.json` — pre-existing lifted TSVC2 corpus (176 loops,
   `tools/c_lift.py --json` output) found on disk from prior work in this
   environment; used to directly inspect s277/s278/s279, s291/s292, and to
   run `capability_ceiling.features()` live

**Primary — external:**
10. Arm, *"SVE and Neon coding compared"*, document 102131, Issue 01, 14
    September 2020 — https://developer.arm.com/-/media/Arm%20Developer%20Community/PDF/Learn%20the%20Architecture/102131_0100_01_SVE_and_Neon_coding_compared.pdf
11. LLVM source: `llvm/include/llvm/Analysis/LoopAccessAnalysis.h`,
    `llvm/Analysis/LoopAccessAnalysis.cpp`,
    `llvm/Transforms/Utils/LoopVersioning.cpp`,
    `llvm::VectorizerParams` — https://llvm.org/doxygen/structllvm_1_1VectorizerParams.html ,
    https://llvm.org/doxygen/classllvm_1_1RuntimePointerChecking.html
12. `llvm/llvm-project` pull request #121104, "[LoopPeel] Peel to make Phis
    loop inductions" (merged 2025-08-20) — https://github.com/llvm/llvm-project/pull/121104
13. `llvm/llvm-project` commit history for `polly/` (queried live via
    GitHub API, 2026-08-24) — https://api.github.com/repos/llvm/llvm-project/commits?path=polly
14. Polly documentation — https://polly.llvm.org/
15. C99 `restrict` semantics — https://en.cppreference.com/c/language/restrict
16. Intel compiler documentation, `ivdep` — https://www.intel.com/content/www/us/en/docs/dpcpp-cpp-compiler/developer-guide-reference/2023-1/ivdep.html
17. HPE Cray Programming Environment, `permutation(7)` — https://h41374.www4.it.hpe.com/docs/25.09/cce/man7/permutation.7.html
18. LLVM Flang, *"DO CONCURRENT isn't necessarily concurrent"* — https://flang.llvm.org/docs/DoConcurrent.md
19. `llvm/llvm-project` issue #69744, "LoopVectorize Miscompilation with
    Aliases in clang 15+" — https://github.com/llvm/llvm-project/issues/69744
20. `llvm/llvm-project` issue #98978, "[BasicAA] Incorrect alias analysis
    causing miscompile in slp-vectorizer" — https://github.com/llvm/llvm-project/issues/98978
21. GCC bug PR91033, "Make scatter/gather vectorization failures non-fatal" — referenced via gcc-patches mailing list
22. Sakib, Prabhu, Santhi, Shalf, Badawy, *"Comparison of Vectorization
    Capabilities of Different Compilers for X86 and ARM CPUs"*, arXiv:2502.11906
    (Feb 2025) — https://arxiv.org/pdf/2502.11906 — fetched and read directly
    (PDF pages 1-6)

**Secondary (used for corroboration; primary text unfetchable due to
Cloudflare/JS-gating, flagged `ASSUMPTION:` inline where relied upon for a
specific quoted claim):**
23. OpenMP 5.1/5.2 specification, `order`/`simd` clauses —
    https://www.openmp.org/spec-html/5.1/openmpsu47.html (blocked by
    Cloudflare on direct fetch; paraphrase corroborated across multiple
    independent secondary summaries)
24. OpenACC best-practices guide, `independent` clause —
    https://github.com/OpenACC/openacc-best-practices-guide
25. VecTrans, arXiv:2503.19449 (2025) — TSVC s291/s292 vs ICC/GCC/Clang
    claim carried via search-engine paraphrase only, not directly quoted
26. NVIDIA Grace CPU Benchmarking Guide, "Arm Vector Instructions: SVE and
    NEON" — https://nvidia.github.io/grace-cpu-benchmarking-guide/developer/vectorization.html
27. Arm Learning Paths, "From Arm Neon to SVE" — https://learn.arm.com/learning-paths/servers-and-cloud-computing/sve/sve_basics/

---

**Epistemological note.** This research represents best available evidence
as of 2026-08-24. The NEON-128 profitability verdict (deliverable c) is the
weakest-evidenced of the five — a physically-grounded extrapolation from
adjacent hardware, not a direct measurement — and should be re-evaluated if
a direct TSVC2-on-NEON-128 gather benchmark becomes available. The
`subscript.wraparound` pricing-artifact finding (§4.1) is the
strongest-evidenced — a reproducible, live-instrumented fact about this
repo's own tooling, not a literature claim — and is immediately actionable:
fixing `capability_ceiling.py::features()` to distinguish the two feature
tokens (by reading the lifter's `deps[].why` field) would let this project
re-run its own pricing tool and get a real, rather than structurally-forced,
answer to "what is wrap-around recognition worth in isolation."
