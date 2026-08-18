# Governance

> For this project, human contributor policy and agent operating policy are the same
> class of document. This file is the human-readable projection; the machine-hosted
> form lives (aspirationally) in `profiles/domain/agent/repo-policy.osil` and the
> per-skill frontmatter in `improvable/`. A standing loop checks their agreement.

## Ground-truth ownership classes

Every subtree has exactly one ground-truth class, which fixes what agents may do there:

| Class | Meaning | Subtrees | Agent verbs |
|---|---|---|---|
| **self** | this project ratifies truth | `spec/`, `grammar/`, `curriculum/`, `profiles/domain/` | draft, refactor; humans ratify normative MUSTs |
| **shared** | truth negotiated with an ecosystem | `spec/interop/`, `conformance/`, `registry/` | propose (contracts/schemas); add/refresh (corpus, matrix cells, entries) |
| **foreign** | an external ecosystem owns truth | `profiles/ecosystem/*` | sync, report — **MUST NOT redefine upstream semantics** |
| **academic** | published artifacts own truth | `profiles/ontology/*` | cite, audit fidelity |
| **empirical** | measured performance owns truth | `improvable/` | edit bodies freely if evals pass; frontmatter is constitutional (below) |

## The merge gate

A change is legal iff:

1. `diff ⊆ scope(skill)` — every touched path is inside the scope declared by the
   skill the agent ran under (`improvable/<skill>/SKILL.md` frontmatter);
2. the target subtree's invariants (stated on its README card) are preserved;
3. cross-representation consistency holds: a spec change introducing a construct
   ships its grammar production and ≥1 corpus example in the same change
   (triple representation: prose ↔ grammar ↔ corpus);
4. grammar enlargements discharge the **boundary obligation**: the same change
   ships a `conformance/rejections/` fixture for each new construct's boundary,
   or declares "no new boundary" with justification (spec/conformance.md §2).

## Constitution vs legislation

Within any `SKILL.md`: the **body** is legislation — improvable freely (evals must
pass, CHANGELOG entry required). The **frontmatter** (`scope`, `verbs`,
`invariants`) is constitution — changes are propose-only and require human
ratification. Automatic narrowing of scope may be permitted; widening never.
`skill-improver` may never edit its own frontmatter.

## Human ratification points

- Normative MUST/SHOULD changes in `spec/`.
- Grammar changes (they trigger full-corpus re-validation).
- Skill frontmatter changes; new skills.
- Deletions in `conformance/corpus/` (additions are free).
- Anything under `CHARTER.md`, licensing, or LF process.

## Witness diversity

Evidence from a single parser/linter lineage is weak against shared blind
spots: the SIR/CIR definition hole (closed at G13) was found by an EXTERNAL
reading while every internal loop was green. Self-audits SHOULD therefore
include a foreign-witness lane — an external human or alternate-model reader
— before any claim of semantic closure. This is the structural form of the
production-quality assessment's category-F conclusion: epistemic diversity
is a conformance requirement, not a courtesy.

## Versioning

Subtrees are independent version streams (see each README card). Real conformance
is the 3-D matrix in `conformance/matrix/`: spec version × adapter version ×
upstream version. Matrix cells are agent-maintained and machine-checkable.

## Licensing & foundation status

RATIFIED 2026-08-18: Apache-2.0 repo-wide + DCO sign-off (see LICENSING.md).
Contributions are open (CONTRIBUTING.md). LF onboarding path per research U1:
Community-Spec-template-free phase now, LF AI & Data Sandbox at GX. The OAAX
naming collision was resolved 2026-08-18 by the rename to OSIL (ADR-0012);
no naming blocker remains before submission.
