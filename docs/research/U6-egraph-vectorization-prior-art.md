# U6 — E-graph Loop Vectorization: Prior Art and the Binder Problem

**Date:** 2026-08-24
**Researcher:** research-agent
**Question:** Can OSIL's scalar-only egglog term language (`grammar/osil.ebnf` lines 144–146; `Num` sort in `tools/egraph_roundtrip.py`) be extended to express loop vectorization (`for i in range(n): r[i] = x[i]*2  <=>  r = x*2`) given that equality saturation rewrites ground terms, and a vectorization rule is quantified over the loop's bound index variable?

**Naming note (flag, not resolved here):** `docs/intake/synthesis-repo-organization.md` already used the id "U6" for a different, never-written unknown ("Capability-claim verification: MLIR dialect metadata persistence, StableHLO compatibility guarantees, TVM search claims"). That U6 has no file in `docs/research/`. This document answers the *vectorization* question the orchestrator dispatched under the same id. Whoever next touches the U-ledger should either renumber one of the two or fold the capability-claim question into this document's scope — flagged, not silently resolved.

## Method (wave decomposition)

Default line I would have run: "read the Diospyros and Glenside papers, summarize their IRs." Simulated finding: both papers described as doing "vectorization via equality saturation over tensor-like terms" — true but too coarse to answer OSIL's actual question, which is specifically about **what happens to the bound loop index at the moment a term enters the e-graph**. Gaps relative to that question, to OSIL's actual constraints (egglog, not egg; a spec that must ship a grammar production + corpus example for anything it adds — CLAUDE.md rule 3; ADR-0009's already-closed egg-vs-egglog decision), and to the user's higher-order goal (a *concrete, skeptical* verdict, not a survey):

- Gap A — **exact term grammar**: does Diospyros's e-graph ever contain a node representing "the loop", or is the loop gone before saturation starts? → primary-source PDF read, not abstract-only.
- Gap B — **Glenside's access-pattern encoding precisely enough to implement**, and its hard edges (what shapes of computation the formalism cannot express) — the CartProd/windows/reduce combinators are the leading "maybe this is the ground-term trick" candidate and deserved a from-the-paper, not from-a-summary, answer.
- Gap C — **is there a General Theory of this** (the binder problem, independent of any one paper) — slotted e-graphs, de Bruijn-in-egg, and whether the field has since produced a reusable mechanism rather than one-off avoidance tricks.
- Gap D — **currency**: everything above is 2021. Four to five years is a long time in this sub-field; EGRAPHS 2022–2026 and MLIR+eqsat work needed checking on their own terms, not assumed unchanged.
- Gap E — **OSIL's own already-closed decision (ADR-0009/U5)**: does any of this change the egg-vs-egglog calculus specifically for arrays/loops, or is it orthogonal?
- Gap F — **Tensat's actual scope**, since "tensor graph superoptimization" sounds adjacent but needed a direct check for whether it is graph-level (operators as black boxes) or loop-level (rewrites inside a kernel).

Each gap below is answered from a **primary source I read directly** (PDF pages, not search-engine paraphrase) except where explicitly marked otherwise. Synthesis: **convergent** — five independent primary sources spanning 2021–2025 (Diospyros, Isaria, Glenside, the eqsat MLIR dialect, DialEgg) agree on one structural fact: *no production-quality system found solves the binder problem by making the e-graph binder-aware; every one of them eliminates the binder before equality saturation starts, or explicitly declares binder-aware loop rewriting future work.* One source (Slotted E-Graphs, PLDI 2025) is a genuine counter-example in principle but is not integrated with OSIL's chosen engine and has never been used to express vectorization. This is not a hedge — it is the paper trail's own verdict, section-by-section, cited below.

---

## 1. Diospyros (VanHattum, Nigam, Lee, Bornholt, Sampson — ASPLOS 2021)

**Source:** Alexa VanHattum, Rachit Nigam, Vincent T. Lee, James Bornholt, Adrian Sampson. "Vectorization for Digital Signal Processors via Equality Saturation." ASPLOS '21. [ACM DOI 10.1145/3445814.3446707](https://doi.org/10.1145/3445814.3446707) · [preprint PDF](https://cs.wellesley.edu/~avh/diospyros-asplos-2021-preprint.pdf). Read in full (13 pp.) directly from the PDF, not summarized.

### 1.1 The exact term language

Figure 3 of the paper gives the complete grammar, verbatim:

```
⟨prog⟩   ::= (List ⟨expr⟩+) | ⟨expr⟩
⟨expr⟩   ::= ⟨scalar⟩ | ⟨vector⟩
⟨scalar⟩ ::= ⟨integer⟩ | ⟨variable⟩
           | (+ scalar scalar) | (- scalar scalar)
           | (* scalar scalar) | (/ scalar scalar)
           | (sgn scalar) | (sqrt scalar) | (- scalar)
           | (Get ⟨variable⟩ ⟨integer⟩)
           | (⟨func⟩ ⟨scalar⟩+)
⟨vector⟩ ::= (Vec ⟨scalar⟩+) | (Concat vector vector)
           | (VecAdd v v) | (VecMinus v v) | (VecMul v v) | (VecDiv v v)
           | (VecMAC v v v) | (VecSgn v) | (VecSqrt v) | (VecNeg v)
```

This is a **flat, ground-term algebra**. There is no loop construct, no bound variable, no lambda anywhere in it. `Get(a, i)` takes a **literal integer** `i`, not a range or a symbolic index.

### 1.2 Where the loop goes — the answer to OSIL's actual question

Figure 1 of the paper (the compiler pipeline) is unambiguous: **Scalar Program → [Symbolic Evaluation] → Abstract Vector DSL → [Equality Saturation] → Optimized Vector DSL → [Backend] → C++ intrinsics.** The e-graph sits strictly *after* symbolic evaluation. Diospyros "first lifts scalar input programs into a high-level DSL via symbolic evaluation" (§3.1) using Rosette (a symbolic-execution framework for Racket) — this step **fully unrolls the loop nest and specializes it to a fixed input size**, producing a flat `(List (+ (Get a 0) (Get b 0)) (+ (Get a 1) (Get b 1)) ...)` term with one ground element per output index. Section 4 states this explicitly: *"Diospyros's compilation flow includes fully unrolling loop nests, which can create very large programs with redundant terms."*

**The binder is eliminated before the e-graph is built, not represented inside it.** Equality saturation in Diospyros never sees `i`; it only ever sees `(Get a 0)`, `(Get a 1)`, `(Get a 2)`, … as distinct ground e-nodes. This is Track A in this document's verdict (§7) — the load-bearing fact for everything downstream.

Consequently: array sizes must be **fixed at compile time**. §2 states plainly: *"Because the array sizes for our problem are fixed, a compiler could unroll the loops and apply non-loop vectorization techniques."* §6 ("Limitations & Portability") reiterates the target is small, fixed-size kernels (3×3, 4×4-scale linear algebra), not general loop nests.

### 1.3 What it demonstrated, and against what baseline

Table 1 / Figure 5 (evaluation, §5): kernels **2DConv** (sizes 2×2…16×16, filters 2×2…4×4), **MatMul** (2×2…16×16), **QProd** (quaternion product, fixed 4×3×3), **QRDecomp** (3×3, 4×4). Baselines: a naive parametric-size loop nest, a naive fixed-size loop nest, **Nature** (Tensilica's vendor-supplied DSP library), and **Eigen** (portable C++ linear-algebra template library). Target: Tensilica Fusion G3 DSP, cycle-accurate simulation (`xt-run`).

- **Geometric-mean speedup 3.1×** over the best non-expert baseline (naive/library) across the kernel suite.
- MatMul kernels: **2.7×–19.3×** faster than fixed-size naive loop nests.
- One 3×3 MatMul case: within **8%** of hand-expert-tuned code (39 vs. 36 simulated cycles), 2.7 s compile time.
- 2DConv at the motivating 3×3/3×5 example: **22.9×** over a naive fixed-size loop, **4.5×** over an optimized vendor kernel.
- QRDecomp application case study: **2.1×** faster than an Eigen-based baseline end-to-end.
- **Where it loses:** Nature (the vendor library) *beats* Diospyros on 2DConv at two sizes where input size ≥ vector width (16×16 and 10×10 inputs) — stated directly in §5.4.

### 1.4 What the paper says does NOT work / does not scale (its own words, ranked above my inference)

- **Timeouts, routinely, not as an edge case:** *"Half of our benchmarks in Section 5 timeout, and yet most still outperform optimized libraries"* (§4, "Timeouts"). A 3-minute wall-clock timeout plus a 10,000,000 e-graph-node limit are the defaults used in evaluation (§5.2). This is the paper's own headline scaling admission, not something I inferred.
- **A genuinely pathological case is shown, with a number:** QRDecomp at 4×4, fully unrolled, produces a **509 MB text file** as the "specification alone"; *"the E-graph does not saturate and it finds no vector instructions"* — the authors need a bespoke post-hoc local-value-numbering pass in the backend (not part of equality saturation) to bring the output down from >100,000 lines of C++ to under 500 (§4, "IR-level optimization"; §5.6).
- **Associativity/commutativity (AC) matching is explicitly named as an NP-complete scalability wall**, not a minor wrinkle: *"applying associative and commutative variants of such rules dramatically increases the size of an E-graph... This theoretical problem is also a scalability challenge for equality saturation in practice"* (§3.3). Diospyros's answer is to **disable general AC rules** and hand-write narrow custom `Applier`/`Condition` Rust code per operator family (e.g. the VecMAC custom searcher, §3.3) instead — i.e., the escape hatch from e-graph blowup is *bespoke matching code*, exactly the "guards are code, not data" pattern OSIL's own ADR-0009 flagged as a cost of targeting egg.
- **Input programs must have control flow and indexing independent of input data:** *"It supports arbitrarily complex indexing expressions and control flow, as long as they are independent of the input data"* (§3.1). Data-dependent branching/early exit is out by the paper's own scoping sentence.
- **An earlier SMT-based version of Diospyros (VanHattum et al. 2020) "encountered scaling issues even on small (2×2) kernels"**; the current term-rewriting version is reported to "scale to kernels 10× larger than the SMT-based version" (§7, Related Work) — i.e. even the *improved* approach is explicitly benchmarked against a predecessor that failed at trivial sizes, and the improvement factor (10×) is modest relative to how far real workloads scale.
- Explicit future work, stated in the paper's own conclusion: extending to *"more DSP targets and other esoteric customizable hardware architectures"* — the 2021 paper does not claim generality beyond the one DSP family (Tensilica Fusion G3) and small, fixed-size linear-algebra kernels it tests.

### 1.5 Code availability and license

**Available**, MIT-licensed. Source: the paper's own **Artifact Appendix**, §A.1 ("Artifact Meta-Information"): *"Code licenses (if publicly available)?: MIT License"*; archived at DOI `10.5281/zenodo.4331404`; repo `github.com/cucapra/diospyros`. Implementation: ~4,800 LOC Racket/Rosette (lifting, translation validation) + ~1,400 LOC Rust using **egg** (not egglog — egg is cited by name, §5.1: *"1,400 lines of Rust implement the rewrite rules and cost model using the egg [40] library"*).

### 1.6 Successor work: Isaria (Thomas & Bornholt, ASPLOS 2024)

**Source:** Samuel Thomas, James Bornholt. "Automatic Generation of Vectorizing Compilers for Customizable Digital Signal Processors." ASPLOS '24. [ACM DOI 10.1145/3617232.3624873](https://doi.org/10.1145/3617232.3624873) · [author PDF](https://jamesbornholt.com/papers/isaria-asplos24.pdf). Read directly (first 6 pp., which contain the term language and the scaling discussion in full).

Isaria is built **directly on top of Diospyros** and, critically for this question, **reuses the exact same ground-term DSL** — Isaria's own Figure 1 reproduces Diospyros's Figure 3 grammar verbatim (`⟨prog⟩ ::= (List ⟨expr⟩+) | ⟨expr⟩`, same `Vec`/`Get`/`VecAdd`/… constructors). Isaria's contribution is **not** a new binder mechanism; it automates the *generation* of the rewrite rules themselves (via the Ruler rule-synthesis engine, so DSP engineers don't hand-write them) and adds a *phase-ordering* scheduler for applying those rules during saturation. The loop-elimination-by-unrolling architecture is untouched — this is strong confirmation that three years of direct follow-on work by (partly) the same research group did not revisit the "is unrolling necessary" question; they treated it as settled and optimized elsewhere.

**Results:** kernels compiled by an Isaria-generated compiler outperform Tensilica SDK libraries by up to **6.9×**, and the Tensilica clang-based auto-vectorizer by up to **25×**; on average **34% faster** than Diospyros's hand-crafted compiler (the paper notes this average is skewed by a few large kernels), though compilation is on average **2.1× slower** than Diospyros's.

**New, sharper evidence on e-graph blowup, directly on point for OSIL's risk assessment:** Isaria's own §2.3 ("E-graph Explosion") reports that when the general-purpose Ruler synthesizer is applied *directly* to Diospyros's kernel language, it generates **300 candidate rewrite rules** — *"an order of magnitude larger than Diospyros's 28 hand-written rules for the same DSP"* — and naively firing all of them: *"Trying to use these rules to vectorize a small 2×2 by 2×2 2D convolution causes equality saturation to exhaust 64 GiB of memory without producing any results... it fails to find any vectorized program after an hour of searching. In contrast, Isaria finds a fast vectorized solution in only 3 seconds while using 0.2 GiB of memory."* This is a **directly measured** (not inferred) demonstration that adding array/vector rewriting to an e-graph-based system, without careful hand-curation or an automated rule-phasing mechanism, can blow the search space up by orders of magnitude even at trivial (2×2) problem sizes.

Isaria's own related-work framing of Diospyros's limitation, quoted verbatim (§2.2): *"Diospyros... does not generalize to different DSP architectures, which each need a new set of hand-crafted rules."* Code/license not independently verified in this pass — **ASSUMPTION:** not confirmed (I did not locate an Isaria artifact-appendix page in the pages read; flagged, falsifiable by reading the paper's remaining pages or its repo, if one exists).

---

## 2. Glenside (Smith, Liu, Lyubomirsky, Davidson, McMahan, Taylor, Ceze, Tatlock — MAPL/MAPS 2021)

**Source:** Gus Henry Smith, Andrew Liu, Steven Lyubomirsky, Scott Davidson, Joseph McMahan, Michael Taylor, Luis Ceze, Zachary Tatlock. "Pure Tensor Program Rewriting via Access Patterns (Representation Pearl)." MAPS '21 (co-located with PLDI). [arXiv:2105.09377](https://arxiv.org/abs/2105.09377) · [PDF](https://arxiv.org/pdf/2105.09377). Read in full (11 pp.) directly from the PDF.

### 2.1 The access-pattern encoding, precisely (implementable-level detail)

An access pattern's defining move is to characterize a tensor not by its shape alone (an n-tuple of positive integers) but by a **pair of shape-tuples** `(S_A, S_C)` — the *access* dimensions and the *compute* dimensions. An access pattern of shape `(S_A, S_C)` represents an `(|S_A|+|S_C|)`-dimensional tensor **viewed as** a tensor of shape `S_A` whose *elements* each have shape `S_C` (§4.1). This is the whole trick: "iterate over these dims, compute on those dims" is expressed as a **static shape annotation**, not as a loop with a named index.

`(access T n_A)` takes a tensor `T` and turns it into an access pattern by declaring the first `n_A` dimensions of `T`'s shape as access dims and the rest as compute dims.

**Access pattern transformers** (Table 1, quoted verbatim from the paper — this is precise enough to implement):

| Transformer | Input(s) | Output shape |
|---|---|---|
| `access` | tensor of shape `(a₀,…)`, integer `i` | `((a₀,…,aᵢ₋₁), (aᵢ,…,aₙ))` |
| `transpose` | access pattern `((a₀,…),(…,aₙ))`, permutation `ℓ` of `0..n-1` | permutes the access dims by `ℓ` |
| `cartProd` | two access patterns with matching compute shape `(c₀,…,cₚ)` | access dims concatenated, compute dims become a 2-tuple `(2,c₀,…,cₚ)` |
| `windows` | access pattern, window shape `(w₀,…,wₙ)`, strides `(s₀,…,sₙ)` | new access dims `b'ᵢ = ⌈(bᵢ-(kᵢ-1))/sᵢ⌉` (sliding-window count) |
| `slice` | access pattern, dimension `d`, bounds `[l,h]` | dimension `d`'s extent becomes `h-l` |
| `squeeze` | access pattern, index `d` where `a_d = 1` | removes dimension `d` |
| `flatten` / `reshape` | access pattern(s) | flattens/reshapes access or compute dims, product-preserving |
| `pair` | two access patterns of the same shape | stacks them with a new leading `2`-dim |

**Access pattern operators** (Table 2 — the *only* constructs that perform computation, and the full list, not a sample): `reduceSum : (…) → ()`, `reduceMax : (…) → ()`, `dotProd : (t, s₀,…,sₙ) → ()`. `(compute f A)` maps operator `f` over the access (not compute) dims of `A`.

**Matrix multiplication in Glenside, concretely** (§4.3, the paper's own worked example):
```
(compute dotProd
  (cartProd
    (access activations 1)
    (transpose (access weights 1) (list 1 0))))
```
This is a **fully ground term**. There is no `i`, `j`, or `k` anywhere — the contraction dimension `k` is implicit in `cartProd`'s pairing of every access-dim tuple from the first pattern with every access-dim tuple from the second, and `dotProd` collapses the matching compute dims. Convolution (`conv2d`) and max-pooling are given the same way in Figure 2 of the paper, using `windows` to materialize the sliding-window structure.

### 2.2 Why Glenside has no binder — the authors' own stated reason, and a later paper's critique

This is not incidental; it is Glenside's central design decision, stated directly in the paper (§3, discussing why they rejected adding lambdas/currying to support arbitrary-dimension operators): *"Unfortunately, these approaches all rely on some form of name binding which can significantly complicate term rewriting... While it is still technically possible to apply state-of-the-art rewrite engines like egg via explicit variable substitution rules and free variable analyses, we have found the additional complexity and rewrite search space blow up substantially eliminate the potential advantages of term rewriting in such IR designs."* Section 6 (Conclusion) restates the same point as the paper's headline contribution: access patterns let Glenside compose "higher-order tensor operators over arbitrary dimensions... **without the need for binding structures like anonymous functions or index notation.**"

A **later, independent paper's assessment of this same design choice**, given here because it is directly on point and the honest evidence-hierarchy move is to surface it rather than let Glenside's self-description stand alone: the Slotted E-Graphs paper (§1, related work — see §5 below) characterizes Glenside as avoiding "the issue of variables altogether with a combinator-only language design," quotes the same "rewrite search space blow up" sentence, and adds: *"a combinator-only language without variables has downsides in itself. Besides being often unfamiliar to users who are used to variables, it is often impractical to translate terms with variables into combinator-only style, as in the worst case it results in a term size of O(n³)"* (citing Lachowski 2018). This is a real, citable, external critique of the exact mechanism this document's user is asking about as a candidate for OSIL.

### 2.3 What Glenside cannot express

**Explicit, from the paper's own formal definitions (not a "Limitations" section — the paper does not have one; the boundary is implicit in the type system, so this is stated here as a grounded inference from Tables 1–2, not a quoted limitation sentence):**

- Every access-pattern shape (`S_A`, `S_C`, window shapes, strides, permutations) is a **static tuple of positive integers**, fixed in the term itself. Nothing in the formalism admits a shape parameterized by a runtime value — data-dependent tensor shapes are not representable by construction.
- The **only** reduction primitives are `reduceSum`, `reduceMax`, `dotProd` (Table 2, exhaustive). There is no general fold/scan and no way to express a reduction whose accumulation logic isn't one of those three fixed operators — a carried-dependency reduction with arbitrary per-step logic is not expressible.
- There is no conditional/branch construct anywhere in the grammar — control flow, let alone data-dependent control flow, is absent by omission, not by an explicit exclusion the authors call out.
- Non-affine indexing is not a meaningful question in Glenside's model at all, because there is no index notation to be affine or non-affine *in* — access patterns replace indexing with shape-typed combinators, and any computation not expressible as `access`/`transpose`/`cartProd`/`windows`/`slice`/`squeeze`/`flatten`/`reshape`/`pair` composed with `reduceSum`/`reduceMax`/`dotProd` (the complete operator vocabulary) is simply outside the language.

### 2.4 Demonstrated results

§5: **im2col rediscovery** — Figure 4/5 shows three general rewrites (an "exploratory" flatten-then-reshape rewrite plus two composition-commutativity rewrites) that, applied by equality saturation with **no phase ordering needed**, automatically derive the im2col data-layout transformation for `conv2d` from generic rules not specific to convolution. **Systolic-array mapping** (§5.2): a single rewrite rule (Figure 3) maps a `(compute dotProd (cartProd …))` pattern directly to a `systolicArray` accelerator-invocation term. **MatMul blocking** (§5.4): six generic rewrites (slice/concat bubbling) automatically discover the standard blocked-matrix-multiply decomposition (e.g. splitting a 32×32 matmul into eight 16×16 matmuls), shown concretely in Figure 7. All three case studies use **egg** (cited by name, §5, footnote/refs), not egglog (egglog did not exist as a published system until 2023).

### 2.5 Code, license, currency

Repo: `github.com/gussmith23/glenside` (footnote 1 of the paper: "Publicly available at https://github.com/gussmith23/glenside"). **Verified via the GitHub API directly** (`api.github.com/repos/gussmith23/glenside`, fetched this session): `"license": null` (no LICENSE file in the repo) and **`"archived": true`** — the repository was archived (made read-only) 2025-05-30. This is a mechanically-checked fact, not inference: Glenside is **unmaintained and has no stated open-source license** as of this research date, which materially weakens it as a code base OSIL could build on or even cite as a currently-usable artifact (as distinct from citing the paper's ideas, which remains valid).

---

## 3. Tensat (Yang, Phothilimthana, Wang, Willsey, Roy, Pienaar — MLSys 2021)

**Source:** Yichen Yang, Phitchaya Mangpo Phothilimthana, Yisu Remy Wang, Max Willsey, Sudip Roy, Jacques Pienaar. "Equality Saturation for Tensor Graph Superoptimization." MLSys 2021. [arXiv:2101.01332](https://arxiv.org/abs/2101.01332) · [PDF](https://arxiv.org/pdf/2101.01332). Read directly (first 6 pp., covering the term language, scope, and results tables in full).

**Scope, precisely: Tensat is graph-level, not loop-level, and this is a structural fact of its representation, not a stated non-goal.** Table 2 (the complete operator table) lists **21 operators**: `ewadd`, `ewmul`, `matmul`, `conv`, `relu`, `tanh`, `sigmoid`, `poolmax`, `poolavg`, `transpose`, `enlarge`, `concat_n`, `split`/`split₀`/`split₁`, `merge`, `reshape`, `input`, `weight`, `noop`. Every operator's type signature is `(T,...) → T` (whole tensors in, whole tensors out) — **`matmul`, `conv`, etc. are opaque, atomic nodes**; there is no decomposition of what happens *inside* a matmul or convolution into loop/index-level terms anywhere in the representation. §3.1: *"Each tensor computation graph is a DAG"* under this representation, and the e-graph is built directly over this DAG (§4). There is no lifting/unrolling step at all, because there is no lower level being represented — Tensat never has a bound variable to eliminate because it never descends below the whole-operator granularity.

**Verdict on relevance to OSIL's question: not directly relevant to the binder problem**, but relevant to two adjacent engineering concerns worth noting for completeness:
- **Cycle handling**: rewrites over a DAG can introduce cycles the e-graph must not extract through (Figure 3 of the paper shows a concrete example of a rewrite that, applied to one output e-class, creates a cycle if a *different* output e-class's node is chosen). Tensat's solution is either an ILP cycle constraint or a pre-filtering pass (§5.2) — orthogonal to loops/binders but relevant if OSIL's flow-composition stratum (`then`, ADR-0010) ever needs egglog-native cycle safety.
- **Extraction at scale**: Tensat's ILP-based extractor (full formulation given in §5.1, a genuine 0/1 integer program over e-nodes and e-classes with topological-order variables to forbid cycles) is offered as an alternative to egg's/egglog's default greedy extractor when cost interactions are non-local. Table 1: **up to 16% runtime speedup** over TASO (prior state of the art) while spending **on average 48× less optimization time**, across BERT/ResNet-50/NasRNN/NasNet-A/SqueezeNet/VGG-19/Inception-v3.

Uses **egg** (§2.2, cited directly: *"a recent technique (Tate et al. 2009; ... Willsey et al. 2020)"* — code released at `github.com/uwplse/tensat`, cited in the paper's own footnote). Not egglog.

---

## 4. Post-2021 work (2022–2026): EGRAPHS workshop and MLIR+equality-saturation

I checked the EGRAPHS workshop (co-located with PLDI) program pages and MLIR-adjacent equality-saturation literature for 2022–2026 directly (not solely via search-engine summary for the three most load-bearing hits below).

### 4.1 `eqsat`: An Equality Saturation Dialect for Non-destructive Rewriting (Merckx, Lopoukhine, Coward, Cheng, De Sutter, Grosser — **EGRAPHS 2025**)

**Source:** [arXiv:2505.09363](https://arxiv.org/pdf/2505.09363). Read in full (7 pp.) directly from the PDF.

This is the single most directly relevant post-2021 result for "egglog/e-graph + MLIR + loop constructs," so it gets full treatment. `eqsat` represents e-graphs **natively as MLIR IR** (a new `eqsat` dialect: `eqsat.eclass`, `eqsat.egraph`, `eqsat.yield` operations) rather than exporting to/from an external engine like egg or egglog — the authors' explicit motivation is that jumping between an external e-graph library and the host compiler "hampers the ability to keep track of equality information as other compiler passes are applied" (§1). Their prototype is implemented in **xDSL**, a Python-native MLIR-like compiler framework — **not built on egg or egglog** (§2.2: *"We use xDSL to implement equality saturation using SSA constructs as defined in MLIR"*).

**Does it touch loops?** Yes, directly, and this is the most useful primary evidence in this whole research pass: **Listing 5** of the paper shows an `scf.for` loop (`%s = scf.for %i = %lb to %ub iter_args(%s = %s_0) { %x = memref.load %a[%i]; %term = arith.mulf %x, %two; %s_new = arith.addf %s, %term; scf.yield %s_new }`) embedded directly inside an e-graph, with the caption: *"eqsat.eclass operations have been left out in this example for clarity. Operations inside the loop body can access values from outside."* Section 3 ("Control Flow") states the general claim: *"By virtue of MLIR's region-based IR, there are dialects that can be used to represent control flow such as if-else-statements or for loops in a structured manner... The presence of these nested control flow regions does not hinder equality saturation but rather allows rewrites to naturally occur across control flow."* — i.e., the loop body's *contents* can participate in congruence/rewriting (values defined outside a loop remain visible inside it, per MLIR's normal block-argument scoping — this is MLIR's own binder mechanism, reused as-is, not a new e-graph-specific binder encoding).

**But — the paper's own stated limitation, exactly on point, quoted verbatim (§6, Future Work):** *"As discussed (Section 3), region-based control flow operations do not inhibit equality saturation. Currently, however, the pdl dialect cannot be used to match regions of operations. This means that, while it is possible to match code in regions, it is not yet possible to match complete control flow operations and rewrite those. In the future, allowing this could open up doors to not only rewrite code in the presence of control flow, but also rewrite control flow operations themselves."*

**This is the decisive negative finding for OSIL's question.** `eqsat` can *preserve* a loop as a region while doing ordinary arithmetic rewriting inside its body — but it **cannot yet rewrite the loop itself**, which is exactly what vectorization is (`for i in range(n): r[i]=x[i]*2` → `r = x*2` *replaces the loop with a different construct entirely* — it is a rewrite *of* control flow, not *inside* it). As of June 2025, the closest "egglog/e-graph-adjacent + MLIR + loops" system in the literature says this is future work.

### 4.2 DialEgg: Dialect-Agnostic MLIR Optimizer using Equality Saturation with Egglog (Zayed & Dubach — **CGO 2025**)

**Source:** [ACM DOI 10.1145/3696443.3708957](https://doi.org/10.1145/3696443.3708957). Full-text access required a proxy fetch (`r.jina.ai` reader) after direct WebFetch and the ACM PDF link both failed (binary-stream parsing failure / HTTP 403 respectively) — **flag: I could not independently re-verify this extraction against a page-image read the way I did for Diospyros/Glenside/Tensat/Slotted/eqsat**, so confidence here is MEDIUM, not HIGH, despite the quotes below looking precise.

DialEgg is the paper OSIL's own U5/ADR-0009 should care about most directly, because **it is egglog, not egg**, used against MLIR. Per the extraction: MLIR block arguments (which is how loop induction variables and carried values are represented in MLIR's region-based SSA) are modeled via a `Value` variant (`function Value (i64 Type) Op`) — a flat identifier-plus-type encoding, not a slotted or de-Bruijn scheme. Reported directly on point: **"DialEgg cannot rewrite loop structure itself. Loops are treated as opaque operations."** Quoted from the paper: *"MLIR operations that are not defined in DialEgg become opaque operations... This enables users of DialEgg to ignore irrelevant operations, while still allowing Egglog to optimize around them."* The benchmark table (five kernels, spanning `arith`/`math`/`linalg`/`scf`/`tensor`/`func` dialects) is reported to include `scf` loops **preserved, not rewritten**, and **no loop transformation (vectorization, fusion, unrolling) is demonstrated** in any benchmark.

If this extraction is accurate — and it converges exactly with `eqsat`'s independently-stated limitation above, which *is* independently verified — then the two most current (2025) MLIR+equality-saturation systems agree: loops are representable as opaque or pass-through structure, but **rewriting the loop itself is not yet demonstrated anywhere in the published literature**, egglog-based or otherwise.

### 4.3 Other 2022–2025 hits, briefly (lower priority, not read in full — noted for completeness)

- **Latent Idiom Recognition for a Minimalist Functional Array Language Using Equality Saturation** (Van der Cruysse & Dubach, CGO 2024; [arXiv:2312.17682](https://arxiv.org/pdf/2312.17682)). Uses a small functional array language + equality saturation to match BLAS/PyTorch idioms; reports a geometric-mean **1.46×** speedup matching BLAS calls from a high-level minimalist language. Not read in full this pass — **ASSUMPTION**: relevance to the binder question is plausible (a "minimalist functional array language" strongly suggests map/fold-style combinators, i.e. likely Glenside-adjacent, combinator-style avoidance of binders) but unverified; flagged as a follow-up read if OSIL pursues Track A/B further (§7).
- **Better Together: Unifying Datalog and Equality Saturation** (Zhang, Wang, Flatt, Cao, Zucker, Rosenthal, Tatlock, Willsey — PLDI 2023, [arXiv:2304.04332](https://arxiv.org/pdf/2304.04332)) — the egglog foundational paper itself, already the primary source behind OSIL's own ADR-0009; not re-litigated here.
- **Tiling-Aware Vectorization Framework for Perfect Loop Nests in MLIR** (ICA3PP 2025) — an MLIR `linalg`-dialect vectorizer with an analytical cost model; **not equality-saturation-based** at all per the search abstract (a classical cost-model-guided pass) — noted only to confirm it is *not* relevant prior art for the e-graph question, despite surface keyword overlap.
- No EGRAPHS 2022, 2023, 2026 paper was found, in the searches run this session, with a title indicating loop/polyhedral/vectorization scope comparable to `eqsat` or DialEgg. **ASSUMPTION: this is a negative result from a finite set of targeted searches, not an exhaustive proceedings read** — I did not fetch and read the full EGRAPHS 2022/2023/2026 program pages line by line; a future pass should, if this question needs a fully closed literature review rather than a decision-grade one.

---

## 5. The binder problem, generally: slotted e-graphs

**Source:** Rudi Schneider, Marcus Rossel, Amir Shaikhha, Andrés Goens, Thomas Kœhler, Michel Steuwer. "Slotted E-Graphs: First-Class Support for (Bound) Variables in E-Graphs." **PLDI 2025**, PACMPL vol. 9. [ACM DOI 10.1145/3729326](https://doi.org/10.1145/3729326) · [author PDF](https://steuwer.info/files/publications/2025/PLDI-Slotted-E-Graphs.pdf). Read in full (20 pp.) directly from the PDF, including all formal definitions.

### 5.1 The problem, in the field's own words

The paper opens by naming the problem OSIL is asking about, generally, and cites egg's own paper as already having flagged it as unsolved: *"An important open problem is extending efficient e-graph representation to languages featuring bound variables... the egg paper acknowledges, that 'better support for languages with binding is important future work' [Willsey et al. 2021]"* (§1, p.223:2). It surveys the three prior approaches and their failure modes:

1. **Named variables** (strings): *"a name in the egg paper... presented as 'contrived'... a couple of obvious downsides: as two equal terms that only differ by their bound variable names are stored twice and not treated as equal. Furthermore, problems arise when variable names collide during rewriting... requiring delicate rules and tracking which variables are free in a context via a dedicated analysis."*
2. **de Bruijn indices**: solves the naming/collision problem but *"introduces new problems... all indices have to be shifted, using a dedicated set of rewrites, to maintain correctness. Getting shifting right is a tedious task and similar to renaming, shifting results in unnecessary duplication that can blow up the e-graph size quickly."*
3. **Combinator-only design** (this is Glenside, named explicitly — see §2.2 above): avoids binders altogether but at the cost of expressiveness/translation blowup.

### 5.2 The mechanism, precisely (formal, implementable-level detail)

A **slotted e-class** is parameterized by a set of **slots** — placeholders for the class's *free* variables (Def. 4: a slotted e-class is a triple `(S, B, G)` where `S` is the set of slots/free-variable-names the class exposes, `B` maps canonicalized "shapes" of contained e-nodes to renamings, `G` is a permutation group recording variable-symmetries the class has, e.g. `a+b ≡ b+a` under swapping slots). Terms are given a small extension to ordinary term syntax (Fig. 5): a distinguished slot-constant syntax `$x`, and a binder constructor `bind $x tc` meaning "`$x` is bound within subterm `tc`." E.g. (Example 1, the paper's own worked example, lambda calculus): `λ$x.t₁` is encoded `lambda(bind $x t₁)`; `let $x = t₁ in t₂` is `let(t₁, bind $x t₂)` — note only the *second* argument's `$x` is bound, exactly matching normal `let` scoping.

Referring to an e-class from an e-node now requires supplying a **renaming** — a bijection from the caller's local variable names to the callee e-class's slots — rather than a bare e-class id. The paper formalizes and implements: **congruence modulo renaming** (an extended congruence-closure relation that also identifies α-equivalent terms automatically, Fig. 6), a **slotted union-find**, **slotted hashcons** (via a renaming-invariant canonical "shape" per e-node, Def. 7), and a full **e-matching algorithm** for slotted patterns (§3.6). This is a from-scratch, from-first-principles data structure and algorithm — not a thin wrapper over egg/egglog.

### 5.3 Case study 1 is literally a loop-fusion problem

§4.1's evaluation is a **functional array language** with `map`, `map-fusion` (`map f (map g y) ↦ map (λx. f (g x)) y`) and `map-fission` (the reverse, splitting one map into two with an intermediate array) as first-class rewrite rules, alongside β/η-reduction — this is the closest structural analogue to `for i in range(n): r[i] = f(x[i])` anywhere in the prior-art surveyed in this document, and it is expressed with a genuinely **bound** index (`λx. …`), not by unrolling. Their own `define_language!` listing (Listing 1) implements this whole language plus all four rewrite rules in **under 40 lines**, versus ~200 lines for a hand-rolled named-variable encoding in egg and ~250 for a de Bruijn encoding in egg (both cited from prior work, Kœhler et al. 2024). Scaling result (Fig. 8, §4.1): with an increasing function-parameter count, both a named-in-egg and a de-Bruijn-in-egg encoding blow up to **millions of e-nodes and multiple GB** within 3–4 parameters and hit a 4 GB/5-minute budget; the slotted implementation stays at **214 e-nodes / 6 MB / 0.22 s** independent of parameter count — **3+ orders of magnitude smaller**, on their own benchmark.

A second case study (§4.2, sparse tensor compilation, reimplementing "Storel" over SDQL) and a third (§4.3, a Lean theorem-proving proof tactic, replacing a de Bruijn-based `egg` backend) both report slotted e-graphs matching or beating the incumbent de Bruijn-in-egg implementation on memory and iteration count while being far simpler to implement (Table 3: "Invalid Capture," "Invalid Matching," "Shifting/Renaming Operation" are all `automatic`/`not required` for slotted vs. `manual` for de Bruijn/named).

### 5.4 Why this does NOT immediately solve OSIL's problem — the engineering gap

Three facts, all independently checked this session, cut against treating slotted e-graphs as a drop-in answer:

1. **It is not egg or egglog.** The implementation, `slotted` (crates.io: [`slotted-egraphs`](https://crates.io/crates/slotted-egraphs), repo [`memoryleak47/slotted-egraphs`](https://github.com/memoryleak47/slotted-egraphs)), is explicitly stated in the paper's own footnote to be built from scratch: *"slotted does not use any egg code, and was built from scratch"* (§4, footnote 5). It is **not** hosted under the `egraphs-good` GitHub org that owns both egg and egglog (confirmed via GitHub search this session) — it is a separate, independently-maintained project by a single named author.
2. **It is young and pre-1.0.** The published crate version found via crates.io search is `0.0.13` — 0.0.x versioning, no stability guarantee implied. The paper itself is three months old relative to this research date (published June 2025).
3. **No integration with egglog was found.** I searched directly for an egglog↔slots bridge (GitHub issues, search engines) and found none. **ASSUMPTION (falsifiable):** no such integration exists as of 2026-08-24; this could change, and should be re-checked before this document is relied on past a few months.
4. **It has never been used to express vectorization.** Its own two compiler-relevant case studies are map-fusion/fission (a genuine structural cousin of vectorization, but not the same rewrite) and sparse-tensor loop fusion (via SDQL semi-ring dictionaries) — nobody has yet published "slotted e-graphs discover a SIMD rewrite."

**Net: slotted e-graphs is the one piece of prior art in this whole survey that attacks the actual binder problem head-on rather than routing around it, and its evaluation data (§5.3) is the strongest evidence in this document that a genuinely bound representation can be tractable at the scale that defeats de Bruijn/named encodings.** But adopting it for OSIL today would mean re-opening ADR-0009 (U5), not extending it — see §7.

---

## 6. egg vs. egglog, specifically for arrays/loops/vectorization

This section directly extends `docs/decisions/ADR-0009-egglog-engine-target.md` and `docs/research/U5-egg-vs-egglog.md`, which I read in full before starting this research (both cited, not re-litigated).

- **Every 2021-era vectorization/tensor system surveyed above (Diospyros, Glenside, Tensat) used egg, not egglog** — mechanically true because egglog's foundational paper (Zhang et al., PLDI 2023) postdates all three. This is a currency fact, not a design endorsement either way.
- **The one egglog-native system found that touches MLIR (DialEgg, CGO 2025, §4.2 above) demonstrates egglog is usable for a real dialect-agnostic optimizer at reasonable scale** — this is a genuine, if MEDIUM-confidence (see the sourcing caveat in §4.2), point in egglog's favor: the engine itself is not the blocker for a Glenside/DialEgg-style project; DialEgg's specific *loop* limitation (opaque pass-through, no structural rewriting) is a scope choice of that paper, not a demonstrated ceiling of egglog as an engine.
- **egglog has a built-in `Vec` primitive sort** (confirmed via `egraphs-good/egglog`'s own `tests/vec.egg` test file, fetched this session: constructors/operations include `vec-of`, `vec-empty`, `vec-push`, `vec-pop`, `vec-set`, `vec-get`, `vec-length`, `vec-range`, `vec-append`, `vec-union`, and an `unstable-vec-map` for applying a function value across elements). **This is a genuinely new capability neither egg nor the 2021 papers had.** But — **ASSUMPTION, medium confidence, inferred from the test file's API shape and egglog's documented primitive/sort distinction (not an explicit doc quote)**: `Vec` is a *primitive* type in egglog's type system, meaning values are compared for content-equality and hashed as opaque data, the same way `i64`/`String` are — **individual elements of a `Vec` do not each get their own e-class and do not individually participate in congruence closure or rewriting**. This means `Vec` is suitable for carrying *static metadata* (e.g. a guard-fact's argument list, a shape tuple, analogous to how Tensat's `reshape`/`transpose` operators carry shape/permutation as opaque `String`-typed parameters, Table 2 of the Tensat paper) but does **not**, by itself, give OSIL a way to equality-saturate *over the contents* of what was a loop — for that, a proper user-defined **sort** with explicit constructors is still needed, i.e. exactly Diospyros's `List`/`Get`/`Vec`-as-constructor pattern (§1.1 above), re-expressed as egglog `datatype` declarations rather than egg `define_language!` enums. The mechanism transfers; the primitive `Vec` sort is a convenience for the surrounding metadata, not a substitute for it.
- **egglog's Datalog layer's one clear, narrow win for this specific problem**: shape-compatibility side conditions (e.g. "only fire a `matmul` fusion rule if the inner dimensions agree") map onto the exact same `guards { k = v }` → nullary-relation-fact mechanism ADR-0009 already established and `tools/egraph_roundtrip.py` already implements (`rel_for`, `:when`). This is real but modest: it reduces the *guard-plumbing* cost of a hypothetical array/vector extension to roughly zero net-new mechanism, but it does nothing for the binder problem itself.
- **egglog has a genuine Rust library API** suitable for a standalone binary — confirmed via `crates.io`/`docs.rs` listings and the `egglog` GitHub README's own instructions (`cargo install --path=egglog` for the CLI; the crate is also consumable as a library, and `egglog-python` — the package OSIL already pins at 13.2.0 per ADR-0009 — is itself built by binding that same Rust core via PyO3, per U5 §5's finding that `egglog-python`'s `Cargo.toml` vendors `egglog` at a pinned git rev). **Recommendation: do not use this as a reason to leave the Python binding.** ADR-0009's entire rationale (§ "no maintained Python binding for egg exists," "zero manual setup in `just test`") was specifically about *packaging*, and a hand-rolled Rust binary for vectorization would reintroduce exactly the setup burden ADR-0009 rejected for egg. If OSIL ever needs Rust-native egglog (e.g. for performance at a scale the Python binding can't sustain — plausible given Isaria's 64 GiB e-graph-explosion data point, §1.6 above), that is a **new, separate decision** requiring its own ADR, not a free corollary of this research.

**Verdict on this section's question ("does egglog's datalog layer help or hurt for loop/tensor rewriting"): net neutral-to-slightly-positive, and orthogonal to the binder problem.** It helps with guard/shape-condition plumbing (an OSIL-specific convenience, already proven at G14) and has at least one credible-if-imperfectly-verified existence proof of MLIR-scale use (DialEgg); it does not solve, worsen, or meaningfully touch the loop-binder question, which is answered independently in §§1–5 above.

---

## 7. Verdict

### (a) Can OSIL's term language be extended to express vectorization, and what is the MINIMAL construct required?

**Yes, but not as a small addition to the existing scalar equivalence corpus, and not by adding "a loop" as a first-class egglog term.** Every working system surveyed (Diospyros, its 2024 successor Isaria, and Glenside) answers "how does a bound loop index get into a ground-term e-graph" with the same structural move: **it doesn't — the binder is eliminated before saturation starts**, either by full static unrolling into an indexed ground-term list (Diospyros/Isaria) or by a combinator/shape-typed encoding that never introduces a named index at all (Glenside). The one mechanism that genuinely represents a *bound* loop index inside the e-graph itself — slotted e-graphs (PLDI 2025) — exists, is well-evidenced (§5.3's 3-order-of-magnitude scaling win is real and primary-sourced), and is structurally the right shape (its own case study *is* map-fusion/fission over a functional array language), but it is implemented in a separate, pre-1.0, single-maintainer Rust crate outside the `egraphs-good` org, with **no found integration path to egglog** — adopting it means reopening ADR-0009/U5, not extending them.

Given OSIL's committed engine (egglog, ADR-0009) and its own grammar discipline (triple representation: prose + grammar production + corpus example per every new construct, CLAUDE.md rule 3), **the only currently-implementable path is Diospyros-style static unrolling ("Track A"):**

Minimal new construct(s), concretely:
1. A **SIR-level bounded iteration construct with a statically-known, closed-form extent** — e.g. a `for` binder whose range bound must resolve to a grammar-level integer literal (or a constant already bound in the enclosing scope), never an arbitrary runtime expression — paired with an indexed assignment target (`r[i] = expr(i)`).
2. A **CIR-level ground-term array pair**: an indexing constructor `Get(array, literal-index)` (the index argument is always a literal after unrolling — the egglog term language never contains a free index variable) plus a fixed-width list/vector constructor to hold the unrolled results — i.e. OSIL's own `Num` sort (`grammar/osil.ebnf` lines 144–149) needs a sibling sort, structurally identical to Diospyros's Figure 3 `⟨vector⟩` production, not a modification of the existing scalar grammar.
3. A **new SIR→CIR lowering/lifting *tool stage*** (not a grammar change) that performs the actual unrolling — the equivalent of Diospyros's Rosette-based symbolic-evaluation pass (§1.2 above) — strictly *before* any term reaches `egglog.EGraph()`. This is genuinely new machinery, not a reuse of `tools/egraph_roundtrip.py`'s existing `translate()`/`build()` functions, which assume the corpus already hands them a ground scalar AST.
4. A **new, non-trivial cost model** for extraction — Diospyros's own paper is explicit that this cost function must be hand-designed and **strictly monotonic** (§3.4) to keep extraction tractable, and that getting it wrong measurably costs performance (§5.6: disabling vector rewrites entirely sometimes *beats* Diospyros's own vectorized output when the cost model doesn't reflect real packing overhead). egglog's current default (`:cost`/ast-size, per `tools/egraph_roundtrip.py`'s docstring) is not this.

None of this is a one-line grammar diff. It is a second term-language stratum plus a new compiler pass plus a new cost model — closer in scope to G14 (a whole new gate) than to a corpus-fixture addition.

### (b) Recommended encoding, with justification

**Adopt Track A explicitly, scoped to statically-bounded loops only, modeled directly on Diospyros's Figure 3 grammar** (`List`/`Vec`/`Get`/`VecAdd`/`VecMul`/`VecMAC`/…), translated into an egglog `datatype` (sort) — not egglog's built-in `Vec` primitive, which (§6) cannot itself carry rewritable per-element structure. Justification: (1) it is the only approach in this entire survey with a *working, measured, MIT-licensed, artifact-evaluated* implementation (Diospyros/Isaria) rather than a paper-only or unmaintained one (Glenside is archived, unlicensed; slotted e-graphs is 0.0.x and unintegrated with egglog); (2) it requires no engine change and therefore no reopening of ADR-0009; (3) OSIL's existing guard-as-Datalog-fact mechanism (ADR-0009, §6 above) transfers directly to the shape-compatibility side conditions this encoding will need (e.g. "only fire a vectorizing rewrite if the unrolled list length matches the target vector width"), so that part of the U5 investment is not wasted.

The honest cost of this recommendation, stated plainly because the task asked for skepticism: this is a genuinely large scope addition (§(a) above), and even Diospyros's own numbers — the single working reference implementation — show it **times out on half its own benchmark suite** and produces a 509 MB intermediate term at a 4×4 problem size, mitigated only by a bespoke, hand-written de-duplication pass outside equality saturation entirely. OSIL's current corpus is six scalar equivalences (per `tools/egraph_roundtrip.py`'s docstring, G14 evidence); Isaria's own measured result — 64 GiB exhausted on a **2×2** convolution with an unrestricted synthesized rule set — is a direct, primary-sourced warning about what happens when array rewriting is added to an e-graph system without the kind of careful, hand-curated (or automatically phased, à la Isaria) rule discipline that took two ASPLOS papers (2021 and 2024) to get right for one narrow domain (small DSP linear-algebra kernels).

### (c) What remains inexpressible even under the recommended encoding

- **Data-dependent / dynamic loop bounds.** Diospyros/Isaria require a compile-time-fixed extent by construction (§1.2, §1.6); Glenside's shapes are static integer tuples throughout (§2.3, inferred from the formal definitions, not a quoted limitation). A loop whose trip count is a runtime value is out, full stop, under Track A.
- **Non-affine or data-dependent indices that determine loop *structure*** (as opposed to *data movement within* a fixed-size unrolled body — Diospyros's own shuffle/select mechanism is explicitly *more* permissive than affine-only movement for that inner case: *"The IR does not restrict the possible values of indices"*, §4). The boundary is precise: arbitrary data movement among already-materialized, statically-many elements is fine; a loop whose *extent or shape* depends on data is not.
- **Data-dependent control flow / early exit inside the loop body.** Diospyros's own scoping sentence draws this line explicitly (§3.1, quoted in §1.4 above): control flow must be "independent of the input data."
- **General carried-dependency reductions** (an accumulator update rule that is not associative/commutative-foldable). Glenside's operator vocabulary is closed to exactly `reduceSum`/`reduceMax`/`dotProd` (§2.3); Diospyros's own associativity/commutativity handling is explicitly a hand-worked-around NP-complete scalability wall (§1.4), not a solved general case.
- **Rewriting the loop construct itself as a first-class e-graph operation, in the general (non-unrolled) case** — i.e. genuine binder-aware vectorization without pre-elimination of the index. This is not merely unimplemented in OSIL; it is, per §4.1's and §4.2's directly-quoted "future work" statements, **unimplemented anywhere in the published literature as of this research date**, egglog-based or otherwise.
- **Anything requiring OSIL to adopt slotted e-graphs' mechanism specifically** — parametric-size loop reasoning (proving a property for all `n` rather than per concrete unrolled `n`), or genuinely sharing structure across differently-shaped unrolled instances — is unavailable given OSIL's committed engine, not because the underlying idea is unsound (§5.3's evidence says the opposite) but because the two pieces of software (egglog and `slotted`) are not currently connected, and connecting them would be new upstream-adjacent engineering, not something OSIL can consume off the shelf today.

### (d) Full citations

1. Alexa VanHattum, Rachit Nigam, Vincent T. Lee, James Bornholt, Adrian Sampson. "Vectorization for Digital Signal Processors via Equality Saturation." ASPLOS '21. DOI: [10.1145/3445814.3446707](https://doi.org/10.1145/3445814.3446707). Preprint PDF: https://cs.wellesley.edu/~avh/diospyros-asplos-2021-preprint.pdf. Code: https://github.com/cucapra/diospyros (MIT License, per the paper's own Artifact Appendix §A.1). Artifact DOI: 10.5281/zenodo.4331404.
2. Samuel Thomas, James Bornholt. "Automatic Generation of Vectorizing Compilers for Customizable Digital Signal Processors." ASPLOS '24. DOI: [10.1145/3617232.3624873](https://doi.org/10.1145/3617232.3624873). PDF: https://jamesbornholt.com/papers/isaria-asplos24.pdf.
3. Gus Henry Smith, Andrew Liu, Steven Lyubomirsky, Scott Davidson, Joseph McMahan, Michael Taylor, Luis Ceze, Zachary Tatlock. "Pure Tensor Program Rewriting via Access Patterns (Representation Pearl)." MAPS '21 (PLDI workshop). arXiv: [2105.09377](https://arxiv.org/abs/2105.09377). Code: https://github.com/gussmith23/glenside (archived 2025-05-30, `"license": null` per GitHub API, confirmed live this session).
4. Yichen Yang, Phitchaya Mangpo Phothilimthana, Yisu Remy Wang, Max Willsey, Sudip Roy, Jacques Pienaar. "Equality Saturation for Tensor Graph Superoptimization." MLSys 2021. arXiv: [2101.01332](https://arxiv.org/abs/2101.01332). Code: https://github.com/uwplse/tensat.
5. Jules Merckx, Alexandre Lopoukhine, Samuel Coward, Jianyi Cheng, Bjorn De Sutter, Tobias Grosser. "eqsat: An Equality Saturation Dialect for Non-destructive Rewriting." EGRAPHS '25 (PLDI workshop). arXiv: [2505.09363](https://arxiv.org/pdf/2505.09363).
6. Abd-El-Aziz Zayed, Christophe Dubach. "DialEgg: Dialect-Agnostic MLIR Optimizer using Equality Saturation with Egglog." CGO '25. DOI: [10.1145/3696443.3708957](https://doi.org/10.1145/3696443.3708957). (Extracted via proxy fetch; MEDIUM confidence — not independently re-verified against a direct page-image read, unlike sources 1–5 and 7.)
7. Rudi Schneider, Marcus Rossel, Amir Shaikhha, Andrés Goens, Thomas Kœhler, Michel Steuwer. "Slotted E-Graphs: First-Class Support for (Bound) Variables in E-Graphs." PLDI 2025 (PACMPL vol. 9). DOI: [10.1145/3729326](https://doi.org/10.1145/3729326). Author PDF: https://steuwer.info/files/publications/2025/PLDI-Slotted-E-Graphs.pdf. Code: https://crates.io/crates/slotted-egraphs (v0.0.13), https://github.com/memoryleak47/slotted-egraphs.
8. Max Willsey, Chandrakana Nandi, Yisu Remy Wang, Oliver Flatt, Zachary Tatlock, Pavel Panchekha. "egg: Fast and Extensible Equality Saturation." POPL 2021. DOI: [10.1145/3434304](https://doi.org/10.1145/3434304). ("Better support for languages with binding is important future work" — quoted here via source 7's citation of it, not independently re-verified against egg's own paper text in this pass; flagged.)
9. Yihong Zhang, Yisu Remy Wang, Oliver Flatt, David Cao, Philip Zucker, Eli Rosenthal, Zachary Tatlock, Max Willsey. "Better Together: Unifying Datalog and Equality Saturation." PLDI 2023. arXiv: [2304.04332](https://arxiv.org/pdf/2304.04332). (Not re-read in this pass — already the primary source behind `docs/decisions/ADR-0009-egglog-engine-target.md`.)
10. Jonathan Van der Cruysse, Christophe Dubach. "Latent Idiom Recognition for a Minimalist Functional Array Language Using Equality Saturation." CGO 2024. arXiv: [2312.17682](https://arxiv.org/pdf/2312.17682). (Abstract/search-result level only, not read in full this pass — flagged §4.3.)
11. `egraphs-good/egglog` — `tests/vec.egg` (built-in `Vec` primitive sort operations): https://raw.githubusercontent.com/egraphs-good/egglog/main/tests/vec.egg. Fetched this session.
12. Repo context read before this research (primary, in-repo): `grammar/osil.ebnf` (term-language grammar, lines 144–149 for the current scalar-only `expr`/`term`/`factor` productions), `tools/egraph_roundtrip.py` (the `Num` sort, guard-as-relation mechanism, cost model), `spec/interop/egraph.md`, `docs/decisions/ADR-0009-egglog-engine-target.md`, `docs/research/U5-egg-vs-egglog.md`, `docs/GATES.md`, `docs/intake/synthesis-repo-organization.md` (source of the U6-id collision flagged at the top of this document).

---

## Validity & limitations

**Valid as of:** 2026-08-24. **Re-evaluate if:** (1) a slotted-egraphs↔egglog integration appears (would materially strengthen Track B and should trigger a follow-up unknown); (2) `eqsat` or DialEgg (or a successor) publishes a result that actually rewrites loop/region structure rather than preserving it opaquely — both explicitly flagged their current inability to do this, but both are 2025 papers with active follow-on communities (EGRAPHS meets regularly; a DialEgg community-meeting talk from 2026-08-21 was found in search results, indicating ongoing activity); (3) Isaria or a successor publishes updated scaling numbers that change the "64 GiB on a 2×2 kernel" risk picture; (4) OSIL's own corpus/gate structure changes such that a full new stratum (Track A's array sort + lowering pass + cost model) becomes proportionate to take on.

**Limitations of this research:** (1) DialEgg (§4.2) was extracted via a single proxy fetch, not independently re-verified by direct PDF page read — flagged, MEDIUM not HIGH confidence. (2) The EGRAPHS 2022/2023/2026 proceedings were not read exhaustively; the "no other directly relevant hit" conclusion in §4.3 is a bounded-search negative result, not a systematic-review negative result. (3) Glenside's explicit inexpressibility claims (§2.3) are my own grounded inference from its formal type system (Tables 1–2), not a quoted "Limitations" section — the paper does not have one — flagged accordingly, per this repo's own evidence-hierarchy rule that a paper's stated limitations outrank inference (here, there were none stated to outrank). (4) The Isaria and DialEgg license/artifact status were not independently confirmed in this pass (unlike Diospyros's MIT license and Glenside's confirmed-null license, both verified via primary/API sources).

**Epistemological note:** every load-bearing claim in §§1–3 and §5 was read directly from the primary-source PDF (page images, not a search-engine or fetch-tool paraphrase) inside this session — this is stronger evidence than most of `docs/research/U5-egg-vs-egglog.md`'s own sourcing, which relied more heavily on API metadata and README text. Where that standard was not met (§4.2 DialEgg, §4.3's minor hits), it is flagged in-line, not silently upgraded.
