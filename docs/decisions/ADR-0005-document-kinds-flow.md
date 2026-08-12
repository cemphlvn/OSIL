# ADR-0005: Two document kinds — `.oaas` (vocabulary) and `.flow` (composition)
Date: 2026-08-12 · Status: accepted (user-directed at G1)

## Context
Building the G1 parser forces the question the transcript never answered: what is
a valid top-level document? Grammar v0 lumped vocabulary declarations (profiles,
concepts, equivalences, invariants, contracts, models) together with graph
statements (inputs, consts, edges) in one `document` production. The corpus
already disagreed: 002 is a dataflow graph; everything else is vocabulary. Mixing
them in one kind is a univocity defect ("document" meant two things) and violates
the ontology rule *distinguish the general from the particular*.

## Decision
The OAAS family has two document kinds, distinguished by extension:

- **`.oaas` — architecture document**: declares the general — vocabulary
  (profiles, concepts, equivalences, invariants, operators, contracts, models).
  TBox, in ontology terms.
- **`.flow` — flow document**: composes the particular — an executable dataflow
  graph (`use` declarations, io declarations, edges) that *references* vocabulary
  declared in `.oaas` documents. ABox composition.

A `use <qualified-id>` declaration in a flow names the profile whose pinned
semantics its native identities (e.g. `onnx::MatMul@13`) resolve against.

## Consequences
1. **The general/particular split becomes a policy address space inside the
   language itself**: `.oaas` vocabulary is spec-space (ratified, slow, owned by
   the standard); `.flow` documents are user-space (authored freely by end users
   and generated cheaply by agents). The folder tree was the policy address space
   (pass 1); document kinds extend it into the file format.
2. **Loops attach per kind**: `.oaas` → univocity, definition audit, equivalence
   consistency. `.flow` → reference resolution, type checking, projection
   round-trips (G3), and the visual identity projection + golden-render loop (G4)
   — flows are what you *draw*; the founding visual requirement lives on `.flow`.
3. The parser gains a successor: `use` introduces cross-document reference, so the
   G1 parser grows into a resolver/linker (name resolution across documents) —
   prerequisite for type checking, the wizard, and G3.
4. Corpus: 002 renamed to `.flow` (id stable; extension is metadata, not identity)
   and normalized with a `use ecosystem.onnx` header. Conventions updated in
   corpus-gardener, CLAUDE.md, AGENTS.md.
5. Naming observation (not a decision): a flow-centric project name is one
   available path around the OAAX collision (research U1).
