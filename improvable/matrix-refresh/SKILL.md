---
name: matrix-refresh
description: Verify and refresh compatibility-matrix cells (spec x adapter x upstream)
scope: [conformance/matrix/]
verbs: [refresh]
cadence: scheduled
invariants: [cells-machine-checkable, timestamps-required, never-fabricate-pass]
evals: evals/
---

# matrix-refresh

STATUS: stub until G3 lands an adapter that can actually round-trip.

The matrix (conformance/matrix/matrix.yaml) is the project's flagship
agent-maintained artifact: each cell = (spec version, adapter, upstream version)
with status pass | fail | stale | unverified.

## Procedure (activates at G3)

1. Enumerate cells; for each with a runnable adapter: run the round-trip eval
   (import -> transform -> export), scoring each field of the adapter's
   preservation contract.
2. Record per-field results, overall status, and a checked timestamp in the cell.
3. A cell may only move to `pass` on mechanical evidence. If the harness cannot
   run, the cell stays `unverified` -- never infer a pass.
4. Report deltas to docs/reports/matrix-<date>.md.
