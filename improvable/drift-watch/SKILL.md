---
name: drift-watch
description: Track upstream releases for one ecosystem; keep pins and matrix honest
scope: [profiles/ecosystem/, conformance/matrix/]
verbs: [sync, report]
cadence: scheduled
invariants: [never-redefine-upstream, stale-before-bump, no-spec-writes]
evals: evals/
---

# drift-watch (per-ecosystem template)

Foreign ground truth moves on its own schedule. This skill runs per ecosystem
(onnx, egg, mlir, wasm) on a schedule matched to that upstream's release tempo.

## Procedure

1. Read `profiles/ecosystem/<eco>/VERSIONS` (the pins).
2. Check upstream's canonical release source (recorded in PROFILE.md) for anything
   newer than the pins. Primary sources only — release pages, tags, changelogs.
3. No drift -> log a one-line heartbeat in the report and stop.
4. Drift found:
   a. Mark affected `conformance/matrix/` cells `status: stale` with the upstream
      version that staled them.
   b. Summarize what changed upstream (breaking? additive? relevant to our
      contract fields?) with source links.
   c. Draft a pin-bump proposal (VERSIONS diff + expected contract impact).
      NEVER apply the bump and NEVER touch CONTRACT.oaas semantics yourself.
5. Report to docs/reports/drift-<eco>-<date>.md.

## Harness notes

Claude Code: WebFetch the release/tag page; do not rely on memory for version
numbers, ever.
