# ADR-0009: egglog is the equivalence projection's execution target

Date: 2026-08-12 · Status: ACCEPTED (direction delegated to U5 evidence by the
G14 gate definition itself — README row: "U5 decides egg-vs-egglog"; maintainer
veto remains open under the ADR-0006/D1–D3 delegated-judgment precedent).

## Context
`spec/interop/egraph.md` (draft-0) left the engine open: egg or egglog as the
target for the EGraph projection (OAAS-SIR -> e-graph -> saturation ->
extraction -> OAAS-SIR, preserve equivalence). G14 requires a TESTED
preservation contract, wired into `just test` with zero manual setup, in a
Python-via-`uv` toolchain. Research U5 (docs/research/U5-egg-vs-egglog.md,
2026-08-12) investigated five independent lines: liveness, Python bindings,
guard mapping, round-trip fidelity, pin stability.

## Decision
**egglog**, bound through `egglog` (PyPI) `== 13.2.0`, invoked as
`uv run --with 'egglog==13.2.0' python3 tools/egraph_roundtrip.py` — the same
idiom as `just roundtrip`. egg is retained as citation/foreign-witness
reference only (POPL 2021, the foundational algorithm), never executed.

Two findings force the choice independently of liveness (U5 §2–§3):
1. **No maintained Python binding for egg exists** — snake-egg's last release
   (2023-01-09) predates every currently-supported CPython; no other binding
   exists. "Zero manual setup in `just test`" is unsatisfiable via egg.
2. **Guards are data in egglog, code in egg** — OAAS `guards { k = v }`
   blocks map mechanically onto egglog fact-guards (nullary relation +
   `:when`/extra-fact argument); egg's conditions are compiled Rust closures,
   demanding a codegen adapter that contradicts egraph.md's "translates to
   native rewrite rules" framing.

U5 verified the mapping END-TO-END on this machine: fixture 003 built,
guard-gated, saturated, checked, extracted via egglog-python — the repo's own
mechanical-evidence bar (spec/conformance.md §1), met before this ADR was
written.

## Consequences
1. `profiles/ecosystem/egg/VERSIONS` pins `egglog pypi = 13.2.0` plus the
   vendored core git rev `2e5657b`. The PyPI and crates.io version schemes are
   provably decoupled (13.2.0 vs 2.0.0) — drift-watch must never cross-check
   them against each other (U5 §5).
2. The G14 harness (`tools/egraph_roundtrip.py`) targets the egglog-python
   API; guard blocks become nullary relations asserted once per lane.
3. The saturation/extraction cost model is declarative (`:cost`/default ast
   size), keeping the adapter data-only end to end.

## Alternatives rejected
- **egg as target**: fails on both forcing findings above; its slower SemVer
  churn (a real advantage, U5 §5) cannot be banked without a binding to run.
- **Both engines, dual contract**: doubles harness surface for no added
  preserved dimension; egg's lane would immediately be the untestable one.
- **In-repo PyO3 binding for egg**: OAAS re-implementing an upstream
  ecosystem's binding layer violates the sovereignty principle
  (ecosystem-contract.md §1) and takes on foreign maintenance burden.

## Honesty
- "egg is in maintenance mode" is U5's flagged INFERENCE (commit-cadence delta
  + egg's own README pointing at egglog), not a maintainer quote; the decision
  does not rest on it.
- **OPEN (ratification-worthy, deliberately not resolved here):** the profile
  directory is `profiles/ecosystem/egg/` while the execution target is egglog.
  Univocity argues for a rename (`egg` names a library we never execute); the
  org umbrella (`egraphs-good`) argues the current name is a tolerable alias.
  Either resolution is a small, reversible `git mv` + reference sweep — held
  for maintainer call, tracked in PROFILE.md.
- egglog's crate-side major-version churn (already 2.0.0) is the accepted
  cost; the PyPI pin's vendored-rev decoupling mitigates but does not erase it
  (re-verify the guard/extraction syntax at every pin bump — U5 Validity).
