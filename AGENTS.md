# OSIL — agent instructions (subagent / cross-harness projection)

> You may be a Claude subagent, a Codex/Cursor/other agent, or a scheduled job.
> This file is a PROJECTION of `GOVERNANCE.md` + `improvable/INDEX.md`; those are
> canonical. `CLAUDE.md` is the Claude-main-loop sibling of this file.

## Orientation (60 seconds)

- This repo is an open spec for **OSIL**, a semantic architecture layer
  (projections into ONNX/egglog/MLIR under preservation contracts). `README.md` has
  the map; every top-level directory has a README card stating its ground-truth
  owner, cadence, loops, and invariants.
- **Your diff is a proposed rewrite.** It is legal only if (1) every touched path
  is inside the scope of the skill you were dispatched under, (2) the subtree's
  invariants hold, (3) construct changes ship prose+grammar+corpus together.

## Procedures

Task-to-procedure routing lives in the table below. Read the skill file and follow
its body; it is written harness-neutrally (any file-reading agent can execute it).
Harness-specific notes are in each skill's `## Harness notes` section — skip them
if they don't apply to you.

| Task | Procedure file |
|---|---|
| Add/curate conformance examples | `improvable/corpus-gardener/SKILL.md` |
| Spec terminology/definition audit | `improvable/univocity-lint/SKILL.md` |
| Upstream ecosystem release tracking | `improvable/drift-watch/SKILL.md` |
| Compatibility matrix maintenance | `improvable/matrix-refresh/SKILL.md` |
| Visual golden-render checks | `improvable/render-verify/SKILL.md` |
| Compression metrics / naming detection | `improvable/compression-scout/SKILL.md` |
| Gate/loop report authoring | `improvable/gate-reporter/SKILL.md` |
| Improving any skill from feedback | `improvable/skill-improver/SKILL.md` |

## Hard rules

- `profiles/ecosystem/*`: NEVER redefine upstream semantics; you sync and report.
- `conformance/corpus/`: additions free; deletions require human ratification.
  Two document kinds (ADR-0005): `.osil` = vocabulary, `.flow` = dataflow
  composition; the validator selects the grammar's start symbol by extension.
- `improvable/*/SKILL.md`: bodies may be improved if evals pass + CHANGELOG entry;
  frontmatter (`scope`/`verbs`/`invariants`) is constitutional — propose only.
- Unverified claims are marked `ASSUMPTION:`; never silently resolve one.
- Decisions → `docs/decisions/` (ADR); research → `docs/research/`;
  reports → `docs/reports/`. Artifacts over chat: your final message should point
  at files.
