# Intake Pass 1 — Content Topology

> Protocol: same ChatGPT transcript pasted 3×; each pass must surface one genuinely new
> nuance at the intersection of repo folder structure × agentic-loop deployment × agent
> operating policy. This file records pass 1. (2026-08-12)

## Trajectory extracted from the transcript

1. **Origin**: assessment of Arden University MSc Cyber Security (admission with a
   Business Management BA via non-standard route; ~£17.5k / €15k Berlin; YÖK denklik is
   an individual evaluation, not automatic). Verdict: security = valuable *constraint
   layer* on Cem's real trajectory (agents, ontology, AI architecture), not its center.
2. **Pivot**: "Convert this to a visual DSL where I can code algorithmic architectures"
   → **OAAS** is born: a semantic architecture layer.
3. **OAAS as compiler-perception layer**: the compiler additionally sees intent,
   semantic role, equivalence, invariants, ontology, acceptable approximation, security
   requirements, information flow. Core object: the *semantic optimization space* — the
   space of semantically valid realizations of an intention.
   - Semantic equality saturation (OAAS supplies equivalence rules; egg supplies
     e-graph machinery).
   - Optimization against purpose (`goal / preserves / memory / privacy` blocks).
   - Category-level substitution (AuthenticatedEncryption → AES-GCM | ChaCha20 by
     hardware affordance) — the security thread from the MSc survives here as
     first-class invariants (ConstantTime, Deterministic, Pure…).
   - Cross-layer (vertical) optimization; semantic metadata surviving lowering
     (StableHLO → MLIR → LLVM); semantic debugging ("where does Attention become
     memory-bound?").
4. **Ecosystem stance**: ONNX and egg are sovereign ecosystems. OAAS defines
   **interoperability contracts**, not reimplementations. Key concepts:
   - **projection** (not "lowering"): each projection preserves a different semantic
     dimension (ONNX ← computation; e-graph ← equivalence; MLIR ← execution).
   - **preservation contracts**: explicit `preserves { … } may_lose { … }` per adapter —
     interoperability becomes *measurable*, not binary.
   - Normative principle: *OAAS MUST NOT redefine the normative semantics of an
     external ecosystem when a native specification already exists.*
5. **Compression substrate**: three compression roles — representational (subgraph →
   concept), configuration (deployment intent → resolved runtime/provider/flags via
   `oaas add onnx` wizard), search-space (implementations → semantic families →
   viable candidates). Ecosystem manifests declare capabilities/requirements/costs.

## Folder structure proposed inside the transcript itself

```
/spec
  core.md
  execution.md
  interchange.md
  /interop
    ecosystem-contract.md
    onnx.md
    egraph.md
/profiles
  /ecosystem   onnx/ egg/ mlir/ wasm/
  /ontology    bfo/ dolce/ ufo/
  /domain      ml/ crypto/ agent/
```

## PASS-1 NUANCE (on the record)

**The tree is not a topic tree — it is a conformance tree cut along "who owns the
ground truth", and that ownership class determines which agentic loop type and which
agent policy can attach to each subtree.**

Three ownership classes fall out of the transcript's own structure:

| Subtree | Ground truth owner | Agentic loop that attaches | Policy verb set |
|---|---|---|---|
| `/spec` core | OAAS itself (self-owned) | consistency/univocity linting, Aristotelian-definition audit, cross-reference integrity — *internal* coherence loops | agents may draft & refactor, humans ratify normative MUSTs |
| `/spec/interop` contracts | shared (OAAS ∧ ecosystem) | the preservation contract is **simultaneously prose and test oracle** — round-trip eval loops score `preserves{}` fields directly | agents may propose; changes require dual review (spec + adapter side) |
| `/profiles/ecosystem/*` | foreign (ONNX, egg, MLIR own their semantics) | **upstream-drift watching** (opset 24 → 25), conformance regression vs. an external spec the repo cannot change | agents may sync/report, MUST NOT redefine — the transcript's own normative clause *is* an agent operating policy line |

Corollaries:

- The transcript's "OAAS MUST NOT redefine external ecosystem semantics" reads as spec
  prose but deploys as **path-scoped agent policy**: write-freely / propose-only /
  never-redefine map to subtrees, which means the folder cut must follow ownership
  boundaries or the policy becomes inexpressible.
- `preserves{}/may_lose{}` blocks are **falsifiable gates that live inside the content
  itself** — each `/profiles/ecosystem/<x>/` is an independently deployable eval loop
  (import → transform → export → check contract), so ecosystem profiles can be
  developed by parallel agents with zero cross-interference.
- Ontology profiles (`/profiles/ontology/bfo/…`) have a *fourth* ground-truth flavor:
  published academic artifacts (BFO 2020, DOLCE, UFO) — stable, citable, versioned
  rarely. Their loop is citation-fidelity, not drift-watching. (Flagged for pass 2/3.)

## Ledger

**Decided (by transcript's end-state so far):** ecosystem-adapter stance (integrate,
don't absorb); projection + preservation-contract concepts; profile-based spec surface;
security invariants as first-class.

**ASSUMPTION (unverified, inherited from ChatGPT):** Arden fee figures & YÖK details
(irrelevant to repo); MLIR/StableHLO/TVM/egg capability claims — plausible but each
needs verification before the spec cites them normatively.

**Unknown (research targets when fan-out begins):** LF onboarding path (sandbox vs
OpenSSF umbrella); license pairing (Apache-2.0 + CC-BY-4.0?); prior art for
"semantic architecture spec" repos and their structures (ONNX repo itself, StableHLO,
W3C-style spec repos); how the "end draft" (still to arrive in later paste rounds)
revises the /spec + /profiles surface.

**Awaiting:** paste rounds 2 and 3; the end-state draft near the transcript's end.
