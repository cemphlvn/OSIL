# `probe/` — headroom measurements, before building machinery

Hand-written C. **No OSIL machinery involved.** The point is to measure whether
a transformation is worth implementing *before* paying to implement it — the
order-of-work lesson from the s312 slice.

## s1113 — the result that refuted the "information vs physics" law

`for i: a[i] = a[LEN_1D/2] + b[i]`. Clang refuses: *"unsafe dependent memory
operations in loop."*

The dependence is real but has **exactly one crossing point**, at `i = mid`:

```
i <  mid : a[mid] still holds its original value  s
i == mid : a[mid] is overwritten with s + b[mid] = s2
i >  mid : a[mid] holds s2
```

So the loop is two independent, dependence-free maps. Declaring that fact is
all the information clang lacks.

### Measured (Apple M4, clang 17, min of 15 trials, 3 runs)

| | ms | speedup |
|---|---|---|
| clang -O3 (refuses to vectorize) | 16.0–16.4 | 1.00x |
| declared split (two clean maps) | 3.07–3.18 | **5.13–5.31x** |

**Bit-identical** to the reference (max abs diff = 0.000e+00). Unlike every
earlier kernel, this needs **no numeric licence at all** — it is exact.

### The escape-hatch ladder is exhausted

Every compiler-side route was tried, and every one refuses:

| attempt | result |
|---|---|
| `-O3` | `unsafe dependent memory operations` |
| `-ffast-math` | still scalar |
| `-Ofast` | still scalar |
| `#pragma clang loop vectorize(enable)` | *"the optimizer was unable to perform the requested transformation"* |
| `#pragma clang loop distribute(enable)` — **clang's own suggestion** | *"cannot isolate unsafe dependencies"* |

`ref_s1113` compiles to **zero** NEON instructions under all of the above.

This is the first kernel where the "you are just doing `-ffast-math`" objection
has no purchase: there is no flag, no pragma, and no `-Ofast` that reaches it.

## Status

Headroom **proven**, implementation **not done**. The OSIL term language has no
map/store realization yet — everything to date reduces to a scalar. Building
that is the next real capability, and this probe is the justification for
spending on it.
