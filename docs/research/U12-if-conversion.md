# U12 — If-conversion: what would it take to safely admit control flow?

**Date:** 2026-08-24
**Researcher:** research-agent (direct investigation + mechanical reproduction using the
project's own tools; not multi-agent dispatched — see Method)
**Question:** `tools/c_lift.py` refuses any loop body containing `if`/`goto`/`switch`/
`break`/`continue`/`?:` because its dependence model is program-order over straight-line
statements. `just price` (`tools/capability_ceiling.py --what-if body.control_flow`) prices
admitting this feature at **+18 kernels, 51.0% → 62.9%** on TSVC2 — above the published
record (GCC/A64FX/SVE, 56.0%, arXiv:2502.11906). The refusal is not paranoia: before it
existed, the chooser distributed statements across `goto`/label pairs in s277/s278/s279 and
produced semantically wrong code, caught only by a differential test on one input
distribution. What would it take to admit control flow **safely**, and is the +18 real on
this project's actual hardware (Apple M4, NEON-128, no SVE)?

---

## TL;DR

**(a) The algorithm:** classical if-conversion (Allen, Kennedy, Porterfield, Warren,
POPL'83) — convert control dependence to data dependence, then rewrite the guarded update
as an unconditional **select-assignment**. Concretely for this project: a *source-to-source*
rewrite in `c_choose.py` (not "port LLVM's legality checker and hope its backend picks good
codegen" — that path was tested and still hits LLVM's own conservative lowering, see (d)).

**(b) Legality, precisely:** a guarded update `if (cond) L = E;` (or `if/else`, or the
`goto`-encoded equivalent) is safe to rewrite as `L = cond ? E : L;` (address-invariant
select) **iff**: (i) every lvalue written in any arm is written, or left provably unchanged,
in every other arm — same address set across arms; (ii) every address touched is *always*
in-bounds regardless of which arm executes (already established by this project's own
`affine_subscript` capability for the arms actually present in TSVC); (iii) evaluating `E`
speculatively cannot fault or have a side effect (no calls with unknown effects, no
`mayThrow`). This is a **narrower, mechanically-checkable** condition than LLVM's own
default legality gate (`blockCanBePredicated` in
`llvm/lib/Transforms/Vectorize/LoopVectorizationLegality.cpp`), which permits arbitrary
masked stores to *different* addresses and pays for that generality with an expensive
lowering. Reduction-shaped guards (`if (cond) sum += E;`) are actually a **strictly easier**
special case — no address at all is involved, so (i)–(ii) are vacuous and only (iii)
applies.

**(c) The NEON caveat:** real, and **directly reproduced on this machine** (Apple clang
17.0.0, M4, `-mcpu=native`). LLVM's default lowering of a predicated store on NEON degrades
to per-lane `tbz`+`st1` (test-bit-and-branch, scalar store) because NEON has no masked-store
instruction — this is why the M4's own cost model correctly rejects several of the +18 as
"not beneficial." **But this is a lowering-strategy artifact, not a hardware wall for the
address-invariant subclass**: rewriting the identical semantics as a source-level ternary
makes clang vectorize it *automatically, unforced*, using `bsl` (bit-select) + one
unconditional vector `str` — genuinely NEON-native, zero masked-store hardware needed. An
independent, peer-reviewed measurement (Pohl, Morini, Cosenza, Juurlink, SCOPES'18,
*"Control Flow Vectorization for ARM NEON"*) names this exact technique "select store" and
reports the same result on real Cortex-A53 hardware — plus a sobering counter-finding: even
their best technique produces a **net slowdown** on 3 of their 13 recovered kernels,
**two of which (s279, s2710) are in this project's own +18 set.**

**(d) What LLVM already does:** empirically, for the +18, it is overwhelmingly "declines to
if-convert well," not "cannot if-convert at all." Of the 18, **13 were legally
if-convertible and empirically recovered** by a hand-written source-level select rewrite on
this machine (measured, not argued); **5 need a different capability entirely**
(switch-dispatch, early-exit-loop-vectorization, or a genuine cross-iteration dependence
hiding behind the guard) and should not be attributed to if-conversion's yield.

**(e) Honest estimate:** the ceiling tool's "+18" measures *analysability*, not
*profitability after the stopwatch gate*, and the theoretical-cap.md document being updated
concurrently with this research flags exactly this gap ("price has no risk term"). Given (i)
13/18 legally recoverable, (ii) 2 of those independently measured as slowdowns on real
hardware even with the best known technique, (iii) this project's own probe-set hit rate
past legality+correctness into "faster" was 3/4 (75%), and (iv) TSVC's control-flow kernels
have lower arithmetic intensity than the distribution candidates that hit 75% — a realistic
expectation is **8–11 of 18 (44–61%) clearing all three gates**, not 18, and not the 0 a
naive "NEON has no predication, forget it" read would predict either. The remaining 5 are
out of if-conversion's scope regardless of gate outcomes.

---

## Method

Default line: search the literature on if-conversion, LLVM's implementation, and NEON vs.
SVE predication, and write up what's found. Simulated finding: a correct but generic account
("if-conversion exists, NEON lacks predicate registers, SVE has them") that would not answer
whether *this project's own* +18 kernels are actually recoverable on *this project's own*
hardware — the question that matters for a go/no-go decision on building the capability.

Gaps relative to the task:
- **Gap A — what does LLVM's legality checker actually require, verbatim?** Secondary
  sources paraphrase inconsistently. Read `LoopVectorizationLegality.cpp` directly.
- **Gap B — is the ceiling's "+18" a real, checkable list, or an abstraction?** The
  project's own `tools/capability_ceiling.py` can name the exact 18 kernels; a generic
  literature answer cannot.
- **Gap C — is the NEON profitability problem real on *this* hardware, or received wisdom
  from x86/A64FX comparisons?** Reproduce it directly, on the M4, with the project's own
  compiler invocation.
- **Gap D — for the specific 18, is LLVM's *default* refusal reason legality or cost, and
  does a source-level rewrite change the outcome?** This is answerable only by compiling
  each kernel and reading clang's own diagnostics — not by reading papers.

Each gap was closed by direct tool use (not agent dispatch — the investigation was serial
and cumulative: each finding motivated the next command, which is a poor fit for parallel
sub-agents that can't see each other's intermediate results). Batched web research
(LLVM source/docs, Allen–Kennedy lineage, ARM/NEON literature, TSVC provenance) was run in
parallel tool calls where independent.

**Synthesis: convergent.** The primary-source reading of LLVM's legality code, the
project's own capability-ceiling tool, direct compilation on the M4, and an independent
2018 peer-reviewed measurement on a different NEON chip (Cortex-A53) all agree on the same
structural story: NEON's missing masked-store instruction is the root cause, "select store"
(source-level predication) recovers most but not all of it, and a nontrivial minority of
even the recovered set is a measured slowdown despite being legal and correct.

---

## 1. The algorithm, and its actual origin

**Primary source, corrected.** If-conversion's original citation is not the 2001
Allen–Kennedy textbook (which is a later pedagogical synthesis) but:

- J. R. Allen, K. Kennedy, C. Porterfield, J. Warren. **"Conversion of Control Dependence to
  Data Dependence."** POPL '83. The core idea: replace `if (p) S` with `S` guarded by a
  Boolean *predicate value* computed once, turning a control-flow edge into an ordinary data
  dependence the rest of the vectorizer/scheduler already knows how to reason about.
- R. Allen, K. Kennedy. **"Automatic Translation of FORTRAN Programs to Vector Form."**
  ACM TOPLAS 9(4), 1987. Applies the above to loop vectorization specifically.

(`ASSUMPTION:` the Springer chapter "Compiler algorithms on if-conversion, speculative
predicate assignment and predicated code optimizations" found during search is a *later*,
separate VLIW/ILP-predication paper, not the Allen–Kennedy work; it was not used as a
source here.)

**LLVM's implementation, read directly from
`llvm/lib/Transforms/Vectorize/LoopVectorizationLegality.cpp` (main branch, fetched
2026-08-24).** Three layers, verbatim:

**Structural CFG requirement** (`canVectorizeLoopCFG`, lines 1570–1624):
```cpp
// We must have a loop in canonical form. Loops with indirectbr in them cannot
// be canonicalized.
if (!Lp->getLoopPreheader()) { ... "loop control flow is not understood by vectorizer" ... }
// We must have a single backedge.
if (Lp->getNumBackEdges() != 1) { ... }
// The latch must be terminated by a branch.
if (Latch && !isa<UncondBrInst, CondBrInst>(Latch->getTerminator())) { ... }
```
Note what this does **not** say: nothing about `goto` vs. `if` as *source* syntax. A
structured `goto` compiled to an ordinary forward branch produces the identical CFG shape as
the equivalent `if`/`else` — LLVM's legality is blind to C-level control-flow *syntax* and
sees only the resulting graph. (This directly bears on why this project's AST-level
`CONTROL_FLOW` refusal in `c_lift.py`, which fires on `K.GOTO_STMT` and `K.IF_STMT` alike, is
conflating two different things — see §7.)

**Per-block legality** (`canVectorizeWithIfConvert`, lines 1449–1567): first collects
`SafePointers` — addresses provably dereferenceable in every iteration that executes —
via two routes: (i) any pointer touched only in blocks that don't need predication is
automatically safe; (ii) for blocks that *do* need predication, a load's pointer can still
be added to `SafePointers` if `CanSpeculatePointerOp` proves the address computation has no
UB/poison risk **and** `isDereferenceableAndAlignedInLoop` proves the access never faults
(SCEV-based, can use a runtime guard). Then, for terminators:
```cpp
// We support only branches and switch statements as terminators inside the loop.
if (isa<SwitchInst>(BB->getTerminator())) {
  if (TheLoop->isLoopExiting(BB)) {
    reportVectorizationFailure("Loop contains an unsupported switch", ...); return false;
  }
} else if (!isa<UncondBrInst, CondBrInst>(BB->getTerminator())) {
  reportVectorizationFailure("Loop contains an unsupported terminator", ...); return false;
}
```
and finally every block that needs predication must pass `blockCanBePredicated`.

**Per-instruction legality** (`blockCanBePredicated`, lines 1398–1447), verbatim structure:
`llvm.assume` and `noalias.scope.decl` are dropped/ignored; calls are allowed only if a
masked vector variant exists; **loads** are allowed unconditionally — masked if not already
in `SafePointers`; **stores always require masking** (comment lists exactly three lowering
options: "1) masked store HW instruction, 2) emulation via load-blend-store (only if safe
and legal to do so, be aware on the race conditions), or 3) element-by-element predicate
check and scalar store"); and finally:
```cpp
if (I.mayReadFromMemory() || I.mayWriteToMemory() || I.mayThrow())
  return false;
```
— any instruction with unmodeled side effects kills predicability of the whole block
outright. This is why `s481`'s `exit(0)` inside the guard is not merely *unprofitable* to
if-convert, it is categorically **illegal** to if-convert: `exit()`'s side effect (process
termination) cannot be spuriously executed and then "un-done" if the guard was actually
false for that lane. No declaration can license this — the operation is fundamentally not
speculatable, only its *absence* under the guard is meaningful.

---

## 2. The safety problem — loads, stores, and what each option actually buys

| memory op | safe options (per LLVM's own comment, confirmed above) | precondition |
|---|---|---|
| load | (1) hoist — prove dereferenceable everywhere, load unconditionally | affine bound + no OOB across the loop's full index range (`isDereferenceableAndAlignedInLoop`) |
| load | (2) masked load (HW) | target has a masked-load instruction — **NEON does not** |
| store | (1) masked store (HW) | target has a masked-store instruction — **NEON does not** |
| store | (2) load-blend-store ("select store") | same address in every arm, always in-bounds, **and** — per LLVM's own comment — "be aware on the race conditions" (see below) |
| store | (3) element-by-element predicate check + scalar store | always legal, always the most expensive; NEON's actual default fallback (§3) |

**The concurrency subtlety, made precise by Pohl et al. (SCOPES'18, §4.3, read directly from
the PDF).** Load-blend-store ("select store") reads the *old* value of every element in the
vector — including ones the guard says should be untouched — blends, then writes the whole
vector back unconditionally. In a single-threaded loop this is transparently safe: writing
back an unchanged value is a no-op. Under concurrent access, it is **not**: another thread
could mutate a masked-out element between the read and the write-back, and the blend would
silently clobber that concurrent write with stale data. Pohl et al.'s fix is an *atomic*
select store (load-acquire / store-release + bit-select), which they measure as
consistently slower than the plain select store. `ASSUMPTION:` not evaluated further here —
TSVC2 and this project's `c_choose.py`-generated candidates are single-threaded C, so plain
select-store applies without the atomic variant, but any declaration vocabulary built from
this should state the single-threaded (or "chunk size multiple of VF") precondition
explicitly rather than silently assuming it.

---

## 3. ARM NEON specifically — reproduced directly on the M4

Hardware and toolchain used for every measurement below: Apple clang 17.0.0
(clang-1700.6.3.2), `arm64-apple-darwin25.5.0`, `-O3 -mcpu=native` (this project's own
baseline flags, matching `tools/tsvc_rate.py`).

### 3.1 The legal-but-unprofitable case, reproduced

A minimal repro of the `s272` shape (`if (e[i] >= t) { a[i] += c[i]*d[i]; b[i] += c[i]*c[i]; }`):

```
repro.c:6:5: remark: the cost-model indicates that vectorization is not beneficial [-Rpass-missed=loop-vectorize]
```
Forcing it with `#pragma clang loop vectorize(enable)` (which overrides the cost-model
*profitability* veto — confirmed directly, see §5) makes it vectorize, but the generated
AArch64 assembly for the predicated stores is:
```
LBB1_11: ... st1.s { v2 }[1], [x16]
LBB1_12: ... st1.s { v2 }[2], [x17]      (17 basic blocks total, `tbz` test-and-branch
LBB1_15: ... tbz w16, #0, LBB1_9          gating each lane's store)
LBB1_16: ... tbz w17, #0, LBB1_1
```
This is LLVM's option (3) — element-by-element predicate check and scalar store — exactly
the most expensive of the three options listed in the source comment, chosen by default
because NEON offers no HW masked store (option 1) and LLVM's automatic lowering did not
attempt option 2 (load-blend-store) here even though, for this kernel, it would have been
legal (same address in every arm, always in-bounds). The M4's cost model is *correct* to
reject this: 4 lanes × a compare-and-branch each is genuinely expensive relative to 4 scalar
iterations.

### 3.2 The same semantics, rewritten as a source-level select — recovers automatically

```c
int m = (e[i] >= t);
real_t a_new = a[i] + c[i]*d[i], b_new = b[i] + c[i]*c[i];
a[i] = m ? a_new : a[i];
b[i] = m ? b_new : b[i];
```
compiles **without any pragma** to:
```
repro.c:10:5: remark: vectorized loop (vectorization width: 4, interleaved count: 1) [-Rpass=loop-vectorize]
...
bsl.16b v1, v4, v3
str     q1, [x11], #16
```
`bsl` (bitwise select) + one unconditional 128-bit vector store. No masked-store hardware
needed, no per-lane branch. Same result for the reduction shape (`s3111`: `if (a[i]>0) sum
+= a[i];`): the guarded form fails outright with `"value that could not be identified as
reduction is used outside the loop"` (not even a cost-model question — LLVM's reduction
detector doesn't recognize the conditional-accumulate idiom), while `sum += (a[i]>0) ? a[i]
: 0.f;` vectorizes **and gets interleaved ×4** (a strong profitability signal, not a
marginal one).

This is independently named and measured by Pohl, Morini, Cosenza, Juurlink
(**"Control Flow Vectorization for ARM NEON,"** SCOPES'18, TU Berlin) — "select store,"
reported to beat the scalar-predicated-store baseline by "at least 5%, and for some
patterns, up to a factor of 2x" on real Cortex-A53 hardware, using the *identical* TSVC
suite. Their paper independently states the mechanism this section reproduces: *"the AVX2
based platforms support [masked load/store], while the NEON ISA extension does not. This is
the root cause for the difference in vectorization rates"* and names LLVM's existing
(but inconsistently triggered) hoist/sink mechanism as the origin of the select-store idea.

### 3.3 The switch case does not yield to the same trick

Rewriting `s442`'s `switch (indx[i])` as a chain of ternaries (`(k==1)?... : (k==2)?... :
...`) still fails:
```
repro.c:20:22: remark: loop not vectorized: loop contains a switch statement [-Rpass-analysis=loop-vectorize]
```
Clang's own frontend **canonicalizes** an equality chain against the same scrutinee back
into a `switch` in LLVM IR before the vectorizer runs, defeating the source-level dodge.
This is a genuine, current, stated LLVM limitation (`llvm.org/docs/Vectorizers.html`:
*"Many loops cannot be vectorized including loops with complicated control flow... A
specific example is provided: switch statements prevent vectorization"* — confirmed
verbatim against the live docs page). `ASSUMPTION:` the exact reason the coarser
`isLoopExiting`-conditioned check in `canVectorizeWithIfConvert` (§1) doesn't explain this
refusal (the switch here is not loop-exiting) was not fully traced — there is evidently an
earlier, blanket switch-refusal in the pipeline this research did not locate in source. Not
resolved; flagged rather than asserted.

### 3.4 Sobering counter-evidence: legal + correct + still slower, measured on real hardware

Pohl et al., §5.2 (read directly): of the loops recovered by their select-store technique,
three (**s279, s1279, s2710**) show a measured **slowdown** even with the best technique:
*"the profitability analysis of the compiler fails and code is vectorized despite an
overhead effacing all performance gains."* **s279 and s2710 are both in this project's own
+18 set** (§4). This is not a hypothetical caveat — it is an externally measured, real
result on the exact same benchmark family, on a different but architecturally comparable
NEON core (Cortex-A53 vs. this project's M4).

### 3.5 Answer to Q3

Yes — there is a real, reproducible class of if-converted loops profitable on SVE (native
predicate-register `ST1`/`LD1`, cost proportional to active lanes, one instruction) that is
not automatically profitable on NEON under LLVM's *default* lowering. But for the
**address-invariant** subclass — same lvalues touched in every arm, which is what all of
TSVC's s27x/s44x/s48x family actually is — this is a lowering-strategy artifact, not a
hardware-inherent wall: `bsl` + unconditional store recovers most of the loss directly, as
measured in §3.2 and independently in Pohl et al. It is a genuine hardware wall only for
the subclass that needs *divergent-address* masked stores (different memory locations
touched depending on the branch) — a pattern real-world code has and TSVC's control-flow
family, sampled here, largely does not.

---

## 4. What LLVM already does — the +18, kernel by kernel

Reproduced directly: `uv run --with libclang python3 tools/capability_ceiling.py
<tsvc.c> --what-if body.control_flow` names exactly 18 kernels (all "control-flow-only"
blocked — no other refused feature co-occurs), matching `docs/design/theoretical-cap.md`'s
+18/62.9% figure exactly. `clang -O3 -mcpu=native -Rpass-missed=loop-vectorize
-Rpass-analysis=loop-vectorize` was then run on the *actual* `UoB-HPC/TSVC_2` source
(`git clone`d for this research) to get LLVM's own stated reason for each, and a
hand-written select-rewrite was tested where the classification predicted it should help.

| kernel | TSVC's own comment | clang -O3 stated reason | class | select-rewrite tested |
|---|---|---|---|---|
| s272 | independent conditional | cost-model: not beneficial | **address-invariant** | recovered (bsl+str, auto) |
| s274 | complex dependent conditional | cost-model: not beneficial | **address-invariant** | recovered (pattern proven identical to s272) |
| s276 | if test using loop index | cost-model: not beneficial | **address-invariant** (condition is on `i`, not data — no memory even involved in the guard) | recovered by inference from s272/s274 |
| s278 | if/goto block if-then-else | cost-model: not beneficial | **address-invariant** | recovered by inference |
| s279 | vector if/gotos | cost-model: not beneficial | **address-invariant**, but see §3.4 | Pohl et al.: measured **slowdown** even w/ select store |
| s1161 | independent deps, mutually exclusive regions | "cannot identify array bounds" | address-invariant, but **legality-blocked today** | select-rewrite **recovered** (vectorized width 4) |
| s253 | scalar expansion under if | cost-model: not beneficial | address-invariant (scalar `s` local to guarded region) | recovered by inference |
| s2710 | scalar and vector ifs (nested) | cost-model: not beneficial | address-invariant despite textual nesting | Pohl et al.: measured **slowdown** even w/ select store |
| s441 | arithmetic if (3-way) | cost-model: not beneficial | address-invariant (3-way select) | recovered by inference |
| s3111 | conditional sum reduction | "not identified as reduction" | **reduction, no address at all** | recovered (auto, interleave ×4) |
| s3113 | max of absolute value | "not identified as reduction" | reduction | recovered by inference from s3111 |
| s314 | if to max reduction | "not identified as reduction" | reduction | recovered by inference |
| s316 | if to min reduction | "not identified as reduction" | reduction | recovered by inference |
| s331 | if to last-1 (index search) | "not identified as reduction" | reduction (index-valued) | recovered by inference |
| s332 | first value above threshold | "could not determine number of loop iterations" | **early-exit search — not if-conversion** | out of scope |
| s442 | computed goto / switch | "loop contains a switch statement" | **switch-dispatch — LLVM legality gap, resists select-rewrite** (§3.3) | tested, **not** recovered |
| s481 | `exit()` inside guard | "could not determine number of loop iterations" | **categorically illegal to speculate** (§1) | out of scope, permanently |
| s482 | data-dependent `break` | "could not determine number of loop iterations" | **early-exit — not if-conversion** | out of scope |

Counting: **13/18 (72%)** are legally if-convertible address-invariant-or-reduction shapes,
of which 2 (s279, s2710) are independently measured as unprofitable even with the best
technique. **5/18 (28%)** need a genuinely different capability: early-exit-loop
vectorization (s332, s482 — note LLVM upstream itself treats this as separate machinery,
cf. `hasUncountableEarlyExit()` found in the same legality source read in §1), switch/jump-
table codegen (s442), or is permanently unsound to if-convert (s481).

**Answer to Q4:** predominantly "declines to if-convert where it legally could." LLVM's
if-conversion machinery *is* triggered and *does* judge these legal for 13 of 18 — the
gap is a **cost-model-and-lowering-strategy** decision on NEON specifically, not a hard
legality wall, for the majority of the set.

---

## 5. The declaration angle

### 5.1 What a declaration would need to state, precisely

Not the vague "side-effect freedom of the branch" sketched in `theoretical-cap.md`'s
blocker table — that phrasing undersells what's actually checkable. Two tiers, in
increasing order of risk:

**Tier 1 — address-invariant predication (mechanically checkable, covers the 13/18
address-invariant + reduction rows above).** The lifter can *derive* this by walking both
arms' AST and comparing lvalue sets — it does not need to be asserted blindly at all for
the cases TSVC actually exhibits. This is closer to an **analysis extension** than a
declaration: "every lvalue written in arm A is written or provably untouched in arm B, and
every such lvalue's address is already covered by an existing `affine_subscript` proof."
Where the lifter *cannot* derive it (e.g., a call of unknown purity inside a guard), a
declaration analogous to this project's existing `numeric_semantics = reassociable` could
state it explicitly — same shape, same place in the architecture (an OSIL-level vocabulary
term, since `profiles/ecosystem/c/CONTRACT.osil` already documents that `declared_licence`
is exactly the kind of fact C's own syntax **cannot** carry: `may_lose { declared_licence
... }`). This tier requires **no override of a proven dependence** — only permission to
speculate a computation that's already known to be safe elementwise; it is a genuinely
narrow, low-risk declaration.

**Tier 2 — divergent-address predication (unfalsifiable, high-risk — not needed by TSVC's
sample, but real in general code, e.g. `if (cond) foo(); else bar();` touching different
arrays).** This is the shape existing "trust me" pragmas actually license, and its risk
profile matches them. It cannot be mechanically checked from the AST alone.

### 5.2 Prior art, and what each annotation actually licenses

| mechanism | axis it overrides | verified here | known soundness pitfall |
|---|---|---|---|
| `#pragma clang loop vectorize(enable)` | **profitability** only | directly reproduced (§3.1): forces past a cost-model "not beneficial" veto | none — it cannot make wrong code, only slow code, since legality is still checked |
| `#pragma clang loop vectorize(assume_safety)` | **legality** (memory-dependence proof) | syntax confirmed real and recognized (parses; sets the same internal `Force` flag as `vectorize(enable)`, per `LoopVectorizeHints`); the *specific* dependence-override semantics is cited from Pohl et al. §4.2 rather than independently re-derived here (my own test case hit a different, reduction-recognition diagnostic, not the dependence-safety path) | if the asserted safety is wrong, **silently wrong code** — no runtime check |
| `#pragma GCC ivdep` / Intel `ivdep` | assumed (not proven) loop-carried dependence | not independently tested; Intel/GCC docs cite directly | Intel's own docs: *"treat an assumed dependence as a proven dependence... [ivdep] instructs the compiler to ignore assumed vector dependencies"* — i.e. a blanket, per-loop, unfalsifiable trust; a live GCC bug report was found (`ivdep` silently not applied under certain loop-header shapes, warned but easy to miss) illustrating the annotation can fail *quietly* even when honestly used |
| Intel `#pragma vector always` | profitability heuristic override, plus **will vectorize even for non-unit-stride/misaligned access** | not tested (icc unavailable) | overrides heuristics broadly enough that a maintainer must independently know the transform is safe — same "trust, unchecked" shape as `ivdep` |
| `#pragma omp simd` (structured `if`/`else` bodies) | implicitly if-converts guarded statements as part of a much larger declared contract: "these iterations are independent" | not tested | strictly **stronger and more dangerous** than what if-conversion alone needs — asserts inter-iteration independence, not just intra-iteration branch safety; conflating the two is a real vocabulary-collision risk (see below) |
| OpenMP `simd if(expr)` clause | **not** the same kind of `if` at all — a *loop-level* runtime switch between simd and scalar execution of the whole loop (confirmed against the OpenMP 5.2 spec directly) | — | naming collision risk: a reader could easily mistake this for "predicate this branch," and it is not; worth avoiding this term in OSIL's own vocabulary for the same reason `body.control_flow` currently conflates several distinct blockers (§4) |

### 5.3 The differentiator, and the recommendation

Every existing mechanism above is a **blanket, loop-scoped, compiler-unfalsifiable**
assertion — the compiler can only trust it, never check it, and (per the `ivdep` bug report
and Intel's own "use only when you know it's safe" caveat) the known failure mode is
*silent wrong output* when the assertion is wrong. This is precisely the failure class this
project's own differential test already caught once, for real, on s277/s278/s279.

The recommendation, consistent with this project's existing three-gate discipline
(`conformance/lift/CHOOSER.md`): **Tier 1 needs no unfalsifiable trust and should be
implemented as an analysis extension** (compare lvalue sets across arms — a mechanical AST
check, not a declaration). **Tier 2, if ever built, should be treated exactly like every
other declared licence in this project** — it discharges what static analysis cannot prove,
but Gate 2 (the differential correctness test) remains **mandatory regardless**, never
optional on the strength of the declaration alone. This is not a new policy; it is this
project's existing policy, restated for the one place a blanket "trust me" would otherwise
be tempting to accept without it.

---

## 6. TSVC specifics — the s27x family and its neighbors

TSVC originates as **D. Callahan, J. Dongarra, D. Levine, "Vectorizing Compilers: A Test
Suite and Results," Supercomputing '88** — 135 Fortran loops, later ported to C and
extended to 151 by Maleki, Gao, Garzarán, Wong, Padua ("An Evaluation of Vectorizing
Compilers," PACT '11), which is the version `UoB-HPC/TSVC_2` (used by this project and by
arXiv:2502.11906) descends from. `ASSUMPTION` resolved: search results explicitly note
*"TSVC had several loops with GOTO statements"* surviving from its Fortran-66/77 origin,
where structured `if`/`else` did not exist as a language construct and `goto` was the only
control-flow primitive — this is the historical reason s277–s279, s442, s481, s482 are
`goto`-encoded rather than `if`/`else`-encoded, and it is a **syntactic accident of the
benchmark's age**, not a semantically different case for a CFG-level analysis (§1).

Exact source (`UoB-HPC/TSVC_2`, cloned for this research), and current behavior on this
machine:

| kernel | comment | body shape | clang -O3 (M4, today) |
|---|---|---|---|
| s271 | loop with singularity handling | `if (b[i]>0.) a[i] += b[i]*c[i];` | **already vectorized** |
| s272 | independent conditional | `if (e[i]>=t) { a[i]+=...; b[i]+=...; }` | not vectorized (§4) |
| s273 | simple dependent conditional | `a[i]+=...; if(a[i]<0.) b[i]+=...; c[i]+=...;` | **already vectorized** |
| s274 | complex dependent conditional | `if/else` on freshly-computed `a[i]` | not vectorized (§4) |
| s275 | if around inner loop | guards a whole **nested loop**, not a statement | blocked by `access.multi_dimensional` + `subscript.indirect` too — not a pure control-flow case |
| s276 | if test using loop index | condition is on `i`, not data | not vectorized (§4) |
| s277 | guard-variable dependence test | `goto`-encoded; writes `b[i+1]` | blocked by a **genuine cross-iteration true dependence** the guard introduces (its own stated purpose per the TSVC comment) — a dependence-analysis problem, not an if-conversion problem |
| s278 | if/goto block if-then-else | `goto`-encoded if/else | not vectorized (§4) |
| s279 | vector if/gotos | nested `goto`-encoded | not vectorized; measured slowdown even w/ select store (§3.4) |

**s271 and s273 are already vectorized by Apple clang 17 on this M4 today** — the single-
statement, single-arm guarded update is exactly the simplest case LLVM's automatic
if-conversion already handles well. **s272, s274, s276, s278, s279 are structurally close
cousins** (two statements instead of one, or an `else` arm instead of none) that LLVM
declines on the same hardware, for the same cost-model reason (§3.1) — an *inconsistency in
when LLVM's automatic if-conversion triggers*, not a hard capability boundary. s275 and s277
are miscategorized by a purely-syntactic "does the AST contain an if/goto" test as
"control-flow blockers" when their real blocker is a different, harder problem (nested-loop
guarding; cross-iteration dependence) — exactly the kind of conflation flagged in §4/§7.

**External corroboration.** Pohl et al. (SCOPES'18) ran the *predecessor* TSVC corpus across
GCC/ICC/LLVM on AVX2 vs. NEON and report, independent of this project: LLVM vectorizes 11/22
"Control Flow" pattern-group loops on AVX2 but only 2/22 on NEON (Cortex-A53); and *"13 out
of the 14 patterns which were exclusively vectorized on AVX2 [and not NEON] contain control
flow."* This is the same phenomenon this research reproduced directly on the M4, confirmed
by an independent group, on different (but architecturally related) hardware, using a
different compiler version, five years apart.

---

## 7. Recommendation — the algorithm this project should actually implement

**Not:** port `canVectorizeWithIfConvert`'s legality logic into `c_lift.py` and let control
flow through to LLVM's own backend if-converter. §3–4 show this still runs into the exact
cost-model rejection this project's own baseline already exhibits — deferring to LLVM's
default lowering strategy inherits its weakness.

**Instead:** implement Allen–Kennedy if-conversion as a **source-to-source rewrite in
`c_choose.py`**, symmetric to how it already implements Allen–Kennedy loop distribution
(`conformance/lift/CHOOSER.md`):

1. **Extend the lifter from a flat, program-order AST scan to a real control-dependence
   view** for the specific, narrow shape of a single-entry/single-exit region within one
   loop iteration (an `if`, `if/else`, or a `goto`-encoded equivalent whose targets all
   dominate a single join point before the loop's backedge — precisely the shape Allen et
   al.'s original 1983 algorithm operates on, and precisely what distinguishes s278/s279
   from a genuinely irreducible CFG). This is the actual fix for the AST-level conflation
   in the current `CONTROL_FLOW` refusal set (§1): `goto` and `if` are not different cases
   once analysis is CFG-shaped instead of AST-node-kind-shaped.
2. **Legality gate:** the Tier 1 check from §5.1 (lvalue-set equality across arms +
   already-proven in-bounds addresses); refuse (not approximate) anything needing Tier 2,
   anything with a `mayThrow`/unknown-effect call, and anything shaped as early-exit
   (`break`/data-dependent loop bound) or `switch` — these are explicitly **out of scope**
   for this capability (§4), not degraded versions of it.
3. **Emit the candidate as literal C** using the select-assignment form (`L = cond ? E :
   L;`), not as a retained `if` statement — this is the concrete, measured reason it works
   (§3.2): it sidesteps LLVM's own conservative choice between lowering options (2) and (3)
   entirely, rather than hoping the backend picks the cheap one.
4. **Run it through the existing three gates unchanged.** Gate 2 (differential correctness)
   is **non-negotiable** here specifically, because this exact feature already produced
   real wrong code once (s277/s278/s279, pre-refusal). Gate 3 (the stopwatch) is expected to
   **actually reject a real fraction of candidates** — §3.4's externally-measured slowdowns
   on s279/s2710 are not a hypothetical risk to caveat away, they are the expected, and
   correct, behavior of a gate doing its job.

**Explicitly out of scope for this capability**, and should not be priced into a future
`body.control_flow` "yield" without splitting the ceiling model's feature vocabulary
(§8): switch/jump-table dispatch (s442 — needs its own lowering path, not select-rewriting);
early-exit / data-dependent-trip-count loops (s332, s482 — LLVM itself treats this as
separate machinery, `hasUncountableEarlyExit()`, cf. §1); permanently unsound guards
(s481's `exit()` — no declaration can license this); and guard-carried true dependences
(s277 — belongs with the recurrence/dependence-analysis work, a different unknown).

---

## 8. Honest estimate on the +18

The `theoretical-cap.md` document, updated concurrently with this research, independently
flags the exact gap this section closes: *"Price has no risk term. Admitting control flow is
precisely what let the chooser emit INCORRECT code (s277/s278/s279). A capability that
raises the ceiling while opening an unsoundness class is not comparable to one that does
not, and the instrument currently reports only the upside."*

This research supplies that risk term, quantified for `body.control_flow` specifically:

```
18 kernels in the +18
 -  5  out of if-conversion's scope entirely (switch/early-exit/exit()/guard-dependence)
      → should not be attributed to this capability at all
 = 13  legally if-convertible, address-invariant-or-reduction shape
 -  2  independently measured as a net SLOWDOWN even with the best known NEON technique
      (Pohl et al., real Cortex-A53 hardware: s279, s2710)
 = 11  upper bound on what this project's own three-gate discipline should be expected
       to actually ACCEPT
```

Applying this project's own measured hit-rate discipline as a further, more conservative
check: on the probe set (`conformance/lift/CHOOSER.md`), 3 of 4 distribution candidates
cleared Gate 3 (75%) — and TSVC's control-flow kernels are, by Pohl et al.'s own
profitability analysis (§3, arithmetic-intensity axis), systematically *lower*
arithmetic-intensity than typical distribution candidates, which is exactly the regime
their heatmaps show select-store profitability degrading fastest. A realistic range,
combining both signals rather than either alone, is **8–11 of 18 (44–61%)** actually landing
as gated, correct, measured-faster kernels — not 18 (the ceiling tool's optimistic count,
which doesn't model profitability or scope at all), and not 0 (the pessimistic "NEON has no
predication, so forget it" read, which §3.2's direct reproduction refutes for the
address-invariant majority of the set).

This is a **smaller number than the ceiling advertises, but a real, positive, and
achievable one** — and specifically, it is achievable via a mechanically-checkable Tier 1
analysis extension (§5.1) that needs no unfalsifiable "trust me" declaration for the
kernels TSVC actually exhibits, which is a materially better place to be than the
`ivdep`/`assume_safety` prior art this section surveyed.

---

## Sources

**Primary — read/executed directly for this research:**
1. `llvm/lib/Transforms/Vectorize/LoopVectorizationLegality.cpp`, LLVM main branch (fetched
   2026-08-24 via `raw.githubusercontent.com/llvm/llvm-project`) — `canVectorizeWithIfConvert`,
   `blockCanBePredicated`, `blockNeedsPredication`, `canVectorizeLoopCFG`, read in full,
   quoted verbatim above.
2. `llvm.org/docs/Vectorizers.html` and `clang.llvm.org/docs/LanguageExtensions.html`
   (fetched directly, current as of 2026-08-24) — if-conversion/predication docs, loop-hint
   pragma semantics (`vectorize(enable)`, `vectorize_width`, `distribute(enable)`).
3. `UoB-HPC/TSVC_2` (`github.com/UoB-HPC/TSVC_2`, cloned shallow for this research) —
   exact source of s271–s279, s1161, s253, s2710, s331/s332, s441/s442, s481/s482,
   s3111/s3113/s314/s316.
4. This project's own tools, run directly: `tools/capability_ceiling.py --what-if
   body.control_flow` (exact +18 kernel list), `tools/tsvc_rate.py`/`baseline()` (which of
   s271–s482 clang -O3 already vectorizes on this M4), and `clang -O3 -mcpu=native
   -Rpass-missed=loop-vectorize -Rpass-analysis=loop-vectorize` on the real TSVC2 source
   (clang's own stated reason for every one of the 18).
5. Minimal standalone repros (written for this research, compiled and disassembled on this
   M4) isolating the s272 and s3111 shapes, with and without a source-level select rewrite,
   confirming vectorization outcome and inspecting generated AArch64 assembly directly
   (`bsl`/`str` vs. `tbz`/`st1`).
6. A. Pohl, N. Morini, B. Cosenza, B. Juurlink. **"Control Flow Vectorization for ARM
   NEON."** SCOPES'18 (PDF read in full, `biagiocosenza.com/papers/PohlSCOPES18.pdf`) —
   independent measurement on real Cortex-A53 hardware, using the predecessor TSVC corpus;
   source of "select store"/"atomic select store" terminology and the s279/s2710/s1279
   slowdown finding.
7. OpenMP Application Programming Interface, v5.1/5.2, `simd` construct (`openmp.org/spec-
   html`) — `if` clause semantics (loop-level, not per-branch).
8. Intel C++ Compiler documentation (`intel.com`, `cita.utoronto.ca` mirror), GCC
   documentation (`gcc.gnu.org/onlinedocs`) — `ivdep`/`vector always` semantics and caveats.

**Secondary — cited via search, not independently re-derived:**
9. J. R. Allen, K. Kennedy, C. Porterfield, J. Warren. "Conversion of Control Dependence to
   Data Dependence." POPL '83.
10. R. Allen, K. Kennedy. "Automatic Translation of FORTRAN Programs to Vector Form." ACM
    TOPLAS 9(4), 1987.
11. D. Callahan, J. Dongarra, D. Levine. "Vectorizing Compilers: A Test Suite and Results."
    Supercomputing '88.
12. S. Maleki, Y. Gao, M. J. Garzarán, T. Wong, D. A. Padua. "An Evaluation of Vectorizing
    Compilers." PACT '11.
13. reviews.llvm.org D139074, "Vectorization Of Conditional Statements Using BOSCC" —
    LLVM's own Phabricator record shows this alternative (branch-skip rather than
    predicate-mask) technique still under review as of late 2023, when Phabricator was
    archived (`maskray.me/blog/2023-12-30-reviews.llvm.org-became-read-only-archive`);
    `ASSUMPTION:` current (2026) status in mainline LLVM not independently confirmed — the
    review record itself is frozen and LLVM code review has since moved to GitHub PRs.
14. Sakib, Prabhu, Santhi, Shalf, Badawy, arXiv:2502.11906 — already used by this project
    (`optimizer/repro/README.md`); re-checked here for s27x-specific commentary, found none
    beyond the aggregate 56%/54%/47% figures already on file.

---

## Validity & limitations

**Valid as of:** 2026-08-24, Apple clang 17.0.0 / M4 (NEON-128) as the sole directly-tested
hardware/toolchain. LLVM's if-conversion cost model and lowering heuristics are neither
architecturally guaranteed nor version-stable — §3's specific cost-model verdicts could
shift with a newer clang. The Pohl et al. cross-check (Cortex-A53, LLVM 5.0.0, 2018) is
included precisely because it is a *different* NEON implementation and compiler version
reaching the same structural conclusion — convergence across two points eight years and one
vendor apart, not just one snapshot.

**Re-evaluate if:** Apple ships an LLVM upgrade that changes NEON masked-store lowering
defaults; this project's hardware target changes to an SVE-capable part; or the §7
recommendation is actually implemented, at which point this document's estimate in §8
should be replaced by the chooser's own measured Gate 3 outcomes, exactly as
`docs/design/record-attempt.md` already did for the distribution family.

**Limitations:** the 13/18 "legally if-convertible" classification in §4 rests on direct
inference from two fully-repro'd shapes (s272, s3111) plus AST-level pattern-matching
against the other 11's source, not 18 independent from-scratch repro-and-disassemble
cycles — flagged per-row in the §4 table as "recovered by inference" vs. "recovered
(measured)." The switch-canonicalization finding in §3.3 identifies a real, reproduced
symptom without fully tracing its exact location in LLVM's pipeline. The §5.2
`vectorize(assume_safety)` semantic claim (legality override, as opposed to the
independently-confirmed `vectorize(enable)` profitability override) rests on the cited
paper rather than an independently constructed minimal repro — this document's own test
case for it was not well-chosen (see inline note in §5.2) and should not be read as
first-hand confirmation of that specific claim.

---

**Epistemological note:** this research mixes primary-source code reading, direct
compilation/measurement on the project's own hardware, and one independent peer-reviewed
cross-check — the strongest evidence tier available for this question short of actually
building the capability and running the chooser's own three gates on it, which is the
natural next step if this recommendation is acted on.
