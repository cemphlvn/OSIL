# Visual Grammar & Layout
Status: stub (draft-0) — restores the project's FOUNDING requirement (a visual DSL).
Position (ratification pending): visual layout is NORMATIVE CONTENT, not decoration.
The native serialization preserves it totally; other projections may declare it in
may_lose. Layout is data (positions, waypoints, anchors — schema TBD per research
U4), never pixels; conformance/golden-render/ carries the deterministic render-diff
loop (gate G4).
Cautionary precedent under verification (U4): BPMN 1.x reportedly lost diagram
layout at interchange until BPMN 2.0 added Diagram Interchange. ASSUMPTION until
the research lands.
