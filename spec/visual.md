# Visual Grammar & Layout
Status: stub (draft-0) — restores the project's FOUNDING requirement (a visual DSL).

Position (ratification pending): visual layout is NORMATIVE CONTENT, not decoration.
The native serialization preserves it totally (identity projection, ADR-0002);
other projections may declare it in may_lose.

Layout schema requirements (grounded by docs/research/U4-visual-layout-interchange.md):
- layout is DATA, embedded in the same document as the semantics (no sidecar files),
  keyed by stable IDs back into the semantic graph;
- per-node bounds; per-edge waypoint lists; independently positioned labels;
  explicit collapse state; explicit z-order key (never implicit document order);
- viewport/pan/zoom persist only as non-normative session state.

Conformance (gate G4): structural diff of the layout-as-data model is the primary,
zero-tolerance gate; a deterministic SVG/DOM diff is a secondary advisory check;
pixel diff never gates CI (fonts/anti-aliasing/platform flakiness).

Precedents (per U4): cautionary — UML Diagram Interchange (OMG, 2006): ratified,
near-zero tool adoption, later replaced by Diagram Definition. Success — BPMN 2.0
BPMNDI: real cross-vendor interop because every layout object carries an explicit
ID-based reference into the semantic model. Correction of an earlier assumption:
BPMN 1.x had NO standardized interchange format at all (semantic or visual) —
stronger than "lost layout at boundaries".
