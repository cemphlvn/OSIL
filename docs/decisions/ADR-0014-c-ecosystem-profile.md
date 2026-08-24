# ADR-0014: C as a lowering ecosystem profile
Date: 2026-08-24 · Status: accepted (G17)

## Context

Every performance claim this project has produced passed through a C compiler,
but C had no profile: no `PROFILE.md`, no pinned versions, no preservation
contract, no harness. The emission path existed only inside `optimizer/`, which
is declared PROBE status and is not gated. A projection nobody has contracted is
a projection nobody can audit.

## Decision

C becomes an ecosystem profile (`profiles/ecosystem/c/`) alongside onnx, egglog,
mlir and wasm. It is a **lowering** ecosystem like MLIR — projection preserves
**execution**, source stratum **OSIL-CIR** — with the distinctive contribution
that it is the substrate where OSIL's claims become *measurable*.

Four `preserves` fields, all mechanically verified by `tools/c_roundtrip.py`
(`just cproj`): `realization_identity`, `value_equivalence`, `guard_selectivity`,
`emission_determinism`. Score 4/4 at G17.

## The consequential part: `may_lose { declared_licence }`

The contract declares that the C projection **loses its own licence**, and this
is measured rather than assumed:

- `restrict` is the only alias declaration C offers and it is **inter-array**.
  Applied to every array pointer across all 151 TSVC loops it recovered **0**
  (`optimizer/repro/`).
- Clang's own diagnostic names the gap — *"Backward loop carried data
  dependence. Memory location is the same as accessed at ..."* — an
  **intra-array** fact for which C has no syntax (`optimizer/probe/none60/`).

So the emitted C carries its guards as a **comment**: provenance a human can
audit, not semantics a compiler can check. Any consumer that re-derives
guarantees from emitted C alone has re-entered the space of things a compiler
must prove for itself — which is exactly the space OSIL exists to sidestep.

This is the first `may_lose` entry in the repo backed by a negative experiment
rather than by inspection.

## Consequences

- `just test` gains a stage; corpus 023 gains a matching `stage cproj`
  declaration (standing agreement loop, 1:1). Pair matrix 28 -> 36, pins hold.
- `cproj` writes `conformance.matrix.matrix_yaml`, so it joins `roundtrip` and
  `egraph` in the non-commuting set. ES004 pins that wart for one pair; the
  same cause now has three writers. **Not** re-pinned per pair — the collision
  is one fact, and multiplying fixtures for it would be ceremony.
- `just test` now requires a C compiler. The harness SKIPS (does not fail) when
  `$CC` is absent, so a toolchain-less clone still passes the rest.

## Improve pass (same change)

The first harness had two weak checks, both found by witnessing rather than by
review:

1. `guard_selectivity` was merely "nothing leaked", which passes vacuously for a
   case with no lanes to withhold. Now a POSITIVE assertion: with the guard
   withheld the space must be **exactly `[chain]`**, and a case declaring
   `exact` must license exactly one realization.
2. The refusal fixture `RC001` passed for the WRONG REASON — an incidental
   `int()` crash, not a deliberate refusal. A fixture that passes because the
   projector crashed is a fabricated pass. Refusals now require a dedicated
   `Unsupported` exception; any other exception reports `WRONG-REASON` and
   fails the gate.

Both are witnessed: perturbing the projector to accept `gather`, and to license
lanes unconditionally, each drops the score to 3/4. See
`conformance/interop/c/README.md`.

## Deferred — open questions, NOT resolved by this ADR

- **OQ-1 (OSIL emits C).** Is C an emission target of convenience or a
  first-class backend with its own cost model and ABI commitments? This ADR
  contracts the projection without settling its status. Falsifiable form: *"the
  C projection needs no information the CIR does not already carry."*
- **OQ-2 (OSIL consumes C).** Can a frontend lift C loops into OSIL-SIR? Every
  SIR file in this repo is hand-written. Until this is answered OSIL cannot be
  pointed at an existing codebase. Falsifiable form: *"a mechanical lifter can
  recover the SIR of the 10 loops in `optimizer/probe/none60/` from their C
  source alone."* This is the load-bearing question for everything downstream.
  **PARTIALLY ANSWERED at G19 (2026-08-24): 10/10 on the probe set.** The
  recovery of dependence FACTS is mechanical (libclang; no annotation). Two
  limits stand: coverage is bounded by code style (TSVC 50% affine, kissfft
  0%), and choosing/justifying a transformation from those facts is NOT yet
  mechanical. See `conformance/lift/README.md`.
  **SECOND HALF ANSWERED at G20:** `tools/c_choose.py` turns the facts into a
  transformation (Allen-Kennedy SCC distribution) under three gates — legal,
  correct, faster. 3 accepted bit-identical, 1 rejected by the stopwatch, 4
  reported as needing other transformations, 2 refused. Building it exposed a
  real unsoundness: scalar-carried dependences were untracked, and distributing
  across one is silently wrong. See `conformance/lift/CHOOSER.md`.
  STILL OPEN: transformations beyond distribution (dead-store elimination,
  preloading, peeling, scalar expansion), and the coverage wall — pointer-based
  code does not lift at all.
- **OQ-3 (projector convergence).** `tools/c_roundtrip.py` and
  `optimizer/src/emit.rs` are now two implementations of one projection. Two
  emitters WILL drift. Which direction should they converge, and when?

These are recorded as candidate future gates, not as work in progress.
