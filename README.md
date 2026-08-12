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

Pre-release, gates **G0–G6 complete / GX (Linux Foundation) terminal**.
Gate convention: numbered gates keep appending BEFORE the terminal gate GX —
GX is always last. ONNX is the
first REGISTERED LF interop; the repo fully self-describes (policy as actors,
pipelines as flows, its own diagram as the first visual golden). `just test` =
grammar/corpus contract + round-trip preservation score + golden render. Two document kinds since ADR-0005: `.oaas` (vocabulary) and `.flow`
(dataflow composition). Since G2, the repo's own operating policy parses as OAAS.
This repository currently is the *grounds*: tree, governance, grammar draft,
seed conformance corpus, and the agent skill layer. Nothing here is normative yet.

| Gate | Claim someone can falsify | Status |
|---|---|---|
| G0 | a fresh agent, given only this repo, can state each subtree's policy | done |
| G1 | 100% of `conformance/corpus/` parses under `grammar/oaas.ebnf`; every production exemplified | **done 2026-08-12** — `just check`: 9/9 files, 42/42 productions |
| G2 | the repo's own operating policy is expressible in OAAS (conformance test #0) | **done 2026-08-12** — grammar v0.2; XPASS guard verified live |
| G3 | ONNX round-trip preserves its declared contract fields | **done 2026-08-12** — preservation score 4/4, cases {add, matmul} (v0 suite, grows monotonically) |
| G4 | visual identity projection: golden-render diff = 0 across round-trip | **done 2026-08-12** — grammar v0.3 layout block; first golden = OAAS's own render pipeline (test #0v); D1–D3 open discussions in `conformance/golden-render/README.md` |
| G5 | vocabulary self-extends from detector findings: ADR-0007 ratified → `domain.numeric` concepts land → corpus fixture added → re-baseline resolves the naming candidate | **done 2026-08-12** — full loop closed (ADR-0007 RATIFIED; fixture 020; TERMS.md born) |
| G6 | GAP-4 closed with teeth: `-> (Y, Z)` ratified (grammar v0.4) via the XPASS ritual on 018, AND the first ONNX multi-output case (Split, with attribute passthrough) round-trips 4/4 | **done 2026-08-12** |
| GX | Linux Foundation submission checklist satisfied | open, TERMINAL (blocked on maintainer calls: name-vs-OAAX, license) |

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
