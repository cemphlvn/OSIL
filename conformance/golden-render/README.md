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
Every format research U4 studied is silent on this (BPMN DI included); OSIL
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

### D3 — multi-output edge syntax — RATIFIED at G6 (2026-08-12)
`-> (Y, Z)` landed in grammar v0.4 as POSITIONAL outputs, closed through the
XPASS ritual on fixture 018, with the revisit trigger honored: ONNX Split is
in the suite (4/4, axis attribute via node-proto passthrough). Resolved:
positional-vs-named -> positional (named outputs would re-open only if an
ecosystem's native semantics are positional-ambiguous). D2 interaction
resolved without change: a layout edge references one (src, dst) pair; a
multi-output edge simply admits several pairs. STILL OPEN under D2: parallel
edges (same src AND same dst twice).

### Standing (from U4, adopted as-is, still discussable)
- `viewport` is stored but NON-NORMATIVE — excluded from the golden gate.
- `z` is a sparse integer key, not fractional indexing; escalate to
  CRDT-adjacent ordering ONLY if concurrent multi-agent editing of a single
  document becomes real (U4's stated validity trigger).
- labels carry geometry only; label CONTENT currently renders as the owner's
  identifier — text overrides are an open design question.

## Ratification 2026-08-24 — view goldens re-blessed (G17)

WHO: maintainer, via the G17 change (ADR-0014).
WHY: the derived view data changed because the DECLARATIONS changed, not the
renderer. Two deliberate additions:
  - `projection C` (profiles/ecosystem/c/CONTRACT.osil) — a new row in
    views/projection-map, requiring `ECOSYSTEM_OF`/`ADAPTER_OF` in
    tools/view_render.py to be grown deliberately (the harness refused to guess).
  - `stage cproj` (conformance/corpus/023) — stage-commutation pair matrix
    28 -> 36.
Lie-detection held through the change (2/2 perturbations still move the data),
and determinism held (double build identical), so the goldens are being
re-blessed against a change that the gate itself witnessed.

## Ratification 2026-08-24 — view goldens re-blessed (G19)

WHO: maintainer, via the G19 change (the C lifter, ADR-0014 OQ-2).
WHY: `stage lift` was added to conformance/corpus/023 and to the justfile
`test:` line (standing agreement, 1:1), so the stage-commutation pair matrix
grew 36 -> 45. The DECLARATIONS changed; the renderer did not. Lie-detection
held through the change (2/2 perturbations still move the data) and determinism
held, so the goldens are re-blessed against a change the gate itself witnessed.
projection-map is unchanged (no new projection at G19).

## Ratification 2026-08-24 — view goldens re-blessed (G20)

WHO: maintainer, via the G20 change (the transformation chooser).
WHY: `stage choose` added to corpus 023 and the justfile `test:` line
(standing agreement, 1:1); stage-commutation pair matrix 45 -> 55. The
DECLARATIONS changed, the renderer did not. Lie-detection and determinism both
held through the change. projection-map unchanged (no new projection).

## Ratification 2026-08-24 — view goldens re-blessed (G21)

WHO: maintainer, via the G21 change (capability declarations).
WHY: `stage ceiling` added to corpus 023 and the justfile `test:` line
(standing agreement, 1:1); pair matrix 55 -> 66. Declarations changed, renderer
did not. Lie-detection and determinism held.

## Ratification 2026-08-24 — view goldens re-blessed (G22)

WHO: maintainer, via the G22 change (harness discipline gate).
WHY: `stage harness` added to corpus 023 and the justfile `test:` line
(standing agreement, 1:1); pair matrix 66 -> 78. Declarations changed, renderer
did not. Lie-detection and determinism held.
