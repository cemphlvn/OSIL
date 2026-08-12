# Production-quality assessment — 2026-08-12
Loop: repo-wide evaluation (maintainer request). RESULT: **process-mature,
artifact-early** — production-grade discipline wrapped around prototype-grade
language infrastructure.

## Sequence (evidence per dimension)

| Dimension | Grade | Evidence |
|---|---|---|
| Conformance discipline | **A** | 21 positive + 6 rejection fixtures; coverage 61/61 productions, 40/40 alternatives, both granularities derived from the EBNF, not self-asserted; pins/rituals/promote exits all exercised at least once; CI green on clean runner first try |
| Governance-as-code | **A−** | policy agreement mechanical (9 actors/8 skills); constitution/legislation; 8 ADRs, 13 reports, full ratification trail; minus: single ratifier, no branch protection |
| Reproducibility | **B+** | dep-free reference parser; ephemeral uv deps; CI = local (`just test`); minus: no lockfile by design keeps CI cache cold |
| Spec prose maturity | **C−** | 2 working chapters (visual, conformance) / 4 stubs (core is "draft-0 non-normative"; execution, interchange, versioning empty); TERMS.md has 3 entries — univocity-lint has never run a full audit |
| Language reality | **D+** | syntax-only: no AST, no resolver (`use` unresolved, ops unchecked vs registry, no type/shape checking). G1-enablement ladder rungs 1–3 all open |
| Implementation hygiene | **C** | FOUR independent token-readers (oaas_check, roundtrip.read_flow, render_check.read, policy_check.parse_actors) — drift risk flagged at G6, never retired; 1,839 LOC tools |
| Suite breadth | **C** | ONNX: 3 cases (~3/200 ops); 1 golden-render fixture; egg/mlir/wasm untested (U5/U6 open) |
| Improvable layer | **D** | 8 skills, **0 eval fixtures** — the empirical ground truth of `improvable/` has never been measured; skill-improver has nothing to regress against |
| External validity | **D** | 1 author, 1 day, 0 external implementations, 0 contributors (blocked pending license — deliberate), scheduled loops never fired |

Headline risk (named repeatedly, still open): **direction-of-fit monoculture**
— grammar, corpus, parser, and policy were co-authored; a shared bug agrees
with itself. No second witness exists for any artifact.

## Strategic repo-wide metrics

Tracked today: coverage (2 granularities) · preservation score per matrix
cell · compression ladder + covering set + naming candidates · policy
agreement · golden zero-diff · curriculum reachability · gates/gaps ledger.

North-star additions (what should steer the next quarter):
1. **Resolution rate** — % of references (use→profile, op→registry entry,
   concept→carrier) mechanically resolved. Today ≈ 0%. THE metric for the
   language becoming real (G1-enablement rungs 1–3).
2. **Independent-witness count** — readers collapsed toward 1 AST (now 4);
   independent implementations (now 0; a second parser enables differential
   testing). Anti-monoculture metric.
3. **Refusal density** — rejections per production (6/61 ≈ 0.10); boundary
   obligation should keep this from decaying as the grammar grows.
4. **Eval density** — fixtures per skill (0/8). Until >0, "improvable" is a
   label, not a property.
5. **Loop liveness** — loops defined vs ever-fired vs on-schedule. Sentinel
   loops (drift-watch, matrix-refresh) are defined and DORMANT: no schedule
   has ever fired one.
6. **Suite breadth** — ops covered per ecosystem vs upstream surface; matrix
   cells verified × upstream versions.
7. **Spec maturity vector** — chapters normative/working/stub (0/2/4);
   definitions with corpus witnesses.

## Categories of establishable dev loops

| Category | Ground truth | Status | Examples / to establish |
|---|---|---|---|
| A. Per-change gates | self (mechanical) | **LIVE in CI** | corpus contract, policy agreement, render gate, round-trip, baseline diff |
| B. Scheduled sentinels | foreign (upstream) | defined, **dormant** | drift-watch per ecosystem, matrix refresh; establish = cron/Actions schedule — cheapest unlit loop |
| C. Feedback/improvement | empirical (evals) | declared, **unpracticed** | skill-improver over skills; blocked on eval density = 0; establish = seed fixtures from the failure signals already in CHANGELOGs |
| D. Discovery/detection | generated proposals | **proven 3×** | compression-scout→ADR-0007; self-description pressure→GAP-4/GAP-5; alternative-gap wishlist; univocity full audit (never run) |
| E. Synthesis/generation | derived views | **proven** | minimal-spine curriculum, matrix, baselines; next: routing-table projections generated from INDEX (now hand-synced), auto-layout proposer, wizard |
| F. Verification-strengthening | adversarial | **absent, highest value** | second parser + differential testing; grammar fuzzing (mutants of fixtures should mostly REJECT); property tests on round-trips — the direct answer to the monoculture risk |
| G. Human-ratification | maintainer | **proven 6×** | ADR propose→ratify (0007, 0008); pin rituals (G2, G6, G9); promote (G11) |

Symmetry note: categories map onto the pass-1 ground-truth classes — A/self,
B/foreign, C/empirical, D–E/generated, G/ratified — the loop taxonomy is the
ownership taxonomy, animated.

## Honesty notes
- This assessment was produced by the repo's sole author; the grades most
  likely to be inflated are exactly the ones grading my own discipline (A/A−
  rows). An external reviewer or a category-F loop is the corrective.
- "Process-mature" is real but cheap while N=1: no rule has yet been tested
  against a contributor who disagrees with it.
