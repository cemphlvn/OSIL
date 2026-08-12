# ADR-0002: The native serialization is the identity projection
Date: 2026-08-12 · Status: accepted (schema details pending research U4)
Context: the founding request was a VISUAL DSL, yet visual_layout was the only
field the drafted preservation contracts sacrificed (may_lose) — the origin
requirement had become the structure's one disposable item.
Decision: define the OAAS native serialization as the unique projection with an
empty may_lose set — total preservation, including visual_layout. Layout is data
(schema TBD), never pixels; gate G4 verifies via deterministic golden-render diff.
Consequence: visual layout is normative content; spec/visual.md is a peer of core.md.
