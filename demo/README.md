# s1113 — a bit-identical speedup no compiler flag or pragma reaches

```
./run.sh
```

Needs `clang` and/or `gcc`. Nothing else. Runs in about ten seconds and proves
every claim below **using your compiler, on your machine**.

## The loop

```c
for (int i = 0; i < N; i++) a[i] = a[N/2] + b[i];
```

`a[N/2]` is read on every iteration and overwritten on exactly one of them.
That single crossing point splits the loop into two independent maps:

```c
float s  = a[MID];
float s2 = s + b[MID];
for (int i = 0;       i <= MID; i++) a[i] = s  + b[i];
for (int i = MID + 1; i <  N;   i++) a[i] = s2 + b[i];
```

## What the run shows

| | clang 17 | gcc 16 |
|---|---|---|
| `-O3` | `unsafe dependent memory operations` | `couldn't vectorize loop` |
| `-O3 -ffast-math` | refused | refused |
| `-Ofast` | refused | refused |
| `#pragma clang loop vectorize(enable)` | refused | — |
| `#pragma clang loop distribute(enable)` | `cannot isolate unsafe dependencies` | — |
| **split, bit-identical** | **~5.2x** | **~4.0x** |

`distribute(enable)` is the pragma clang's **own diagnostic** tells you to use.
It refuses that too.

## Why this is not a fast-math trick

`max |ref - split| = 0.000e+00`. Not "close enough" — the same bits. The split
is a **rewrite, not a relaxation**: the dependence is real, it has one crossing
point, and splitting there changes nothing about what is computed. No flag is
being traded for accuracy because no accuracy is being traded.

The harness refuses to print a timing at all unless the two versions agree
exactly. A wrong transformation is infinitely fast.

## What this is NOT evidence of

- **Not "compilers are bad."** Both are refusing correctly: proving the single
  crossing point requires reasoning neither dependence analyzer performs, and
  refusing is the right behaviour when you cannot prove safety.
- **Not a new technique.** This is loop distribution over a false dependence,
  textbook since the 1980s. TSVC exists precisely to test it.
- **Not a benchmark result.** One loop, one shape. The timing ratio moves with
  machine load — measured on a busy machine it read 1.09x for a related kernel
  that reads 4.14x on a quiet one. Close other work before believing a number.

## Provenance

Loop `s1113` from **TSVC_2** (`github.com/UoB-HPC/TSVC_2`, BSD-3-Clause),
descended from Callahan, Dongarra & Levine's 1988 vectorizing-compiler test
suite via Maleki, Gao, Garzarán, Wong & Padua, *"An Evaluation of Vectorizing
Compilers"*, PACT '11.

Part of [OSIL](../README.md), where the general question is whether declaring a
computation's semantics lets a toolchain reach transformations that inference
alone cannot justify. This loop is the smallest honest example of the gap.

## A note on the evidence

An earlier version of this script counted vector instructions by grepping
disassembly, and got GCC wrong — reporting "0 vectorized" for loops GCC's own
`-fopt-info-vec` said it had vectorized. It now uses each compiler's own
report. **The compiler is the authority on what the compiler did.**
