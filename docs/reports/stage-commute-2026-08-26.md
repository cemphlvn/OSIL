# Stage commutation report — 2026-08-26
Metric: pair matrix 91/91 as declared + 1/1 pins hold -> PASS
The architecture under test is this repository's own pipeline (corpus 023/024).
Agreement: justfile `test:` == corpus stage decls, 14/14 1:1 (the observer is in its own model).

| composition | verdict | why |
|---|---|---|
| `ceiling then check` | COMMUTE | writes disjoint |
| `ceiling then choose` | COMMUTE | writes disjoint |
| `ceiling then cproj` | COMMUTE | writes disjoint |
| `ceiling then egraph` | COMMUTE | writes disjoint |
| `ceiling then harness` | COMMUTE | writes disjoint |
| `ceiling then lift` | COMMUTE | writes disjoint |
| `ceiling then policy` | COMMUTE | writes disjoint |
| `ceiling then render` | COMMUTE | writes disjoint |
| `ceiling then resolve` | COMMUTE | writes disjoint |
| `ceiling then roundtrip` | COMMUTE | writes disjoint |
| `ceiling then stages` | COMMUTE | writes disjoint |
| `ceiling then views` | COMMUTE | writes disjoint |
| `ceiling then witness` | COMMUTE | writes disjoint |
| `check then choose` | COMMUTE | writes disjoint |
| `check then cproj` | COMMUTE | writes disjoint |
| `check then egraph` | COMMUTE | writes disjoint |
| `check then harness` | COMMUTE | writes disjoint |
| `check then lift` | COMMUTE | writes disjoint |
| `check then policy` | COMMUTE | writes disjoint |
| `check then render` | COMMUTE | writes disjoint |
| `check then resolve` | COMMUTE | writes disjoint |
| `check then roundtrip` | COMMUTE | writes disjoint |
| `check then stages` | COMMUTE | writes disjoint |
| `check then views` | COMMUTE | writes disjoint |
| `check then witness` | COMMUTE | writes disjoint |
| `choose then cproj` | COMMUTE | writes disjoint |
| `choose then egraph` | COMMUTE | writes disjoint |
| `choose then harness` | COMMUTE | writes disjoint |
| `choose then lift` | COMMUTE | writes disjoint |
| `choose then policy` | COMMUTE | writes disjoint |
| `choose then render` | COMMUTE | writes disjoint |
| `choose then resolve` | COMMUTE | writes disjoint |
| `choose then roundtrip` | COMMUTE | writes disjoint |
| `choose then stages` | COMMUTE | writes disjoint |
| `choose then views` | COMMUTE | writes disjoint |
| `choose then witness` | COMMUTE | writes disjoint |
| `cproj then egraph` | WITHHELD | collision: conformance.matrix.matrix_yaml |
| `cproj then harness` | COMMUTE | writes disjoint |
| `cproj then lift` | COMMUTE | writes disjoint |
| `cproj then policy` | COMMUTE | writes disjoint |
| `cproj then render` | COMMUTE | writes disjoint |
| `cproj then resolve` | COMMUTE | writes disjoint |
| `cproj then roundtrip` | WITHHELD | collision: conformance.matrix.matrix_yaml |
| `cproj then stages` | COMMUTE | writes disjoint |
| `cproj then views` | COMMUTE | writes disjoint |
| `cproj then witness` | COMMUTE | writes disjoint |
| `egraph then harness` | COMMUTE | writes disjoint |
| `egraph then lift` | COMMUTE | writes disjoint |
| `egraph then policy` | COMMUTE | writes disjoint |
| `egraph then render` | COMMUTE | writes disjoint |
| `egraph then resolve` | COMMUTE | writes disjoint |
| `egraph then roundtrip` | WITHHELD | collision: conformance.matrix.matrix_yaml |
| `egraph then stages` | COMMUTE | writes disjoint |
| `egraph then views` | COMMUTE | writes disjoint |
| `egraph then witness` | COMMUTE | writes disjoint |
| `harness then lift` | COMMUTE | writes disjoint |
| `harness then policy` | COMMUTE | writes disjoint |
| `harness then render` | COMMUTE | writes disjoint |
| `harness then resolve` | COMMUTE | writes disjoint |
| `harness then roundtrip` | COMMUTE | writes disjoint |
| `harness then stages` | COMMUTE | writes disjoint |
| `harness then views` | COMMUTE | writes disjoint |
| `harness then witness` | COMMUTE | writes disjoint |
| `lift then policy` | COMMUTE | writes disjoint |
| `lift then render` | COMMUTE | writes disjoint |
| `lift then resolve` | COMMUTE | writes disjoint |
| `lift then roundtrip` | COMMUTE | writes disjoint |
| `lift then stages` | COMMUTE | writes disjoint |
| `lift then views` | COMMUTE | writes disjoint |
| `lift then witness` | COMMUTE | writes disjoint |
| `policy then render` | COMMUTE | writes disjoint |
| `policy then resolve` | COMMUTE | writes disjoint |
| `policy then roundtrip` | COMMUTE | writes disjoint |
| `policy then stages` | COMMUTE | writes disjoint |
| `policy then views` | COMMUTE | writes disjoint |
| `policy then witness` | COMMUTE | writes disjoint |
| `render then resolve` | COMMUTE | writes disjoint |
| `render then roundtrip` | COMMUTE | writes disjoint |
| `render then stages` | COMMUTE | writes disjoint |
| `render then views` | COMMUTE | writes disjoint |
| `render then witness` | COMMUTE | writes disjoint |
| `resolve then roundtrip` | COMMUTE | writes disjoint |
| `resolve then stages` | COMMUTE | writes disjoint |
| `resolve then views` | COMMUTE | writes disjoint |
| `resolve then witness` | COMMUTE | writes disjoint |
| `roundtrip then stages` | COMMUTE | writes disjoint |
| `roundtrip then views` | COMMUTE | writes disjoint |
| `roundtrip then witness` | COMMUTE | writes disjoint |
| `stages then views` | COMMUTE | writes disjoint |
| `stages then witness` | COMMUTE | writes disjoint |
| `views then witness` | COMMUTE | writes disjoint |

## pins
- ES004-matrix-write-collision-pin.osil: **XFAIL-HOLDS** — no commutation without disjoint writes

## honest notes
- Write-sets are DECLARED (self-class truth); mechanical extraction from tool source is future work (ADR-0010).
- Guard is write-write disjointness only; the Bernstein read-write refinement is recorded, not implemented — egraph READS matrix_yaml, so the refinement would also pin roundtrip-then-egraph ordering, not just the write collision.
- Undeclared identifiers in the GENERIC rule become pattern variables silently; pins reject undeclared stages loudly.
