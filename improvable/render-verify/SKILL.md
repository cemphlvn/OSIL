---
name: render-verify
description: Golden-render diff loop for the visual identity projection
scope: [conformance/golden-render/]
verbs: [add, verify]
cadence: per-PR
invariants: [deterministic-render-only, zero-diff-gate, layout-as-data]
evals: evals/
---

# render-verify

STATUS: stub until G4 lands a deterministic renderer in tools/.

Guards the founding requirement: OAAS is a VISUAL DSL, and the native
serialization (identity projection) preserves visual_layout totally.

## Procedure (activates at G4)

1. For each corpus item carrying layout data: render deterministically (pinned
   fonts, pinned renderer version, no time/randomness inputs).
2. Compare against the golden render (structural/SVG diff preferred over pixel
   diff -- pending research U4's recommendation).
3. Round-trip check: serialize -> parse -> render again; diff must be zero.
4. Intentional visual changes update goldens ONLY via human-ratified PR.
5. Report to docs/reports/render-<date>.md.
