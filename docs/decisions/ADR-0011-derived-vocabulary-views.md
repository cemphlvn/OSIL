# ADR-0011: vocabulary views are DERIVED, not declared

Date: 2026-08-13 · Status: ACCEPTED (G16 staged and started by maintainer
instruction "G16"; direction chosen under the delegated-judgment precedent —
the gate's shape was proposed to and accepted by the maintainer in-session
as "layout blocks for vocabulary documents, and goldens generated from the
same declarations the harnesses read"; this ADR resolves the tension between
those two halves in favor of the second).

## Context
After G15 the repo's most load-bearing structures — strata, projections,
contracts, stage commutation — have no visual form in-repo: layout blocks
are flow-only, and the G4 golden loop governs exactly one diagram family.
The atlas (out-of-repo) proved the demand and named the risk: ungoverned
diagrams drift from ground truth.

## Decision
**A vocabulary view is a deterministic function of declarations, never an
authored drawing.** `tools/view_render.py` reads the SAME sources the
harnesses read (via the shared reader `tools/oaas_read.py` — the G12
anti-fifth-reader module, extended rather than forked), computes canonical
view DATA (nodes, edges, labels, verdicts; volatile fields like checked
dates excluded), and renders an austere advisory SVG. The G4 three-tier
verdict is reused verbatim: data zero-diff GATES against blessed goldens in
`conformance/golden-render/views/`; SVG byte-diff ADVISES; pixels never.
Blessing (`just views-bless`) is a ratification act.

Two witnesses ship inside the gate run:
1. **Determinism**: the view is built twice in-process; any byte difference
   fails the run.
2. **Lie-detection**: the view data is recomputed from a deliberately
   perturbed in-memory copy of the declarations (a dropped write-set entry;
   a dropped contract field); if the perturbed data does NOT differ from
   the real data, the run fails — proving the diagram is coupled to ground
   truth, not decorative.

Consequences: a change to any declaration a view depends on changes the
derived data, fails the zero-diff gate, and forces a re-blessing — a
diagram that lies is a build failure. ZERO grammar growth: views span
documents, so no document needs new syntax. The `views` stage is declared
in corpus 023 with an EMPTY write-set (normal runs only compare; blessing
writes), so it commutes with every stage and the agreement loop grows to
8/8.

## Alternatives rejected
- **Declared layout blocks in .oaas documents** (the other half of the
  original proposal): a view like the projection map SPANS many documents —
  no single document owns its geometry, so authored layout would need a new
  owner concept, new grammar, and hand-maintenance that drifts. Rejected
  FOR CROSS-DOCUMENT VIEWS; recorded as the right tool for a future
  single-document vocabulary diagram whose aesthetics are part of its
  identity. REVISIT WHEN: a vocabulary document needs an authored visual
  form that the identity projection must round-trip.
- **Governing the atlas itself**: the claude.ai artifact is presentation,
  not conformance; governing it would couple the repo to an external host.
  The governed views are its in-repo counterparts.

## Honesty
- The advisory SVGs stay in the repo's austere idiom (monospace, strokes,
  no color semantics); D1 (units) and D2 (parallel edges) remain open.
- `views` READS matrix.yaml (scores) — another read-write ordering the
  write-only guard cannot see (must run after roundtrip/egraph to see fresh
  scores); the Bernstein refinement (ADR-0010) now has two motivating
  cases.
- View geometry constants (box sizes, gaps) live in the renderer; changing
  them changes SVGs but NOT view data — the gate is on meaning, not pixels.
