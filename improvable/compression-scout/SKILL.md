---
name: compression-scout
description: Measure the system on the compression ladder; detect covering sets and naming opportunities
scope: [conformance/compression/, docs/reports/]
verbs: [measure, report, propose]
cadence: on-demand + per-release
invariants: [rung-named-per-claim, propose-only-on-vocabulary, baselines-never-silently-regress]
evals: evals/
---

# compression-scout

Runs the compression lens over the system (`just compress`) and turns the
results into loops.

## Procedure

1. Run `just compress` (tools/compression_scan.py). It writes the dated report
   and refreshes `conformance/compression/baselines.yaml`.
2. **Compare against the previous baseline.** If any tracked ratio got worse
   (corpus tokens per production up, covering set larger, interop ratios
   worse) without a corresponding ratified change, report it as a regression —
   never silently overwrite an unexplained delta.
3. **Cover direction**: if the covering set shrank or grew, note which
   fixtures entered/left the "books" — curriculum paths may want re-ordering
   (report to humans; pedagogy is ratified).
4. **Name direction**: for each naming candidate (recurring pattern across
   >=3 fixtures), decide the class: (a) candidate CONCEPT for a domain profile
   (representational compression — draft the `concept` block in the report),
   (b) candidate grammar sugar (file in grammar/GAPS.md), or (c) noise
   (explain why). NEVER apply vocabulary or grammar changes yourself.
5. Every claim in your report names its ladder rung
   (bytes / tokens / productions / concepts).

## Harness notes

Claude Code: `just compress` uses uv to supply onnx for the interop axis; if
run without network, the axis reports skipped — that is honest, not a failure.
