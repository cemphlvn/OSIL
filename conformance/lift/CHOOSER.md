# The transformation chooser (G20 / OQ-2, second half)

The lifter answers *"is this dependence false?"*. This answers *"so what?"*.

## Algorithm — Allen & Kennedy loop distribution

Build the statement-level dependence graph, find strongly-connected components,
emit one loop per SCC in topological order.

- statements in the **same SCC** form a recurrence and must stay together;
- **distinct SCCs** may be split — and splitting is what lets a vectorizable
  statement escape a loop pinned by a neighbouring recurrence;
- **one SCC** means indivisible. Reported, never forced.

## Three gates, in order

| gate | check | deterministic? |
|---|---|---|
| 1. LEGAL | a topological order exists | yes |
| 2. CORRECT | differential test against the original, same inputs | yes |
| 3. FASTER | measured, by a margin wider than run-to-run noise (5%) | **no** |

Gate 3 is not optional. `optimizer/probe/none60/` produced an exact
transformation that ran at **0.33x** — three times slower. Correct-but-slower is
a regression, and a chooser without a stopwatch would ship it.

## Results on the probe set

| loop | decision | correctness | outcome |
|---|---|---|---|
| s212 | distribute | EXACT | ACCEPT ~2.2-2.8x |
| s211 | distribute | EXACT | ACCEPT ~1.9-2.5x |
| s1213 | distribute | EXACT | ACCEPT ~1.7-2.2x |
| s221 | distribute | EXACT | ~1.0x contended / **1.27x quiet** — see RETRACTION below |
| s261 | none | — | scalar `t` welds the statements together |
| s244 | none | — | needs dead-store elimination |
| s241 | none | — | needs preloading |
| s116 | none | — | needs anti-dependence collapse |
| s291, s292 | refuse | — | non-affine `b[im1]` |

On `s1213` the chooser found a distribution measuring **better than the one
written by hand**.

**RETRACTION (2026-08-24).** This document previously cited `s221` as the
flagship case of the stopwatch correctly rejecting a legal-but-unprofitable
transformation. Re-measured on a quiet machine it is **1.27x and ACCEPTED** —
the earlier ~1.0x was background load from concurrently running subagents, not
a property of the transformation. The example is withdrawn; `s116` at 0.33x
remains valid evidence for gate 3, being far too large an effect for contention
to explain. See `docs/design/measurement-contention.md`.

## The unsoundness this work found

The first chooser tracked **array** dependences only. On `s261`:

```c
t = a[i] + b[i];   a[i] = t + c[i-1];   t = c[i]*d[i];   c[i] = t;
```

the scalar `t` links statements S0→S1 and S2→S3 — and the lifter did not see it.
The chooser happily proposed splitting S0 from S1, which is **silently wrong**: a
scalar is one memory cell reused every iteration, so after the first loop
finishes the reader sees the LAST iteration's value, not its own.

Only an undeclared-variable compile error stopped a wrong transformation from
being accepted. Had the scalar been in scope, it would have compiled and run.

Fixed in two places: the lifter now tracks scalar reads/writes as dependences,
and the chooser makes scalar edges **bidirectional** so the statements are
forced into one SCC and never separated. Doing it legally requires scalar
expansion, which is not implemented — so the chooser refuses rather than
approximates.

## What is gated, and what is not

**Gated** (deterministic): the decision per loop, and that no accepted candidate
is ever INCORRECT. That is the safety property.

**Not gated** (machine-dependent): the measured speedup, and therefore
ACCEPT vs REJECT. Those move with machine load and thermal state; gating them
would make `just test` flaky, and a flaky gate is worse than an honest report.
The stopwatch still runs on every `tools/c_choose.py` invocation.

## Witnesses

| perturbation | result |
|---|---|
| remove the scalar-dependence guard | `s261` distributes -> DECISION MISMATCH + COMPILE-FAIL -> FAIL |
| reverse the topological order | `s212`,`s211` emit **INCORRECT** code, caught by the differential test -> FAIL |

The second is the one that matters: it demonstrates the correctness gate
actually catches a semantically wrong distribution, rather than being assumed to.
