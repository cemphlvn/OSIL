---
name: corpus-gardener
description: Grow and curate the conformance corpus; the G1 loop's hands
scope: [conformance/corpus/, grammar/GAPS.md, curriculum/paths/]
verbs: [add, refresh, report]
cadence: per-PR, on-demand
invariants: [every-example-parses-or-gap-filed, one-construct-per-file, provenance-header-required, no-deletion-without-ratification]
evals: evals/
---

# corpus-gardener

The conformance corpus (`conformance/corpus/`) is the ONE canonical example pool —
fixtures for the grammar, oracle for round-trips, and raw material for curriculum
paths. This skill keeps it growing and honest.

## Sources of candidates (in priority order)

1. Code fences in `spec/*.md` — every DSL block in normative prose is a latent
   fixture; extracting it is mandatory (triple-representation rule).
2. New constructs arriving via spec PRs.
3. Contributions and issues.
4. The intake transcript (`docs/intake/`) — historical source, mostly mined.

## Procedure

1. **Normalize**: one construct per file. File name `NNN-slug.oaas` (NNN =
   next free id, ids are stable forever). Header comment:
   `// provenance: <where this came from, with date>` plus
   `// normalized: <what you changed>` if you adapted the raw source.
2. **Parse-check** against `grammar/oaas.ebnf`. While no parser exists in
   `tools/`, do a by-hand derivation against the EBNF and say so in the PR.
   - Parses → done.
   - Doesn't parse → DO NOT edit the grammar. File the gap in `grammar/GAPS.md`
     (construct, failing production, corpus id). Grammar changes are
     constitutional-grade (human ratification; full-corpus re-validation).
     A deliberately unparseable file (e.g. conformance test #0) gets an
     `// EXPECTED-FAIL:` header line naming the gap.
3. **Curriculum reachability**: check `curriculum/paths/*.yaml` still resolve, and
   report (not fix) corpus items unreachable from any path — pedagogy ordering is
   a human call.
4. **Never delete or renumber.** Supersede: add the better example, mark the old
   one `// deprecated-by: NNN` and propose the removal for ratification.

## Report format

PR description or `docs/reports/corpus-<date>.md`: items added (ids), gaps filed,
unreachable items, parse status summary (n/n by-hand-derived until tools/ exists).

## Harness notes

Claude Code: batch-create files with Write; keep each fixture minimal — a fixture
that needs a paragraph of explanation is two fixtures.
