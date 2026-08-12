# Synthesis — OAAS Repository Organization (v0 proposal)

> Integrates intake passes 1–3 into one concrete tree. Each subtree is annotated with
> its ground-truth owner (P1), attachable agentic loops + fixtures (P2), and cadence /
> version stream / policy verbs (P3). Status: PROPOSAL — gates below are falsifiable;
> unknowns are queued for research fan-out. (2026-08-12)

## The tree

Monorepo at v0, but **every top-level directory is repo-shaped** (own README, own
version manifest, own CI jobs, own policy line) so fission along cadence boundaries
is mechanical, not a rewrite.

```
oaas/
├─ CHARTER.md  GOVERNANCE.md  LICENSE  LICENSE-docs     ← LF surface (license pairing: unknown U2)
├─ CLAUDE.md  AGENTS.md                                 ← conventions that actually reach (sub)agents
│
├─ spec/                        P1: self-owned          P3: consensus-slow
│  ├─ core.md  execution.md  interchange.md
│  ├─ visual.md                                         ← restored founding requirement (P3)
│  ├─ interop/  ecosystem-contract.md  onnx.md  egraph.md
│  └─ INVARIANTS                                        ← univocity, Aristotelian definitions (BFO rules)
│     loops: coherence lint · definition audit · xref integrity · prose↔grammar↔corpus 3-way check
│     policy: agents draft/refactor; humans ratify normative MUSTs
│
├─ grammar/                     P1: self-owned          P3: slow, gates everything
│  ├─ oaas.ebnf (or tree-sitter)  + JSON Schemas (manifests, layout, contracts)
│  └─ layout schema                                     ← layout-as-data (identity projection, P3)
│     loops: every production has ≥1 corpus example; every example parses
│     policy: propose-only; grammar changes trigger full-corpus re-validation
│     NOTE: CRITICAL PATH — until this exists no loop anywhere can bite (P2)
│
├─ conformance/                 P1: shared              P3: continuous
│  ├─ corpus/                                           ← ONE canonical example pool; fixtures
│  │                                                      extracted from the transcript's own DSL blocks
│  ├─ golden-render/                                    ← deterministic render→diff loop (visual, P3)
│  └─ matrix/                                           ← spec × adapter × upstream compatibility
│     loops: round-trip evals scoring preserves{} fields · matrix-cell refresh (scheduled)
│     policy: agents add/refresh cells freely; deleting corpus items is propose-only
│
├─ profiles/
│  ├─ ecosystem/  onnx/ egg/ mlir/ wasm/  P1: FOREIGN   P3: upstream-driven cadence, each repo-shaped
│  │     each: PROFILE.md · VERSIONS (upstream pins) · preservation contract (parseable, not fenced)
│  │     loops: drift-watch at upstream tempo · conformance regression · round-trip
│  │     policy: sync & report; MUST NOT redefine upstream semantics (transcript's own clause)
│  ├─ ontology/  bfo/ dolce/ ufo/         P1: academic  P3: citation-stable
│  │     loops: citation-fidelity audit (near-static)
│  └─ domain/    ml/ crypto/ agent/       P1: self-owned
│        agent/ is DUAL-USE (P2): domain profile for agentic architectures AND the
│        repo's own operating policy self-hosted in OAAS syntax = conformance test #0
│
├─ registry/                    P1: shared              P3: fast, data-shaped
│  └─ one-entry-per-file ecosystem manifests, schema at root
│     loops: schema validation · freshness; parallel agent writes are conflict-free by layout
│     policy: agents write freely within schema; schema changes are propose-only
│
├─ curriculum/                  P1: self-owned          P3: continuous
│  └─ learning paths = INDEX/VIEW layers over conformance/corpus (ids only, no content)
│     loops: every corpus item reachable from ≥1 path; every path step resolves & parses
│     policy: agents author freely; pedagogy review by humans
│
├─ tools/                       P1: self-owned          P3: fastest; earliest fission candidate
│  └─ (later) cli / oaas-add wizard / renderer
│
└─ docs/
   ├─ intake/                                           ← this analysis (passes 1–3)
   └─ decisions/                                        ← ADRs; every gate outcome lands here
```

## The three-pass ruleset the tree encodes

1. **P1 — ownership cut:** every subtree has exactly one ground-truth class
   (self / shared / foreign / academic); loop type and policy verbs follow from it.
2. **P2 — fixtures & self-hosting:** loops bite only on parseable artifacts → triple
   representation (prose / grammar / corpus); the repo's own policy is written in
   OAAS (`profiles/domain/agent/`) and an agent PR is a rewrite whose merge-legality
   = invariant preservation (transcript §9 pointed at the repo).
3. **P3 — cadence cut:** version streams per subtree; compatibility matrix as
   flagship agent-maintained artifact; identity projection makes `visual_layout`
   preservable; corpus/curriculum = one pool + views.

## Chronological partitions with falsifiable gates

- **G0 Bootstrap** — git init; seed CLAUDE.md/AGENTS.md; skeleton tree; CI stub.
  *Gate: a fresh agent, given only the repo, can state each subtree's policy.*
- **G1 Grammar + corpus** — minimal grammar covering the transcript's own DSL blocks
  (`profile`, `projection`, `equivalence`, `model`, `invariant`, preservation
  contracts); corpus extracted from them. *Gate: 100% of corpus parses; every
  production exemplified.* ← critical path (P2)
- **G2 Self-description** — repo operating policy expressed in OAAS.
  *Gate: conformance test #0 passes — the formalism can express its own repo's
  actors/verbs/invariants; failure = expressiveness defect in spec.*
- **G3 First projection** — ONNX adapter round-trip on a toy model.
  *Gate: `preserves{}` fields verified mechanically; unknown ONNX fields survive as
  opaque namespaced annotations.*
- **G4 Visual identity projection** — native serialization carries layout; renderer
  deterministic. *Gate: golden-render diff = 0 across round-trip.*
- **G5 LF readiness** — charter, license pairing, governance, contribution ladder.
  *Gate: submission checklist for the chosen LF path satisfied.*

(G1↔G2 share the grammar; kept separate because their evidence differs: parse
success vs expressiveness. G3 and G4 are parallel once G1 passes.)

## Unknowns queued for research fan-out (one agent per independent unknown)

- **U1 LF onboarding path**: sandbox vs LF AI & Data (ONNX's home) vs OpenSSF; entry
  requirements, timelines, what "with the help of LF" can concretely mean at day 0.
- **U2 License pairing** for spec+code+corpus repos (Apache-2.0 / CC-BY-4.0 /
  Community Specification License — what LF spec projects actually use).
- **U3 Prior-art repo organization**: ONNX, StableHLO, OCI spec, W3C spec repos —
  how they cut spec/conformance/registry, versioning schemes, governance files.
- **U4 Visual-DSL layout interchange prior art**: BPMN DI history (verify the 1.x
  layout-loss story), Mermaid/PlantUML/diagrams-as-code norms, layout-as-data schemas.
- **U5 egg/egglog current state** (egg vs egglog succession, API stability) — which
  to target as the equivalence-search ecosystem.
- **U6 Capability-claim verification**: MLIR dialect metadata persistence, StableHLO
  compatibility guarantees, TVM search claims — everything the spec would cite
  normatively. (All currently ASSUMPTION: inherited from ChatGPT.)
- **U7 Agent-policy enforcement mechanics**: state of the art for path-scoped agent
  permissions in CI (merge-gate patterns, CODEOWNERS semantics, policy-as-code).

## Standing assumptions (marked, not silently resolved)

- ASSUMPTION: monorepo-with-fission-lines beats multi-repo at day 0 (revisit at G5).
- ASSUMPTION: Apache-2.0 + CC-BY-4.0 pairing acceptable to LF (U2 decides).
- ASSUMPTION: transcript's technical claims about MLIR/TVM/StableHLO/egg (U6 decides).
