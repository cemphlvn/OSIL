# golden-render/ — the G4 loop's fixtures (subtree card)

Goldens for the visual identity projection: `<id>.layout.json` (canonical
layout-as-data — the GATE) + `<id>.svg` (deterministic render — ADVISORY).
Run `just render`; bless goldens via `just render-bless` (a ratification act —
record who/why in the PR). Three-tier verdict per spec/visual.md: data diff
gates, SVG byte-diff advises, pixels never.
invariants: deterministic-render-only · zero-diff-gate · layout-as-data ·
goldens change only via ratified blessing

## OPEN DISCUSSIONS (working decisions, adopted under delegated judgment 2026-08-12)

Adopted to unblock G4; each stays open with its revisit trigger stated.

### D1 — coordinate convention
ADOPTED: top-left origin, +y down, abstract px-like units (CSS/SVG-aligned).
Every format research U4 studied is silent on this (BPMN DI included); OAAS
chooses to be explicit. OPEN: unit semantics for zoom-independent export; and
whether a device-independent unit declaration belongs in `viewport`.
REVISIT WHEN: a second renderer appears, or an import from a y-up coordinate
world (CAD/traditional graphics) is attempted.

### D2 — edge identity for layout anchoring
ADOPTED: layout edges anchor by `src -> dst` pair (unique in v0 flows) —
BPMNDI's anchor-by-reference principle without introducing edge names.
OPEN: parallel edges (two semantic edges sharing src+dst) are inexpressible;
candidate fixes are optional edge names or ordinal disambiguation.
REVISIT WHEN: the first flow needs parallel edges, or GAP-4 ratification
introduces edge naming anyway.

### D3 — multi-output edge syntax (GAP-4, pinned by corpus 018)
PROPOSED, not yet grammar: `-> (Y, Z)`. Needed by toolchain ExportFlow and by
ONNX Split/Dropout as the suite grows. OPEN: positional vs named outputs at
the arrow; interaction with D2 anchoring once one edge has several
destinations. REVISIT WHEN: the first ONNX multi-output case lands — that PR
must close GAP-4 through the XPASS ritual on fixture 018.

### Standing (from U4, adopted as-is, still discussable)
- `viewport` is stored but NON-NORMATIVE — excluded from the golden gate.
- `z` is a sparse integer key, not fractional indexing; escalate to
  CRDT-adjacent ordering ONLY if concurrent multi-agent editing of a single
  document becomes real (U4's stated validity trigger).
- labels carry geometry only; label CONTENT currently renders as the owner's
  identifier — text overrides are an open design question.
