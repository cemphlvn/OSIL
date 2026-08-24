# Applied probe — darknet (YOLO) batch-norm variance

**Read the baseline caveat first. The headline number is not a result.**

Found by harvesting clang's vectorization remarks across four real numeric
codebases and looking for reductions clang refuses.

## WHAT THE BASELINE ACTUALLY IS (written after overclaiming this once)

`variance_cpu` is **not** a previously-tuned limit that we beat:

- **dead repo** — last commit 2022-07-18, a README edit
- **shadowed by CUDA** — `variance_gpu` exists; the CPU path is the
  no-GPU fallback
- **training path** — inference uses `rolling_variance`; nobody trains
  darknet on CPU

Nobody optimized this and gave up. Nobody looked. And `pow(x,2)` instead of
`x*x` is a code smell, not a compiler limitation.

Against a genuinely optimized baseline the picture is much smaller:

| | ms/call | |
|---|---|---|
| darknet v0 verbatim | 1.3238 | |
| numpy 2.5.2 `((x-mean)**2).sum(axis=(0,2))` | 0.1499 | 8.8x faster than darknet |
| our v3 | 0.0326 | 4.6x faster than numpy |

And even that 4.6x is mostly **fusion**, not vectorization quality: numpy
materializes a 2 MB temporary before reducing. We beat an architectural
constraint of its API, not its SIMD. In absolute terms v3 sustains ~64 GB/s,
roughly half the M4's achievable bandwidth — decent, not near-optimal.

**No tuned baseline has been beaten by this project. Not once.** The only
rival that ever had equivalent information (`-ffast-math` on s352) tied us.

## What survives

Not the 40x. The **ladder structure** below: each declaration removes one
blocker and reveals the next, and the first rung is bit-identical.

Source: `darknet/src/blas.c:110`, `variance_cpu`. The inner loop computes a
**sum of squares** — `(reduce add (zip mul d d n))` in OSIL's SIR — using a libm
`pow()` call for the square.

## The ladder (Apple M4, clang 17, batch=8 filters=64 spatial=1024)

| version | ms/call | speedup | exactness |
|---|---|---|---|
| v0 verbatim darknet (`pow`) | 1.3238 | 1.00x | reference |
| v1 `pow(v,2)` -> `v*v` | 0.4788 | **2.76x** | **BIT-IDENTICAL** (rel.err 0.00e+00) |
| v2 + accumulator hoisted out of memory | 0.3208 | 4.13x | rel.err 1.59e-07 |
| v3 + lanes w4 i4 + contraction | 0.0326 | **40.59x** | rel.err 3.32e-06 |

## The finding: the blocker CHANGES at every rung

Each declaration removes one obstacle and reveals the next. This is the semantic
optimization space opening progressively, visible in clang's own remarks:

| version | clang's verdict |
|---|---|
| v0 | `value that could not be identified as reduction` — the opaque `pow` call |
| v1 | `cannot prove it is safe to reorder floating-point operations` — sees the reduction now, refuses to reorder |
| v2 | `vectorized loop` — hoisting the accumulator unlocks clang's own vectorizer |
| v3 | ours; 14 vector instrs vs v2's 6 |

**v1 is the notable rung**: 2.76x for free, bit-identical, no numeric licence
required at all. `pow(v,2) == v*v` is a semantic identity, and it is the single
biggest obstacle in the verbatim code. That rung is pure recognition.

## Caveat on attribution

v2's gain is partly clang's — once the accumulator is a local, clang vectorizes
the loop itself. The honest split is: v0->v1 is ours (recognition), v1->v2 is
mostly clang unblocked, v2->v3 is ours (explicit lanes + interleave + FMA).

## Status

Headroom measured, **not implemented**. The OSIL term language cannot express
this kernel yet: it needs a `zip` over a *strided/offset* source (`x[j*F*S +
i*S + k]`) and a map-shaped output, neither of which exists.
