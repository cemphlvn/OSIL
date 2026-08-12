# The Improvable Skill Layer — `improvable/*/SKILL.md`

> Design doc: the repo's agent-instruction infrastructure as a first-class,
> improvable, harness-portable layer. Extends intake passes 1–3. (2026-08-12)

## What this layer is

The synthesis tree gave every subtree an owner, a cadence, and attachable loops —
but a "loop" was still abstract. This layer makes it concrete:

**A deployed agentic loop = skill × subtree × cadence.**

The subtree and cadence come from the synthesis tree. The *procedure* comes from a
skill: `improvable/<skill-name>/SKILL.md`. Skills are the deployment unit of
collective intelligence in this repo — the thing you dispatch, schedule, and improve.

```
improvable/                          ← canonical agent-instruction pool (harness-agnostic)
├─ skill-improver/                   ← the meta-skill: edits other skills from feedback
│  ├─ SKILL.md
│  ├─ evals/                         ← fixtures an edited skill must still pass
│  └─ CHANGELOG.md                   ← improvement ledger
├─ corpus-gardener/                  ← extract/curate conformance corpus fixtures
├─ univocity-lint/                   ← spec coherence, BFO definition audit
├─ drift-watch/                      ← per-ecosystem upstream tracking (scheduled)
├─ matrix-refresh/                   ← compatibility-matrix cell maintenance
├─ render-verify/                    ← golden-render diff loop (visual projection)
└─ INDEX.md                          ← router source; projections generated from it
```

Each skill folder: `SKILL.md` (frontmatter + harness-neutral body) + `evals/` +
`CHANGELOG.md`. Nothing in `improvable/` is sacred — the directory name IS the
contract: everything inside is subject to the skill-improver loop.

## Realization 1 — the instruction layer is itself a projection problem

CLAUDE.md, AGENTS.md, and SKILL.md are not three document types to keep in sync.
They are **three projections of one canonical instruction source**, each with a
different preservation contract — exactly the OAAS interop pattern, recursively
applied to the repo's own agent infrastructure:

| Projection | Reaches | Preserves | May lose |
|---|---|---|---|
| `CLAUDE.md` | Claude Code main loop | project conventions, routing table to skills | procedure bodies (routed, not inlined) |
| `AGENTS.md` | subagents + non-Claude agents (Codex, Cursor, …) | routing table + the conventions subagents need (user CLAUDE.md never reaches them) | Claude-specific harness features |
| `SKILL.md` | on-demand procedural load | full procedure, scope, evals pointer | nothing (this is the identity projection) |
| `.claude/skills/<n>` | Claude Code skill discovery | frontmatter contract | — (symlink/generated from `improvable/`) |

Consequences:
- **Router pattern**: CLAUDE.md and AGENTS.md contain a stable routing layer
  ("for task X, read `improvable/<skill>/SKILL.md` and follow it"), never procedure
  bodies. Non-Claude agents can't invoke skills natively but can always read files —
  routing-by-reference is the lowest common denominator that makes one source serve
  every harness.
- **Harness-neutral bodies**: a SKILL.md body must execute as plain instructions for
  any file-reading agent. Harness-specific affordances (Claude tool names, MCP
  calls) go in a clearly marked `## Harness notes` section that foreign agents may
  skip without losing the procedure.
- **Generated, never hand-synced**: CLAUDE.md/AGENTS.md routing tables and
  `.claude/skills/` entries are generated from `improvable/INDEX.md`. Drift between
  projections is a CI failure, not a doc-review discovery. (Same pool-and-views
  discipline as corpus/curriculum in pass 3.)

## Realization 2 — skill frontmatter is the policy binding

The per-subtree policy from passes 1–3 was declared *on the tree*. Skills bind it
*to procedures*:

```yaml
---
name: drift-watch-onnx
description: Track ONNX releases; refresh pins, contracts, matrix cells
scope: [profiles/ecosystem/onnx/, conformance/matrix/]   # subtrees it may touch
verbs: [sync, report]                                     # per pass-1 ownership class
cadence: scheduled                                        # per pass-3 stream
invariants: [never-redefine-upstream, matrix-cells-machine-checkable]
evals: evals/
---
```

This closes the enforcement loop from pass 2: **an agent runs under a skill; its
diff is a proposed rewrite; the merge gate checks `diff ⊆ scope(skill)` and
`invariants(subtree) preserved`.** Policy stops being ambient and becomes the
declared contract of the procedure that produced the change.

And it extends conformance test #0: skill frontmatter (scope/verbs/invariants) must
be *expressible in OAAS* and must **agree** with `profiles/domain/agent/` — a
cheap, permanent consistency loop between the two policy representations. The repo
now dogfoods its spec twice: once in policy (pass 2), once in instructions (here).

## Realization 3 — a new cadence class with an empirical ground truth

Pass 3's cadence table gains a row, and it's categorically different:

| Subtree | Cadence | Ground truth |
|---|---|---|
| `improvable/` | **feedback-speed (fastest in repo)** | **empirical performance** — measured by evals, not ratified by consensus |

Every other subtree's ground truth is normative (self, shared, foreign, academic).
Skills are judged by whether the loops they drive get better. That makes the skill
layer the one place where the eval-driven discipline applies wholesale:

- each skill ships `evals/` — fixtures describing situations and the behavior class
  the skill must produce;
- `skill-improver` is the optimizer: feedback signal (gate failure, agent error,
  human correction) → proposed SKILL.md edit → edited skill must still pass its
  evals → CHANGELOG entry (the ledger);
- never score on what you optimized: eval fixtures grow from *new* failures, and a
  held-out subset stays out of the improver's view;
- state lives on disk (ledger + changelog + best pointer), so any fresh agent can
  resume the improvement loop — agents are stateless, the loop is not.

## Realization 4 — constitution vs legislation (self-modification guardrail)

`skill-improver` editing skills is a self-modifying system; it needs asymmetric
amendment rules *within a single file*:

- **Body = legislation**: the improver may edit procedure text freely, provided the
  skill's evals still pass and the change is CHANGELOG-logged.
- **Frontmatter = constitution**: `scope`, `verbs`, `invariants` changes are
  propose-only — they require human ratification, because widening a scope is a
  policy change, not an improvement. (Automatic *narrowing* may be permitted;
  widening never.)
- `skill-improver` may never edit its own frontmatter, and edits to its own body
  require passing the strictest eval set in the repo.

This is transcript §9 one more time: an improvement is a rewrite, legal only if it
preserves the invariants — applied now to the layer that writes the rewriters.

## Placement in the synthesis tree

`improvable/` enters as a top-level, repo-shaped subtree (own CI: skill-schema
validation, projection-drift check, eval runs). Bootstrap order: the skill layer is
part of **G0/G1** — `corpus-gardener` and `univocity-lint` are needed to *reach*
G1, so the first two skills and the router projections are bootstrap deliverables,
with `skill-improver` itself allowed to start as a stub (the loop can improve the
improver later; it cannot retroactively create the ledger discipline — that must
exist from the first skill).
