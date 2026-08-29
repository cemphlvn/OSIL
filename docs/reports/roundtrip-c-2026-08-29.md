# C projection round-trip — 2026-08-29

Status: **pass** — preservation score 4/4
Cases: c001, c002, c003

| field | result |
|---|---|
| `realization_identity` | PASS |
| `value_equivalence` | PASS |
| `guard_selectivity` | PASS |
| `emission_determinism` | PASS |

| case | realization | result | note |
|---|---|---|---|
| c001 | `chain` | ok | 16 |
| c001 | `lanes-w4i1` | ok | 16 |
| c001 | `lanes-w4i2` | ok | 16 |
| c001 | `lanes-w4i4` | ok | 16 |
| c001 | `lanes-w4i8` | ok | 16 |
| c001 | `guard-withheld` | ok | space 5 -> exactly [chain] |
| c001 | `determinism` | ok | 1801 bytes |
| c002 | `chain` | ok | 6144 |
| c002 | `lanes-w4i1` | ok | 6144 |
| c002 | `lanes-w4i2` | ok | 6144 |
| c002 | `lanes-w4i4` | ok | 6144 |
| c002 | `lanes-w4i8` | ok | 6144 |
| c002 | `guard-withheld` | ok | space 5 -> exactly [chain] |
| c002 | `determinism` | ok | 1801 bytes |
| c003 | `chain` | ok | 16 |
| c003 | `guard-withheld` | ok | space 1 -> exactly [chain] |
| c003 | `determinism` | ok | 432 bytes |
| c001 | `may_lose` | XFAIL-HOLDS | licence is comment-only, as declared |
| c002 | `may_lose` | XFAIL-HOLDS | licence is comment-only, as declared |
| c003 | `may_lose` | XFAIL-HOLDS | licence is comment-only, as declared |
| rc001 | `REFUSED` | XFAIL-HOLDS | unsupported source form: gather |
| rc002 | `REFUSED` | XFAIL-HOLDS | unsupported reduction operator: maxof (no declared i |

## Declared losses (not failures)

`may_lose { declared_licence }` — C has no syntax for the guards.
The emitted C carries its licence as a comment: provenance, not
semantics. Evidence: `restrict` on every array pointer across all
151 TSVC loops recovered 0 (`optimizer/repro/`).
