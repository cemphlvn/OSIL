# G12 Resolver — plan (grounded 2026-08-12)

## Grounding facts (measured, not assumed)
- 6 `use` decls across flows (4× domain.toolchain, 2× ecosystem.onnx); 10
  distinct op refs (onnx::MatMul@13 ×3; 9 toolchain ops).
- `use ecosystem.onnx` is DANGLING today: no in-language `profile
  ecosystem.onnx` exists — pins live only in VERSIONS (plain text).
- 9/9 toolchain flow-ops are undeclared vocabulary.
- Registry `operators` oracle: schema supports, no entry populates.

## Accumulated perspectives (synthesized into the design)
1. **Linker**: resolution = two-pass linking (index symbols, then resolve);
   duplicate namespace = duplicate symbol; unresolved = undefined reference.
   Error style follows linkers: name the reference, the searcher, and a
   nearest-match suggestion.
2. **Language-server**: the indexes (profiles, namespaces, ops, concepts) are
   exactly a future LSP's tables — build them as a reusable module, not
   inline. Also the moment to stop minting readers: the resolver ships a
   shared flow/vocabulary reader (`tools/oaas_read.py`) instead of a FIFTH
   copy; migrating the other four is a follow-up (north-star metric #2).
3. **Ontology (ADR-0005 enforced at last)**: parse-level kind-purity kept the
   general and the particular apart; RESOLUTION is where the particular must
   finally FIND its universal. A dangling reference is a particular without a
   universal — the BFO framing goes in the spec prose.
4. **Security heritage**: namespace binding to a PINNED profile is provenance;
   ambiguous/unbound namespaces are the language-level analog of dependency
   confusion. Collision detection is therefore a security control, not a
   convenience.
5. **ONNX precedent (U3)**: checker vs shape-inference separation → rung 3
   (types/shapes) is explicitly OUT of G12 scope.
6. **Boundary obligation, generalized voluntarily**: G12 enlarges no grammar,
   but it creates a NEW acceptance layer — so it ships that layer's refusals:
   resolution-rejection fixtures (`// MUST-FAIL-RESOLUTION:`) in
   `conformance/resolution/`, scanned by the resolver only (they PARSE fine).

## Scope (G1-enablement rungs 1–2; rung 3 out)
- **Rung 1 — name resolution**: every `use` resolves to a declared profile
  (universe: `profiles/**/*.oaas`); namespace binding rule made normative:
  a use binds the profile id's TERMINAL SEGMENT as the flow's namespace
  (ecosystem.onnx → onnx::); collisions are errors. Dataflow wiring: every
  edge source is an io name or a produced value; declared outputs are
  produced; unused values reported as info.
- **Rung 2 — oracles**: ecosystem namespaces check ops against
  `registry/entries/<eco>.yaml` operators (name + @version); domain
  namespaces check ops against operator/concept declarations in the
  profile's own directory. Pin consistency: `profile.oaas` pins ==
  `VERSIONS` pins (two artifacts, one truth, checked).

## Gate claim (falsifiable)
Resolution rate = 100% over all corpus flows against the repo universe;
resolution refusals pinned and REJECTing; pin-consistency green; wired into
`just test` + CI.

## Deliverables
profiles/ecosystem/onnx/profile.oaas (canonical in-language pins) ·
toolchain.oaas vocabulary completed (9 operator decls) · registry onnx
operators list · tools/oaas_read.py (shared reader) + tools/oaas_resolve.py ·
conformance/resolution/ (3 refusal fixtures + card) · spec/execution.md
Resolution section · justfile + CI wiring · g12 report · idea-coverage row
update.
