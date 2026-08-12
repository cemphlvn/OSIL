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

**profile** — a named set of declarations (genus) that pins the versioned identity
and semantics of one ecosystem, ontology, or domain for use inside OAAS graphs
(differentia). Corpus: `001-profile-ecosystem-onnx.oaas`.

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

## 5. Open sections (stubs)

- Execution semantics → `spec/execution.md`
- Interchange format → `spec/interchange.md`
- Visual grammar & layout → `spec/visual.md`
- Ecosystem contracts → `spec/interop/`
