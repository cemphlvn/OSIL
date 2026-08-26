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
| 3. FASTER | measured under TWO input regimes, worst reported, by a margin wider than run-to-run noise (5%) | **no** |

Gate 3 gained a fourth answer at G24 (ADR-0016): **UNDECIDED**. When the two
regimes disagree — and a `probe()` confirms they genuinely differ in the
quantity the family depends on — the rig declines to decide rather than picking
the flattering one. Every family declares what its profitability turns on
(`PROFILE_DEPENDENCE`); `if-convert` turns on branch probability, and the
fixture `p001` swings **1.16x to 12-15x** on that alone.

Gate 3 is not optional. `optimizer/probe/none60/` produced an exact
transformation that ran at **0.33x** — three times slower. Correct-but-slower is
a regression, and a chooser without a stopwatch would ship it.

And a stopwatch measuring the wrong thing is worse than none. Until G24 the
timing loop reset once per trial and then ran 200 repetitions over whatever the
previous repetition left behind: a converging kernel was timed on degenerate
data. Predication fixture `p004` was published at **ACCEPT 1.56x** and is in
fact a **5.9x regression** — the gate inverted the decision. See ADR-0016.

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

## Repo pins (2026-08-25)

Pointing this chooser at ten repositories this project did not author — 5,147
loops, from xiph/opus to milc_qcd and PolyBench — found four defects in it, plus
one in the differential harness that had been hiding the second. Every loop in `repo-pins/` is correct as written;
the pin is that the chooser leaves it alone.

| pin | defect |
|---|---|
| `step.c` | the recognisers ignored the loop STEP, while the lifter has always honoured it. On a 4x-unrolled copy, `dead-store` proposed deleting three of four live stores |
| `replay.c` | `dead-store` is an EMITTER promise: the removed store is replayed once, after the loop. It assumed the overwrite was one iteration away and skipped the dead statement's own reads at any offset. Both were false on `src/analysis.c:915`, and it emitted wrong code |
| `member.c` | arrays were named by the first identifier in the base, merging `p->x` with `p->y`. The lifter INVENTED a carried output dependence between disjoint struct members |
| `iteration.c` | a DESCENDING loop (`k--`) yields no step from the header parser, and the body was analysed anyway under the default ascending assumption — inverting every dependence direction. From `NPB3.0-omp-C MG/mg.c:343` |

The harness defect is the one that matters most: it indexed past its own
buffers, so the wrong code from `replay.c` was scored **EXACT** — the comparison
was over undefined behaviour. Buffers are now padded by the largest offset the
loop touches and the pad is compared. All ten none60 loops remain EXACT.

Full account: `repo-pins/README.md` and `docs/design/repo-scale-probe.md`.

## Witnesses

| perturbation | result |
|---|---|
| remove the scalar-dependence guard | `s261` distributes -> DECISION MISMATCH + COMPILE-FAIL -> FAIL |
| reverse the topological order | `s212`,`s211` emit **INCORRECT** code, caught by the differential test -> FAIL |

The second is the one that matters: it demonstrates the correctness gate
actually catches a semantically wrong distribution, rather than being assumed to.
