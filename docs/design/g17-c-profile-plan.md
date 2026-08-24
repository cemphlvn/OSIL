# G17 plan — the C ecosystem profile

Status: **plan**, written before building (2026-08-24). G17 was reserved-open by
the maintainer on 2026-08-18 when the rename was renumbered to G18.

## The claim someone can falsify

> OSIL's projection to C has a mechanically tested preservation contract: every
> licensed realization emits C that compiles and computes the declared values,
> a withheld guard removes the realization it licensed, emission is
> byte-deterministic — and the contract **honestly declares what C cannot
> carry**.

The last clause is what distinguishes this from a formality. It is grounded in
measurement, not asserted: see `optimizer/repro/`, where `restrict` on every
array pointer across all 151 TSVC loops recovered **0**, and
`optimizer/probe/none60/`, where clang's own diagnostic names the reason
("Backward loop carried data dependence... same memory location"). C has no
syntax for intra-array dependence facts. A projection to C therefore *loses the
licence* — and the contract must say so.

## Where C sits among the ecosystems

| Ecosystem | Contributes | Projection preserves | Source stratum |
|---|---|---|---|
| ONNX | executable graph interchange | computation | OSIL-CIR |
| egglog | equivalence-space search | equivalence | OSIL-SIR |
| MLIR | lowering toward hardware | execution | OSIL-CIR |
| **C** | **portable lowering + measurement** | **execution** | **OSIL-CIR** |

C is a *lowering* ecosystem like MLIR, not an interchange format. Its distinctive
contribution is that it is the substrate where OSIL's claims become **measurable**
— every performance number this project has produced went through a C compiler.

## Preservation contract

`preserves` — each field must be mechanically verified for the gate to close:

| field | verified how |
|---|---|
| `realization_identity` | every realization the guards license emits C that compiles |
| `value_equivalence` | emitted C computes the declared reduction (differential vs an independent reference) |
| `guard_selectivity` | with the guard withheld, the realization it licensed is ABSENT (negative lane, the G14 pattern) |
| `emission_determinism` | same declaration -> byte-identical C across runs |

`may_lose` — declared sacrificial, each with evidence:

| field | why |
|---|---|
| `declared_licence` | **measured**: C cannot express the guards. `restrict` is inter-array only; 0/151 recovered. The emitted C carries the licence as a *comment*, which is provenance, not semantics. |
| `visual_layout` | C has no layout dimension |
| `ontology_annotations` | no carrier in C |

## Build order

1. `profiles/ecosystem/c/{PROFILE.md,VERSIONS,profile.osil,CONTRACT.osil}`
2. `registry/entries/c.yaml` (triad link, per G8)
3. `conformance/corpus/025-profile-ecosystem-c.osil` (triple representation)
4. `conformance/interop/c/` — the case suite
5. `tools/c_roundtrip.py` — the harness
6. `justfile` recipe + `test:` line
7. `conformance/corpus/023` stage declaration — **standing agreement loop**: the
   justfile `test:` line and 023's stage decls must stay 1:1 or `just stages` fails
8. `docs/GATES.md` row, ADR-0014

## Decision: the harness is Python, not the Rust optimizer

`tools/c_roundtrip.py` implements its own small projector rather than shelling
out to `optimizer/`. Rationale: (a) every other harness is Python in `tools/`;
(b) the gate tests the CONTRACT, not the optimizer's performance research;
(c) `just test` must not require a Rust toolchain. `optimizer/` stays PROBE.

**Cost, recorded honestly:** this creates TWO implementations of the same
projection — `tools/c_roundtrip.py` and `optimizer/src/emit.rs`. That is a
fission risk. Recorded as OQ-3 below rather than silently accepted.

## Open questions — deferred, NOT resolved here

- **OQ-1 (OSIL emits C).** Is C an emission target of convenience, or a
  first-class backend with its own cost model and ABI commitments? This gate
  formalizes the *contract* without settling the *status*. Falsifiable form:
  "the C projection needs no information the CIR does not already carry."
- **OQ-2 (OSIL consumes C).** Can a frontend lift C loops into OSIL-SIR? This is
  the load-bearing question for ever applying OSIL to existing code — every SIR
  file in this repo is hand-written. Falsifiable form: "a mechanical lifter can
  recover the SIR of the 10 loops in `optimizer/probe/none60/` from their C
  source alone." Until answered, OSIL cannot be pointed at a real repository.
- **OQ-3 (projector convergence).** Should `tools/c_roundtrip.py` and
  `optimizer/src/emit.rs` converge to one implementation, and in which
  direction? Two emitters WILL drift.
