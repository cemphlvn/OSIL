# Machine contention changed both the numbers and the DECISIONS

Prompted by Hal Finkel's LLVM-dev post of 2011-10-29 benchmarking a
BasicBlock autovectorization pass on Maleki's TSVC, which caveats:

> *"these are preliminary results because I did not do the things necessary to
> make them real (explicitly quiet the machine, bind the processes to one cpu,
> etc.)"*

In 2011, on this exact benchmark, that discipline was stated. This project did
not state it, and — worse — ran its timing measurements **while three research
subagents were executing in the background.**

## Same code, same machine, same day. Only the load differs.

| kernel | contended (reported) | quiet | ratio |
|---|---|---|---|
| s244 dead-store | 1.09x | **4.14x** | 3.8x |
| s241 preload | 1.39x | 2.84x | 2.0x |
| s212 preload | 1.59x | 2.44x | 1.5x |
| s1244 preload | 1.26x | 2.28x | 1.8x |
| s1213 distribute | 1.71x | 2.74x | 1.6x |
| s211 distribute | 1.66x | 1.99x | 1.2x |
| s291 peel-wraparound | 3.87x | 4.48x | 1.2x |
| s292 peel-wraparound | 4.23x | 4.03x | 0.95x |
| **recovered** | **8** | **10** | |
| **rate** | **72/151 = 47.7%** | **74/151 = 49.0%** | |

Two kernels (`s221`, `s222`) crossed the accept threshold on a quiet machine
that were REJECTED on a contended one.

## The `NOISE_MARGIN = 1.05` is not fit for purpose

It was justified by run-to-run spread measured at 0.5%-2.4% **within a single
session under constant load**. The spread caused by *changing* load is up to
**280%**. A 5% margin is roughly two orders of magnitude too small for the
variance that actually exists.

## RETRACTION

`s221` was used repeatedly in this project's own write-ups as the flagship
example of the measurement gate working — "legal, correct, and correctly
REJECTED at ~1.00x by the stopwatch," cited in `conformance/lift/CHOOSER.md`
and in the G20 gate row as evidence the third gate earns its place.

On a quiet machine `s221` measures **1.27x and is ACCEPTED.**

The gate was not discriminating a marginal transformation from a good one. It
was responding to background load. **That example is withdrawn.** The gate may
still be right in principle — a correct-but-slower transformation must be
rejected, and `s116` at 0.33x is a much larger effect that no plausible
contention explains — but `s221` is not evidence for it.

## What this does NOT invalidate

Correctness is unaffected: every accepted transformation was bit-identical or
within 1e-6, and that verdict does not depend on machine load. The lifter, the
chooser's decisions, the capability model and the ceiling arithmetic are all
counts and classifications, not timings.

What is affected is every speedup figure and every accept/reject verdict in
this project, all of which were measured under uncontrolled load and none of
which disclosed it.

## Required, not optional

1. **Disclose machine state with every timing.** A number without its
   conditions is not a measurement.
2. **Replace the fixed margin with repeated independent runs and a
   confidence interval** (U15 item 3, from Kalibera & Jones). The decision must
   be stable across process invocations, not merely across trials inside one.
3. **Re-measure every published figure quietly** before it is cited again.
