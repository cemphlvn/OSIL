# U11 — Automatic Rewrite-Rule Synthesis: Can OSIL Expand Its Own Corpus?

**Date:** 2026-08-24
**Researcher:** research-agent
**Question:** OSIL's central bet is "the corpus IS the rule set" — every declared
`equivalence` in `conformance/corpus/` is simultaneously a spec fixture, a
rewrite rule the engine runs, and a preservation test (G14). All six existing
equivalences, and the optimizer probe's five guard-gated rules
(`optimizer/src/main.rs`), are hand-written. Can OSIL automatically **synthesize**
new, trustworthy rewrite rules instead of waiting for a human to write each
one — and if so, with what tool, validated how, and with guards/side-conditions
handled how?

## Method (wave decomposition)

Default line I would have run: "read the Ruler and Isaria papers, summarize
rule synthesis." Simulated finding: a general description of
enumerate-candidates → validate → minimize — true, but too coarse for what this
task actually needs, which is a **decision-grade, mechanism-level** answer
(precisely how does Isaria avoid the blowup U6 already measured; can any tool
emit a rule shaped like OSIL's own `guards { regime = ... }`; is there a
reported unsoundness incident; is LLM-assisted synthesis real or vaporware).
Gaps relative to that bar, to OSIL's actual constraints (a 6-fixture corpus
that doubles as its conformance suite, a `never-fabricate-a-pass` invariant
per `conformance/README.md`, a guard mechanism already built and specific —
`guards { k = v }` → nullary Datalog relation per ADR-0009), and to the
maintainer's higher-order goal (an honest premature-or-not verdict, not a
survey):

- Gap A — **Ruler's own mechanics**: enumeration strategy, validation pipeline,
  what "a good rule set" means to it, stated limitations, maintenance/license.
- Gap B — **Enumo**: verify it is real (not assumed from a search snippet),
  get the correct citation, and find precisely what problem with Ruler it fixes.
- Gap C — **Isaria's phase-ordering scheduler, mechanism-level**: U6 read only
  the first 6 pages (the 64 GiB explosion). The scheduler itself — the thing
  that makes 300 synthesized rules usable — was unread going into this task.
  This is the single most actionable finding the maintainer asked for.
- Gap D — **conditional/guarded rule synthesis**: decisive for whether a
  synthesized rule could ever be sound for OSIL's FP-reassociation guard.
- Gap E — **2024–2026 currency**, including LLM-assisted rule proposal,
  checked skeptically for what validation (if any) backs it.

Five parallel research forks were dispatched, each reading primary sources
directly (PDF full-text reads and live GitHub API checks, not search-snippet
paraphrase unless explicitly flagged). **Synthesis: convergent.** All five
lines agree on the load-bearing facts below without contradiction; where a
claim rests on a single source or a search-bounded negative result, it is
flagged in-line as `ASSUMPTION`.

**Methodology note (transparency, not hedging):** one fork (Gap A, Ruler's own
mechanics) independently wrote a draft to this same output path partway
through its 604-second, 30-tool-call run — its inherited context included the
original task's instruction to write findings to this file, and as a fork it
reasonably (if not intentionally instructed to) acted on that. This
coordinating pass's own write superseded it on disk; nothing was lost — the
fork's substantive findings were still delivered via its completion report
and are integrated below, cited as such. Flagged here because intellectual
honesty about method extends to the research process itself, not just its
conclusions.

---

## 1. Ruler (Nandi, Willsey, Zhu, Wang, Saiki, Anderson, Schulz, Grossman, Tatlock — OOPSLA 2021)

**Citation:** "Rewrite Rule Inference Using Equality Saturation." *Proc. ACM
Program. Lang.* 5, OOPSLA, Article 119 (2021).

### 1.1 Enumeration

Ruler enumerates candidate terms **exhaustively from a user-supplied grammar**,
by size, without regard to which terms are semantically interesting. This is
not a hedge — it is the exact problem Enumo was built to fix, and Enumo's own
paper quantifies it concretely: deriving a single deeper rule
(`(/ a a) ↦ (if a 1 (/ a a))`) required Ruler to enumerate **3,236,142 smaller
terms first** (Enumo §3.2, direct citation of Ruler's behavior). Ruler's paper
itself frames this as inherent to a "one-shot" design with no mechanism for a
domain expert to narrow the search space (Enumo §1, characterizing Ruler).

### 1.2 Candidate generation and validation

Two-stage pipeline. **Stage 1 (cvec matching):** every enumerated term is
evaluated on a fixed battery of concrete input assignments, producing a
**characteristic vector (cvec)** — terms with matching cvecs become *candidate*
equal pairs. This stage is explicitly a pre-filter, not a proof: candidates are
"likely, but not guaranteed, to be valid" (Ruler §3.3). Partial operators
(e.g. division) are handled by treating null/undefined cvec entries as
matching anything, so `x/x ↔ 1` never spuriously merges with `a-a`.

**Stage 2 (validation):** Ruler §3.4, quoted directly: *"Ruler supports
arbitrary validation procedures: small domains may use model checking, larger
domains may use SMT, and undecidable domains may decide to give up a guarantee
of soundness and use a sampling-based validation."* SMT (Z3) is the actual
soundness guarantee where the domain admits it; cvec/fuzz testing alone is
explicitly **not** treated by the paper's own authors as sufficient — see §4
below.

### 1.3 What "a good rule set" means to Ruler

**Minimality via derivability, not completeness.** A validated candidate is
only added to the output rule set if it is **not already derivable** from the
rules already accepted — checked by running equality saturation with the
existing rule set and testing whether the candidate's two sides already merge.
This is the same idea Enumo's `.minimize()` reuses. Ruler does not claim or
attempt completeness (deriving every valid equality up to some term-size
bound) — it targets a small generating set sufficient to reconstruct
downstream-useful equalities via saturation.

### 1.4 Stated limitations (paper's own words, ranked above inference)

- Exhaustive grammar enumeration does not scale to rules requiring deep
  nesting — the 3.2-million-term example above is Ruler's own failure mode,
  not a hypothetical.
- **§6.2 sensitivity study — a concrete, reported instance, not a
  hypothetical risk.** Table 2 of the paper reports a fuzzing-only
  configuration (bitvector-4, sparse random sampling) in which validation
  **admitted a candidate that was subsequently found unsound** by the
  system's own internal check — the paper is reporting this as something
  that happened in its own evaluation, not warning about a theoretical edge
  case. For bitvector-32, naive random sampling *"was insufficient for
  uncovering all the edge cases during rule validation."* The paper's own
  conclusion: *"we emphasize that fuzzing alone cannot guarantee soundness in
  general."*
- **No first-class conditional-rule representation — stated directly by the
  paper, not only inferred from a workaround.** Beyond the `ite`-encoding
  workaround for partial operators (footnote 7, §5 below), Ruler's own
  discussion (§7) names the inability to synthesize genuinely conditional
  rules as a limitation of the system, independently corroborating the
  workaround pattern rather than merely implying it.

### 1.5 Domains evaluated

Booleans, bitvectors (4-bit and 32-bit), and rationals. The rational-arithmetic
rules were fed into **Herbie** (the floating-point-accuracy rewriting tool,
same research lineage — Panchekha/Tatlock) to replace Herbie's hand-written
algebraic-simplification-phase rules. **This is not floating-point rule
synthesis in the IEEE-754 sense** — Ruler synthesized over exact rationals,
where associativity needs no guard at all; Herbie's own separate, hand-written
regime-inference and error-sampling machinery (roughly **52 hand-written
rules**, a useful scale anchor for §7) is what keeps the actual FP *output*
sound under rounding. No domain in the paper models NaN/Inf/signed-zero/
reassociation semantics directly.

### 1.6 Code, license, maintenance

`github.com/uwplse/ruler` — **MIT licensed, actively maintained**: confirmed
via direct GitHub API check: last push **2026-08-16** (eight days before this
research), **15 open issues**. Not archived. A targeted search of open issues
found **no report of a shipped (post-release) unsound rule** — absence of
evidence, not evidence of absence (see §4); the one confirmed unsound-rule
event (§1.4) was caught during the paper's own evaluation, before anything
shipped.

---

## 2. Enumo (Pal, Saiki, Tjoa, Richey, Zhu, Flatt, Willsey, Tatlock, Nandi — OOPSLA 2023)

**Citation:** "Equality Saturation Theory Exploration à la Carte." *Proc. ACM
Program. Lang.* 7, OOPSLA2, Article 258 (Oct 2023). DOI:
[10.1145/3622834](https://doi.org/10.1145/3622834). Verified real via direct
PDF read (not a fabricated or guessed citation) — this is a genuine, correctly
identified successor to Ruler, not a rumor.

### 2.1 What problem with Ruler motivated it

Ruler's paper itself is quoted (Enumo §1) admitting the "one-shot" design
problem: *"existing theory explorers are still not widely used... their
monolithic implementations make them too inflexible... designed for idealized
'one-shot' use cases"* with no way for a domain expert to steer the search.
The 3.2-million-term example (§1.1 above) is Enumo's own headline illustration
of the cost.

### 2.2 What changed, mechanically

Enumo is a **composable embedded Rust DSL**, not a different validation
theory. Two core value types: **workloads** (sets of terms, built via
`Set`/`Union`/`Filter`/`Plug` operators — `Plug` recursively substitutes a
placeholder symbol with terms from another workload, letting a human hand-
shape *which* subset of the term space gets enumerated) and **rulesets**
(composed via `EqSat`/`Derive`/`Filter`, with a `.minimize()` reusing Ruler's
derivability idea). Candidate generation and validation are otherwise
**unchanged from Ruler** — cvec fuzzing plus an external, user-supplied checker
(Enumo's own worked example uses Z3 directly, §3.1). Enumo's contribution is
enumeration *guidance*, not a new soundness model.

A second, genuinely novel piece: **"fast-forwarding"** (§5) — synthesizes
rules for domains where an interpreter is unavailable (equality is
undecidable, e.g. real transcendentals) by finding merged e-classes under
already-known rules rather than by direct evaluation.

### 2.3 Results

On Halide-scale grammars, 845 Enumo-synthesized rules derive 80.7%/90.6% of a
hand-written 300+ rule reference set, where Ruler-style exhaustive enumeration
becomes "computationally infeasible" past roughly 5 atoms. Fed into Herbie,
Enumo's rules gave **128% higher accuracy** than Ruler's rules at comparable
runtime; Ruler does not support trig/exponential domains at all, Enumo does.

### 2.4 Conditional rules — Enumo's narrow form

Enumo *can* synthesize what it calls conditional rules, via a
`guard_pattern = (if GUARD THEN ELSE)` template plugged with domain-specific
terms harvested from already-found unsound candidates, then re-validated
(§3.2's division-by-zero worked example: a human-supplied "here's what could
be unsound" hint, followed by automatic guard-wrapping and re-validation —
guided, not fully automatic, side-condition inference). **The condition lives
inside the rewritten term as an `if`-expression, not as an external predicate
gating rule applicability.** This is a materially different notion of
"conditional" from OSIL's own `guards { regime = ... }` mechanism (§5 below
expands this distinction — it is decisive).

### 2.5 Code, license, maintenance

Same repository as Ruler, `github.com/uwplse/ruler/tree/main/tests/recipes` —
MIT licensed, last push 2026-08-16, 15 open issues, not archived, actively
maintained.

### 2.6 Successor

`github.com/ninehusky/chompy` — "Conditional Rewrite Rule Synthesis Using
E-Graphs and Implication Propagation," targeting **FMCAD 2026** (i.e.
essentially contemporaneous with this research, not yet a published,
peer-reviewed artifact). Covered in full in §5 and §6.

---

## 3. Isaria's phase-ordering scheduler — the load-bearing mechanism

U6 already established Isaria (Thomas & Bornholt, ASPLOS 2024,
DOI [10.1145/3617232.3624873](https://doi.org/10.1145/3617232.3624873))
used Ruler to generate 300 rules (vs. Diospyros's **28 hand-written**, a
second scale anchor for §7), and that firing all 300 naively exhausts 64 GiB
on a 2×2 convolution with no result — while Isaria itself solves the same
problem in 3 seconds at 0.2 GiB. This research read past page 6 into the
paper's actual mechanism.

### 3.1 The mechanism: offline, cost-based, three static phases

Not ILP, not a learned/ML priority ranking, not manual semantic
categorization. Isaria's own §3 rejects a "look at the rule's root node
shape" strawman because it fails on rules that are semantically
optimization-only but syntactically nest a vector node. Instead, **every
Ruler-synthesized rule gets two scalar metrics** computed from a user-supplied
*strictly monotonic* cost function `C` (the same style of cost model OSIL's
own `optimizer/src/main.rs` already uses for `chain`/`lanes` realizations):

- **cost differential** `C_D(P⇝Q) = C(P) − C(Q)`
- **aggregate cost** `C_A(P⇝Q) = C(P) + C(Q)`

Assignment: if `C_D > α` → **Compilation** phase (rewrites that meaningfully
lower a program's cost, e.g. scalar→vector lowering); else if `C_A > β` →
**Expansion** phase (exploring scalar rewrites of the yet-unvectorized
program, generally expensive both sides); else → **Optimization** phase
(cheap improvements to an already-vectorized program). `α`/`β` are the only
tuning knobs, chosen by inspecting the cost model (e.g. `β` set between
scalar-add and vector-add cost); pushing them to extremes collapses Isaria
back to Diospyros's undifferentiated single-phase search.

### 3.2 The algorithm (`Compile(P, R)`, Isaria's Fig. 3)

Loop: `EqSat(E, R_Expansion)` → `EqSat(E, R_Compilation)` → `Extract`; break
if cost stops improving; finally one pass of `EqSat(E, R_Optimization)`.
**Each phase-loop iteration reseeds a fresh e-graph from only the single
best-extracted term of the prior iteration** ("pruning," §3.3) — discarding
everything but the current-best solution between iterations. This is
explicitly greedy (the paper's own word) and sacrifices completeness for
tractability. These are **separate, sequential equality-saturation runs**,
not a single run with dynamic mid-saturation rule toggling — an important
implementation-level clarification: the phases are whole `EqSat` calls
chained together, not a scheduler operating inside one saturation loop.

### 3.3 Online vs. offline, precisely

**Rule generation and phase assignment are offline** — one Ruler run plus one
cost-metric pass over the output, done once, independent of any target
program. **Scheduling/application is online**, at compile time, per input
program — the `Compile` loop runs with a 180-second timeout per `EqSat` call,
degrading gracefully rather than exhausting memory.

### 3.4 Ablation evidence isolating the scheduler as causal (§5.2, direct quotes)

- **Phases removed** (single `EqSat` call over the union of all 300 rules):
  *"even our smallest benchmark quickly runs out of memory, and no benchmark
  successfully saturates... none of these solutions for any benchmark used
  any vector instructions. Phases are therefore essential to making Isaria
  practical on even the smallest benchmarks."*
- **Pruning removed** (retaining one e-graph across the phase loop instead of
  reseeding from the best extraction): smaller benchmarks run out of memory;
  *"no benchmarks ran out of memory with pruning enabled."*

Both ablations isolate the scheduler mechanism itself — not merely "fewer
rules" — as what prevents the blowup.

### 3.5 Generality

Isaria's own Discussion (§7) states an **expectation**, not a demonstrated
result: *"We expect these techniques would generalize to other applications
of Ruler for compilation."* No second domain is evaluated in the paper. This
should be read as a plausible hypothesis from the authors, not evidence.

### 3.6 Artifact

**No public Isaria repository was found** — checked directly against the
15-page PDF (full-text search for "artifact," "available," "github,"
"zenodo," "license" returns zero hits referencing Isaria's own code). Isaria
reuses Diospyros's egg-based front/back-end and Ruler for synthesis, but
Isaria's own phase-selection/`Compile` implementation (reported as 1,113 LOC
offline + 819 LOC online) appears unreleased. `ASSUMPTION` (bounded search,
not exhaustive — a separate GitHub search beyond the PDF itself was not run):
no Isaria artifact exists publicly as of this research date.

---

## 4. Rule validation soundness — residual risk

Ruler's own soundness story, stated precisely (not inferred): cvec/fuzz
testing is a **pre-filter only**; SMT (Z3) is what actually establishes
soundness, and is used "where the domain admits it" per §3.4's own hedge
("small domains model checking, larger SMT, undecidable domains give up the
guarantee and sample"). The paper's §6.2 sensitivity study, with the concrete
Table 2 instance described in §1.4, is the strongest evidence of the residual
risk available anywhere in this research: it is the paper's own authors
reporting that, in at least one evaluated configuration, fuzzing-only
validation **did admit an unsound candidate**, caught only by a second,
independent internal check — not a hypothetical the paper raises and then
dismisses. Their own conclusion stands as the field's clearest statement of
the risk: *"fuzzing alone cannot guarantee soundness in general."* Chompy's
later design choice — gating every candidate, including LLM-proposed ones, on
"syntactically and semantically (Z3) valid" — is a direct continuation of
this lesson: the field has converged on SMT as the load-bearing soundness
mechanism, with cvecs as an efficiency pre-filter only.

**No third-party report of a shipped (post-release) unsound Ruler/Enumo rule
was found** — 15 open GitHub issues on the shared repo, most recent activity
within weeks of this research, none describing a soundness escape that
reached a downstream user. `ASSUMPTION` (falsifiable): this is a
bounded-search negative result, not a systematic audit of the issue tracker's
full history. The one confirmed unsound-rule event (§1.4/Table 2) was caught
during Ruler's own evaluation, before shipping — i.e. the validation pipeline
did eventually work as intended in the one documented instance, but only
because a second check existed behind the fuzzing pre-filter.

**No published rule-synthesis case study targets IEEE-754 floating point
directly** (NaN/Inf/signed-zero/reassociation) — the only FP-adjacent work
(Ruler→Herbie, Enumo→Herbie) synthesizes over exact rational arithmetic and
relies on Herbie's separate, hand-built regime/rounding machinery for the
actual float soundness story. This is a load-bearing gap for OSIL specifically
because OSIL's own most guard-sensitive hand-written rule — the
`numeric_semantics = reassociable`-gated `reduce-to-lanes` rewrite in
`optimizer/src/main.rs` — is precisely an FP-reassociation rule. No tool
surveyed has been run on this exact class of problem.

---

## 5. The guard/side-condition problem — decisive finding

**Ruler and Enumo emit only unconditional equational rules, as a
rule-representation matter — stated directly by Ruler's own paper (§7), not
only inferred from a workaround.** Where a domain has partiality or a
regime-dependent legality condition, the field's answer is to push the
condition **into the term grammar itself** — Ruler's own footnote 7 states
Halide's `x/0=0` semantics *"can easily be encoded using the `ite`
operator"* — rather than attaching an external side-condition to the rule.
Enumo's "conditional rules" (§2.4) are the same move formalized: the guard is
an `if`-expression **inside** the rewritten term, not a predicate gating
whether the rule fires.

**This is structurally close to — but not identical to — what OSIL already
does by hand in two different places, at two different strata:**

1. In `optimizer/src/main.rs`, the `numeric_semantics = reassociable` guard is
   handled by **Rust-level conditional inclusion**: the `reduce-to-lanes-*`
   rules are pushed into the `rules()` vector only when the guard map contains
   the right key/value, *before* the e-graph or synthesizer ever runs. This is
   exactly the same shape as "synthesize a separate rule set per domain
   instance" — i.e., compatible with Ruler/Enumo's native output if a
   **separate synthesis run is made per numeric regime** and each output rule
   set is wrapped by the existing Rust-level (or egglog-level) conditional
   inclusion mechanism, by a human, before it enters the corpus.
2. At the spec/egglog level (`tools/egraph_roundtrip.py`), `guards { k = v }`
   compiles to a **nullary Datalog relation fact**, asserted once per e-graph
   run and attached to the rewrite as a condition via egglog's
   `rewrite(lhs).to(rhs, *conds)` (ADR-0009). This is a genuinely engine-level
   conditional mechanism — and it is **more expressive, in the global sense,
   than anything Ruler or Enumo natively emits**: neither tool has any concept
   of "this rule is licensed only when an external fact holds." OSIL's own
   architecture is ahead of the synthesis tooling on this specific axis.

**What neither Ruler nor Enumo can do, and what OSIL does not currently need
but should not assume it will get for free later: a genuinely conditional
rule whose precondition is checked *per match*, against the bound variables of
that specific instance** (e.g. "`a - b = a + (-b)` only when `a` and `b` are
both provably finite at this program point," as opposed to "only when a
global regime fact holds for the whole run"). **This is Chompy's specific
target** (github.com/ninehusky/chompy, targeting FMCAD 2026): candidate
preconditions are validated via an implication-lattice
(`implication.rs`/`implication_set.rs`) built on egglog as a Datalog backend,
soundness via Z3, and matching restricted to inputs satisfying the candidate
precondition ("pvec matching"). Chompy targets Halide's **Caviar** term-
rewriting system specifically — a hand-written ruleset of **1,579 rules, of
which roughly 74% are conditional** — and reportedly subsumes up to **73.3%**
of it. (Two independent research lines converged on the Caviar name and
these figures independently, raising confidence above a single-source flag.)
Chompy itself, checked directly: a **thesis-stage, single-maintainer
artifact** (single-digit GitHub star count, dozens of open issues, MIT
licensed, thousands of commits reflecting active but solo development).
Pre-publication (FMCAD 2026) and **not integrated with mainline Ruler/Enumo**
— not a tool to adopt today.

**Net finding for OSIL: the practical path, if synthesis is ever attempted, is
"synthesize an unconditional rule set per declared regime, then wrap each
output rule with OSIL's own already-built external-guard machinery" — not
"wait for a tool that natively emits `guards { regime = ... }`-shaped
rules."** No tool does that natively; OSIL's own architecture already
supplies the missing piece. What remains genuinely unproven is whether
Ruler/Enumo-style synthesis produces *sound* rules when the target regime is
actually IEEE-754 floating point (§4) — that would be new ground, not an
established recipe.

---

## 6. 2024–2026 currency, including LLM-assisted rule proposal

- **EGRAPHS 2024**: "Towards Relational Contextual Equality Saturation"
  ([pldi24.sigplan.org](https://pldi24.sigplan.org/details/egraphs-2024-papers/3/Towards-Relational-Contextual-Equality-Saturation))
  conditions rules on term *context* (where a subterm sits structurally), a
  different problem from OSIL's value-level regime guards — noted, not a hit.
- Isaria's synthesis+scheduler work was also given as an informal EGRAPHS
  community-meeting talk, 2024-09-19
  ([egraphs.org/meeting/2024-09-19-isaria](https://egraphs.org/meeting/2024-09-19-isaria))
  — a talk, not a new paper.
- **No 2025 or 2026 EGRAPHS paper on rule synthesis was found** in the
  searches run (2025's "Destructive E-Graph Rewrites" is about in-place
  rewriting mechanics, out of scope). `ASSUMPTION`: bounded-search negative
  result, not an exhaustive proceedings read.
- **LLM-assisted rule *proposal* — one credible 2026 hit, and it does not
  propose rules.** "EggMind" (Chenyun Yin et al., Peking University, arXiv
  2604.17364, April 2026, preprint, unconfirmed code availability). The LLM
  proposes **EqSat strategies/schedules** — rule partitioning, ordering,
  application budget — and explicitly defers actual rule generation to
  "frameworks like Enumo and Ruler." Validation is **runtime/performance-only**
  (cost, memory, wall-clock); there is **no soundness check on anything the
  LLM outputs**, which is consistent with the LLM never touching the trust
  boundary — it schedules already-validated rules, it does not invent new
  ones. Reports 45.1% cost reduction, 69.1% peak-RAM reduction vs. full EqSat
  on 2D-conv/matmul/XLA-tensor/circuit-synthesis benchmarks.
- **Chompy's own LLM-assisted mode**: one research line reported that
  Chompy's artifact also has a mode where LLM-proposed rules are gated
  through the same soundness bar as ordinary synthesized candidates — "kept
  iff syntactically and semantically (Z3) valid." This is a materially
  different (and more defensible) pattern than EggMind's scheduling-only use:
  here the LLM output *does* enter the correctness path, but only ever as an
  unverified proposal subject to the identical Z3 check every other candidate
  passes — the LLM is a hypothesis generator, not a trust source.
- A separate mention of a tool named **"ASPEN"** surfaced in one research
  line's report as further LLM+rule-synthesis-adjacent 2025–2026 work,
  alongside EggMind and Chompy. This was **not independently corroborated**
  by the dedicated newer-work search line, which found only EggMind and
  Chompy through its own targeted searches. `ASSUMPTION` (unverified,
  single-source): flagged as a pointer requiring confirmation, not a
  citation to rely on — a follow-up pass should verify ASPEN's existence,
  venue, and validation methodology before this document's LLM-assisted-work
  survey is treated as complete.
- **Verdict on LLM-assisted synthesis: not yet a validated, trust-worthy
  technique as of this research date, with one interesting exception.** The
  most common 2026 pattern (EggMind) keeps LLM output out of the correctness
  path entirely by restricting it to scheduling. The one pattern that *does*
  let an LLM propose rules (Chompy's LLM mode) does so only by treating the
  proposal as disposable unless it independently passes the same SMT bar
  every other candidate faces — i.e., the LLM never substitutes for
  validation, only for the (cheap-to-be-wrong) enumeration step. No paper was
  found in which an LLM's rule proposal is trusted without independent
  formal validation.
- **Chompy** (already covered §2.6, §5) is the most important 2024–2026 hit
  for OSIL specifically, because it is the sole tool doing per-match
  conditional rule synthesis with an SMT soundness bar — and it is not yet
  usable in production (pre-publication, single-maintainer).
- Tangential, noted only: "Rewrite System Showdown: Stochastic Search vs.
  EqSat" (arXiv 2605.19005, May 2026) compares search *strategies* over a
  fixed, already-known rule set — not rule discovery, out of scope.
- **No 2024–2026 work synthesizing rules specifically for array/loop/
  vectorization domains was found beyond Isaria itself** — EggMind targets
  that domain but for scheduling, not rule discovery.

---

## 7. Applicability verdict

### The honest answer: not yet, and the prerequisite is concrete

OSIL's ratified scalar term language (`Num` sort: `+ - * / << >>`, per
`grammar/osil.ebnf`) has **six operators and six hand-written equivalences**,
one per structurally distinct algebraic fact (associativity, strength
reduction, inverse, identity, shift-zero, stage-commute). The optimizer probe
(`optimizer/src/main.rs`) adds a second, much smaller and explicitly
provisional term language (`Num`/`Get`/`Mul`/`Add`/`Reduce`/`Chain`/`Lanes`)
with **five hand-written rules**, and its own README states plainly: *"n=1.
One kernel, one operator, one width. Nothing here generalizes yet"* and flags
its own SIR reader as *"not grammar-legal... a throwaway reader; delete it
when the spec catches up."* Eleven hand-written rules total, across both
strata.

Every tool surveyed here exists to solve a problem OSIL does not yet have,
and the scale gap is not subtle. For calibration: **Diospyros ships 28
hand-written rules; Herbie roughly 52** — both are the *smallest* hand-curated
rule sets among the tools/systems surveyed in this document, and both already
sit 2.5×–5× above OSIL's current total. Ruler and Enumo are built for
grammars with **dozens to hundreds of operators/rules** where hand-writing
stops scaling — Enumo's own headline example is subsuming 80–90% of a
**300+ rule hand-written Halide ruleset**; Chompy targets a **1,579-rule**
hand-written Caviar system. Isaria's scheduler exists to make **300
synthesized rules** tractable against a 32-element unrolled array term.
OSIL's current e-graphs, per its own probe README, run at **8 e-classes / 13
nodes**. There is no rule-writing burden here that automation would relieve;
the six-fixture corpus is not a bottleneck, it is proportionate to a
six-operator language. Attempting synthesis now would mean pointing a tool
built to tame combinatorial rule explosions at a term language too small to
produce one — solving a scaling problem OSIL does not have, for a language
OSIL does not know it will keep.

Three independent facts converge on the same conclusion:

1. **Grammar instability.** Ruler/Enumo need a stable grammar to enumerate
   over. OSIL's own U6 research already concluded that expressing anything
   beyond scalar arithmetic (loops, arrays, vectorization) requires a **new
   term-language stratum** (a Diospyros-style ground-term array/vector sort)
   that does not exist in the ratified grammar yet. Synthesizing rules against
   a grammar that is about to change discards the synthesis effort at the
   next grammar revision.
2. **No FP-regime precedent.** OSIL's single most guard-sensitive rule (the
   `reassociable`-gated lane-splitting rewrite) sits exactly in the one domain
   — IEEE-754 floating point — that no rule-synthesis paper surveyed here has
   targeted directly (§4, §5). Attempting synthesis there first makes OSIL
   the pioneer, not the adopter of settled tooling.
3. **The `never-fabricate-a-pass` invariant.** `conformance/README.md`
   declares this as a standing invariant of the corpus subtree. A synthesized
   rule entering `conformance/corpus/` must clear the same G14 preservation
   fields (`rule_identity`, `equivalence`, `guard_selectivity`,
   `term_extraction`) as a hand-written one — and, per §4's finding, Ruler's
   own authors both state that cvec/fuzz validation alone cannot guarantee
   soundness *and report a concrete instance where it didn't*. An SMT (Z3)
   verification step would be **required, not optional**, before any
   synthesized rule could ethically enter this corpus. No z3/SMT dependency
   currently exists anywhere in the repo (checked directly this session) —
   this is new infrastructure, not a checkbox.

### The concrete prerequisite

Rule synthesis becomes a sensible next capability when **all** of the
following hold, not before:

1. A term-language stratum is ratified (triple representation: grammar
   production + corpus example, per `CLAUDE.md` rule 3) with enough operators
   that hand-writing every useful equivalence pair becomes the actual
   bottleneck. A concrete, falsifiable calibration point, anchored to the
   *smallest* hand-curated rule sets among the tools surveyed here (Diospyros:
   28 rules; Herbie: roughly 52): **when a ratified grammar stratum's
   hand-written ruleset grows past roughly 20–30 rules**, and the
   corpus-gardener loop's own candidate-pair count exceeds what a human
   comfortably reviews per release cycle. The exact threshold remains the
   maintainer's call; this is a calibration anchor, not a rule.
2. A **Z3-backed validation harness** exists as new project tooling (e.g.
   `tools/rule_synthesis_check.py`), extending G14's preservation fields with
   a fifth, `smt_verified`, that must hold before a synthesized candidate is
   even proposed for human review — mirroring Chompy's "kept iff syntactically
   and semantically (Z3) valid" bar, not Ruler's weaker cvec-only default.
3. An ADR decides the **process**, not just the tool: synthesis should run
   **per declared regime** (one Enumo invocation for `ExactArithmetic`, a
   separate one — if and when attempted — for a domain that actually models
   IEEE-754 reassociation semantics), with every output rule **manually
   reviewed and guard-wrapped** by a human using OSIL's existing external-fact
   guard machinery before corpus entry. This preserves "corpus is
   hand-curated, machine-assisted" rather than converting it to
   "corpus is machine-generated" — a posture change the six-fixture corpus's
   own provenance-header discipline (`// provenance: ...` on every fixture)
   suggests the project has not decided to make.

### Tool recommendation, if/when triggered

**Enumo, not raw Ruler.** Same actively maintained (MIT, last push
2026-08-16), same repository, same underlying cvec/SMT validation core, but
with the `Plug`/`Filter`/workload mechanism needed to keep synthesis scoped
to OSIL's small, deliberately curated term strata instead of triggering an
Isaria-style unguided explosion. Isaria's phase-ordering scheduler (§3) is a
**blueprint worth keeping in reserve**, not something to build now — it
exists to solve a 300-rule/tens-of-thousands-of-nodes problem OSIL is nowhere
near; revisit it only if/when OSIL's own e-graphs start approaching the scale
where Diospyros-style timeouts became routine (U6's own finding: "half of
Diospyros's benchmarks timeout"). Chompy (conditional, per-match rule
synthesis) is a **2027-or-later dependency to watch**, not a 2026 tool — it is
pre-publication and single-maintainer today.

### Bottom line

**Not yet.** The prerequisite is concrete and two-part: (1) grammar/corpus
growth to a scale where hand-writing rules is genuinely the bottleneck —
which OSIL is not at, by roughly an order of magnitude even against the
*smallest* hand-curated reference sets surveyed (Diospyros's 28, Herbie's
~52, both 2.5×–5× above OSIL's current 11) — and (2) a Z3-backed validation
harness as new, not-yet-built tooling, required by the corpus's own
`never-fabricate-a-pass` invariant before any synthesized rule could enter a
suite that doubles as the project's conformance gate. Neither Ruler nor Enumo
natively emits rules shaped like OSIL's own `guards { regime = ... }`
mechanism, but this is not a blocker — OSIL's existing external-fact guard
architecture (ADR-0009) is already more expressive on this specific axis
than anything the tools produce natively, so the missing piece is process
(per-regime synthesis runs, human guard-wrapping), not new engine machinery.
The one place synthesis would be genuinely novel research rather than
routine tool application — FP-reassociation-regime rules — is also OSIL's
most safety-sensitive guard, which argues for waiting until the general
prerequisite is met before using that domain as the first target.

---

## Citations

1. Chandrakana Nandi, Max Willsey, Amy Zhu, Yisu Remy Wang, Brett Saiki, Adam
   Anderson, Adriana Schulz, Dan Grossman, Zachary Tatlock. "Rewrite Rule
   Inference Using Equality Saturation." *PACMPL* 5, OOPSLA, Article 119
   (2021). Code: https://github.com/uwplse/ruler (MIT; confirmed active,
   last push 2026-08-16, 15 open issues).
2. Anjali Pal, Brett Saiki, Ryan Tjoa, Cynthia Richey, Amy Zhu, Oliver Flatt,
   Max Willsey, Zachary Tatlock, Chandrakana Nandi. "Equality Saturation
   Theory Exploration à la Carte." *PACMPL* 7, OOPSLA2, Article 258 (2023).
   DOI: [10.1145/3622834](https://doi.org/10.1145/3622834). Code: same repo
   as (1), `tests/recipes`.
3. Samuel Thomas, James Bornholt. "Automatic Generation of Vectorizing
   Compilers for Customizable Digital Signal Processors." ASPLOS '24. DOI:
   [10.1145/3617232.3624873](https://doi.org/10.1145/3617232.3624873). PDF:
   https://jamesbornholt.com/papers/isaria-asplos24.pdf. (Already cited in
   U6 for the 300-rule/64 GiB finding; this document adds the §3
   phase-ordering-scheduler mechanism, read directly from the full PDF.)
   Artifact: none found (`ASSUMPTION`, bounded search).
4. `ninehusky/chompy` — "Conditional Rewrite Rule Synthesis Using E-Graphs
   and Implication Propagation," targeting FMCAD 2026 (pre-publication as of
   this research date). Repo: https://github.com/ninehusky/chompy (MIT,
   active, single-maintainer/thesis-stage).
5. Chenyun Yin et al. "EggMind" (working title as cited by search hit).
   arXiv:2604.17364 (April 2026, preprint). LLM-proposed EqSat scheduling,
   not rule synthesis; code availability unconfirmed.
6. "Towards Relational Contextual Equality Saturation." EGRAPHS 2024
   (PLDI workshop). https://pldi24.sigplan.org/details/egraphs-2024-papers/3/Towards-Relational-Contextual-Equality-Saturation
   — noted for scope-adjacency only, not a rule-synthesis hit.
7. Isaria community-meeting talk, EGRAPHS meeting, 2024-09-19.
   https://egraphs.org/meeting/2024-09-19-isaria — pointer only, not a paper.
8. "Rewrite System Showdown: Stochastic Search vs. Equality Saturation."
   arXiv:2605.19005 (May 2026). Extraction/search comparison over a fixed
   ruleset — not rule discovery; noted for completeness only.
9. "ASPEN" — name only, surfaced by a single research line, not
   independently corroborated. `ASSUMPTION`, unverified; see §6.
10. Repo context read directly this session: `optimizer/README.md`,
    `optimizer/src/main.rs` (the `rules()` function — 5 hand-written
    guard-gated rewrites), `conformance/corpus/003, 009, 013, 014, 015, 020`
    (the six hand-written equivalences), `conformance/README.md`
    (`never-fabricate-a-pass` invariant), `tools/egraph_roundtrip.py` (the
    `guards { k = v }` → nullary-relation mechanism, ADR-0009),
    `docs/decisions/ADR-0007-numeric-regime-concepts.md`, `docs/GATES.md`,
    `improvable/INDEX.md`, `docs/research/U6-egraph-vectorization-prior-art.md`
    (already-established Isaria 300-rule/64 GiB finding, cited not repeated).

---

## Validity & limitations

**Valid as of:** 2026-08-24. **Re-evaluate if:** (1) Chompy publishes at
FMCAD 2026 and/or merges with mainline Ruler/Enumo — would materially
strengthen the guard/side-condition story and should trigger a follow-up
unknown; (2) any tool is run against an actual IEEE-754 floating-point
reassociation domain — currently unattempted anywhere found; (3) OSIL's own
term-language grammar grows a second or third stratum with enough operators
to make the "not yet, by an order of magnitude" comparison in §7 close;
(4) ASPEN (§6, citation 9) is confirmed or refuted as a real, separate
contribution; (5) a genuine LLM-proposes-rules-with-independent-formal-
validation paper appears beyond Chompy's own LLM mode.

**Limitations of this research:** (1) Isaria's artifact/code-availability
finding (§3.6) is a bounded PDF-text-search negative result, not a
systematic GitHub search — flagged `ASSUMPTION`. (2) Chompy's Caviar-scale
figures (§5: 1,579 rules, 74% conditional, 73.3% subsumed) were corroborated
by two independent research lines rather than a single one, which raises
confidence relative to an earlier internal draft of this document, but
neither line independently re-verified the figures against Chompy's own
repository/paper text directly — still flagged `ASSUMPTION`, now
cross-corroborated rather than single-sourced. (3) The EGRAPHS
2022/2023/2025/2026 proceedings were not read exhaustively line-by-line; the
"no other rule-synthesis hit" conclusions in §6 are bounded-search negative
results. (4) "ASPEN" (§6, §9) is a single-source, unverified pointer — treat
as unconfirmed until independently checked. (5) Ruler's §3.3/§3.4/§6.2/§7
content in this document was surfaced convergently by three independent
research lines, one of which (Gap A) performed a dedicated, thorough
full-paper read (30 tool calls); the other two encountered the same sections
incidentally while investigating Enumo and conditional rules respectively.
All three converge without contradiction, which is why this document treats
the Ruler-mechanics findings as high-confidence despite arriving via parallel
rather than single-threaded investigation.

**Epistemological note:** every load-bearing claim about Ruler, Enumo,
Isaria's scheduler, and Chompy in this document traces to a direct
primary-source PDF/repository read performed by one of five parallel
research lines, cross-checked for convergence where more than one line
touched the same source. Where a finding rests on a single line or a
bounded (not exhaustive) search, it is marked `ASSUMPTION` in place, per this
project's own evidence-hierarchy discipline.
