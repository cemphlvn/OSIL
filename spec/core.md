# OAAS Core Specification

Status: **draft-0, non-normative.** Every definition below follows the repo's
ontology rules: univocity, Aristotelian form (an A is a B which Cs), essential
features, no circularity. Terminology inventory: `spec/TERMS.md` (to be created by
`univocity-lint`).

## 1. Purpose

OAAS is a semantic architecture layer: it records what a computation is *for* —
intent, semantic role, equivalence, constraints, invariants, ontological identity,
security requirements — so that toolchains can optimize, substitute, verify, and
explain against meaning rather than against syntax alone.

## 2. Core definitions

**semantic optimization space** — the space of program realizations (genus) whose
members are semantically valid realizations of one declared intention
(differentia). The central object of OAAS: compilation selects from this space
under constraints and cost, rather than rewriting a single fixed program.
Given technical teeth at G13 by the constitutional equation under
*realization* below.

**stratum** — a metamodel level (genus) at which an architecture document's
content stands — a level OF the language, never a thing described IN it
(differentia). Strata are CORE-DEFINED symbols (design A, G13): the normative
core universe is `{OAAS-SIR, OAAS-CIR, OAAS-NATIVE}`; profiles MAY later
declare compatible strata, but no `.oaas` document redeclares the metamodel.

**OAAS-SIR** — the stratum (genus) at which an architecture states what it
IS: semantic identity, intention, constraints, invariants — independent of
computational form (differentia).

**OAAS-CIR** — the stratum (genus) at which an architecture states HOW it is
computed: explicit operators and dataflow structure (differentia).

**OAAS-NATIVE** — the stratum (genus) comprising the total native document —
both strata plus visual layout — from which only the identity projection
departs (differentia).

**realization** — a semantics-preserving commitment (genus) from an abstract
semantic architecture (OAAS-SIR) to one computationally explicit architecture
(OAAS-CIR) that satisfies the declared intention, constraints, and invariants
(differentia). Defined by what it preserves and satisfies — never merely by
its endpoints. One-to-many: an SIR has a realization SET, which yields the
constitutional equation:

> **semantic optimization space = valid realizations(SIR, constraints, invariants)**

Projection-source legality derives from the preserved dimension: equivalence
originates at OAAS-SIR; computation and execution at OAAS-CIR; everything at
OAAS-NATIVE. Name resolution ("does the stratum exist?") and stratum legality
("may this projection originate there?") are DISTINCT checks — the fixture
pair RS005/RS006 pins them apart.

**concept** — a semantic identity (genus) that names a computation independently of
any particular realization and enumerates its equivalence conditions (differentia).
Example: `Attention`, equivalent under `{fp16, causal=true}` to a set of
decompositions and fused kernels.

**projection** — a transformation (genus) that maps an OAAS graph into an external
ecosystem's native representation while preserving a declared semantic dimension
(differentia). "Lowering" is the special case whose preserved dimension is
execution. Corpus: `004-projections.oaas`.

**preservation contract** — a declaration (genus) that enumerates, for one
projection, the semantic properties preserved and those that may be lost
(differentia). Contracts make interoperability measurable rather than binary.
Corpus: `005-preservation-contract.oaas`.

**identity projection** — the projection (genus) whose preservation contract is
total: every property, *including visual layout*, is preserved (differentia). The
OAAS native serialization is defined as the identity projection; this is what makes
the visual dimension normative content rather than disposable metadata. See
`spec/visual.md`.

**invariant** — a semantic property (genus) whose preservation is a necessary
condition for the legality of a rewrite (differentia). Invariants turn optimization
into constrained search: maximize performance subject to semantic preservation +
architecture constraints + security invariants. Corpus: `007-invariants.oaas`.

**equivalence** — a declared bidirectional rewrite (genus) valid only under its
guard conditions (differentia). Equivalences are the OAAS-side input to
equality-saturation ecosystems. Corpus: `003-equivalence-distributivity.oaas`.

**realizability** — a property of one direction of an equivalence (genus): the
direction is realizable iff its match side both binds every variable the
opposite side requires and is not a bare variable (differentia). An
equivalence is bidirectional as assertion; it realizes as a bidirectional
rule when both directions are realizable, as a directed rule from the
groundable side when exactly one is, and MUST be refused as untranslatable
when neither is — never silently dropped. Engine-forced, discovered at G14;
realized directions are recorded per case (`just egraph`). Ratified into core
by maintainer instruction 2026-08-12.

**profile** — a named set of declarations (genus) that pins the versioned identity
and semantics of one ecosystem, ontology, or domain for use inside OAAS graphs
(differentia). Corpus: `001-profile-ecosystem-onnx.oaas`.

**architecture document** (`.oaas`) — a document (genus) that declares vocabulary:
the general — profiles, concepts, equivalences, invariants, operators, contracts,
models (differentia). ADR-0005.

**flow document** (`.flow`) — a document (genus) that composes declared vocabulary
into a particular executable dataflow graph (differentia). Flows are the primary
visual objects: the identity projection's layout guarantee (spec/visual.md)
attaches here. Corpus: `002-graph-onnx-matmul.flow`.

**use declaration** — a flow statement (genus) that names the profile whose pinned
semantics the flow's native identities resolve against (differentia). Corpus: `002`.

**actor** — a policy subject (genus) that binds a named role to the subtrees it
may modify (scope), the operations it may perform (verbs), the invariants it
must preserve, and the change classes requiring human ratification
(differentia). Introduced at G2; the repo's own policy is conformance test #0.
Corpus: `010`, `022`. Scope paths may be file-granular (dotted components,
grammar v0.5 / G9).

**regime** — a validity domain (genus) whose carriers are the concrete
arithmetics realizing it (differentia). Declared as concepts in
`profiles/domain/numeric/`; canonical guard form `regime = <Concept>` (ADR-0007).
Corpus: `020`.

**rejection fixture** — a negative fixture (genus) pinning a normative refusal
that must never parse (differentia). Permanent, never flipped — distinct from
temporal gap-pins (spec/conformance.md §2). Home: `conformance/rejections/`.

**role binding** (`:`) — a declaration form (genus) that binds a closed grammar
role — `purpose`, `goal`, `preserves` — to a term or constraint (differentia).
Roles are grammar keywords; user keys never bind with `:` (refusal pinned by
R006). ADR-0008.

**asserted equality** (`=`) — a relational expression (genus) asserting that a
key equals a value, whose force is supplied by its block kind — stipulated in
profile fields, guards, args, and layout attributes; required in constraint
blocks (differentia). One meaning spec-wide. ADR-0008.

## 3. The sovereignty principle (normative once ratified)

OAAS MUST NOT redefine the normative semantics of an external ecosystem when a
native specification already exists. `onnx::MatMul@13` means what ONNX says it
means, at that version, always. OAAS contributes shared architectural context —
never substitute semantics. Full contract: `spec/interop/ecosystem-contract.md`.

## 4. Security invariants (heritage section)

Security requirements are first-class semantic properties, not annotations:
`ConstantTime`, `NoExternalMemory`, information-flow labels, and category-level
requirements (`authenticated_encryption` rather than a cipher name) participate in
rewrite legality and in projection contracts. A rewrite with a 1.8× speedup that
breaks `ConstantTime` is illegal under a security profile — by construction.

## 5. Chapter map

- Execution semantics → `spec/execution.md` (stub)
- Interchange format → `spec/interchange.md` (stub)
- Visual grammar & layout → `spec/visual.md` (working, G4)
- Conformance & testing → `spec/conformance.md` (working: preservation score,
  compression ladder, negative-fixture taxonomy)
- Versioning & compatibility → `spec/versioning.md` (stub)
- Ecosystem contracts → `spec/interop/`
- Term inventory → `spec/TERMS.md` (maintained by univocity-lint)
