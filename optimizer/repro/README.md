# Reproduction — arXiv:2502.11906 (TSVC vectorization rates, x86 vs ARM)

Sakib, Prabhu, Santhi, Shalf, Badawy. *"Comparison of Vectorization Capabilities
of Different Compilers for X86 and ARM CPUs."*

## Their methodology (extracted from the PDF, §II–III)

- **151 loop nests**, one per function; "we use the name of the containing
  function to refer to a loop nest."
- Metric is **compiler-reported**, not measured speedup: *"GCC reported 54% of
  the loops in the suite as having been vectorized."* Clang reports via
  `-Rpass=loop-vectorize -Rpass-missed=loop-vectorize`.
- **They modified TSVC2** so array sizes and trip counts are *not* compile-time
  constants, bundling them in a struct passed to each function — to make it
  "more representative of real-world code." Variant published at
  `github.com/NMSU-PEARL/tsvc_withArgs` (their ref [15]).
- ARM hardware: **Fujitsu A64FX**, flags `-O3 -mcpu=a64fx+sve -msve-vector-bits=512`,
  Clang 18.1.8.
- ARM result: **Clang 47%**, GCC 56%, ACFL 54%. **60 of 151 loops vectorized by
  no compiler at all.**

## What we reproduced (Apple M4, Apple clang 17, `-O3 -mcpu=native`)

| variant | vectorized | rate |
|---|---|---|
| stock TSVC_2 (sizes known at compile time) | 64 / 151 | 42.4% |
| `tsvc_withArgs` (their info-withdrawn variant) | 54 / 151 | **35.8%** |
| *paper: Clang 18.1.8, A64FX SVE-512* | *71 / 151* | *47.0%* |

**Not a contradiction.** A64FX has SVE-512 with predication, which vectorizes
control flow NEON cannot express; plus a newer Clang. We reproduced the
**method** and obtained *our* baseline — we did not reproduce their hardware.

## The measured result: withdrawing information costs 12 loops

`s124 s1279 s243 s254 s255 s271 s2711 s2712 s273 s3251 s4117 s443`

Of the 5 whose failure reason could be attributed cleanly, **all 5 are Class-2**:

| loop | reason after withdrawal |
|---|---|
| s243, s3251 | `unsafe dependent memory operations` |
| s254, s255 | `value that could not be identified as reduction` |
| s4117 | `cannot identify array bounds` |

## The negative result: C cannot express what was withdrawn

We decomposed the withdrawal into two declarations and measured each:

| variant | vectorized | recovered |
|---|---|---|
| A — as published | 54 | — |
| B — `+ restrict` on every array pointer (no-alias declared) | 54 | **0** |
| C — `+ const` trip count (extent declared) | 52 | **-2** |
| BC — both | 52 | **-2** |

Both transformations verified applied (1080 `restrict` insertions; 151 const
extents). **They recover nothing.**

The reason is visible in `s243`:

```c
a[i] = b[i] + c[i] * d[i];
b[i] = a[i] + d[i] * e[i];
a[i] = b[i] + a[i+1] * d[i];   // reads a[] one ahead -- INTRA-array
```

`restrict` declares that *distinct pointers* do not alias. This dependence is
*within* `a`. **C has no syntax for intra-array dependence structure** —
consistent with the independent `probe/s1113` finding that `-Ofast`,
`vectorize(enable)`, and `distribute(enable)` all refuse that class.

Scope: we tested `restrict` and const extent, not every possible C annotation.

## FAILED: the recovery demo (`probe/s243`)

An attempt to show a declared node-split recovering `s243` was **invalid**.
Extracting the loop dropped its outer repeat loop and its `dummy()` call;
in isolation clang vectorizes the original fine, so the probe never reproduced
the refusal. With the context restored the blocker is a *different* one
(`call instruction cannot be vectorized`). The node split was also **0.90x —
slower** — the extra temp-array pass costs more than breaking the dependence saves.

Recorded as a failure, not deleted.

## Status

Reproduction of the method: **done**. Recovery demonstration: **not achieved**.
