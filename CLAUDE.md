# OAAS — project instructions (Claude Code main-loop projection)

> This file is a PROJECTION of canonical sources: `GOVERNANCE.md` (policy) and
> `improvable/INDEX.md` (skill routing). If it disagrees with them, they win and
> this file has drifted — fixing the drift is a bug fix. Its sibling `AGENTS.md`
> carries the same content for subagents and non-Claude agents; keep them in sync.

## What this repo is

An open specification for OAAS, a semantic architecture layer. Core concepts:
semantic optimization space, projection, preservation contract, identity
projection, invariants-as-rewrite-guards. Read `README.md` first; deep context in
`docs/intake/` (three-pass analysis) and `docs/design/`.

## Operating rules

1. **Policy first**: before writing anywhere, check the target subtree's README
   card (owner, invariants, verbs) and `GOVERNANCE.md`. Your diff must stay inside
   the scope of the skill you operate under.
2. **Route through skills**: for a task matching the table below, read the skill
   file and follow it — do not improvise a parallel procedure.
3. **Triple representation**: any spec change that adds/renames a language
   construct must ship a grammar production + ≥1 corpus example in the same change.
4. **Corpus discipline**: one construct per file, `//` provenance header, ids are
   stable (`NNN-slug.oaas` vocabulary / `NNN-slug.flow` flows — ADR-0005). Never
   delete without human ratification.
5. **Mark, don't resolve**: unverified claims get `ASSUMPTION:`; decisions get an
   ADR in `docs/decisions/`; research lands in `docs/research/U#-slug.md`.
6. **Definitions** in `spec/` follow the ontology rules: univocity, Aristotelian
   genus+differentia, essential features, no circularity, no mass nouns.
7. Python tooling uses `uv`; prefer a `justfile` for repeatable commands.

## Skill routing (generated from improvable/INDEX.md — do not edit here)

| Task | Skill |
|---|---|
| Add/curate conformance examples | `improvable/corpus-gardener/SKILL.md` |
| Spec terminology/definition audit | `improvable/univocity-lint/SKILL.md` |
| Upstream ecosystem release tracking | `improvable/drift-watch/SKILL.md` |
| Compatibility matrix maintenance | `improvable/matrix-refresh/SKILL.md` |
| Visual golden-render checks | `improvable/render-verify/SKILL.md` |
| Improving any skill from feedback | `improvable/skill-improver/SKILL.md` |

## Current gate

G1 is the critical path: `grammar/oaas.ebnf` must parse 100% of
`conformance/corpus/`. No parser exists yet (`tools/` is empty); building the
minimal parser/validator is the highest-leverage next task.
