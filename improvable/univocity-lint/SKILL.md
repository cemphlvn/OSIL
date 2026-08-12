---
name: univocity-lint
description: Audit spec/ terminology and definitions against the ontology rules
scope: [spec/TERMS.md, docs/reports/]
verbs: [report, propose]
cadence: per-spec-PR
invariants: [read-only-on-spec-prose, findings-cite-line, no-silent-fixes]
evals: evals/
---

# univocity-lint

Keeps `spec/` terminologically sound. This skill READS spec prose and WRITES only
`spec/TERMS.md` (the term inventory) and reports; definition fixes themselves go
back through a spec-editor change with human ratification.

## The checklist (from Arp, Smith & Spear 2015, applied deliberately)

For every audit run over changed spec files:

1. **Univocity of terms**: one term = one meaning everywhere. Flag any term used
   in two senses (e.g. "projection" must never drift between the interop sense and
   a colloquial sense).
2. **Univocity of relational expressions**: `preserves`, `equivalent_under`,
   `implementedBy` etc. mean one thing each, spec-wide.
3. **Every nonroot term has a definition**, in **Aristotelian form**: "an A is a B
   which Cs" — genus + differentia. Flag definitions by example-only.
4. **Essential, not accidental features** in definitions.
5. **No circularity** (A defined via B, B via A).
6. **No mass nouns** as class terms.
7. **General vs particular** kept distinct (the concept `Attention` vs a node
   instance in some graph).
8. **Synonyms tracked**, not tolerated silently: record in `spec/TERMS.md` with
   one canonical term chosen.

## Procedure

1. Build/refresh the term inventory in `spec/TERMS.md`: term, defining file:line,
   definition form (aristotelian / example-only / undefined), synonyms seen.
2. Run the checklist; every finding cites file:line and quotes the offending text.
3. Write findings to `docs/reports/univocity-<date>.md`, severity-ordered:
   BLOCKER (univocity violations in normative text) > DEFECT (missing/circular
   definitions) > STYLE.
4. For each BLOCKER, draft the corrected definition as a *proposal* inside the
   report — do not edit spec prose directly.

## Harness notes

Claude Code: Grep with word boundaries for term occurrence maps before judging
univocity; a term inventory built from memory instead of search is invalid.
