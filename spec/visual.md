# Visual Grammar & Layout
Status: draft-0 with WORKING layout grammar (v0.3; gate G4 green 2026-08-12).
The founding requirement (a visual DSL) is normative: layout is content, not
decoration. The native serialization is the identity projection (ADR-0002) —
preserves everything including visual_layout; other projections may declare it
under may_lose.

## Layout block (grammar v0.3)
Embedded in the SAME document as the semantics (BPMNDI lesson: separable, never
decoupled), defined in the SAME artifact class as the rest of the grammar (U4
rec 8), anchored by stable identifiers, never by position/order:

- `node <id> [x, y, w, h]` with optional `collapsed = <bool>`, `z = <int>`
- `edge <src> -> <dst> waypoints [(x,y) ...]` — control points STORED, never
  recomputed (the Mermaid trade rejected: recompute-only means no manual layout)
- `label <owner> [x, y, w, h]` — labels are independently positioned objects
- `viewport [x, y, zoom]` — stored but NON-NORMATIVE (session ergonomics, not
  diagram identity; excluded from the conformance gate)

Coordinate convention (working decision D1): top-left origin, +y down, abstract
px units. Edge anchoring by src -> dst pair (D2). D1–D3 remain OPEN
DISCUSSIONS with revisit triggers: conformance/golden-render/README.md.

## Conformance (gate G4)
Three-tier verdict: (1) structural diff of layout-as-data vs golden —
zero-tolerance GATE; (2) deterministic SVG byte-diff — ADVISORY (fixed-metrics
monospace text, char-count x constant width: font measurement is deleted by
construction, not mitigated); (3) pixel diff NEVER gates. The identity
round-trip (structure -> emitted text -> structure) must be zero-diff.
Harness: tools/render_check.py (`just render`); goldens change only via
ratified `--bless`.

## Precedents (research U4)
Cautionary: UML Diagram Interchange (OMG 2006) — complete, ratified, near-zero
adoption, replaced by Diagram Definition. Success: BPMN 2.0 BPMNDI —
cross-vendor round-trips because every layout object carries an ID reference
into the semantic model. Corrected history: BPMN 1.x had NO standardized
interchange format at all (not "lost layout" — there was no format to lose it
from).
