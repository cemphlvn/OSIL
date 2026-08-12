# improvable/ — skill index (canonical routing source)

Everything in this directory is subject to the skill-improver loop; nothing here is
sacred. Ground truth for this subtree is EMPIRICAL: a skill is good iff the loop it
drives gets better, as measured by its `evals/`. The routing tables in `CLAUDE.md`
and `AGENTS.md` are projections of this index — if they disagree, this file wins.

| Skill | Drives which loop | Scope | Verbs | Cadence | Status |
|---|---|---|---|---|---|
| `skill-improver` | meta: improves skills from feedback | `improvable/` | edit-body, propose-frontmatter | feedback | stub-active |
| `corpus-gardener` | corpus growth & integrity (G1) | `conformance/corpus/`, `grammar/GAPS.md`, `curriculum/paths/` (read) | add, refresh, report | per-PR + on-demand | active |
| `univocity-lint` | spec coherence & definition audit | `spec/` (read), `docs/reports/` (write), `spec/TERMS.md` | report, propose | per-spec-PR | active |
| `drift-watch` | upstream release tracking | `profiles/ecosystem/<eco>/`, `conformance/matrix/` | sync, report | scheduled | template |
| `matrix-refresh` | compatibility matrix cells | `conformance/matrix/` | refresh | scheduled | stub (needs G3 adapters) |
| `render-verify` | visual golden-render diffing | `conformance/golden-render/` | add, verify | per-PR | stub (needs G4 renderer) |

## Skill file contract

Each skill folder: `SKILL.md` (YAML frontmatter + harness-neutral body) +
`evals/` (fixtures an edited skill must still pass) + `CHANGELOG.md` (ledger).

Frontmatter fields: `name`, `description`, `scope` (paths the runner may touch),
`verbs`, `cadence`, `invariants`, `evals`. Frontmatter is CONSTITUTIONAL
(propose-only; human ratification; see GOVERNANCE.md). Bodies are legislation.

Frontmatter must stay in agreement with `profiles/domain/agent/repo-policy.oaas`
(the self-hosted policy). Checking that agreement is a standing loop — currently
manual, mechanical once G2 lands.

## Projection maintenance

When a skill is added/renamed or its scope changes (post-ratification), regenerate:
1. the routing tables in `CLAUDE.md` and `AGENTS.md`;
2. (later) `.claude/skills/` entries for Claude Code discovery — deliberately not
   created at bootstrap; revisit when skills stabilize.
Drift between this index and any projection is a CI failure once CI exists.
