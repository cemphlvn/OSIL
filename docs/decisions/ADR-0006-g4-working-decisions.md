# ADR-0006: G4 working decisions D1-D3 under delegated judgment
Date: 2026-08-12 · Status: accepted as WORKING decisions; discussions OPEN
Context: G4 required three design decisions (coordinate convention, edge
identity for layout anchoring, multi-output edge syntax). Maintainer delegated
judgment and directed that they remain open discussions in the golden-renderer
README.
Decision: D1 top-left origin/+y down/abstract px · D2 anchor by src->dst pair ·
D3 propose `-> (Y, Z)` while GAP-4 stays pinned by corpus 018.
Consequence: adopted normatively in spec/visual.md and grammar v0.3; the
canonical discussion venue (with revisit triggers) is
conformance/golden-render/README.md — this ADR records only the adoption.
