# ADR-0016: gate 3 measures a profile, and says which one
Date: 2026-08-26 · Status: accepted (G24)

## Context

This project has a rigorous theory of correctness and, until now, a naive theory
of performance. Gates 1 and 2 have refusal species, negative fixtures,
perturbation witnesses, lie-detectors and a held-out corpus. Gate 3 was a
stopwatch on fabricated data.

Two defects were found by asking whether a rig number transfers to a repository.

### Defect 1 — the timing loop destroyed its own input distribution

The harness called `reset()` once per trial and then ran **200 repetitions over
whatever the previous repetition left behind**. For a kernel that converges —
`min_curve`'s `if (c2[i] < c[i]) c[i] = c2[i];` reaches a fixed point after one
pass — repetitions 2..200 timed degenerate data. For an accumulating kernel,
200 repetitions drive values to infinity, and the rig times denormals.

Measured consequence: the rig reported **the same 2.2x whether the guard held 5%
or 50% of the time**. It was structurally blind to the single quantity that
decides if-conversion.

### Defect 2 — a verdict with no stated conditions

`ACCEPT` was returned unconditionally for a question whose answer depends on the
caller's data. On fixture `p004`:

```c
for (i...) { b[i] = b[i]*1.5f; if (c[i] > 0.0f) a[i] = b[i]; }
```

the old harness reported **ACCEPT at 1.56x**. Under fresh inputs it is a **5.9x
REGRESSION** (0.17x at p=0.5), confirmed independently outside the rig. Gate 3
did not merely mis-estimate the magnitude; it **inverted the decision**.

## Decision

### 1. Fresh input per measurement, reset outside the timed region

Each timing is a single call on freshly restored data, minimum over 151 trials,
with the `reset` *excluded* from the timed region. Repetition-based timing over
mutating data is not recoverable by averaging — the later repetitions are
measuring a different problem.

### 2. Two input regimes, and a verdict that names the one it holds under

Every candidate is measured under two seedings: strictly positive values, and
sign-randomised values of the same magnitude (so nothing drifts into denormals).
The reported `speedup` is the **worst** of the two.

| regimes agree faster | `ACCEPT` |
|---|---|
| regimes agree not-faster | `REJECT-not-faster` |
| regimes disagree, and the probe shows they differ | `UNDECIDED-profile` |
| regimes disagree, but the probe shows them inert | `UNSTABLE-margin` |

`UNDECIDED` is the point of the change. The decision genuinely depends on a
quantity this rig cannot know for the caller's workload, and choosing the
flattering regime would be a lie. It is the stopwatch's version of *refuse,
never approximate*.

### 3. Every family declares what its profitability depends on

`PROFILE_DEPENDENCE` in `tools/c_choose.py`:

| family | depends on |
|---|---|
| `if-convert` | branch probability, trip count |
| `preload` | working set, trip count |
| `distribute` | trip count, register pressure |
| `dead-store`, `peel-wraparound` | trip count |

The capability model exists because the **analyser** has blind spots that must be
declared and priced. This is the same move for the **stopwatch**.

### 4. The rig measures the quantity it decided under

For `if-convert`, the emitted candidate now carries a `probe()` function counting
how often each guard holds on the harness's own data, so the verdict is reported
alongside the branch probability that produced it. Declaring a dependence is
only half the job; the rig has to be able to state the value.

Distinguishing *inert regimes* from *real dependence* matters: the first regime
pair scaled alternate arrays, which cannot move a `c[i] > 0.0f` guard on strictly
positive data. The probe reported `p=1.000` in both regimes, and a disagreement
there is the margin, not the data. Attributing it to profile dependence would
have been inventing a cause.

### 5. Profitability is reported in the pin vocabulary, and stays ADVISORY

`PASS` / `FAIL` / `XFAIL-HOLDS` / `XPASS-ALARM` / `UNDECIDED`, per fixture,
against a declared expectation. Advisory, because a speedup is machine-dependent
and gating one makes `just test` flaky — but a documented claim that quietly
stops holding is exactly what a pin is for.

`XPASS-ALARM` is the load-bearing one: a transformation declared unprofitable
that measures faster must be investigated, not blessed.

## Consequences

- **The headline result survives a strictly better measurement.** All ten
  none60 loops keep their decisions, and the accepted ones remain faster on
  worst-of-two-regimes numbers: s212 1.86x, s211 1.62-1.75x, s1213 1.57-1.83x,
  s241 1.30-1.44x, s244 2.17x, s291/s292 4.00x. Both rejections still reject
  (s221 0.97x, s116 0.40x). Reported speedups are now **conservative** where
  they were previously optimistic.
- Two predication fixtures are reclassified. `p001` swings **1.16x → 12-15x**
  purely on branch predictability; `p004` is a regression that was being
  published as a 1.56x win.
- Measurement is noisier per invocation, which is the honest cost of measuring
  a real quantity instead of a converged one. Profitability stays advisory for
  exactly this reason.

## What is NOT closed

The rig still measures an **extracted shape**, and a shape's speedup does not
transfer to a repository without its trip count, element types, and a profile.
Three partitions remain, in dependency order, each with a falsifiable gate:

- **C — preserve static facts through extraction.** The lifter is type-blind and
  the emitter types every array `float`; most of opus is Q14 `int32`. *Gate:* for
  a loop with a compile-time-constant bound, the emitted `orig` and the loop in
  its own file produce the same vectorization decision under
  `-Rpass=loop-vectorize`.
- **D — hotness.** *Gate:* build one repository, sample its own test suite, and
  show the candidate list shrinks to loops that actually execute. `min_curve`,
  called once per stream, must drop out.
- **E — in-situ transfer.** *Gate:* one patched loop, built in the real
  repository, measured on the repository's own benchmark, agreeing with the rig
  within a stated tolerance.

**Until E passes once, no number this rig produces licenses an upstream patch** —
and that is now written down rather than assumed.
