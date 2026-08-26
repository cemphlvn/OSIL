# Repo pins — bugs found by pointing the tools at code they did not author (G20)

Fixtures for `tools/choose_check.py`. **Every loop in these files is correct as
written.** The pin is that the chooser leaves them alone.

All five were found on 2026-08-25 by running the shipped G19 lifter and G20
chooser over **xiph/opus**, a repository this project did not author. None of
them is reachable from `optimizer/probe/none60/`, and that is the point: the
probe set is ten TSVC loops that all step by 1, all write their dead store last,
and all touch offsets small enough to stay inside the differential harness's
buffers. All ten also ASCEND. Five separate defects hid behind those coincidences.

## Pin 1 — the step (`step.c`)

The lifter's dependence test has always carried the step:

> `W writes arr[i+q]; A touches arr[i'+p]` — same address iff `i' - i = q - p`,
> and that iteration exists iff `(q-p) % s == 0` (`conformance/lift/README.md`).

The chooser's *recognisers* did not. `dead_stores()` asked only whether some
other statement wrote a **lower offset**; `preloadable()` asked only whether a
read offset was **greater than** some write offset. Under `s == 1` those are the
same question — so the two layers agreed by accident for the whole of G19–G22.

Manually unrolled loops break the accident, and they are the dominant idiom in
production DSP code. The scan ranked `silk/float/scale_copy_vector_FLP.c:46`:

```c
for( i = 0; i < dataSize4; i += 4 ) {            /* SILK's 4x unrolled copy */
    data_out[ i + 0 ] = gain * data_in[ i + 0 ];
    ...
    data_out[ i + 3 ] = gain * data_in[ i + 3 ];
}
```

`data_out[i+0]` and `data_out[i+3]` are different addresses under step 4. No
store is dead; the chooser proposed deleting three of four.

| loop | step | property pinned |
|---|---|---|
| `unrolled_v0` | 4 | `dead-store` must NOT fire — all four stores are live |
| `unroll_pre_v0` | 2 | `preload` redirects `a[i+2]` (genuinely overwritten) and NOT `a[i+1]` (written by S0 in that same iteration) |

The second is the sharper one. Its offered *set* is `{preload, distribute}`
either way — only the **offsets** change. A pin comparing decision kinds alone
would have passed on the broken chooser, and the lie-detector said so on its
first run; that is why the signature it compares carries the plan's payload.

## Pin 2 — the replay (`replay.c`)

Dead-store elimination is an **emitter** promise, not only an analysis result.
The removed store is replayed once, after the loop, and that replay reads the
*post-loop* state. Reduced from `src/analysis.c:915`:

```c
for (i=0;i<8;i++) { m[i+24]=m[i+16]; m[i+16]=m[i+8]; m[i+8]=m[i]; m[i]=BFCC[i]; }
```

`m[i+24]` *is* overwritten — eight iterations later, by S1 — and S0 reads it
before then. Two things follow, and neither was checked:

1. the store is live for the last 8 iterations, while the emitter replays 1;
2. condition (3) skipped **all** of the dead statement's own reads, on the
   reasoning that a statement's read of its own address is consumed. That holds
   only at the SAME offset; `m[i+16]` is a different address on a different
   iteration and must still block.

Three conditions were added, each justified separately: the overwrite must be
exactly one iteration away, the statement must be **last** in the body (so the
post-loop replay sees the state it would have seen), and condition (3) now skips
only same-offset self-reads. The overwriter search also now takes the **nearest**
aliasing write rather than whichever appeared first in access order.

## Pin 3 — the member (`member.c`)

Every access in `silk/NSQ_del_dec.c:428` has the form `psDD->sAR2_Q14[j]`. The
lifter named the array by the **first identifier in the base expression**, so
every array member of `psDD` collapsed onto the single name `psDD` — and two
disjoint members then look like one location.

On the reduction, the lifter INVENTED a loop-carried output dependence between
`p->x` and `p->y`, and the chooser proposed deleting every store to `p->x`
because `p->y` was written. The emitted code did not compile (`float * restrict
p` cannot be written `p->y[i]`), which is the only reason this did not reach
gate 2 as wrong code rather than as a build error.

Arrays are now named by the **qualified base** (`p->x`), which is both sound —
distinct members are distinct storage — and strictly more precise than before.
Bases that are not identifier chains (`p[k]->m`, a call, arithmetic) are refused
rather than named after whichever identifier came first.

The chooser gained a matching refusal: a member-qualified name is a valid array
but not a valid **parameter**, so there is no emission form for it. Such loops
were previously counted as candidates and then died as `compile-fail`; they are
now refused honestly, up front.

## Pin 4 — the iteration space (`iteration.c`)

`for (k = lt-1; k >= 1; k--)` yields no upper bound and no step from the header
parser — and the lifter analysed the body **anyway**, under the default step-1
ascending assumption. That inverts every dependence direction, because under a
descending step a LOWER offset is reached EARLIER.

Reduced from `NPB3.0-omp-C MG/mg.c:343`. The fixture holds the SAME BODY twice,
ascending and descending:

* ascending — `a[i+1]` is written at iteration `i` and overwritten at `i+1`:
  dead but for the last iteration, and `dead-store` is legal;
* descending — `a[i+1]` is written *before* `a[i+0]` is reached and is never
  overwritten: every store is live, and the lifter must **refuse**.

The contrast is the witness. If the lifter ever stops distinguishing the two,
both answers converge and the gate fails — no perturbation needed.

The refusal is named in the declared vocabulary as `iteration.unparsed_header`
(`conformance/corpus/026`), so G21 can price it: it blocks **204 loops** across
the probe corpus and prices at **+55**.

## Pin 5 — the harness bounds (why pin 2 was invisible)

The wrong emission for `shift_v0` was scored **EXACT** by the differential test.
It was not: a bounded rerun differs in 8 of 140 elements, all in the tail.

`HARNESS` sized every array `[N]` and ran the loop for `i < N` while the loop
indexes `arr[i+24]` — so the last rows ran off the end of the object, and the
comparison was over undefined behaviour. Buffers are now padded by the largest
offset the loop touches, and **the pad is compared**, since a tail difference is
exactly what this class of bug produces.

All ten none60 loops remain EXACT under the strictly stronger test.

## Witnesses

Re-run mechanically by `just choose`:

| perturbation | result |
|---|---|
| force `step = 1` on `unrolled_v0` | `dead-store [1,2,3]` -> **INCORRECT 1.959e+00** |
| force `step = 1` on `unroll_pre_v0` | `preload offsets [1,2]` -> **INCORRECT 6.953e-01** |
| offer the refused `dead-store [0]` plan on `shift_v0` | **INCORRECT 1.595e+00** |
| collapse qualified names to their first identifier on `member_v0` | `dead_stores` fires on a **live** store |
| `asc_v0` vs `desc_v0`, identical bodies | `dead-store` vs `refuse` — the answers must differ |

If either step pin stops moving when the step test is removed, the fixture has
stopped exercising what it claims to and the gate fails. If the `shift_v0`
witness ever scores EXACT again, the harness has stopped comparing the tail.

## Scope, stated

The step test was added to condition (2) of `dead_stores()` and to the offset
selection in `preloadable()`. Condition (3) was deliberately left without a
congruence test: over-blocking eliminates fewer stores, which is the safe
direction.
