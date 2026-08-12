# ADR-0010: stage composition — the toolchain becomes vocabulary

Date: 2026-08-13 · Status: ACCEPTED (G15 staged by maintainer instruction
2026-08-12 "Put G15 before GX", started by "Kesin — start G15"; the gate row
itself authorizes ONE new construct, triple representation due).

## Context
G15: the repo's own pipeline becomes the test object. Needs (a) stages as
declared vocabulary carrying their resource footprint, (b) a composition
form equivalences can range over, (c) commutation guarded by write-set
disjointness — with `render∘policy` deriving and `roundtrip∘egraph` pinned
non-commuting (the G14 matrix.yaml wart made normative).

## Decision
1. **Composition keyword, not operator: `then`.** `render then policy`.
   Keywords are CONTEXTUAL in this grammar, so no tokenizer change. `.` was
   rejected: it already means namespace path — overloading it would make `.`
   equivocal, the exact violation ADR-0008 closed for `:`/`=`.
2. **The construct is `stage` + `compose_expr`** (with `resource_block`),
   read as ONE construct: a stage-composition term language. Grammar grows
   61 -> 64 productions; the boundary obligation ships TWO rejection
   fixtures (R007 stage-in-flow — document-kind boundary, ADR-0005 family;
   R008 compose mixed with arithmetic — sort boundary).
3. **Corpus 024 declares commutation GENERICALLY**: `a then b <=> b then a`
   under `guards { writes_disjoint = true }`. Universals live in vocabulary;
   instances (which pairs actually commute) are DERIVED by machinery.
   Operand disambiguation: an identifier naming a declared stage is a ground
   stage constant; any other identifier is a pattern variable.
4. **`writes_disjoint` is the first COMPUTED guard.** G14 guards are
   hand-asserted nullary facts; here the harness computes the binary
   relation `writes_disjoint(a, b)` from declared write-sets and asserts it
   for disjoint pairs only (both orders — symmetry is asserted, not
   assumed). The declared guard key has ONE meaning (core.md): the composed
   stages' declared write-sets do not intersect.
5. **Write-sets are file-granular resource ids** (dotted, underscored:
   `conformance.matrix.matrix_yaml`). Directory granularity was rejected: it
   over-approximates (both round-trip harnesses write distinct files under
   docs/reports — dir-level would false-pin that as a collision; the REAL
   collision is the single file matrix.yaml).
6. **Suite separation by directive**: `conformance/equivalence/` fixtures
   gain an optional `// SUITE: stages` header; the G14 arithmetic adapter
   suite skips foreign suites LOUDLY (printed SKIP), never silently.

## Consequences
- `tools/stage_commute.py` (`just stages`, wired into `just test`): checks
  the FULL pairwise matrix — every disjoint pair must derive commuting,
  every colliding pair must be withheld; ES004 pins roundtrip/egglog-
  roundtrip non-commutation with XPASS-alarm semantics (fixing the matrix
  wart later must trip the alarm and demand ratification, not silently
  flip).
- The G14 corpus reader skips compose-shaped equivalences (loudly) — sorts
  are disjoint: Num-arithmetic vs Stage-composition.
- Declared write-sets are VOCABULARY (self class): fidelity to the tools'
  actual writes is declared, not yet mechanically extracted from code.

## Alternatives rejected
- `.` as composition operator: equivocality (see Decision 1).
- Instance-form corpus equivalences per pair: particulars in vocabulary,
  and each new stage would demand O(n) new fixtures.
- Full Bernstein conditions (read-write independence) as the guard NOW:
  recorded as the refinement — `roundtrip∘egraph` also collides read-vs-
  write (egraph READS matrix.yaml to preserve foreign cells), but the
  write-write collision already forces the pin; the weaker guard is honest
  for v0 and the refinement is a future, separately-ratifiable tightening.

## Honesty
- Declared-vs-actual write-set drift is possible (a tool gaining a write
  the declaration misses). Mechanical extraction from tool source is future
  work; until then the stage declarations carry the same trust class as any
  self-owned vocabulary.
- A stage named `then` would collide with the contextual keyword; the
  grammar's existing contextual-keyword note covers this, and R008's family
  documents the sort boundary.
