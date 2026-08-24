# Attacking the "None" set — loops NO compiler vectorizes

Motivated by arXiv:2502.11906, whose ARM results report **60 of 151 TSVC loops
vectorized by none of GCC, Clang, or ACFL**. See `optimizer/repro/` for the
reproduction of that paper's method.

## Our None set (M4 / NEON, `-O3 -mcpu=native`)

Computed on the paper's own info-withdrawn variant (`NMSU-PEARL/tsvc_withArgs`):

| | vectorized | rate |
|---|---|---|
| Apple clang 17 | 54 / 151 | 35.8% |
| GCC 16.1.0 | 60 / 151 | 39.7% |
| either | 67 / 151 | 44.4% |
| **NEITHER — our None set** | **84 / 151** | **55.6%** |
| *paper's None on A64FX (3 compilers)* | *60 / 151* | *39.7%* |

Larger than the paper's 60 because we have two compilers rather than three, and
NEON-128 rather than SVE-512 (SVE's predication vectorizes control flow NEON
cannot express).

### Composition — **54 of 84 (64%) are Class-2**

| n | clang's stated reason | class |
|---|---|---|
| 42 | `unsafe dependent memory operations` / `cannot identify array bounds` | **Class-2 dependence** |
| 21 | `call instruction cannot be vectorized` | opaque call |
| 12 | `value that could not be identified as reduction` | **Class-2 recognition** |
| 4 | `cannot prove it is safe to reorder floating-point` | Class-1 numeric |
| 3 | `could not determine number of loop iterations` | dynamic bounds |

Cross-referencing TSVC's own per-loop comments, the Class-2 set decomposes into
**classical named loop transformations neither compiler applies**: statement
reordering, node splitting, array/scalar expansion, loop distribution, loop
interchange.

## Result: 10 attacked, 10 recovered

Context preserved (outer repeat loop + opaque call). An earlier probe was
invalidated by extracting the inner loop alone, which changed the blocker.

| loop | TSVC's own label | transformation declared | speedup | equivalence |
|---|---|---|---|---|
| s291 | loop peeling / wrap-around, 1 level | peel first iteration | **4.42x** | BIT-IDENTICAL |
| s244 | node splitting / false dependence cycle | dead-store elimination | **4.22x** | BIT-IDENTICAL |
| s292 | loop peeling / wrap-around, 2 levels | peel first two | **4.10x** | BIT-IDENTICAL |
| s211 | statement reordering allows vectorization | restructure recurrence | **2.31x** | BIT-IDENTICAL |
| s212 | statement reordering / needs temporary | loop distribution | **2.28x** | BIT-IDENTICAL |
| s1213 | statement reordering / needs temporary | loop distribution | 1.70x | BIT-IDENTICAL |
| s241 | node splitting / preloading necessary | preload old a[] | 1.70x | BIT-IDENTICAL |
| s261 | scalar expansion / wrap-around scalar | expand to pre-loop c[] | 1.63x | rel < 1e-5 |
| s116 | linear dependence testing | collapse to anti-dependence | 1.53x | BIT-IDENTICAL |
| s221 | loop distribution / partially recursive | distribute | 1.08x | BIT-IDENTICAL |

**n=10, geometric mean 2.24x, range 1.08x-4.42x. Nine of ten bit-identical** —
no numeric licence of any kind, so `-ffast-math` is irrelevant to all of them.
Speedups are medians over 3-4 runs; s241 is the noisiest at +/-13%.

### `restrict` alone recovers NONE of them

Tested directly: the same loop bodies with every pointer declared `restrict`
and no restructuring. All five tried (s116, s212, s241, s244, s291) are **still
refused**. Clang's own diagnostic says why:

> *"Backward loop carried data dependence. Memory location is the same as
> accessed at ..."*

The dependence is **intra-array**. `restrict` declares that distinct pointers
do not overlap; it says nothing about a loop-carried dependence within one
array. This confirms at loop level what the full-suite test in
`optimizer/repro/` found (restrict recovered 0 of 151). What these loops need
is **restructuring knowledge**, not aliasing knowledge — and C has no syntax
for "this dependence is false."

### Two honest results worth keeping

- **s221 is a near-miss at 1.08x.** Distribution is exact and the `a`-loop does
  vectorize, but the `b`-loop is a genuine first-order recurrence that cannot.
  Amdahl caps the win. Half of this loop is irreducibly scalar.
- **s116 was a 0.33x LOSS before being fixed.** The first transformation
  preloaded the array; the preload pass cost 3x what vectorizing saved. The
  preload turned out to be unnecessary — going forward, `a[j+1]` is still the
  old value when `a[j]` is written, so it is a pure anti-dependence, which
  vectorizes natively. An over-conservative declaration is a real cost, not a
  free safety margin.

Verified mechanically: every `v0` reports **0** vectorized loops and is blocked
by `unsafe dependent memory operations`; every `v1` vectorizes with no
dependence blocker remaining.

### The semantic content of each declaration

- **s212 / s1213** — one statement reads an array element the other writes
  *later* in the same pass, so it reads the PRE-LOOP value. Distributing with
  the reading loop first is exact.
- **s211** — a true carried dependence through `b`; restructuring lets the
  compiler forward-substitute it away.
- **s261** — the wrap-around scalar makes `a[i]` depend on `c_new[i-1]`, which
  equals `c_old[i-1]*d[i-1]`. So `a` depends only on the pre-loop `c`.
- **s244** — `a[i+1]` written at iteration `i` is **overwritten** by iteration
  `i+1`. Every one of those stores is dead but the last. Declaring that removes
  an entire store stream — the largest win here, and not a vectorization fact at
  all but a *liveness* one.

## Why this is the strongest result so far

These are the only wins in this project that are simultaneously:

1. against a baseline **no compiler reaches** (both clang and gcc refuse),
2. **bit-identical** (4/5) — no `-ffast-math`, no pragma, no numeric licence,
3. on a **published, externally-motivated** headroom set,
4. with the refusal reproduced **in context**, not in a stripped extraction.

## Status and limits

- 5 of 84 attacked. The transformations are hand-written C; **no OSIL machinery
  is involved** — the term language cannot express maps, stores, or multi-array
  loops yet.
- Speedups are modest (1.7x-4.4x), far below the FP-bucket headline numbers, but
  they are against a genuinely unreachable baseline rather than against code
  nobody optimized.
- Whether the remaining 37 dependence loops are as tractable is **unmeasured**.
  Several TSVC loops are deliberately non-vectorizable.
