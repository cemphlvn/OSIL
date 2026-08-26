# `conformance/lift/` — the C lifter suite (G19 / OQ-2)

Answers the falsifiable form of ADR-0014's **OQ-2**:

> *"a mechanical lifter can recover the SIR of the 10 loops in
> `optimizer/probe/none60/` from their C source alone."*

**Result: 10/10.** `just lift`.

Why it matters: every `.osil` file in this repo was hand-written. Until a lifter
existed, OSIL could not be pointed at a codebase it did not author.

## Method

`tools/c_lift.py` parses with **libclang — the actual compiler frontend**, not a
bespoke parser. For a real repository the flags come from `compile_commands.json`,
which build systems already emit, so nothing is hand-fed.

The dependence test, for single-index affine accesses under loop step `s`:

```
W writes arr[i+q] at iteration i;  A touches arr[i'+p] at iteration i'
same address  <=>  i' - i = q - p     dependence iff (q-p) % s == 0
delta > 0 -> A later  -> flow (RAW)      delta < 0 -> A earlier -> anti (WAR)
delta = 0 -> same iteration, program order decides
```

**The first version got this wrong** by classifying on statement order alone. In
`a[i] *= c[i]; b[i] += a[i+1]*d[i];` the read of `a[i+1]` textually *follows* the
write of `a[i]`, but the write that would supply it happens a LATER iteration —
so the value read is the pre-loop one. That is an anti dependence, and a false
one. Statement order says "flow"; the iteration equation says "anti". Only the
second is right, and it is the difference between "cannot vectorize" and
"distribute it and go 2.28x faster".

## Coverage — measured, not estimated

The analyzer handles affine `arr[i + c]` subscripts and **refuses** everything
else rather than approximating. Refusal is the correct behaviour: a lifter that
silently guesses at a non-affine subscript emits a declaration licensing an
unsound transformation.

| corpus | loops | affine (handled) | refused | breakable | true-carried |
|---|---|---|---|---|---|
| TSVC_2 | 176 | 88 (50%) | 88 | 47 | 14 |
| darknet numeric core | 13 | 10 (77%) | 3 | 4 | 0 |
| genann | 10 | 9 (90%) | 1 | 0 | 0 |
| **kissfft** | 2 | **0 (0%)** | 2 | 0 | 0 |

> Those rows were measured before 2026-08-25 and with the pre-qualified-base
> naming (`p->x[i]` was recorded as `p`). A whole-repository scan of six
> projects — 1,871 distinct loops, 38% fully affine — is in
> `docs/design/repo-scale-probe.md`, together with the four defects that scan
> found in the shipped tools.

**Coverage is set by code style, not by effort.** Array-indexed numeric code
lifts at 50-90%. Pointer-walking code (kissfft's FFT, libsvm's sparse dot
products) lifts at **0%** — and no amount of work on the affine analyzer changes
that, because the information simply is not in an affine form. This is the same
wall the applied survey hit: real code is substantially sparse and
pointer-based.

## What "non-manual" does and does not mean here

Non-manual is achieved for: finding loops, recovering iteration spaces,
classifying dependences, deciding breakability. No human annotates anything.

Not achieved: **choosing the transformation**. The lifter reports that a
dependence is false; it does not decide whether to distribute, peel, preload, or
expand — nor whether the transformation pays. `optimizer/probe/none60/` showed
both risks concretely: `s221` was exact but only 1.08x (an irreducible
recurrence caps it), and `s116`'s first transformation was a **0.33x loss**.
Recovering the facts is mechanical. Acting on them is not, yet.
