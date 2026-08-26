# ADR-0015: predicated execution, and the retirement of `body.control_flow`
Date: 2026-08-25 · Status: accepted (G23)

## Context

The repo-scale probe (`docs/design/repo-scale-probe.md`) priced the declared
capabilities on a held-out corpus of 5,147 loops from ten repositories. The
result was unambiguous and different from every price derived on TSVC:

```
+599   body.control_flow    -> 51.9%   (blocks 2108 loops in total)
+415   subscript.indirect   -> 48.3%   (blocks 1695 loops)
+98    access.multi_dimensional -> 42.2% (blocks 1419 loops)
```

Control flow in the loop body is the single largest declared refusal on real
code, and nothing in the repo could express it. That is the definition of a
capability worth building, arrived at by measurement rather than by taste.

The same probe also found that this project's four transformation families
match **zero** loops in those ten repositories. The binding constraint was never
what the analyser could see; it was what the catalogue could do. `if`-conversion
is the first entry added to the catalogue on evidence.

## Decision

### 1. The analyser admits one species of control flow

`if (P) lhs = rhs;` — a **guarded assignment** — is NORMALISED rather than
refused: the predicate is lifted onto the statement, and the loop body becomes
straight-line again, so every downstream analysis applies unchanged. This is the
same move `subscript.wraparound` got at G22 (normalisation, not new analysis)
and it is deliberate: predication is a *front-end* concern, and making it one
keeps the dependence machinery untouched.

The chooser gains a fifth family, `if-convert`, emitting the select form:

```c
if (P) a[i] = b[i];        ->     a[i] = (P) ? (b[i]) : (a[i]);
```

The false arm is the lvalue itself. That is what makes the store unconditional
without changing the value, and it is why the lifter records a **read** of the
store location for a guarded statement — the converted form genuinely reads it.

### 2. `body.control_flow` is retired, replaced by its species

A genus-level refusal stops being univocal the moment the analyser admits one of
its species. Per the ontology rules this repo works under (one term, one
meaning), `body.control_flow` is replaced in `conformance/corpus/026` by:

| feature | status | meaning |
|---|---|---|
| `body.guarded_assignment` | **admitted** | `if (P) lhs = rhs;`, P side-effect-free, guarded work non-trapping |
| `body.early_exit` | refused | `break`, `continue`, `return`, `goto`, a label, `switch` |
| `body.nested_loop` | refused | a loop inside the body |
| `body.nested_guard` | refused | a conditional inside a conditional |
| `body.unsafe_speculation` | refused | the guarded work cannot be run unconditionally |
| `body.guarded_nonassignment` | refused | the guarded branch is not one assignment to an array element |
| `body.guarded_alternative` | refused | `if/else` |

`body.guarded_alternative` is genuinely convertible — `lhs = P ? a : b` when
both arms assign the same lvalue — and is deliberately **declared and priced
rather than built**. Naming a gap you could close is the mechanism this project
uses to keep its own reach honest; silently including it would have inflated
the capability.

### 3. What makes speculation unsafe, stated

If-conversion runs the guarded work on iterations the original skipped. Four
conditions, each refused separately so each is priced separately:

1. **Effectful predicate** — a call, assignment or increment in `P` would run on
   iterations the original never evaluated it on.
2. **Index-dependent predicate** — `if (i < m)` bounds the *iteration space*;
   converting it speculates loads outside the range the guard was protecting.
   That is index-set splitting's job, not predication's.
3. **Trapping guarded expression** — `if (c[i] != 0) a[i] = b[i]/c[i];` converts
   to a division by zero on exactly the iterations the guard existed to prevent.
   Division and modulo are refused outright.
4. **Call in the guarded expression** — side effects and faults, same as (1).

### 4. The speculation this DOES accept, stated plainly

Conversion makes the store — and every load in the guarded expression —
unconditional across the loop's iteration space. That requires those locations
to be dereferenceable on every iteration, which this analyser cannot prove.

It is accepted, on the grounds that it is **not a new assumption**: the
`preload` family already copies `arr[lower .. upper + max_offset)` wholesale,
and the emitter already declares every array parameter `restrict`. Predication
speculates over exactly the range the existing machinery already touches. The
assumption is recorded here rather than buried, and it is the first thing to
revisit if a preservation failure is ever traced to this family.

### 5. Predication composes with nothing, for now

A guarded loop is offered `if-convert` and nothing else. The other four
emitters rewrite statement text in ways a predicate would have to be threaded
through (`preload` substitutes subscripts inside statements; `peel` substitutes
scalars), and a family that dropped a guard would emit an unconditional store —
correct-looking code that runs the guarded work every iteration.

Composing them is a **stage** question (G15) and belongs there. Refuse, do not
approximate.

## Consequences

- `conformance/lift/predication/cases.c` — four loops that must convert, six
  that must be refused, one refusal species each. Gated by `just choose`.
- Every accepted conversion must be **bit-exact**; the correctness gate checks
  equivalence, not just "no crash". The speedup is reported and never gated, as
  with every other family.
- Measured on the fixture set: 1.28x, 3.72x, 1.60x accepted bit-identical, and
  `p002` REJECTED at 1.05x — clang already handles the guarded-accumulate shape,
  and the stopwatch says so.
- Two wrong-code classes were found while building this, both by pointing the
  new capability at real repositories, and both are refused rather than
  detected: **pointer-validity guards** (`if (da) da[i] += x;` — the select
  subscripts `da` on both arms, a null dereference; darknet `src/blas.c:61`) and
  **trapping guarded expressions**. The correctness gate CANNOT catch the first:
  the differential harness only ever passes valid, non-null arrays, so the input
  that would expose it is not in the test distribution. Refusal is therefore an
  analysis obligation, not a stopwatch one.
- `EXPECT_RECOVERABLE` in `tools/ceiling_check.py` is unchanged: none60 contains
  no guarded assignment, so admitting the species is inert there. The corpus
  that motivated the capability is the one that measures it.

## What this predicts, and how it was checked

The price said **+599 loops** for admitting `body.control_flow`. That number is
for the GENUS. This ADR builds one SPECIES, so the realized gain must be lower,
and the gap between them is the finding rather than an error: **capability
prices are quoted for a genus and capabilities get built for a species.**

**Measured: +14, against a priced +599 — an overstatement of 43x.** 47 loops in
the ten-repository corpus contain a guarded assignment the lifter normalises;
14 of them were blocked by nothing else and become analysable. The rest of the
genus turned out to be mostly `body.nested_loop` (+2,888) — loop nests, not
conditionals at all.

The arithmetic was never wrong. `+599` correctly answers "how many loops become
analysable if ALL control flow is admitted". It is the wrong answer to "how many
does building a capability deliver", because nobody builds a genus. The rule
this establishes: **prices must be quoted for the species that will actually be
implemented.** A genus-level price is an upper bound on the genus, and here the
buildable species is two orders of magnitude smaller.

This is the first *prospective* test of the pricing instrument in this repo —
every earlier price was computed retrospectively, against a corpus already
understood. The instrument's arithmetic survived; its interpretation did not.
Full record: `docs/design/repo-scale-probe.md`.
