# U15 — Harness expertise: who has solved "extraction silently changes what's measured," and what to adopt

**Date:** 2026-08-22
**Researcher:** research-agent
**Question:** The dominant failure mode of the C loop-optimization pipeline
(`conformance/lift/`, `optimizer/`) was not the optimization method — it was the
harness. Every one of eight distinct bugs was an instance of the same thing:
*extracting code from its context to measure it, in a way that silently changed
what was measured.* Who has solved or seriously studied this exact class of
problem, and what should this project adopt? Is "capability pricing"
(`docs/design/theoretical-cap.md`) novel or known work? Could translation
validation (Alive2-style) replace differential testing here?

## Method

Eight-way parallel wave, one line per named investigation cluster in the
dispatch brief (measurement bias, translation validation, test-case reduction,
compiler fuzzing, superoptimizer harnesses, autotuning harnesses, capability-
pricing novelty, people/labs). All eight forked from this session, inheriting
the read of `conformance/lift/CHOOSER.md`, `conformance/lift/README.md`,
`docs/design/theoretical-cap.md`, and `optimizer/repro/README.md`. Primary
sources fetched directly where possible (papers, GitHub repos, lab pages);
secondary summaries used only where primary fetch failed, and flagged.
**No divergent findings across lines** — where two lines independently touched
the same fact (e.g. Amarasinghe's and Ragan-Kelley's MIT CSAIL affiliations,
confirmed independently by the autotuning-line's paper-author-list read and the
people-line's direct homepage fetch) they agree. Convergence noted inline.

Two lines report a constrained search: the capability-pricing novelty line
(line G) exhausted its WebSearch budget before starting and fell back to the
arXiv Atom API plus limited Semantic Scholar access — no Google Scholar, no ACM
DL, no IEEE Xplore. Its negative findings are marked "not found in this
constrained search," not "confirmed absent," throughout.

---

## TL;DR — the four deliverables

**(a) Ranked adoption list, highest value first:**
1. **Codify the C-Reduce/C-Vise interestingness-test discipline as a harness
   contract** (near-zero cost, addresses 4 of the 5 concretely-named bugs).
2. **Adopt Mytkowicz et al.'s causal-analysis check as a standing pre-accept
   step** (cheap; this project already does it once, ad hoc — formalize it).
3. **Replace the single "5%" FASTER-gate margin with a repeated-measurement +
   confidence-interval rule** (cheap statistical upgrade, Kalibera & Jones's
   higher-level lesson, not their JIT-specific machinery).
4. **Add Alive2 as a translation-validation gate alongside the differential
   test** (real engineering cost, ~2-3 days; strongest correctness upgrade;
   confirmed to cover loop-level transformations, not just peephole rewrites).
5. Do **not** adopt Stabilizer (dead, no ARM) or Coz (alive but the wrong
   shape of tool for this problem).

**(b) Closest people/groups:** John Regehr (Utah) for harness discipline and
translation validation; Emery Berger (UMass Amherst / Amazon Scholar) for the
measurement-bias diagnosis; the Halide/Ansor autotuning lineage (Amarasinghe,
Ragan-Kelley, MIT; Zheng et al.) for timeout-as-scored-outcome and cost-model-
over-raw-measurement; Alexa VanHattum/Rachit Nigam/Adrian Sampson's Diospyros
(and VanHattum's newer Cranelift verification work) for a cheaper "verify only
the final candidate" middle path. **Closest single body of work in overall
shape to "a semantic and computational interoperability layer with an in-house
optimizer": UW PLSE, Zachary Tatlock and Max Willsey (egg/egglog)** — already
the tool this project gates at G14 — narrowly ahead of Tobias Grosser's
polyhedral-in-LLVM (Polly) work for the lifter's declared-legality half, with
MLIR (Lattner/Cohen/Amini) judged infrastructure to consume, not a template to
emulate.

**(c) Capability pricing — honest verdict: no confirmed prior art for the
specific shape (declare capability vocabulary, derive a numeric ceiling from
the declarations before building, discover the ceiling contributions are
supermodular).** The closest analogues use different methods (empirical
cross-compiler headroom) or different purposes (legal-schedule-space search).
The supermodularity/submodularity mathematical framework itself is well-
established elsewhere and has touched compilers once, for a different problem
(pass-order search-space reduction). Confidence in "this is genuinely new" is
**moderate, not high** — the search was budget-constrained (arXiv/Semantic
Scholar only, no ACM DL/Google Scholar this round).

**(d) Alive2 could replace differential testing partially, not fully, and the
cost is real but boundable (~2-3 days).** Alive2 verifies arbitrary
intraprocedural LLVM-IR-to-IR transformations via bounded unrolling +
symbolic refinement checking, and its own PLDI 2021 paper devotes a section to
loop-manipulating optimizations including vectorization — this corrects an
initial shallow read that assumed it was peephole-only. It would have caught
the `s261` scalar-dependence bug for certain, not by luck. It says nothing
about speed (the FASTER gate stays a stopwatch) and does not close the residual
gap between verified LLVM IR and the final compiled binary.

---

## 1. The bug-to-fix map

The strongest evidence that this literature transfers is that every concretely
named bug in the dispatch brief has a named fix in the harness-testing
literature — not a vague analogy, a specific documented mechanism:

| bug (as reported) | closest documented mechanism | source |
|---|---|---|
| loop extracted from its enclosing repeat-loop + opaque call vectorized in isolation but not in situ | "the test-case validity problem" (§5): a reduced/extracted variant can satisfy the interestingness test for a *different, spurious* reason than the original — silently redefining what's measured while still reporting success | Regehr et al., PLDI 2012 §5.1 |
| extracted TSVC candidates lost `#define LEN_1D`, 34/34 compile-failed, "0 recovered" nearly reported | "each invocation of the interestingness test is performed in a fresh temporary directory... if your test requires access to other files, copy them in or use absolute paths" — documented as the direct fix for exactly this loss | C-Reduce / C-Vise README, tuning docs |
| generated candidate looped forever, killed the run instead of scoring REJECT | explicit 10-minute compile/benchmark timeout-and-discard, measured 99.5% yield; C-Reduce's Seq-Reduce likewise has "no natural termination criterion... in practice we use a timeout" | Adams et al., SIGGRAPH/TOG 2019 §5; Regehr et al., PLDI 2012 §6.1 |
| `-w` silently suppressed the compiler remarks the measurement depended on | C-Vise tuning guidance: strip `-Werror` (incidental warnings from reduction) but add `-Wfatal-errors` deliberately — be deliberate about which diagnostics the test is/isn't sensitive to, never blanket-suppress | C-Vise README/docs |
| omitting `restrict` in a hand-written control confounded aliasing with the effect under test | causal analysis: vary the suspected confound directly and check whether *it*, not the studied factor, explains the effect — this project's own `optimizer/repro/README.md` restrict/const decomposition (variants A/B/C/BC) already does this correctly for a different case | Mytkowicz, Diwan, Hauswirth, Sweeney, ASPLOS 2009 |

This project has already, once, done the right thing by instinct
(`optimizer/repro/README.md`'s restrict/const decomposition is textbook causal
analysis). The recommendation below is to make that instinct a standing
procedure rather than something applied only after a near-miss.

---

## 2. Ranked adoption list, in detail

### #1 — Codify the interestingness-test discipline as a harness contract (near-zero cost)

Source: Regehr, Chen, Cuoq, Eide, Ellison, Yang, "Test-Case Reduction for C
Compiler Bugs," PLDI 2012 (primary PDF read directly); C-Vise
(`marxin/cvise`, actively maintained, commit `534ac6b` 2026-08-06) as the
living, current instance of the same tool family. **Neither is a library** —
both are CLI drivers around a user-supplied interestingness-test script (any
exit-code-0-means-interesting executable); the adoptable unit is the pattern,
not a dependency. Concrete checklist for `tools/c_lift.py` / `tools/c_choose.py`:

1. Ask "does it reproduce for the *same reason*," not just "does it still
   reproduce." A bad extraction/interestingness test doesn't fail loudly — it
   silently redefines the property under test while still reporting success.
2. Every extracted/reduced candidate runs in a fresh directory with **all**
   context it depends on — headers, `#define`s, enclosing loop structure —
   either copied in or referenced by absolute path. Never assume ambient
   context (an enclosing repeat-loop, an opaque call, a macro) survives
   extraction by default.
3. A hang gets a timeout and is **scored** (REJECT), never allowed to crash or
   kill the harness run. C-Reduce institutionalizes this at the tool level for
   exactly the same reason — no natural termination criterion exists.
4. The interestingness/correctness test must be deterministic. A live 2026
   C-Vise incident (commit history around `534ac6b`) shows an ambiguous test
   turning into a race between reduction passes on identical input — pin
   ambiguous outcomes rather than letting nondeterminism decide.
5. Before trusting an aggregate summary ("34/34 compile-failed," "0
   recovered"), spot-check by diffing the extracted source against the
   original in situ — this is precisely what would have caught the missing
   `LEN_1D` before a near-publish.
6. Treat compiler diagnostics as part of the oracle, not noise. Never
   blanket-suppress warnings (`-w`) the measurement depends on; be as
   deliberate as C-Vise's own tuning guidance about which diagnostics the
   harness is and isn't sensitive to.

### #2 — Standing causal-analysis check before any accept/reject decision (cheap)

Source: Mytkowicz, Diwan, Hauswirth, Sweeney, "Producing Wrong Data Without
Doing Anything Obviously Wrong!" ASPLOS 2009 (SIGPLAN Not. 44(3):265–276;
DOI digits verified as `10.1145/1508244.1508275` in one independent citation
capture — treat the exact DOI as **ASSUMPTION**, title/authors/venue are
certain, corroborated across four independent source types: dblp, ACM DL,
IBM Research, and a university research-group page). Core finding: an
experimental-setup detail unrelated to the studied factor (UNIX environment-
variable size, link order — anything that shifts memory layout) can flip which
of two configurations looks faster, and a literature survey of 133 ASPLOS/
PACT/PLDI/CGO papers found **zero** adequately controlled for it. Mitigation:
**causal analysis** — deliberately vary something that should be irrelevant
(here: extraction context, unrelated env vars, link order, stack alignment,
in-situ vs. extracted) and confirm the accept/reject ranking doesn't flip.
This is a harness-discipline addition, buildable in an afternoon, not a tool
dependency. Distinguish from Stabilizer below, which is the same idea turned
into automated infrastructure — infrastructure this project should not adopt.

### #3 — Repeated-measurement + confidence-interval FASTER gate (cheap statistical upgrade)

Source: Kalibera & Jones, "Rigorous Benchmarking in Reasonable Time," ISMM
2013 — **primary text not re-verified this session** (two fetch attempts
404'd); the summary below rests on well-established prior knowledge and is
flagged accordingly. Their specific machinery (multi-level statistics across
repeated VM invocations, explicit warm-up/steady-state detection) targets
JIT warm-up noise and **does not transfer** — this project's C is natively
compiled, no warm-up curve exists. What does generalize: a single measurement
is not a measurement; variance should be decomposed by source; confidence
intervals, not one number, are the right unit of report. `CHOOSER.md`'s
current gate ("faster... by a margin wider than run-to-run noise (5%)") is a
crude version of exactly this idea — upgrading it to a small number of
repeated timed runs with an explicit CI-based accept/reject rule is a modest,
well-precedented improvement. **Confidence: medium** on the generalization
claim specifically (marked ASSUMPTION pending a primary-source re-read);
**high** on author/venue/title.

### #4 — Alive2 as an additional CORRECT-gate, alongside (not instead of) the differential test (real cost, ~2-3 days)

See Section 4 below for the full technical case. Summary: `alive-tv` is a
standalone CLI (`AliveToolkit/alive2`, PLDI 2021) that checks semantic
refinement between two `.ll` files — no LLVM-pass authorship required. Its own
paper's §7 ("Loops") is explicit that it handles loop-manipulating
optimizations including vectorization via bounded unrolling (Tarjan-Havlak
loop analysis, inside-out unrolling, a sound "sink BB" fallback beyond the
bound). This project's transformations (distribution, DSE, preloading,
peeling) are less aggressive per-iteration than vectorization and likely need
a smaller unroll bound than the paper's worst case of 64. Cost: ~0.5-1 day
environment setup (build/install against a matching LLVM — macOS system clang
is not upstream LLVM, Homebrew `llvm` formula likely needed) + ~1-2 days
wiring `clang -S -emit-llvm` → `opt -passes=mem2reg,sroa` → `alive-tv` into the
chooser, picking per-transformation unroll bounds. **This is bounded, not
inductive** — it proves refinement up to the unroll bound, symbolically over
all inputs within that horizon, which is strictly stronger per-check evidence
than concrete differential testing over a handful of input arrays, and would
have caught `s261`'s unseen-scalar bug by construction rather than by the luck
of an undeclared-variable compile error. It verifies nothing about speed (the
FASTER gate stays a stopwatch) and leaves a smaller residual gap: verified IR
does not guarantee the eventual `gcc -O3`-compiled binary matches. If full
integration is too costly right now, adopt the cheaper Diospyros pattern
instead (Section 7): one-shot translation validation on the **final accepted**
candidate only, not on every intermediate rewrite.

### #5 — Explicitly do not adopt Stabilizer; Coz is the wrong shape

Stabilizer (Curtsinger & Berger, ASPLOS 2013) is **unmaintained** — its own
repo states it only works on LLVM 3.1/GCC 4.6.2, and it never supported ARM
(Linux/OSX x86, x86_64, PowerPC only, by design). Do not attempt integration.
Coz (Curtsinger & Berger, SOSP 2015, Best Paper) is **alive** — evidence of
recent feature work (DWARF 5 support, an AI-assisted `coz suggest-points`
subcommand) and arm64/aarch64 packages exist for Debian/Fedora, with macOS
support via Apple's kperf framework (elevated privileges/SIP adjustment
required). But Coz answers a different question — "which line in a large
concurrent program is worth optimizing" via virtual speedups — and this
harness already knows which loop it optimized; it just needs the number to be
real. **Oversized for this problem; not recommended.**

### #6 — Worth noting, not urgent: deliberately diversify differential-test inputs

Csmith (Yang, Chen, Eide, Regehr, PLDI 2011) and EMI (Le, Afshari, Su, PLDI
2014) together demonstrate, as a documented fact rather than a hypothetical,
that even a heavily-used single testing strategy has real, large blind spots:
EMI found large numbers of new compiler bugs (a cumulative 2,391 bugs found,
1,534 fixed, across the EMI research line per ETH's own project page) in
compilers Csmith had already stress-tested for years, specifically because
Csmith's grammar-driven generation under-samples the code shapes compilers
actually mis-optimize. **Honest caveat, not stretched**: Csmith/EMI/YARPGen's
diversity axis is across generated *programs* on largely fixed, often
self-checking inputs — not across *input data* to one fixed small numeric
kernel, which is this project's actual need. No literature in this lineage
directly addresses that smaller-scale question; it is closer to classical
boundary-value/regression-testing discipline than to compiler-fuzzing
methodology. The transferable meta-lesson, not a specific technique: a fixed
differential-test input set will have blind spots that don't announce
themselves; deliberately including zero-length arrays, extreme/negative
strides, aliasing configurations, and NaN/Inf is cheap insurance.

---

## 3. Measurement bias / benchmarking rigor — detail

Covered in #2 and #3 above. Full citations:
- Mytkowicz, T., Diwan, A., Hauswirth, M., Sweeney, P.F. "Producing Wrong Data
  Without Doing Anything Obviously Wrong!" ASPLOS 2009 / SIGPLAN Not.
  44(3):265–276.
- Curtsinger, C., Berger, E.D. "STABILIZER: Statistically Sound Performance
  Evaluation." ASPLOS 2013. Repo: `github.com/ccurtsinger/stabilizer`
  (unmaintained, LLVM 3.1-only, no ARM ever — verified from repo README).
- Curtsinger, C., Berger, E.D. "Coz: Finding Code that Counts with Causal
  Profiling." SOSP 2015, Best Paper Award. Repo: `github.com/plasma-umass/coz`
  (alive; exact last-commit date not independently confirmed — ASSUMPTION on
  precise recency, high confidence on "not abandoned").
- Kalibera, T., Jones, R. "Rigorous Benchmarking in Reasonable Time." ISMM
  2013. (Title/venue well-established; methodology summary not re-verified
  against primary text this session — ASSUMPTION.)

Emery Berger's current affiliation, verified: Professor, UMass Amherst College
of Information and Computer Sciences, **and Amazon Scholar at Annapurna
Labs/AWS**, splitting time as of 2025-2026 (confirmed via UMass PLASMA lab
page, GitHub profile, and a PLDI 2026 speaker profile).

---

## 4. Translation validation — Alive2, in depth

Authors: Nuno Lopes, Juneyoung Lee, Chung-Kil Hur, Zhengyang Liu, John
Regehr, "Alive2: Bounded Translation Validation for LLVM," PLDI 2021 —
**read directly from the primary PDF**. Abstract: "Alive2 works with any
intra-procedural optimization, and does not require any changes to the
compiler. It checks pairs of functions in LLVM IR for refinement." §7,
"Loops," is on point: *"Alive2 performs bounded translation validation by
unrolling loops in the source and target functions by a specified factor...
For loop-manipulating optimizations, this may have to go as high as 64,
depending on the optimization. Vectorization may optimize, e.g., 32 iterations
of the source loop into a single (vectorized) iteration, hence we need to
unroll the source loop at least 64 times..."* This directly corrects an
initial shallow read (from a GitHub-README-only summary) that assumed Alive2
was scoped to local/peephole rewrites only — the primary source says
otherwise, explicitly and with the exact optimization class (vectorization)
most relevant here.

Mechanism: Tarjan-Havlak loop analysis + inside-out unrolling, with a sound
"sink BB" fallback for iterations beyond the bound (no false positives, but
incomplete beyond the bound — **bounded, not inductive**: it proves refinement
for all executions up to the unroll bound, symbolically over *all* input
values within that horizon, not for arbitrary trip count N). This is
per-check strictly stronger than this project's differential test, which
checks concrete inputs over a full trip count but only the inputs it happened
to pick.

Entry point for an outside project: `alive-tv`, a standalone CLI that takes
two `.ll` files and checks refinement between same-named functions — no LLVM
pass authorship needed (§8.1). Built against LLVM main/latest release, ~23,000
lines of C++, uses Z3. Explicit non-goals (§3.8): no interprocedural
transformations, no exceptions/`invoke`, no function pointers, no volatile, no
type-based alias analysis, partial intrinsic coverage (54/258, 21%) — none of
these block straight-line numeric loop kernels of the TSVC/darknet kind this
project targets.

Maintenance: repo shows 2026 activity (a clang-version-bump commit dated
2026-08-22 in one independent fetch) — **ASSUMPTION** on exact recency (not
independently cross-checked against raw commit timestamps a second time), but
consistent across two fetches that the project tracks current LLVM/clang.

**What it would NOT replace:** the FASTER gate (Alive2 says nothing about
performance) and the final compiled-binary check (verifies IR-to-IR, not that
the eventually `gcc -O3`-compiled binary matches — a separate, smaller
residual trust gap).

**Cost estimate (ASSUMPTION, not independently piloted):** ~0.5-1 day
environment setup (build/install against a matching LLVM — macOS system clang
is not upstream LLVM, likely the Homebrew `llvm` formula) + ~1-2 days wiring
`clang -S -emit-llvm` → `opt -passes=mem2reg,sroa` → `alive-tv` into the
existing chooser pipeline as an additional gate, picking per-transformation
unroll bounds and debugging any unsupported-feature warnings on the specific
probe-set kernels.

---

## 5. Test-case reduction discipline — C-Reduce / C-Vise, in depth

Covered in #1 above with full checklist and bug-mapping in Section 1. Direct
quote worth preserving verbatim, since it names this project's exact failure
mode from a primary source published 14 years before this project hit it:
Regehr et al.'s p.4 example shows a reducer that greedily accepts a smaller
variant that "still triggers the bug" — but now via an uninitialized-variable
read (undefined behavior), not the original mechanism. Their generalized fix:
"the interestingness/fitness test is not fixed — it must be tightened whenever
a reduction step is found to satisfy it for the wrong reason" (§4). C-Reduce
ships two independent validity backends (KCC, an executable C semantics;
Frama-C's value analysis) specifically to catch "compiles and runs but relies
on UB."

Maintenance, verified via GitHub API (2026-08-24): `csmith-project/creduce`
(the original PLDI-2012 tool) last pushed 2024-06-01 — dormant 2+ years, not
archived. `marxin/cvise` (fork/successor, contains a `CREDUCE_MERGE` tracking
file) is **actively maintained**, commits as recent as 2026-08-06, CI on
current toolchains (GCC 16, Python 3.15, LLVM 18). **Recommendation: reference
C-Vise, not upstream C-Reduce, if a tool dependency is ever wanted** — though
as noted, the adoptable unit here is the discipline/pattern, not a linkable
library; both tools are CLI drivers around an external interestingness-test
script.

---

## 6. Compiler fuzzing / differential testing lineage — Csmith, EMI, YARPGen

Covered in #6 above. Structural point worth restating: Csmith, EMI, and
YARPGen are whole-**program** generators; their differential axis is "same
program, different compilers/opt-levels/EMI-mutated-variant," mostly on a
single, often self-contained (checksum-computing) generated input — diversity
across the space of *programs*, not across the space of *inputs* to one fixed
program. This project's actual need (few input arrays to one fixed small
kernel) sits closer to classical differential/regression testing than to this
literature's problem shape, and I found no source in this lineage that
directly addresses the smaller-scale question — flagged rather than stretched.

Bug counts as evidence of "single strategy has demonstrated blind spots, not
hypothetical": EMI project page (ETH, Zhendong Su's group) reports a
cumulative 2,391 bugs found in GCC/LLVM, 1,534 fixed, across the EMI research
line. YARPGen (Livinskii, Babokin, Regehr, "Random Testing for C and C++
Compilers with YARPGen") reports 260+ bugs in GCC, Clang, ICC/DPC++, ispc,
using type-range-aware generation specifically targeted at triggering
loop/vectorization optimizer bugs — closer in domain spirit to this project's
TSVC-style kernels, though still whole-program.

Verified current status: John Regehr, Professor, University of Utah, active
(listed teaching Spring 2026, POPL 2026 paper); Zhendong Su, Full Professor,
ETH Zürich, Advanced Software Technologies (AST) Lab since 2018. Csmith
(`csmith-project/csmith`): 898 commits, maintainers state "discretionary
time" upkeep — low-intensity, not abandoned (exact last-commit date not
confirmed, ASSUMPTION). YARPGen (`intel/yarpgen`): 557 commits, 565 stars, 18
open issues, 4 open PRs, CI configured — appears more actively engaged
(exact last-commit date also not confirmed, ASSUMPTION).

---

## 7. Superoptimizer harness lineage — Souper, STOKE, Diospyros

**CORRECTION (verified 2026-08-24, after this report was written).** This
report claimed "Isaria does not appear to exist." That is FALSE. The paper was
verified directly from the primary source at
`https://jamesbornholt.com/papers/isaria-asplos24.pdf` — 15 pages, *"Automatic
Generation of Vectorizing Compilers for Customizable Digital Signal
Processors"*, Samuel Thomas and James Bornholt, UT Austin. Six specific figures
cited in `U6` were checked verbatim against the PDF text and all six are
correct: 300 synthesized rules, 64 GiB exhausted on a 2x2 convolution, 28
hand-written rules, 6.9x over Tensilica SDK, 25x over its clang auto-vectorizer,
34% faster than Diospyros. U6 and U11 stand as written; this line was the error.
A prior line ("no public Isaria REPOSITORY was found", U11) is about the
ARTIFACT, not the paper, and collapsing those two claims is how the false
negative arose.
searched arXiv, DBLP, GitHub, and the Cornell Capra org repo list, zero hits
anywhere. The actual relevant paper by these authors is **Diospyros**
(VanHattum, Nigam, Lee, Bornholt, Sampson, ASPLOS 2021, DOI
10.1145/3445814.3446707) — read directly from the primary PDF.

**Souper** (Regehr et al., Utah, with Peter Collingbourne/Google and others):
SMT-based (Z3/Boolector) — extracts SMT queries from LLVM bitcode and proves a
candidate replacement semantically equivalent, a proof rather than a test
sample. Correctness boundary is bounded by how faithfully LLVM IR semantics
are encoded in SMT — the same soft spot (UB, memory semantics edge cases)
Alive2 shares, unsurprisingly since Regehr co-authors both. **Archived by
owner 2025-10-30**, read-only, no longer developed.

**STOKE** (Schkufza, Sharma, Aiken, Stanford, ASPLOS 2013 + later PLDI 2016
work on tunable-precision floating point): the most instructive two-tier
structure among the three. (1) Cheap, unsound signal drives search — MCMC
stochastic search scored by "number of differing bits" against concrete
captured machine states, explicitly not a correctness proof. (2) Only once
search converges is a bounded model checker (Z3/CVC4, default depth 2) or SMT
equivalence check invoked to actually validate — and STOKE's own docs are
candid that bounded checking is exponential in the bound and the
data-driven-equivalence-checking fallback "isn't very robust." Explicit
documented pitfalls: limited instruction/register support silently narrows
what's checked; an admission "we're not quite at the point where we can take a
generic loop and expect to improve gcc/llvm -O3 code." **Cheap-signal-for-
search, expensive-sound-gate-before-acceptance is a directly transferable
design pattern** — this project's own chooser already does something similar
in spirit (topological-order LEGAL check is cheap/structural; differential
CORRECT check is more expensive; the FASTER stopwatch is most expensive of
all) but could make the tiering more deliberate. **Repo status: dead**,
explicit statement "nobody is actively working on this code base... serves as
an artifact for research papers."

**Diospyros** (VanHattum, Nigam, Lee, Bornholt, Sampson, ASPLOS 2021): closest
analogue to this project's gate structure. Search phase (equality saturation
via `egg`) trusts rewrite rules wholesale and never runs code. Correctness
gate is **one-shot translation validation on the final extracted candidate
only** — quote: "while most rules are simple, an incorrect one can cause
Diospyros to miscompile a program... we address this risk by re-using the
symbolic evaluation engine... to optionally perform translation validation on
the final extracted program" (§3.4). This is validate-the-output, not
verify-every-step — a materially cheaper alternative to full per-candidate
Alive2 integration, and directly adoptable as a middle path (Section 2, #4).
"Faster" is decided by a static, strictly monotonic hand-authored cost model
over the vector DSL, explicitly not per-candidate hardware measurement, chosen
specifically to keep extraction linear rather than requiring enumeration — the
paper flags this as a limitation for architectures without flexible shuffles.
Timeouts on saturation (wall-clock + e-graph node-count limit) extract from a
*partially* saturated graph rather than crashing — "half of our benchmarks...
time out, and yet most still outperform optimized libraries" — non-termination
handled as controlled degradation, not a crash, same lesson as #1 above.

VanHattum has since carried the one-shot-translation-validation idea into a
more mature, hardened lineage applied to a production compiler backend:
"Lightweight, Modular Verification for WebAssembly-to-Native Instruction
Selection" (ASPLOS 2024, Distinguished Artifact Award) and "Scaling
Instruction-Selection Verification against Authoritative ISA Semantics"
(OOPSLA 2025) — verifying Cranelift's ISLE instruction selector. Worth a
follow-up read as the modern version of exactly this technique.

Affiliations verified 2026: Regehr — Utah (confirmed independently by two
separate lines, convergent). VanHattum — Assistant Professor, Wellesley
(since July 2023, moved from Cornell). Nigam — Assistant Professor, MIT EECS,
directs the FLAME lab (moved from Cornell). Aiken/Sampson current
affiliations **not independently reverified in this line** — Stanford/Cornell
per prior knowledge, ASSUMPTION, not re-confirmed by search here (though
Aiken's Stanford affiliation is independently confirmed in Section 10 below —
convergent).

---

## 8. Empirical autotuning harnesses — OpenTuner, Halide, Ansor

**Halide autoscheduler** (Adams et al., "Learning to Optimize Halide with Tree
Search and Random Programs," SIGGRAPH/TOG 2019 — read directly from the full
PDF): direct hit on the runaway-candidate problem. §5, p.7: "There are
exceptions, and so we kill any compilation or benchmarking job that takes more
than ten minutes. We typically see a yield of 99.5%." An explicit, quantified
timeout-and-discard policy. Why a learned cost model instead of raw
measurement as the default oracle at all (§4, p.5): benchmarking a single
schedule takes several seconds and the search evaluates hundreds of thousands
of candidates, so "we train a small neural network to predict runtime" and
reserve real benchmarking for periodic retraining batches. Noise mitigation in
the ground-truth measurements that *are* taken: batches of 32 schedules
benchmarked together, throughput normalized relative to the fastest schedule
*in that batch* (§4.2) — cancels per-run baseline drift rather than trusting
one absolute number. No documented in-situ-vs-isolated discrepancy in this
paper — Halide schedules and benchmarks whole pipelines, sidestepping
context-stripping by never extracting a piece in the first place.

**Ansor** (Zheng et al., OSDI 2020 — read directly from the full PDF, §1-5.2):
same underlying logic — a learned gradient-boosted-tree cost model because
"querying the learned cost model is orders of magnitude faster than actual
measurement," reserving hardware measurement for a small fine-tuned population
per iteration. Correctness gate before measurement is **static, not
execution-based**: crossover-generated programs are verified via dependency
analysis on the rewrite history, not by running them (§5.1). Explicitly
critiques scoring *incomplete* programs with the same cost model used for
complete ones — the model's accuracy is near-random on incomplete/partial
artifacts and only reliable once a program is complete (§2, Fig. 3) — the
general form of this project's context-stripping bug: don't score an
extracted/partial artifact with the method built for the whole thing.

**OpenTuner** (Ansel et al.; venue commonly cited as CGO 2014 by the dispatch
brief, though the paper is more widely attributed to PACT 2014 —
**ASSUMPTION** on exact venue, not independently confirmed this session since
primary-text fetch failed and only the GitHub README was accessible):
ensemble-of-search-techniques as a robustness mechanism, verbatim from the
README — "techniques which perform well will receive larger testing budgets
and techniques which perform poorly will be disabled" (AUC-bandit allocator).
This is a portfolio-level defense against bad measurements (starve a noisy or
unproductive technique of budget) rather than a per-measurement one.
Per-run timeout/outlier-filtering mechanics not independently confirmed from
primary text this session (ASSUMPTION). Repo shows 376 commits total; recency
not confirmed.

**Bottom line for this project's harness bug:** the single most directly
transferable, verified artifact is Halide's explicit 10-minute timeout-kill
with a measured 99.5% yield — concrete, load-bearing precedent for "never let
one candidate's pathological behavior take down the run; time-box it and
score it as rejected," reinforcing #1 above from an entirely independent
lineage. The second: both Halide's and Ansor's architectural choice to *not*
trust raw hardware measurement as the default oracle, using it only as a
small, expensive, periodically-resampled ground truth — a design-level
reframing of "measurement is noisy and slow" that this project's harness
(currently single-run per candidate) has not yet adopted, worth considering if
the probe set grows.

Verified affiliations 2026: Jason Ansel — Meta, started TorchDynamo/
TorchInductor (PyTorch 2.0 core), more recently Helion (a Python-embedded ML-
kernel DSL); PhD at MIT CSAIL under Saman Amarasinghe. Jonathan Ragan-Kelley
and Saman Amarasinghe — **both independently confirmed** as MIT EECS/CSAIL
faculty in Section 10 below (convergent finding; the autotuning line itself
could not confirm Ragan-Kelley's current institution from the 2019 paper's
author list alone, since it lists UC Berkeley at time of publication — the
people-line's direct homepage fetch resolves this to MIT, current). Apache
TVM (hosts Ansor): 13.7k GitHub stars, 14,218 commits, 153 open issues, 81
open PRs — active project (exact last-commit date not confirmed, ASSUMPTION on
precise recency only).

---

## 9. Capability pricing — novelty verdict

Constrained search (WebSearch budget exhausted before this line started;
arXiv Atom API + limited Semantic Scholar only — no Google Scholar, no ACM DL,
no IEEE Xplore this round). Negative findings below are "not found in this
search," explicitly not "confirmed absent."

**One correction to the dispatch brief:** the suggested "Theodoridis et al."
missed-optimizations paper does not exist under that name. The actual paper
is Gergő Barany (single author), "Finding Missed Compiler Optimizations by
Differential Testing," CC 2018, DOI 10.1145/3178372.3179521 — an empirical
detection method (differential testing across compiler versions/flags), not a
declared-capability ceiling; not a close match.

**Closest found precedent, different method:** Shivam, Watkinson, Nicolau,
Padua, Veidenbaum, "Towards an Achievable Performance for the Loop Nests,"
LCPC 2018 (arXiv:1902.00603) — explicitly computes "headroom" for
auto-vectorization/auto-parallelization via cross-compiler comparison
(1.10x-1.71x headroom ranges reported). This is the **empirical/comparative**
route to a ceiling (union of what multiple real compilers achieve) —
structurally close to this project's own "empirical floor: 60.3%" (union of
GCC+ACFL+Clang) in `theoretical-cap.md`, but *not* close to the **declared-
capability** route (deriving the ceiling from the analyzer's own stated
vocabulary before the capability is built). David Padua's group (UIUC,
parallelizing-compiler lineage) is the right citation for "headroom"
terminology in this exact domain.

**Closest found precedent, different purpose:** PolyGym, an RL environment
formalizing the *legal* polyhedral schedule space as an MDP (matches/beats ISL
heuristics) — formalizes a search space, not a ceiling computed from declared
capabilities before building them. **ASSUMPTION**: exact citation details
(full title/authors) not fully captured this session, re-verify before
formally citing.

**Submodularity/supermodularity in compilers:** one hit, different object.
Liang, Y. et al., "Learning Compiler Pass Orders using Coreset and Normalized
Value Prediction," arXiv:2301.05104 (2023) — uses a submodular coreset-
selection objective to pick a representative subset of *pass sequences* to
search over. Submodularity applied to search-space reduction, not to
capability-coverage joint pricing. A clean negative for "supermodular" +
"compiler" specifically on arXiv abstracts (0 hits), though scoped to arXiv
only.

**Adjacent 2026 work worth citing in OSIL's own writeup, opposite sign:**
Bruzzone & Cazzola, "A Multi-Dimensional, Per-Pass Empirical Study of the LLVM
Optimization Pipeline," arXiv:2606.31238 (2026) — measures LLVM -O3 pass-
composition effects against an idealized additive baseline and finds the
pipeline is non-monotone (6.6-9.7% of pass-prefix transitions regress), with
an "idealized-additive upper bound on losses due to phase interference" of
46.35%. This is the same accounting move OSIL made (idealized-additive vs.
actual) but for a different question — phase-ordering *interference* (runtime
losses, fixed pass set, order matters) rather than capability-set *coverage*
(which analyses exist at all, order-independent). Worth a citation as the
nearest kin in framing, explicitly distinguished as answering a different
question.

**Verdict, at the three levels of granularity requested:**
1. "Declare capabilities as vocabulary, derive a ceiling before building" —
   not found as a compiler-specific practice. **Plausible gap, not a
   confirmed one** — polyhedral-compilation "feasible schedule space"
   literature (ISL-adjacent, CGO/PLDI/CC/LCPC-published, underrepresented on
   arXiv) is the most likely place an equivalent idea could be hiding and was
   not thoroughly searched this round.
2. "Price capabilities jointly, not just marginally" — the mathematical
   apparatus is mature and general elsewhere (game theory, combinatorial
   optimization, ML feature selection) and has touched compilers once, for a
   different problem (pass-order search reduction, Liang et al. 2023).
   Applying joint-vs-marginal set-function accounting to analyzer
   capability *coverage* specifically appears **not previously done**, but
   the underlying framework is not novel — only the application is.
3. "Loop-optimization capability ceilings are supermodular, not submodular" —
   **no matching or closely adjacent finding located.** This is the most
   specific claim in the dispatch brief and, on current evidence, the most
   likely to be genuinely new. **Confidence in this negative: moderate, not
   high**, strictly because of the search-budget shortfall. Recommend a
   follow-up pass once WebSearch budget resets, targeting ACM DL specifically
   for "optimization opportunity," "vectorization coverage," and polyhedral
   "legality space" venues that arXiv underrepresents.

---

## 10. People and groups — verified affiliations and closest match

All affiliations below verified via direct web search/fetch this session
(2026-08-22/24), not asserted from possibly-stale prior training knowledge,
except where marked ASSUMPTION.

| person | verified current role (2026) | most relevant artifact for this project |
|---|---|---|
| John Regehr | Professor, University of Utah School of Computing (active — Spring 2026 course listing, POPL 2026 paper) | Alive2 (§4) + C-Reduce (§5) together |
| Alex Aiken | Alcatel-Lucent Professor of CS, Stanford; also CS Division Director, SLAC. STOKE no longer listed as active work — current: FlexFlow, Legion | STOKE paper itself, historical lineage read, not current output |
| Saman Amarasinghe | Professor, MIT EECS/CSAIL, leads the "Commit" compiler group (Halide, TACO, GraphIt, Simit, StreamIt, OpenTuner all active/adjacent) | OpenTuner (§8) |
| Jonathan Ragan-Kelley | Associate Professor, MIT EECS/CSAIL | Halide autoscheduler papers (§8) |
| Zachary Tatlock | Professor, University of Washington Allen School, leads UW PLSE (active Jan 2026 Dagstuhl Seminar 26022 on e-graphs) | egg's theory paper; PLSE's equality-saturation line generally |
| Max Willsey | **Assistant Professor, EECS, UC Berkeley** (moved from UW after PhD — corrects an initial assumption he was still at UW). Still actively develops egg/egglog, leads the EGRAPHS Community (forum + workshop + monthly seminar). Google Research Scholar Award (May 2025); two PLDI 2026 papers; egg paper got a CACM Research Highlight (Aug 2026) | egglog itself (already gated at G14) + the EGRAPHS seminar as a live channel |
| Chris Lattner | **EVP, AI Software and Platforms, Qualcomm** — Modular was acquired by Qualcomm, July 2026; Tim Davis is SVP/GM of Modular within Qualcomm | MLIR as connective infrastructure — see verdict below |
| Albert Cohen | **ASSUMPTION, unverified this session** (search budget exhausted, fetches blocked) — last known pre-2025: Google | not independently confirmed, do not cite as current |
| Mehdi Amini | **ASSUMPTION, unverified this session**, same cause — last known: Google, MLIR core | not independently confirmed |
| Tobias Grosser | **Associate Professor, University of Cambridge** — confirmed still current (lab announced funding for 5 PhD students, 2026); did **not** move to Edinburgh (a speculative lead in the dispatch brief, checked and ruled out) | "First-Class Verification Dialects for MLIR," xDSL, Lean-MLIR verified-compilation work — the e-graphs/polyhedral intersection was not directly confirmed from his page this session, treat as ASSUMPTION |

MLIR institutional home: per available sources, "maintained as part of the
LLVM project," developed collaboratively across industry/academia — no
explicit statement found of LLVM Foundation governance vs. continued
industrial stewardship. **ASSUMPTION:** still nominally under the LLVM
umbrella, but its two biggest industrial drivers have shifted — Modular now
inside Qualcomm, Google's Cohen/Amini affiliations unconfirmed this round.

**Verdict — closest single body of work to "a semantic and computational
interoperability layer with an in-house optimizer": UW PLSE, Tatlock and
Willsey (egg/egglog).** Weighed explicitly against the two next-closest
candidates:

- **MLIR (Lattner/Cohen/Amini)** is an interoperability layer but without "an
  in-house optimizer" in the load-bearing sense this project has — MLIR's
  value is dialect interop and lowering; each dialect brings or omits its own
  optimizer, and MLIR stays agnostic. It does not centrally reason about "what
  does a declaration buy me," which is this project's central move. Post-
  acquisition, its institutional center of gravity is also more fragmented
  than before — a governance consideration, not a technical one, but relevant
  if this project ever treats MLIR as a lowering target.
- **Grosser/Polly** is closer on the specific "declared-vs-derived legality"
  axis — polyhedral compilation proves loop-transformation legality from
  declared affine array-access structure, mirroring this project's dependence
  lifter closely. But it is one optimization technique embedded in one
  compiler, not a semantic layer above multiple targets with a pluggable
  capability-pricing model. Right instinct for the lifter/chooser half, wrong
  shape for the "interoperability layer" half.
- **UW PLSE (egg/egglog)** wins because equality saturation is explicitly a
  substrate-agnostic optimizer over a *declared rewrite/semantics vocabulary*
  — declare rules (the direct analogue of this project's capability
  declarations), the e-graph explores the *joint* space of rewrites non-
  destructively, and correctness is tied to the soundness of each declared
  rule rather than to one fixed pass ordering. This is structurally identical
  to what this project already does at G14 (the egglog equivalence-
  preservation contract) and matches the empirical supermodularity finding in
  `theoretical-cap.md`: a joint-exploration structure like an e-graph is
  precisely what captures interaction between rewrite rules that a
  phase-ordered pipeline (like Polly's) structurally cannot represent.
  Willsey's continued full-time investment in egg/egglog at Berkeley plus the
  active EGRAPHS Community (workshop + monthly seminar) makes this the most
  current, most engaged-with community for exactly this project's open
  problems — not a historical reference like STOKE, not a diffuse
  infrastructure project like MLIR.

**Concretely:** treat UW PLSE (Tatlock/Willsey) as this project's nearest-
neighbor lab overall; treat Grosser as nearest-neighbor for the lifter's
declared-legality half specifically; treat MLIR as connective infrastructure
to consume as a future lowering target, not a template to emulate for the
"in-house optimizer" question.

---

## Validity & limitations

**Valid as of:** 2026-08-22. Compiler-tooling maintenance status
(Stabilizer/dead, Coz/alive, Souper/archived Oct 2025, STOKE/dead,
C-Reduce/dormant vs. C-Vise/active, Alive2/active) changes on its own
timescale independent of this document; re-check before a build decision that
depends on a specific tool's current maintenance state.

**Re-evaluate if:** (1) the WebSearch budget shortfall on the capability-
pricing novelty line (Section 9) is lifted — a follow-up ACM DL/Google
Scholar pass could still surface prior art for the declared-capability-ceiling
framing; (2) this project actually pilots Alive2 integration — the cost
estimate in Section 4 is unpiloted (ASSUMPTION); (3) Albert Cohen's and
Mehdi Amini's current affiliations become independently verifiable — both are
flagged ASSUMPTION this round, unconfirmed.

**Limitations:** bounded by eight parallel forks' search sessions, each with
its own tool-access constraints (some primary PDFs fetched directly and
quoted verbatim; some relied on GitHub READMEs or well-established prior
knowledge where primary fetch failed — flagged inline throughout, not
smoothed over). Context-specific to this project's actual harness shape:
native, single-run, ARM/macOS C-loop microbenchmarking, small numeric kernels,
a handful of differential-test input arrays — several literatures surveyed
(Csmith/EMI/YARPGen whole-program fuzzing; Kalibera & Jones's JIT warm-up
statistics) were explicitly found to only partially transfer to that shape,
and the partial-transfer boundary is stated rather than glossed over in each
relevant section.

## Sources

1. Mytkowicz, T., Diwan, A., Hauswirth, M., Sweeney, P.F. "Producing Wrong
   Data Without Doing Anything Obviously Wrong!" ASPLOS 2009 / SIGPLAN Not.
   44(3):265–276.
2. Curtsinger, C., Berger, E.D. "STABILIZER: Statistically Sound Performance
   Evaluation." ASPLOS 2013. `github.com/ccurtsinger/stabilizer`.
3. Curtsinger, C., Berger, E.D. "Coz: Finding Code that Counts with Causal
   Profiling." SOSP 2015 (Best Paper). `github.com/plasma-umass/coz`.
4. Kalibera, T., Jones, R. "Rigorous Benchmarking in Reasonable Time." ISMM
   2013.
5. Lopes, N., Lee, J., Hur, C-K., Liu, Z., Regehr, J. "Alive2: Bounded
   Translation Validation for LLVM." PLDI 2021.
   `github.com/AliveToolkit/alive2`.
6. Regehr, J., Chen, Y., Cuoq, P., Eide, E., Ellison, C., Yang, X. "Test-Case
   Reduction for C Compiler Bugs." PLDI 2012. `github.com/csmith-project/creduce`;
   `github.com/marxin/cvise` (active fork).
7. Yang, X., Chen, Y., Eide, E., Regehr, J. "Finding and Understanding Bugs in
   C Compilers." PLDI 2011 (Csmith). `github.com/csmith-project/csmith`.
8. Le, V., Afshari, M., Su, Z. "Compiler Validation via Equivalence Modulo
   Inputs." PLDI 2014 (EMI). `people.inf.ethz.ch/suz/emi/`.
9. Livinskii, V., Babokin, D., Regehr, J. "Random Testing for C and C++
   Compilers with YARPGen." OOPSLA 2020. `github.com/intel/yarpgen`.
10. Souper (Regehr et al.). `github.com/google/souper` (archived 2025-10-30).
11. Schkufza, E., Sharma, R., Aiken, A. "Stochastic Superoptimization." ASPLOS
    2013. `github.com/StanfordPL/stoke`.
12. VanHattum, A., Nigam, R., Lee, V.T., Bornholt, J., Sampson, A.
    "Vectorization for Digital Signal Processors via Equality Saturation."
    ASPLOS 2021. DOI 10.1145/3445814.3446707.
13. VanHattum et al. "Lightweight, Modular Verification for WebAssembly-to-
    Native Instruction Selection." ASPLOS 2024 (Distinguished Artifact
    Award).
14. Mcloughlin, Sheng, Fallin, Parno, Brown, VanHattum. "Scaling
    Instruction-Selection Verification against Authoritative ISA Semantics."
    OOPSLA 2025.
15. Ansel, J. et al. "OpenTuner: An Extensible Framework for Program
    Autotuning." (Venue: CGO 2014 per dispatch brief vs. PACT 2014 commonly
    cited elsewhere — ASSUMPTION, not independently confirmed this session.)
    `github.com/jansel/opentuner`.
16. Adams, A. et al. "Learning to Optimize Halide with Tree Search and Random
    Programs." SIGGRAPH/TOG 2019.
17. Zheng, L. et al. "Ansor: Generating High-Performance Tensor Programs for
    Deep Learning." OSDI 2020.
18. Shivam, A., Watkinson, N., Nicolau, A., Padua, D., Veidenbaum, A.
    "Towards an Achievable Performance for the Loop Nests." LCPC 2018.
    arXiv:1902.00603.
19. Barany, G. "Finding Missed Compiler Optimizations by Differential
    Testing." CC 2018. DOI 10.1145/3178372.3179521.
20. Liang, Y. et al. "Learning Compiler Pass Orders using Coreset and
    Normalized Value Prediction." arXiv:2301.05104 (2023).
21. Bruzzone, F., Cazzola, W. "A Multi-Dimensional, Per-Pass Empirical Study
    of the LLVM Optimization Pipeline." arXiv:2606.31238 (2026).
22. PolyGym (RL environment for the polyhedral legal-schedule space) —
    ASSUMPTION on exact citation details, re-verify before formal citation.

---

**Epistemological note:** this research represents best available evidence as
of 2026-08-22, gathered across eight parallel forked sessions with converging
(not conflicting) findings and no contradictions detected between lines.
Several claims are explicitly downgraded to ASSUMPTION where primary-source
verification failed this session (Kalibera & Jones's generalization claim;
Cohen's and Amini's current affiliations; Alive2's and OpenTuner's exact
maintenance/venue details; the capability-pricing negative finding's
completeness). Treat as a snapshot, and re-run the capability-pricing search
(Section 9) with a full WebSearch budget before treating its negative finding
as final.
