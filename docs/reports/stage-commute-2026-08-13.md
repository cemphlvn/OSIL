# Stage commutation report — 2026-08-13
Metric: pair matrix 15/15 as declared + 1/1 pins hold -> PASS
The architecture under test is this repository's own pipeline (corpus 023/024).

| composition | verdict | why |
|---|---|---|
| `check then egraph` | COMMUTE | writes disjoint |
| `check then policy` | COMMUTE | writes disjoint |
| `check then render` | COMMUTE | writes disjoint |
| `check then resolve` | COMMUTE | writes disjoint |
| `check then roundtrip` | COMMUTE | writes disjoint |
| `egraph then policy` | COMMUTE | writes disjoint |
| `egraph then render` | COMMUTE | writes disjoint |
| `egraph then resolve` | COMMUTE | writes disjoint |
| `egraph then roundtrip` | WITHHELD | collision: conformance.matrix.matrix_yaml |
| `policy then render` | COMMUTE | writes disjoint |
| `policy then resolve` | COMMUTE | writes disjoint |
| `policy then roundtrip` | COMMUTE | writes disjoint |
| `render then resolve` | COMMUTE | writes disjoint |
| `render then roundtrip` | COMMUTE | writes disjoint |
| `resolve then roundtrip` | COMMUTE | writes disjoint |

## pins
- ES004-matrix-write-collision-pin.oaas: **XFAIL-HOLDS** — no commutation without disjoint writes

## honest notes
- Write-sets are DECLARED (self-class truth); mechanical extraction from tool source is future work (ADR-0010).
- Guard is write-write disjointness only; the Bernstein read-write refinement is recorded, not implemented — egraph READS matrix_yaml, so the refinement would also pin roundtrip-then-egraph ordering, not just the write collision.
- Undeclared identifiers in the GENERIC rule become pattern variables silently; pins reject undeclared stages loudly.
