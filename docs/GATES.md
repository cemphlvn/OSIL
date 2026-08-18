# Gate Ledger

> Naming note: the project was renamed OAAS -> OSIL on 2026-08-18 (ADR-0012,
> gate G17). Ledger rows are dated history and retain the names used at the
> time.

Development proceeds through **falsifiable gates**: each gate is a claim someone
could prove false, closed only when machinery demonstrates it. Numbered gates
append before the terminal gate **GX** (Linux Foundation submission), which is
always last. The grammar-gap ledger (`grammar/GAPS.md`) is fully closed.
Quick status: `just gates`.

| Gate | Claim someone can falsify | Status |
|---|---|---|
| G0 | a fresh agent, given only this repo, can state each subtree's policy | done |
| G1 | 100% of `conformance/corpus/` parses under `grammar/oaas.ebnf`; every production exemplified | **done 2026-08-12** — `just check`: 9/9 files, 42/42 productions |
| G2 | the repo's own operating policy is expressible in OAAS (conformance test #0) | **done 2026-08-12** — grammar v0.2; XPASS guard verified live |
| G3 | ONNX round-trip preserves its declared contract fields | **done 2026-08-12** — preservation score 4/4, cases {add, matmul} (v0 suite, grows monotonically) |
| G4 | visual identity projection: golden-render diff = 0 across round-trip | **done 2026-08-12** — grammar v0.3 layout block; first golden = OAAS's own render pipeline (test #0v); D1–D3 open discussions in `conformance/golden-render/README.md` |
| G5 | vocabulary self-extends from detector findings: ADR-0007 ratified → `domain.numeric` concepts land → corpus fixture added → re-baseline resolves the naming candidate | **done 2026-08-12** — full loop closed (ADR-0007 RATIFIED; fixture 020; TERMS.md born) |
| G6 | GAP-4 closed with teeth: `-> (Y, Z)` ratified (grammar v0.4) via the XPASS ritual on 018, AND the first ONNX multi-output case (Split, with attribute passthrough) round-trips 4/4 | **done 2026-08-12** |
| G7 | the language's refusals are falsifiable: permanent rejections (`conformance/rejections/`, MUST-FAIL, never flipped) + GAP-2 pinned bidirectionally (021) | **done 2026-08-12** |
| G8 | the structure is self-checking: policy agreement mechanical (`tools/policy_check.py`, actors parsed from OAAS text vs skill frontmatter), definition debt cleared, triad indexed, curriculum reachability measured, CI carries the gates | **done 2026-08-12** — GAP-5 discovered & pinned (022) |
| G9 | GAP-5 closed: dotted path components (grammar v0.5) via the XPASS ritual on 022; policy scopes narrowed to file granularity matching skill declarations | **done 2026-08-12** |
| G10-A | boundary obligation discharged for v0.5: R005 pins the dangling-dot refusal G9 left owed | **done 2026-08-12** |
| G10-B | ritual completeness normative: pin lifecycle (flip / delete / PROMOTE), boundary obligation, ritual-vs-alarm XPASS — spec + merge gate | **done 2026-08-12** (executed before A: norm before instance) |
| G11 | GAP-2 closed: binding univocity ratified (ADR-0008 — `:` roles, `=` equality; grammar unchanged); pin 021 PROMOTED to R006 — the lifecycle's third exit, first performance | **done 2026-08-12** — no open gaps remain |
| G12 | the resolver (rungs 1–2): resolution rate 1.00 over all flows; namespace binding normative; registry oracle live; pin-consistency; refusals RS001–004 REJECT | **done 2026-08-12** |
| G13 | stratification closure: SIR/CIR/NATIVE + realization defined (constitutional equation); every projection.from resolves; source-stratum legality is a DISTINCT check (RS005/RS006); corpus unchanged; grammar productions added = 0 | **done 2026-08-12** |
| G14 | e-graph contract: U5 decides egg-vs-egglog, then the equivalence projection gets a tested preservation contract (the search-ecosystem analog of G3) | **done 2026-08-12** — egglog (ADR-0009); score 4/4 over the 6 corpus equivalences (`just egraph`); realizability discovered: 3 of 6 declared `<=>` realize as directed rules; egg/-vs-egglog dir naming held open |
| G15 | architecture as test object: a stage-composition term language (ONE new construct — triple representation due: prose + grammar production + corpus example) with commutation equivalences guarded by write-set disjointness; the repo's own pipeline is the suite — render∘policy must DERIVE as commuting, roundtrip∘egraph must be pinned NON-commuting (shared matrix.yaml write, the G14 wart made normative) | **done 2026-08-13** — grammar v0.6 (`then` contextual keyword; stage/resource/compose, 64/64); pair matrix 15/15 as declared (`just stages`); ES004 pins the matrix_yaml collision with XPASS-alarm; first COMPUTED guard (writes_disjoint from declarations) |
| G16 | governed vocabulary views: a deterministic renderer derives layout-as-data for cross-document views (projection map, stage commutation) from the SAME declarations the harnesses read; zero-diff data gate vs blessed goldens, SVG advisory (G4 three-tier reused); lie-detection witnessed mechanically (a perturbed declaration must change the view data); ZERO grammar growth | **done 2026-08-13** — `just views` 4/4 VIEW-OK, witnesses 2/2 (determinism + lie-detect); agreement 8/8, matrix 28/28; surfaced: Identity contract declared-but-unverified |
| G17 | the rename: OSIL everywhere living (repo, brand, extensions, strata tokens, tools), history frozen under docs/, full suite green under the new name, zero grammar growth | **done 2026-08-18** — ADR-0012; 38 files git-mv'd, 64 swept; first-run green |
| GX | Linux Foundation submission checklist satisfied | open, TERMINAL — license RATIFIED (Apache-2.0 + DCO); naming RESOLVED (OSIL, ADR-0012). No maintainer blockers remain; submission prep is the gate |

Dated gate reports with sequences, evidence, and honesty notes live in
`docs/reports/`; the decisions behind them in `docs/decisions/` (ADRs).
