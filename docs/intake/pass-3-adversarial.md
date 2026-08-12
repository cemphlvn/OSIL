# Intake Pass 3 — Adversarial Re-read

> Same transcript, third reading. Pass 3's job: attack what passes 1–2 made
> invisible — including their own hidden assumptions. (2026-08-12)
> Confirmed: all three pastes byte-identical; the compression-substrate section +
> `/spec`+`/profiles` tree IS the end-state draft.

## PASS-3 NUANCE (on the record)

**Passes 1 and 2 analyzed a snapshot. The invisible axis is TIME: the subtrees of
this project have heterogeneous version cadences, and a folder tree that forces one
version stream over all of them cannot host the loops that matter. The correct cut is
along version-cadence boundaries — which are exactly the future repo-fission lines —
so every top-level directory must be repo-shaped (own README, own version manifest,
own CI, own policy) even while the project is a single repo.**

The cadence classes hiding in the transcript:

| Subtree | Cadence | Driven by | Loop that needs this isolation |
|---|---|---|---|
| `spec/` core | consensus-slow | internal ratification | coherence lint; changes rare, reviewed |
| `profiles/ecosystem/*` | upstream-driven | ONNX opset releases, egg/egglog releases, MLIR API churn | drift-watch + conformance re-run **at the upstream's tempo, not the spec's** |
| `profiles/ontology/*` | citation-stable | BFO/DOLCE/UFO publications (years) | citation-fidelity audit, near-static |
| `registry/` manifests | fast, data-shaped | hardware/runtimes/capabilities | schema validation + freshness; near-continuous |
| `conformance/corpus/` + curriculum | continuous growth | contributions | consistency + coverage loops on every PR |

Evidence from the transcript itself: `profile ecosystem.onnx { ir_version = 11,
opset "ai.onnx" = 24 }` — the adapter pins upstream versions. That makes real
conformance a **3-dimensional compatibility matrix**: OAAS spec version × adapter
version × upstream version. A monorepo with a single version stream cannot even
*name* the cells of that matrix. The matrix must exist as a first-class artifact
(`conformance/matrix/`), and it is the single most agent-maintainable object in the
project: machine-checkable cells, refreshed by scheduled drift-watch agents per
ecosystem.

Policy consequence (semantic-infrastructure axis): the pass-1 verb sets and pass-2
self-hosted invariants attach *per version stream*, not just per path. LF-organized
projects express this as multi-repo orgs with per-repo maintainer sets — which is
also the recruitment mechanism: ONNX experts can own the ONNX adapter without
touching spec governance. Day 0 reality: single repo, but cut so fission is a `git
filter-repo`, not a rewrite.

## Resolved flag 1 — the founding requirement is the structure's only sacrifice

The founding ask was "convert this to a **visual** DSL." Three readings later, the
only field the end-draft's preservation contracts ever place under `may_lose` is
`visual_layout`. The origin requirement became the one officially disposable thing —
nobody decided this; it fell out of an example block and hardened into structure.

Structural fix: define the **identity projection**. The OAAS native serialization is
the one projection whose preservation contract is total — `preserves { everything,
including visual_layout }`. That single move makes visual layout *normative content*
rather than decoration, and it demands:

- `spec/visual.md` — visual grammar as a normative spec chapter (peer of core.md);
- a layout schema in `grammar/` (layout-as-data, not layout-as-pixels);
- a golden-render corpus in `conformance/` — deterministic render → diff loop, the
  agentically-checkable form of "the diagram survived."

Prior art to verify in research phase: BPMN reportedly added a Diagram Interchange
sub-spec in 2.0 precisely because 1.x lost diagram layout at interchange boundaries
(ASSUMPTION: verify before citing normatively). If true, it's the canonical cautionary
tale this fix pre-empts.

## Resolved flag 2 — the education origin has no home

The conversation began as an MSc decision; the user's own framing: the transcript
drifts "from wanting to do an MSc in Cyber Security to drafting an open resource."
Two consequences the tree must absorb:

1. **The repo is partly the credential.** The transcript says the non-standard MSc
   application needs "demonstrable technical work... framed as genuine computing
   experience." A public, LF-associated spec repo with real governance IS that
   demonstration — arguably it replaces the credential need that started everything.
   This is a *purpose* of the artifact, not sentiment; it raises the weight of
   visible engineering discipline (governance docs, CI, release hygiene).
2. **Corpus and curriculum are the same content under two orderings.** A conformance
   example ordered by grammar-coverage is a lesson when ordered by pedagogy. Storing
   them separately guarantees drift. Structure: ONE canonical example pool
   (`conformance/corpus/`), with `curriculum/` holding only **index/view layers**
   (learning paths referencing corpus items by id). Attachable loops: every corpus
   item reachable from ≥1 path; every path step resolves to an existing, parsing
   corpus item. Views-as-first-class-citizens is itself a folder-structure nuance:
   ordering metadata over a canonical pool, never duplicated content.

## Delta over passes 1–2

P1: ownership determines loop + policy per subtree. P2: policy is self-hostable in
OAAS; loops need fixtures; grammar is critical path. P3: **cadence heterogeneity**
means those subtrees must be independently versioned, repo-shaped, fission-ready;
the compatibility matrix is the flagship agent-maintained artifact; the identity
projection rescues the visual founding requirement; corpus/curriculum unify as
pool + views.
