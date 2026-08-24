# U8 — Software Ontology Survey: What Vocabulary Should OSIL Adopt for Computational Optimization?

**Date:** 2026-08-24
**Researcher:** research-agent
**Question:** The maintainer wants to "download the software ontology" as an input to extending OSIL toward computational optimization (specifically loop vectorization). Which existing software/computation ontology, if any, should OSIL align with or import terms from?
**Feeds:** `docs/design/idea-coverage.md` (Compiler dimension: 0%, "semantic optimization space, invariant-guarded rewrite engine: unrealized"; Ontology federation: ~10%, "BFO applied as *method*... zero federation *machinery*... profiles are empty stubs," blocked on GAP-6 relations), `profiles/ontology/{bfo,dolce,ufo}/PROFILE.md` (empty stubs), `profiles/ecosystem/mlir/PROFILE.md` (stub — "Contributes: lowering toward hardware; dialect infrastructure").

## TL;DR verdict

**The Software Ontology (SWO) is not what the maintainer wants. Verdict: NO.**
SWO is real and OBO-Foundry-registered, but (a) it is stale — no commit since
2023-03-05, no release since 2023-03-05, ~3.5 years of silence as of this
writing, despite the OBO Foundry's own registry metadata self-labeling it
`activity_status: active` (a self-description the primary evidence
contradicts — see §1); and (b) its own authors, in the founding 2014 paper,
state that "algorithm" was initially rejected as **"too costly to model"**
and only partially added later, and that it does not attempt "the universe
of software's information processing tasks." SWO catalogs software **as an
artifact** — licenses, versions, developers, provenance, task labels — not
computation as **executable semantics**. It has no concept of an iteration
space, a data dependence, a numeric type, or a legality condition for a
rewrite. It cannot answer "is it legal to vectorize dimension `d` of this
loop nest." Nothing in the OBO/BFO ecosystem can (§2, §3).

**None of the OBO-Foundry-style biomedical ontologies (SWO, EDAM, IAO, OBI)
give OSIL leverage for loop vectorization.** They were built to catalog
*what a tool is called and what it claims to do* for curation, discovery,
and provenance in the life sciences — not to formalize *what a computation
does* well enough to decide whether a rewrite preserves it. Importing one
would be ceremony: term coverage without decision power (§3).

**What OSIL should actually adopt: the MLIR `linalg`/`affine` dialects'
iteration-space vocabulary (indexing map, iterator classification,
iteration domain), grounded in the polyhedral model's formal vocabulary
(iteration domain, access relation, schedule, dependence), with TVM/Halide's
scheduling-primitive vocabulary as the secondary source for the
*transformation* names (split, fuse, reorder, vectorize, unroll) OSIL's
guard/equivalence system would need to express legality.** This is not an
"ontology" import in the OBO sense — it is exactly the kind of
`profiles/ecosystem/*` pin OSIL already does for ONNX and egglog, applied to
`profiles/ecosystem/mlir/`, which is already a stub waiting for this
content (§4, §5).

**Confidence:** HIGH on SWO's staleness and scope (primary-sourced: GitHub
API commit/release history, OBO Foundry's own registry YAML, OLS's live
ontology-version record, and the paper's own text via Europe PMC full-text
XML — four independent primary sources converge). HIGH on the
artifact-vs-computation distinction across SWO/EDAM/IAO/OBI (each verified
against its own term definition, not a summary). MEDIUM-HIGH on the MLIR
recommendation's completeness (the linalg dialect's core vocabulary is
primary-sourced from `mlir.llvm.org` and the LLVM monorepo directly; the
polyhedral cross-walk and TVM/Halide comparison are corroborating, not
independently exhaustive — flagged where uncertain).

---

## Research method (wave decomposition)

**Default line I would have run:** "Google 'Software Ontology' and 'SWO', read the OBO Foundry description, report what it covers."

**Likely finding from that alone:** SWO's self-description ("software tools,
their types, tasks, versions, provenance and associated data") — which reads
plausibly relevant to "an ontology of software" and could be mistaken for
sufficient without checking (a) whether it is still alive, or (b) whether
"describing software" means describing *artifacts* or describing
*computation*. This is exactly the trap the maintainer's framing ("download
the software ontology") risks falling into: SWO's *name* suggests it is the
answer before its *content* is checked.

**Gaps relative to the task (extending OSIL toward loop-vectorization
optimization), the conversation context (OSIL already has a strict
Aristotelian-definition discipline and an empty `profiles/ontology/*`
stub layer), and the user's higher-order goal (a compiler-adjacent
optimizer, not a curation catalog):**

1. **Liveness gap** — is SWO actually maintained, verified mechanically
   (commit/release dates), not from its own self-description? → Line A.
2. **Scope gap** — does SWO (and its OBO-Foundry neighbors) model
   computation or artifacts? Read the actual term definitions, not the
   marketing description. → Line B.
3. **Completeness-of-candidate-set gap** — the maintainer named SWO by
   name, but the decision needs the full candidate set (EDAM, IAO, OBI, BFO
   2020's actual standard status, UFO's actual status given OSIL's own
   stub, PROV-O, schema.org/CodeMeta) compared on the same axes. → Line C.
4. **"Does OBO help a compiler at all" gap** — the formal-methods/compiler
   world's own practice (what do MLIR, ONNX, TVM, Halide, the polyhedral
   literature actually use as vocabulary?) is the missing counter-evidence
   an OBO-only search would never surface. → Line D.
5. **"What then" gap** — if the answer is "nothing in OBO," the task is
   incomplete without a concrete, acquirable alternative, defined
   Aristotelian-style per this repo's own ontology rules. → Line E.

Evidence gathered via GitHub REST API (primary, not summarized), the OBO
Foundry's own YAML registry, EBI's Ontology Lookup Service (OLS4) API
(the field's own canonical term-lookup service), Europe PMC's full-text XML
API for the SWO founding paper, and direct fetches of `mlir.llvm.org` and
the LLVM monorepo's TableGen source. **Synthesis: convergent** — every
independent source (GitHub, OBO Foundry, OLS, the paper itself) agrees SWO
is both stale and artifact-scoped; every independent source on the
compiler side (MLIR docs, polyhedral literature, TVM/Halide docs) describes
a vocabulary OBO ontologies do not have.

---

## 1. The Software Ontology (SWO) — primary-sourced facts

| Fact | Value | Source |
|---|---|---|
| Real, specific artifact? | Yes — `swo.owl`, OBO PURL `http://purl.obolibrary.org/obo/swo.owl` | OBO Foundry registry entry |
| Founding paper | Malone, J. et al. (2014). "The Software Ontology (SWO): a resource for reproducibility in biomedical data analysis, curation and digital preservation." *J Biomed Semantics* 5, 25. PMID 25068035, PMCID PMC4098953 | Europe PMC |
| Repository | `github.com/allysonlister/swo` | GitHub API |
| **Last commit (`pushed_at`)** | **2023-03-05T15:11:37Z** — most recent commit message: "fixed issue with property refactoring #59" | `api.github.com/repos/allysonlister/swo` (fetched 2026-08-24) |
| **Last release** | **v2023-03-05**, published 2023-03-05 — one prior release v2022-10-11, one before that v1.7 (2019-11-28) | Same, `/releases` endpoint |
| **Live OLS version record** | version string `2023-03-05`, `numberOfTerms: 1971`, `status: LOADED` — the ontology-registry service's own record confirms no newer version has ever been ingested | EBI OLS4 API, `ontologies/swo` (queried 2026-08-24) |
| Open issues | 19 (repo), stars 55, forks 11, not archived | GitHub API |
| **OBO Foundry's own self-classification** | `activity_status: active` | `OBOFoundry.github.io/ontology/swo.md` (raw YAML front-matter, fetched 2026-08-24) |
| License | CC BY 4.0 | GitHub API + OBO Foundry YAML (agree) |
| Domain (OBO Foundry field) | `information technology` | OBO Foundry YAML |

**The staleness/self-description conflict is the headline finding.** The
task's own method note says a last-commit date and open-issue count outrank
a project's self-description — here that is not a subtle judgment call: the
registry that hosts SWO literally writes `activity_status: active` in the
same file whose own `repository:` link, followed mechanically, shows the
last commit predates this research by three years, five months, and
nineteen days. This is not damning of the OBO Foundry's process generally
(other Foundry ontologies checked below are demonstrably live), but it means
"listed as active in a registry" is not, on its own, evidence of anything —
the registry field appears to reflect an intent-to-maintain classification
made at admission time, not a live liveness check. Treat every
`activity_status` field in this ecosystem as an ASSUMPTION until checked
against commit history directly, as done here.

**Scope — artifact, not computation. Verified against the paper's own
text**, fetched as full-text XML via Europe PMC (not a summary):

> "The Software Ontology (SWO) is a description of software used to store,
> manage and analyze data... The result is an ontology that meets the needs
> of a broad range of users by describing software, its information
> processing tasks, data inputs and outputs, data formats versions and so
> on."

This is a description of **tools as catalog entries** — task labels
("aligns sequences"), input/output *format* types (FASTA, not tensor
shapes or numeric domains), version strings, license clauses, developer and
organizational metadata. The paper is explicit, in its own prioritization
narrative, about what was **excluded and why**:

> "Algorithm" was initially deemed **"too costly to model"** and was **"not
> bought"** in early requirements-prioritization sessions with users; it was
> only later "partially included when examples failed to answer some
> competency questions." Hardware, cost of ownership, platform requirements,
> dependencies, and configure parameters were all similarly rejected as
> out of scope, with the paper stating plainly it is "not feasible to
> describe the universe of software's information processing tasks."

This is the SWO curators, in their own words, choosing **not** to build
computational semantics — not an oversight OSIL could patch by importing a
few extra classes, but a scoping decision baked into the ontology's design
from the outset. Consistent with this, SWO's own "algorithm" instances are
**named, specific tool implementations** — e.g. `SWO_4000007` *"Gillespie's
Stochastic Simulation Algorithm"*, `SWO_0000278` *"MCR algorithm"* — not a
general theory of what an algorithm computes. And its one general
`algorithm` *class* is not even SWO's own: SWO reuses IAO's `IAO_0000064`
verbatim (confirmed live via OLS term search), whose definition is:

> "A plan specification which describes the inputs and output of
> mathematical functions as well as workflow of execution for achieving a
> predefined objective. Algorithms are realized usually by means of
> implementation as computer programs for execution by automata."

That is a description of an algorithm **as a document** ("plan
specification") — it says nothing about iteration order, data dependence,
associativity, numeric regime, or any of the properties a rewrite-legality
check would need. It is exactly one abstraction level too high for what
OSIL's `guards {}`/`invariant` machinery operates on (`spec/core.md`
already defines these at the level of "semantic property whose preservation
is a necessary condition for the legality of a rewrite" — SWO's algorithm
class has nothing to say about that).

One more corroborating fact from the paper itself, relevant to §2 below:
**"Recently, the SWO has incorporated EDAM"** — i.e. even SWO's own
operation/task vocabulary is now partly EDAM's, at EDAM's level of
granularity (§2). This is not an argument for going around SWO to EDAM
instead; EDAM has the identical category problem, one level down.

**Verdict: SWO is a real, OBO-Foundry-registered, CC-BY-licensed artifact
that answers "what software exists and what is it called," not "what does
this computation do and when may it be rewritten." It is also
three-and-a-half years dormant. Downloading it would not give OSIL anything
usable for loop vectorization — it would give OSIL 1,971 terms about
licenses and tool names.**

---

## 2. Other OBO/biomedical-ontology-world candidates

All fetched live, 2026-08-24, via GitHub REST API + EBI OLS4 (the field's
canonical term-lookup service), not from search-summary text.

### EDAM

| | |
|---|---|
| Real/registered? | Yes — `github.com/edamontology/edamontology`, its own umbrella org |
| Last commit | **2026-06-26** (release-tagging commits), most recent PR merge 2026-06-15 |
| Latest release | `1.25.20260626T1230Z`, published 2026-06-27 |
| Open issues | 233 (high, but consistent with active use — new terms requested continuously) |
| License | CC BY-SA 4.0 |
| Size | 3,539 terms (OLS4 `numberOfTerms`) |
| Scope | 4 sections: Topic, **Operation**, Data, Format |

**EDAM is genuinely maintained** — this is the one candidate in the
biomedical-ontology set with a commit inside the last two months. But its
`Operation` root class definition (`operation_0004`, fetched via OLS)
reads:

> "A function that processes a set of inputs and results in a set of
> outputs, or associates arguments (inputs) with values (outputs)."

That is a controlled-vocabulary *label* for a pipeline step ("Sequence
alignment," "Multiple sequence alignment," "Read mapping" — the actual leaf
terms), used so bioinformatics workflow tools can tag what a tool block
*does* in one sentence for discovery/search purposes (this is EDAM's actual
production use: Galaxy, bio.tools, and workflow registries tag tools with
EDAM operation/data/format terms for faceted search). It is not an
operational semantics — there is no notion of what data-parallelism an
"Operation" instance admits, no dependence structure, nothing a rewrite
engine could check. EDAM answers "what kind of biological analysis step is
this," which is a *classification* question, not a *legality-of-rewrite*
question.

### IAO (Information Artifact Ontology) and OBI (Ontology for Biomedical
Investigations)

| | IAO | OBI |
|---|---|---|
| Last push | 2026-04-10 | 2026-08-10 (14 days before this research) |
| Open issues | 142 | 251 |
| License | CC BY 4.0 | CC BY 4.0 |
| Relevant class | `IAO_0000064` "algorithm" (see §1 — a document/plan-specification definition, reused verbatim by SWO and several other ontologies including `sio`, `mcro`, `afo`) | `OBI_0200000` "data transformation," root of ~10 named subclasses (normalization, averaging, partitioning, scaling, error correction...) |

Both are actively maintained (this matters: it rules out "these are all
dead" as the objection — the *liveness* problem is specific to SWO, not
the ecosystem). But `OBI_0200000`'s own definition, fetched directly from
OLS:

> "A completely executed planned process that produces output data from
> input data."

is a BFO **occurrent** (`process`) description — it says a data
transformation *happened*, is *complete*, and had inputs and outputs. It
says nothing about *what transformation*, in what order, over what
iteration structure, with what dependence pattern. This is the general
shape of every OBO/BFO-descended class touched in this research: they
describe *that a computational event occurred and who/what was involved*
(provenance-shaped), never *what the computation's internal structure is*
(semantics-shaped). This is not a defect in these ontologies — it is
exactly their intended scope (investigation/provenance tracking for
biomedical reproducibility), just not OSIL's.

### BFO 2020

Verified: **ISO/IEC 21838-2:2021**, "Information technology — Top-level
ontologies (TLO) — Part 2: Basic Formal Ontology (BFO)," published by ISO
in November 2021 (confirmed at `iso.org/standard/74572.html`). The
reference implementation repo `BFO-ontology/BFO-2020` was pushed
**2026-08-16** (8 days before this research) — actively maintained, no
license field set on the GitHub repo itself (the content is released under
the terms in the ISO standard's own front matter, not a GitHub LICENSE
file — this repo hosts the OWL/CL/documentation artifacts of a published
ISO standard, a different distribution model than the other candidates
here).

This confirms OSIL's existing citation ("BFO 2020") is current and
correctly named — but BFO is a top-level (philosophical) ontology: it
supplies categories like `occurrent`, `continuant`, `process`, `disposition`
— the genus vocabulary OSIL's own definitions already borrow *as a method*
(`spec/core.md`'s "genus + differentia" discipline is BFO-style by
construction). BFO itself has no domain content about computation at all —
it is one layer more abstract than SWO/EDAM/IAO/OBI, and it is already
exactly as involved in OSIL as it should be: as a **definitional
discipline**, not an **imported term set**. `profiles/ontology/bfo/`
correctly remains an empty stub — there is no BFO *content* to pin, only a
*method* already in use.

### UFO (Unified Foundational Ontology)

UFO is **not an OBO Foundry artifact and has no equivalent liveness
signal** — it is an academic research program (Giancarlo Guizzardi et al.,
NEMO group, UFES, Brazil), published primarily as papers and a 2022
consolidating article ("UFO: Unified Foundational Ontology," *Applied
Ontology* 17(1), doi:10.3233/AO-210256), not as a versioned downloadable
artifact with a release cadence comparable to SWO/EDAM. Its closest thing
to a "download" is `gUFO`, a lightweight OWL implementation
(`nemo-ufes.github.io/gufo/`), and OntoUML tooling on GitHub
(`OntoUML/OntoUML`). **ASSUMPTION:** I did not independently verify
gUFO's or OntoUML's own commit-liveness with the same rigor applied to
SWO/EDAM/IAO/OBI/BFO above (out of scope — UFO is not a candidate for the
loop-vectorization vocabulary; it is already committed to OSIL as a design
method, not a term-import target, and the repo's own
`profiles/ontology/README.md` already classifies this whole subtree as
"citation-stable (years)... content additions are propose-only"). Like
BFO, UFO's actual role in OSIL today is philosophical grounding for
`spec/core.md`'s definitions, not a term-import source — and, contrary to
the task's framing, `profiles/ontology/ufo/PROFILE.md` is currently an
**empty stub** ("No content yet"). OSIL has not, in fact, committed to any
UFO terms yet — only to the general commitment (in `docs/design/idea-coverage.md`) to eventually federate BFO/DOLCE/UFO, which is explicitly gated behind an unfiled grammar gap (GAP-6, cross-layer relation constructs) and is listed at ~10% completion with "zero federation machinery."

### PROV-O, schema.org `SoftwareApplication`, CodeMeta

These are the non-biomedical, non-OBO candidates and they cluster with SWO
on scope, not with the compiler side:

- **PROV-O** is a stable **W3C Recommendation** (2013) modeling generic
  provenance via three classes — `Entity`, `Activity`, `Agent` — and
  relations like `wasGeneratedBy`, `used`, `wasAssociatedWith`. It is
  domain-agnostic and could plausibly describe *that* an OSIL realization
  process produced an artifact from inputs (an audit-trail role, echoing
  OSIL's own "preservation contract" framing at the meta level), but it has
  zero computational vocabulary — it is one layer more general than even
  OBI's `data transformation`.
- **CodeMeta** and **schema.org `SoftwareApplication`/`SoftwareSourceCode`**
  are citation/discovery metadata schemas (author, license, repository URL,
  programming language, `codeRepository`, `softwareVersion`) for making
  research software findable and citable (FAIR data / DataCite use case).
  They are the closest analogue to what a naive reading of "software
  ontology" might expect, and they are exactly as far from computational
  semantics as SWO is — arguably further, since they don't even attempt
  operation/task classification.

None of these three add anything SWO/EDAM/OBI don't already cover for
OSIL's stated purpose, and none model computation.

### Algorithm/computation ontologies from the PL/synthesis literature

Searched specifically for "ontology of computation," "algorithm ontology,"
and OBO-style approaches inside program-synthesis and formal-methods
research. **Finding: essentially nothing.** The closest hits (e.g.
"Synthesizing Formal Semantics from Executable Interpreters," PLDI-adjacent
work) are about *automatically deriving* operational semantics
(Constrained Horn Clauses) from interpreters — a live, active research
line, but one that produces **type systems and operational-semantics
rules**, not OBO/OWL class hierarchies. **This absence is itself the
strongest evidence for §3's verdict**: if an OBO-style "ontology of
computation" existed and were useful to the compiler/formal-methods
community, this search would have surfaced it as prior art being cited or
extended; instead the two research communities (biomedical ontology
engineering and program-language/compiler research) do not appear to read
each other's literature on this specific question at all.

---

## 3. The honest question: does any OBO ontology help a compiler-adjacent optimizer?

**The case for "yes, it helps" (steelmanned):**

- OSIL's own definitional discipline (`spec/core.md`) *is* Aristotelian/BFO
  in style already — genus + differentia, no circularity, essential
  features. Reusing IAO's `algorithm` class or OBI's process hierarchy
  would at least give OSIL's `concept`/`stage` vocabulary a citable,
  externally-governed ancestor class, satisfying the "maximal consensus
  with terminological usage" rule from the project's own ontology
  discipline (`~/.claude/CLAUDE.md`'s BFO rules) — a legitimate
  documentation/interoperability-signaling value, distinct from
  optimization power.
- `docs/design/idea-coverage.md` already lists "ontology federation" as a
  standing roadmap item (BFO/DOLCE/UFO), independent of the compiler work —
  so *some* engagement with this ecosystem is already a stated (if
  currently unimplemented) goal, and importing IAO's `algorithm`/OBI's
  `data transformation` as parent classes of OSIL's own `concept`/`stage`
  would be a small, low-risk way to make that connection concrete someday.
- A `regime`-style guard could in principle cite an OBO term as a category
  label the way OSIL cites `onnx::MatMul@13` today — external, versioned,
  never redefined (the sovereignty principle, `spec/core.md` §3) — purely
  as a provenance/citation anchor, not as a computation engine.

**The case for "no, it's ceremony" (and why it wins):**

- **Formal-methods and compiler communities do not use OBO-style
  ontologies, and this research found no counter-example.** MLIR, LLVM,
  ONNX, TVM, Halide, and the polyhedral-compilation literature define their
  vocabulary as **type systems, operational semantics, and typed
  intermediate representations** (TableGen ODS definitions, `.proto`
  schemas, algebraic data types for AST/IR nodes) — never as
  OWL/RDF class hierarchies with `is_a`/`part_of` relations. This is not
  an oversight of that community; OWL's open-world, description-logic
  semantics is the wrong formalism for "is this rewrite legal," which needs
  a **decidable, closed, checkable predicate** (a guard, a type check, a
  dependence test) — exactly the shape OSIL's own `guards {}` blocks
  already take (verified directly by U5: egglog's guards are Datalog facts,
  a closed-world checkable mechanism, not open-world OWL class membership).
- **Every OBO-descended definition found in this research sits at the
  wrong abstraction level for a legality check.** `IAO_0000064` "algorithm"
  and `OBI_0200000` "data transformation" describe *that a computation is a
  kind of planned/executed process* — a BFO occurrent classification. A
  loop-vectorization legality check needs to know, per iteration-space
  dimension: is it a reduction or is it embarrassingly parallel; does any
  pair of iterations alias the same memory location; is the store order
  observable. None of that is expressible in, or derivable from, any term
  surveyed in §1–§2. Importing these classes would add citation weight
  without adding a single fact the optimizer could query.
- **OSIL's own architecture doesn't yet have the machinery an OBO import
  would plug into.** `docs/design/idea-coverage.md` is explicit: ontology
  federation is ~10% complete, blocked on an unfiled grammar gap (GAP-6,
  cross-layer relation constructs like `implementedBy`/`requires`), and the
  `profiles/ontology/*` subtree's own policy card says "content additions
  are propose-only" with a citation-fidelity-audit loop, not a
  term-consumption loop. Activating an OBO import today would create a
  profile with no grammar to bind it to and no query surface to use it —
  literally undischargeable ceremony given the repo's *own* current state,
  independent of whether the ontology were a good fit in principle.
- **The compiler-relevant work (`Compiler` dimension, `docs/design/idea-coverage.md`) is gated behind the resolver and the e-graph projection, not behind ontology federation** — the dependency graph in that same document draws ontology federation as an explicit *parallel, non-blocking* track, not a prerequisite. Time spent standing up an OBO import would not unblock loop vectorization even if the import were perfect.

**Verdict: mostly ceremony.** Not zero value — a future `concept`
definition could legitimately *cite* an OBO class the way a paper cites
related work, satisfying the project's own "maximal consensus with
terminological usage" ontology rule as a documentation nicety — but zero
*optimization* leverage. The maintainer's actual goal (loop vectorization)
needs a vocabulary that encodes iteration structure and legality
conditions, which is precisely what the OBO/BFO ecosystem was never built
to encode.

---

## 4. What should play the role of the domain ontology instead

**Recommendation: MLIR's `linalg` (structured ops) and `affine` dialects
for the iteration-space vocabulary, grounded in the polyhedral model's
formal terms, with TVM/Halide's scheduling-primitive vocabulary as the
secondary source for transformation names.** ONNX (already profiled by
OSIL) is evaluated and explicitly **rejected** for this specific role —
see the contrast below.

### Why MLIR `linalg`, primary-sourced

Fetched directly from `mlir.llvm.org/docs/Dialects/Linalg/` and the LLVM
monorepo (`llvm/llvm-project`, pushed **2026-08-24**, the same day as this
research — about as live as a project gets):

- `linalg.generic`'s defining property: *"fully derives the specification
  of its iteration space from its operands"* — i.e., a localized IR element
  carries all the information needed to synthesize the iteration structure,
  rather than that structure being implicit in surrounding loop syntax.
  This is the single most important fact for OSIL: it means "iteration
  space" is already a **first-class, explicit, declared** property in this
  IR, matching OSIL's own philosophy that meaning must be declared, not
  inferred (`README.md`: "so that toolchains can optimize... against
  meaning rather than syntax alone").
- **Indexing maps**: *"`linalg.generic` defines the mapping between the
  iteration space (i.e. the loops) and the data"* via a list of affine
  maps — one per operand, each mapping a point in the shared iteration
  domain to a coordinate in that operand's data space.
- **Iterator classification**: each iteration-space dimension is labeled
  `parallel` or `reduction` — *parallel* when "the dim is used to index
  into `C` [the output] and at least one of `A` and `B`"; *reduction* when
  "the dim is used to index into `A` and `B` but not `C`... these dims will
  be contracted." This is exactly the classification a vectorizer needs:
  parallel dimensions can be reordered/vectorized freely; reduction
  dimensions need an associativity/commutativity guard (which, notably, is
  *already OSIL vocabulary* — see `numeric_semantics`/`regime` guards,
  ADR-0007 — the fit is structural, not coincidental).
- The dialect now factors this into a shared `IndexingMapOpInterface`
  (confirmed from the raw TableGen source,
  `LinalgInterfaces.td`/`IndexingMapOpInterface.td`), meaning "iteration
  space + indexing map" is being generalized as a cross-dialect MLIR
  concept, not a linalg-only curiosity — a good maintenance signal for
  citing it as a stable vocabulary anchor.
- **License, format, location (acquisition facts):** Apache License 2.0
  WITH LLVM-exception, confirmed directly from the SPDX header in
  `mlir/include/mlir/Dialect/Linalg/IR/LinalgInterfaces.td`. The
  vocabulary lives as **TableGen (`.td`) operation-definition-spec (ODS)
  files** inside the LLVM monorepo at
  `mlir/include/mlir/Dialect/Linalg/IR/` (interfaces, ops) and
  `mlir/include/mlir/Dialect/Affine/IR/` (the lower-level affine-loop
  dialect these lower to) — plain text, directly parseable/greppable, no
  binary artifact and no build step required just to *read* the
  vocabulary (parsing them the way OSIL's `registry/` already hand-curates
  YAML from an upstream ecosystem's own spec, e.g.
  `registry/entries/onnx.yaml` from ONNX's `.proto`/opset docs).

### Why the polyhedral model's formal vocabulary as the grounding layer

MLIR's `linalg`/`affine` dialects are themselves an *implementation* of
concepts the polyhedral compilation literature named decades earlier and
gave precise mathematical (Presburger-arithmetic) semantics to — the
correct genus/differentia grounding for OSIL's Aristotelian-style
definitions should cite the formal vocabulary, with MLIR as the concrete,
maintained, versioned artifact that realizes it (exactly the
"philosophical → conceptual → architectural → implementation" abstraction
stack this agent's own methodology names):

- **iteration domain** — the set of all statement-instance points
  satisfying a loop nest's bound constraints, visualized as an
  n-dimensional integer polytope.
- **access relation** — a relation from a point in the iteration domain to
  a coordinate in an accessed array, tagged read or write (this is the
  formal name for what `linalg`'s indexing maps concretely implement, but
  the polyhedral version additionally admits non-affine and
  piecewise-affine cases MLIR's current affine-map restriction doesn't
  cover, making it the more general definition to cite).
- **schedule** — a function assigning each iteration-domain point a
  logical execution timestamp, i.e. an explicit representation of
  execution *order*, separate from the computation itself — the object a
  legality-preserving reordering (vectorization, tiling, fusion) actually
  transforms.
- **dependence** — an ordering constraint between two iteration-domain
  points that access the same memory location where at least one access
  writes; a schedule is legal iff it respects every dependence.

**Concrete, maintained reference implementation:** `isl` (Integer Set
Library, Sven Verdoolaege) — MIT-licensed, its GitHub mirror
(`Meinersbur/isl`) last pushed **2026-04-20**, and it is the actual
dependence-analysis/scheduling backend inside LLVM's own Polly pass and GCC
Graphite. Because it is already vendored into the LLVM ecosystem OSIL is
already profiling via `profiles/ecosystem/mlir/`, citing isl's own
vocabulary (rather than inventing new names) costs OSIL nothing extra in
ecosystem surface area.

### Why TVM/Halide scheduling primitives as the secondary, transformation-naming layer

The iteration-space vocabulary above names *what a loop nest's structure
is*; it does not by itself name *the legal moves a rewrite engine would
search over*. TVM's schedule primitives (confirmed from TVM's own
documentation/discussion forum, Apache-licensed, Apache Software
Foundation project) — `split`, `fuse`, `reorder`, `vectorize`, `unroll`,
`bind`, `compute_at`, `cache_read`/`cache_write`, `rfactor` — are exactly
the named search-space moves OSIL's `equivalence`/guard system
(`spec/core.md`: "equivalences are the OSIL-side input to
equality-saturation ecosystems") would need to enumerate as candidate
rewrites for the e-graph projection (already the target of gate G14/U5).
Halide's scheduling language (compute_at, store_at, split/fuse/reorder,
vectorize/unroll) is the original source of most of these names and is
worth citing as the primary attribution even though TVM is the more
actively-developed artifact today. **This is a naming/vocabulary source,
not a system OSIL needs to depend on or execute** — the way OSIL already
cites ONNX operator names without executing ONNX Runtime.

### Contrast: why ONNX (already profiled) does NOT give OSIL this vocabulary

Checked directly against ONNX's own operator spec
(`onnx.ai/onnx/operators/onnx__Loop.html`,
`onnx/onnx/defs/controlflow/defs.cc`): ONNX's `Loop`/`Scan` operators are
**explicit control-flow operators over a dataflow graph** — a loop is one
opaque node with a trip-count input, a body subgraph, and
loop-carried-dependency wiring. ONNX has **no concept of an iteration
*space*, no indexing maps, no parallel/reduction classification, and no
dependence analysis** — the loop body is an opaque subgraph, and whether
its iterations are independent is not expressible in the format at all.
This is expected and correct given ONNX's own scope (a portable *dataflow
graph* interchange format, not a *loop nest* IR), and it is exactly why
OSIL's existing ONNX profile cannot be extended to cover loop
vectorization — the vocabulary genuinely does not exist there, confirming
the maintainer needs a second ecosystem profile, not a deeper ONNX one.

---

## 5. Proposed OSIL terms, Aristotelian-style (draft — not yet ratified)

Following `spec/core.md`'s existing form (`an A is a B which Cs`) and the
project's ontology rules (univocity, essential features, no circularity,
general-before-particular). These are drafted for review, not inserted
into `spec/core.md` by this research — per `GOVERNANCE.md`, spec changes
require the appropriate skill/ADR path.

- **iteration space** — a coordinate domain (genus) whose points enumerate
  the individual instances of one computation's repeated execution
  (differentia). Realized per-operator in `linalg.generic` (MLIR) as a
  set of affine maps derived from operand shapes; formally, an integer
  polytope constrained by affine inequalities (the polyhedral model's
  *iteration domain*).

- **indexing map** — a mapping (genus) from a point in an iteration space
  to a coordinate in one operand's data space (differentia). Corresponds
  1:1 to MLIR's per-operand `AffineMap` in `linalg.generic` and to the
  polyhedral model's *access relation*, restricted to the affine case.

- **iteration dimension classification** — a property of one dimension of
  an iteration space (genus) that is `parallel` if distinct indices along
  it write disjoint output locations, or `reduction` if distinct indices
  along it accumulate into one shared output location (differentia).
  Directly reusable as an OSIL guard predicate: `vectorizable(d)` legality
  should read as *"d is classified parallel AND no dependence crosses d"*
  — the same shape as OSIL's existing `guards { regime = ExactArithmetic }`
  pattern (ADR-0007), extended with a second, iteration-space-scoped guard
  family.

- **dependence** — an ordering constraint (genus) between two points of an
  iteration space that access the same memory location, where at least one
  access is a write (differentia). The invariant a legal schedule
  transformation (including vectorization) must never violate — the
  natural OSIL `invariant` (`spec/core.md`: "a semantic property whose
  preservation is a necessary condition for the legality of a rewrite").

- **schedule** — a mapping (genus) from iteration-space points to logical
  execution order, admitting reordering subject to every dependence
  (differentia). The object OSIL's rewrite/equivalence machinery would
  search over for loop-nest optimization — the compiler-domain analogue of
  `realization` (`spec/core.md`) restricted to one loop nest's execution
  order rather than a whole SIR's computational form.

These five terms compose cleanly with what already exists: `iteration
space`/`indexing map`/`dependence` describe the *object* being optimized
(parallel to how `concept` describes semantic identity today);
`iteration dimension classification` and `dependence` supply the *guard
predicates* a `vectorize` equivalence would need (parallel to
`regime`/ADR-0007); `schedule` is the loop-nest-scoped instance of the
existing `realization` idea. No new grammar construct is obviously
required beyond what `guards {}` already supports — this is a domain
vocabulary extension, closer in shape to `profiles/domain/numeric/` than
to a new stratum.

---

## 6. Acquisition — concrete, checkable

| Item | URL | Format | License | Size | Programmatically consumable? |
|---|---|---|---|---|---|
| MLIR `linalg` dialect ODS defs | `github.com/llvm/llvm-project` → `mlir/include/mlir/Dialect/Linalg/IR/*.td` | TableGen (`.td`), plain text | Apache-2.0 WITH LLVM-exception (verified via file SPDX header) | Dialect subtree is dozens of `.td`/`.cpp` files (low thousands of LOC); LLVM monorepo itself is large (39,901 GitHub stars, actively pushed same day as this research) but only this subdirectory need be vendored/cited | Yes — plain text, directly parseable by OSIL's own tooling (grep/regex or a small TableGen-lite reader) without building LLVM; this is how `mlir-tblgen` itself consumes them |
| MLIR `affine` dialect ODS defs | same repo, `mlir/include/mlir/Dialect/Affine/IR/*.td` | TableGen | Apache-2.0 WITH LLVM-exception | similar | Same |
| Polyhedral formal vocabulary | no single "download" — literature term (Feautrier; Bastoul; Verdoolaege's `isl` paper, IMPACT 2010) | N/A (mathematical vocabulary, cite the papers) | N/A | N/A | N/A — cite as definitional grounding, not a consumable artifact |
| `isl` (concrete polyhedral library) | `repo.or.cz/isl.git` (canonical); mirror `github.com/Meinersbur/isl` | C source + docs | MIT | moderate C library | Yes — C API; already vendored transitively via LLVM Polly if OSIL ever needs live dependence computation rather than just vocabulary |
| TVM schedule primitives | `github.com/apache/tvm`, `docs/reference/api/python/tir.rst` and schedule primitive docs | Python API + docs | Apache-2.0 | N/A (cite primitive names, not the whole project) | Yes if OSIL ever wants live scheduling, but recommended use here is naming-only |
| Halide scheduling language | `github.com/halide/Halide`, scheduling docs | C++ DSL + docs | MIT | N/A | Naming-only, same as TVM |
| ONNX `Loop`/`Scan` (contrast, already profiled) | `onnx.ai/onnx/operators/` | `.proto`-defined | Apache-2.0 | Already in `profiles/ecosystem/onnx/` | Already consumed — confirmed to lack the needed vocabulary, not a candidate for extension here |

**Recommended concrete action (not executed by this research — proposal
only, per `GOVERNANCE.md`):** populate `profiles/ecosystem/mlir/PROFILE.md`
(currently a stub) and a new `registry/entries/mlir-linalg.yaml` — mirroring
the existing `registry/entries/onnx.yaml` pattern exactly — hand-curated
from `LinalgInterfaces.td`/`IndexingMapOpInterface.td`, pinned to an exact
LLVM commit or release tag the way `profiles/ecosystem/onnx/VERSIONS` pins
`ir_version = 13`. **Do not** create or activate a `profiles/ontology/swo/`
or similar OBO-import profile — per §3, there is no grammar surface for it
to bind to yet (GAP-6 is still unfiled), and per §1–§2 there is no content
in that ecosystem that would answer a rewrite-legality question even if
there were.

---

## Assumptions and unresolved items

- **ASSUMPTION:** OBO Foundry's `activity_status: active` field for SWO was
  not independently corroborated with a maintainer statement explaining the
  discrepancy against the 2023-03-05 commit/release evidence — I checked
  three independent mechanical sources (GitHub commits, GitHub releases,
  OLS's live version record) and all three agree with each other and
  disagree with the registry's self-classification; I did not reach a human
  maintainer to ask why. Falsifiable by a new SWO commit/release appearing,
  or a maintainer statement explaining the field's intended (non-liveness)
  meaning.
- **ASSUMPTION:** UFO's own GitHub-hosted tooling (`OntoUML/OntoUML`,
  `nemo-ufes/gufo`) liveness was not checked with the same commit-API rigor
  applied to the OBO Foundry ontologies — out of scope, since UFO's role in
  OSIL (per `profiles/ontology/README.md`) is citation-stable definitional
  method, not a term-import target for this specific question.
- **ASSUMPTION:** "MLIR Python bindings" as a generically pip-installable
  package does not exist under that name (`mlir-python-bindings` on PyPI is
  a name-squat placeholder, confirmed live) — real consumption paths run
  through building LLVM with `-DMLIR_ENABLE_BINDINGS_PYTHON=ON` or via a
  downstream project's wheel (e.g. `iree-compiler`, `torch-mlir`). This
  does not affect the recommendation, since the proposed use (reading
  `.td` vocabulary to hand-curate a registry entry, per the ONNX
  precedent) needs no Python bindings at all — flagged only so a future
  implementer doesn't assume a bindings-based extraction pipeline is
  necessary.
- **Not investigated (out of scope for this pass):** a line-by-line
  feature comparison of MLIR `affine` dialect vs. Polly's own IR-level
  representation vs. raw `isl` — this research recommends citing MLIR's
  vocabulary as the primary, actively-maintained, already-profiled-adjacent
  source and `isl`/the polyhedral papers as formal grounding, but does not
  resolve which concrete artifact OSIL should parse first if it needs to
  automate extraction rather than hand-curate it (a natural G-numbered gate
  question for whoever executes this, not a research-unknown question).

## Validity

Valid as of 2026-08-24. Re-evaluate if: SWO receives a new commit/release
(would partially undercut the staleness argument, though not the scope
argument — re-check §1's scope quotes specifically, since a revival could
in principle also expand scope); the MLIR `linalg`/`affine` dialects
undergo a breaking redesign (re-verify the indexing-map/iterator-type
vocabulary against the new docs before citing it in a ratified `spec/`
change); OSIL's grammar gains cross-layer relation constructs (GAP-6),
which would remove the "no grammar surface" objection in §3 and might
justify revisiting a citation-only OBO link at that point (still not an
optimization-power argument, only a documentation one).

## Sources (all fetched/executed 2026-08-24)

1. SWO GitHub repo metadata (commits, releases, license, issues):
   `https://api.github.com/repos/allysonlister/swo`,
   `https://api.github.com/repos/allysonlister/swo/commits`,
   `https://api.github.com/repos/allysonlister/swo/releases`
2. OBO Foundry registry entry for SWO (raw YAML front matter, incl.
   `activity_status: active`):
   `https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/ontology/swo.md`
3. OBO Foundry SWO landing page: `http://obofoundry.org/ontology/swo.html`
4. EBI Ontology Lookup Service (OLS4), live SWO ontology record (version
   `2023-03-05`, 1971 terms): `https://www.ebi.ac.uk/ols4/api/ontologies/swo`
5. Malone, J. et al. (2014), "The Software Ontology (SWO): a resource for
   reproducibility in biomedical data analysis, curation and digital
   preservation," *J Biomed Semantics* 5:25, doi not directly captured —
   PMID 25068035, PMCID PMC4098953. Full text XML fetched via Europe PMC:
   `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC4098953/fullTextXML`
6. IAO term `algorithm` (`IAO_0000064`) definition, and confirmation SWO
   reuses it verbatim: EBI OLS4 search/term API,
   `https://www.ebi.ac.uk/ols4/api/search?q=algorithm`,
   `https://www.ebi.ac.uk/ols4/api/ontologies/iao/terms?iri=...IAO_0000064`
7. OBI term `data transformation` (`OBI_0200000`) definition and subclass
   list: `https://www.ebi.ac.uk/ols4/api/ontologies/obi/terms?iri=...OBI_0200000`,
   `https://www.ebi.ac.uk/ols4/api/search?q=data%20transformation&ontology=obi`
8. IAO GitHub repo metadata: `https://api.github.com/repos/information-artifact-ontology/IAO`
9. OBI GitHub repo metadata: `https://api.github.com/repos/obi-ontology/obi`
10. EDAM GitHub repo metadata + commits + releases:
    `https://api.github.com/repos/edamontology/edamontology`,
    `.../commits`, `.../releases`
11. EDAM `Operation` root term definition (`operation_0004`):
    `https://www.ebi.ac.uk/ols4/api/ontologies/edam/terms?iri=http%3A%2F%2Fedamontology.org%2Foperation_0004`
12. EBI OLS4 live EDAM ontology record (3539 terms, version
    `1.25-20260626T1230Z`): `https://www.ebi.ac.uk/ols4/api/ontologies/edam`
13. BFO-2020 GitHub repo metadata:
    `https://api.github.com/repos/BFO-ontology/BFO-2020`
14. ISO/IEC 21838-2:2021 standard page: `https://www.iso.org/standard/74572.html`
15. UFO/OntoUML background: `https://ontouml.readthedocs.io/en/latest/intro/ufo.html`,
    `https://ontouml.org/ufo/`, Guizzardi et al., "UFO: Unified Foundational
    Ontology," *Applied Ontology* 17(1), doi:10.3233/AO-210256
16. PROV-O (W3C Recommendation): `https://www.w3.org/TR/prov-o/`
17. CodeMeta/schema.org software terms comparison:
    `https://codemeta.github.io/terms/`
18. MLIR `linalg` dialect docs: `https://mlir.llvm.org/docs/Dialects/Linalg/`
19. MLIR `LinalgInterfaces.td` raw source (SPDX license header, indexing-map
    interface definitions):
    `https://raw.githubusercontent.com/llvm/llvm-project/main/mlir/include/mlir/Dialect/Linalg/IR/LinalgInterfaces.td`
20. `llvm/llvm-project` GitHub repo metadata (liveness: pushed same day as
    this research): `https://api.github.com/repos/llvm/llvm-project`
21. Polyhedral model vocabulary (iteration domain, access relation,
    schedule, dependence) — secondary synthesis grounded in Feautrier's and
    Bastoul's polyhedral-compilation work and Verdoolaege, S. (2010), "isl:
    An Integer Set Library for the Polyhedral Model," ICMS 2010,
    Springer LNCS 6327.
22. `isl` GitHub mirror metadata (liveness, license):
    `https://api.github.com/repos/Meinersbur/isl`
23. TVM scheduling primitives (`split`/`fuse`/`reorder`/`compute_at`/
    `cache_read`/`cache_write`/`rfactor`): TVM discussion/docs, via web
    search of `discuss.tvm.apache.org` and TVM's own TensorIR
    documentation.
24. ONNX `Loop` operator spec: `https://onnx.ai/onnx/operators/onnx__Loop.html`;
    `onnx/onnx` control-flow op definitions:
    `https://github.com/onnx/onnx/blob/main/onnx/defs/controlflow/defs.cc`
25. `mlir-python-bindings` PyPI listing (confirmed name-squat placeholder,
    not the real distribution): `https://pypi.org/pypi/mlir-python-bindings/json`
26. Repo context read before this research: `spec/core.md`, `README.md`,
    `profiles/ontology/{bfo,dolce,ufo}/PROFILE.md`,
    `profiles/ontology/README.md`, `profiles/ecosystem/mlir/PROFILE.md`,
    `profiles/ecosystem/onnx/PROFILE.md` + `profile.osil`,
    `docs/design/idea-coverage.md`, `docs/research/U5-egg-vs-egglog.md`
    (format/rigor precedent).

---

**Epistemological note:** The decisive findings in this document — SWO's
staleness (§1) and every OBO-descended term's artifact/process-level rather
than computation-level scope (§1–§2) — rest on primary-sourced,
independently-converging mechanical evidence (GitHub API commit/release
history, the OBO Foundry's own registry file, EBI's live ontology-registry
service, and the founding paper's own full text), not on any single
source's self-description. The recommendation in §4–§5 is comparatively
more constructive/synthetic — it proposes a vocabulary mapping rather than
reporting a settled fact — and is graded MEDIUM-HIGH accordingly: the MLIR
vocabulary's existence and definitions are primary-sourced and current
(same-day repo activity), but the specific term list in §5 is this
researcher's synthesis for OSIL's needs, not a pre-existing consensus
document, and should be treated as a draft input to a future ADR, not as
ratified spec content.
