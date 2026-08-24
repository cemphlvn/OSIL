# The record attempt — TSVC2 vectorization rate

Written 2026-08-24, after measuring the slope rather than estimating it.

## The record exists, is published, and is directly comparable

arXiv:2502.11906 publishes vectorization rates on the canonical 151-loop TSVC2
suite, using **compiler-reported** vectorization — a metric we already reproduce
(`optimizer/repro/`).

| | rate | hardware |
|---|---|---|
| GCC 14.1.1 | **56.0%** (85/151) | A64FX, SVE-512 | **<- the record** |
| ACFL 22.2 | 54.0% (82/151) | A64FX, SVE-512 |
| Clang 18.1.8 | 47.0% (71/151) | A64FX, SVE-512 |
| Apple clang 17 | 35.8% (54/151) | **M4, NEON-128** (ours) |

## Measured slope, not estimated

Running `tools/c_lift.py` + `tools/c_choose.py` over all 176 TSVC2 loops:

| chooser decision | loops | of which in the None set (no compiler vectorizes) |
|---|---|---|
| distribute | 23 | **17** |
| none (one SCC — needs another family) | 128 | 52 |
| refuse (non-affine) | 25 | 15 |

## The arithmetic

```
clang alone                          54/151 = 35.8%
+ all 17 distribution candidates     71/151 = 47.0%   == Clang's published SVE-512 rate
ceiling if EVERY family lands       108/151 = 71.5%
                                                the record to beat: 56.0%
```

**Discount it honestly.** On the probe set only 3 of 4 distribution candidates
cleared all three gates (`s221` was rejected by the stopwatch at ~1.0x). At that
rate 17 candidates yield ~13, giving **~44%** — just under Clang's 47% and well
under GCC's 56%. Distribution alone does **not** take the record.

The record needs the families the chooser currently reports as `none`: dead-store
elimination (`s244`), preloading (`s241`), peeling / scalar expansion (`s291`,
`s292`, `s261`), anti-dependence collapse (`s116`). Each was already validated by
hand in `optimizer/probe/none60/` — the algorithms are known and the wins are
measured. What is missing is the mechanical chooser for each, not the insight.

## Stop conditions — decided in advance

- **Kill at Phase 1** if the 17 distribution candidates yield fewer than 10
  accepted. That would mean the probe set was unrepresentative and the families
  do not generalize. Cost to find out: days.
- **Kill at Phase 2** if, after two more families, the rate plateaus below 47%.
  Below Clang's own published number there is no result worth writing up.
- **Succeed and STOP at >56%.** That is the record. Write it up, freeze the
  exploration, do not keep adding families for their own sake.

## Scope the ambition permanently

"Point it at any repository" is **not** reachable and should stop being the
framing. Measured coverage: TSVC 50% affine, darknet 77%, genann 90%,
**kissfft 0%**. Pointer-walking and sparse code does not lift at all, and no
work on the affine analyzer changes that — the information is not in affine
form. The honest scope is *affine array code*, permanently.

## The uncomfortable part

**The record path does not need OSIL.** `tools/c_lift.py` + `tools/c_choose.py`
is a standalone C-to-C tool: parse, analyse dependences, distribute, verify,
measure. None of it consults a `.osil` file.

What OSIL contributes is the governance layer — declared licences, preservation
contracts, guard selectivity, determinism, the XFAIL/XPASS discipline. Those are
real and they are why the tool's claims are auditable. But they are not what
generates the speedup, and a paper claiming a TSVC record would be a **compiler
tooling** paper, not a semantic-architecture paper.

Recorded here so the choice of deliverable is made deliberately rather than
discovered late.


---

# RESULT (2026-08-24) — the Phase-1 kill condition FIRED

## The number

```
kernels                                       151
clang -O3 -mcpu=native alone           64/151 = 42.4%
kernels the chooser could even attempt         12
RECOVERED (correct + faster + clang then vectorizes)   6
clang + chooser                        70/151 = 46.4%

published (A64FX, SVE-512):  Clang 47.0%  ACFL 54.0%  GCC 56.0%
```

| kernel | family | speedup |
|---|---|---|
| s244 | dead-store | 2.01x |
| s1213 | distribute | 1.67x |
| s212 | preload | 1.67x |
| s241 | preload | 1.67x |
| s211 | distribute | 1.66x |
| s1244 | preload | 1.27x |

**The record was NOT broken.** GCC's 56.0% stands, comfortably.

## The absolute numbers are NOT comparable

46.4% vs their Clang's 47.0% is a coincidence of similar figures on different
machines, not a comparison. Ours is Apple clang 17 on **M4, NEON-128**; theirs
is Clang 18.1.8 on **A64FX, SVE-512** — a 4x wider vector unit with predication
that vectorizes control flow NEON cannot express. The only figure that is ours
is the **delta: +6 kernels, +4.0 points**, on top of whatever compiler you have.

## An unsound intermediate result, and what it cost

The first complete run reported **10 recovered, 49.0%** — above Clang's
published number. It was wrong. Three candidates came out INCORRECT, all of
them loops containing `goto`/label pairs that the chooser reordered: the
dependence model is program-order over straight-line statements and has no
notion of branching.

Fixing it (refusing any body containing control flow) cut the result from
**10 recovered to 6**, and 49.0% to 46.4%. Four kernels that had counted —
s221, s222, s274, s482 — were either unsound or marginal.

The differential test caught the three wrong ones, so nothing incorrect was ever
counted as recovered. But a differential test on a single input distribution is
not a control-flow soundness argument, and leaning on it would have been wrong.

## Why the record is out of reach on this path

Not because the transformations fail. **6 of 12 attempted succeeded — a 50% hit
rate on what the analyzer can see.** The families work.

The binding constraint is that only **12 of 151 kernels are analyzable at all**
by a model restricted to affine, single-index, straight-line loops. Reaching
56% needs +21 kernels over baseline; we found +6. The rest sit behind control
flow (needs if-conversion / predication), non-affine subscripts (needs a real
dependence test), and 2D arrays (needs multi-dimensional analysis). Each is a
substantially larger piece of machinery than any transformation family.

## DECISION: stop the record attempt

`record-attempt.md` set the condition in advance — *"kill at Phase 1 if the
candidates yield fewer than 10 accepted."* Six were accepted. **The condition
fires and the record attempt ends here.**

What is worth keeping is not the rate. It is that the pipeline runs end to end,
mechanically, with a correctness gate that caught a real unsoundness and a
stopwatch that rejected four correct-but-not-faster transformations.
