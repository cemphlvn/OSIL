# OAAS

**A semantic architecture layer, as an open specification.**

OAAS lets toolchains see what conventional IRs cannot: intent, semantic role,
equivalence, constraints, invariants, ontology, security requirements. Its core
object is the **semantic optimization space** — the space of semantically valid
realizations of an intention — and its core stance is coordination, not absorption:
external ecosystems (ONNX, egg/e-graphs, MLIR, WASM) remain sovereign, reached
through **projections** governed by **preservation contracts**.

> Name note: "OAAS" is currently a proper name; its expansion is an open naming
> decision. Research U1 found a live collision risk: **OAAX** (Open AI Accelerator
> eXchange), an existing LF AI & Data project one letter away in an adjacent
> domain — resolve the name before any LF-facing announcement
> (`docs/research/U1-lf-onboarding.md`).

## Status

Pre-release, gate **G0 (bootstrap) complete / G1 (grammar+corpus) open**.
This repository currently is the *grounds*: tree, governance, grammar draft,
seed conformance corpus, and the agent skill layer. Nothing here is normative yet.

| Gate | Claim someone can falsify | Status |
|---|---|---|
| G0 | a fresh agent, given only this repo, can state each subtree's policy | done |
| G1 | 100% of `conformance/corpus/` parses under `grammar/oaas.ebnf`; every production exemplified | **open — critical path** |
| G2 | the repo's own operating policy is expressible in OAAS (conformance test #0) | open (currently EXPECTED-FAIL, see `profiles/domain/agent/`) |
| G3 | ONNX round-trip preserves its declared contract fields | open |
| G4 | visual identity projection: golden-render diff = 0 across round-trip | open |
| G5 | Linux Foundation submission checklist satisfied | open (pending research U1/U2) |

## The tree

Every top-level directory is **repo-shaped** (own README card stating ground-truth
owner, cadence, loops, policy) so future fission into separate repos is mechanical.

```
spec/          normative prose (consensus-slow, self-owned)
grammar/       EBNF + schemas — the critical path: no loop bites until this exists
conformance/   corpus (canonical example pool) · golden-render · compatibility matrix
profiles/      ecosystem (foreign-owned) · ontology (academic) · domain (incl. self-hosted repo policy)
registry/      one-entry-per-file ecosystem manifests (fast, data-shaped)
curriculum/    learning paths = index layers over the corpus (never duplicated content)
improvable/    agent skills with evals — the repo's engineering loops, themselves improvable
tools/         (later) parser, CLI, wizard, renderer
docs/          intake analysis · design docs · ADRs · research · reports
```

## How agents operate here

Read `GOVERNANCE.md`, then the routing table in `AGENTS.md`/`CLAUDE.md`.
Rule of the repo: **an agent's diff is a proposed rewrite, legal only if it stays
within the scope of the skill it runs under and preserves the target subtree's
invariants** — the spec's own rewrite-legality principle (§ invariants as guards),
pointed at the repository itself.

## Provenance

Born from a conversation that drifted from evaluating an MSc in Cyber Security to
designing an open semantic architecture standard. The full intake analysis (three
reading passes + synthesis) lives in `docs/intake/`. Security did not leave the
project: it survives as first-class invariants (`ConstantTime`, information flow,
category-level crypto substitution).
