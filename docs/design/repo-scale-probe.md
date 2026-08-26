# Pointing the optimizer track at repositories it did not author

Run 2026-08-25, immediately after G17–G22 shipped. The question was the obvious
next one: *the pipeline recovers dependence facts and transforms TSVC loops —
does it find anything in production C?*

Ten repositories, cloned at HEAD, scanned with the shipped `tools/c_lift.py` and
`tools/c_choose.py` through a driver that adds only two things TSVC-scale work
never needed: **dedupe** (libclang walks whole translation units, so a
static-inline loop in a header lifts once per TU — this inflated opus ~10x on
the first run) and **rank** (`distribute` fires on any loop with two SCCs, which
is most loops and almost always pointless).

## What the scan found first: five bugs in what we shipped

None is reachable from `optimizer/probe/none60/`. All ten probe loops step by 1,
ascend, write their dead store last, name their arrays with plain identifiers,
and touch offsets small enough to stay inside the differential harness's
buffers. Five separate defects hid behind those coincidences.

| # | defect | found on | consequence |
|---|---|---|---|
| 1 | recognisers ignored the loop **step** | `silk/float/scale_copy_vector_FLP.c:46` | proposed deleting 3 of 4 **live** stores in a 4x-unrolled copy |
| 2 | dead-store assumed the overwrite was **one iteration** away, and skipped the dead statement's own reads at any offset | `src/analysis.c:915` | emitted wrong code: 8 of 140 elements differ |
| 3 | arrays named by the **first identifier** of the base, merging `p->x` with `p->y` | `silk/NSQ_del_dec.c:428` | INVENTED a carried output dependence between disjoint members |
| 4 | a **descending** loop yields no step from the header parser, and the body was analysed anyway as ascending | `NPB3.0-omp-C MG/mg.c:343` | every dependence direction inverted; proposed deleting a live store |
| 5 | the differential harness indexed **past its own buffers** | (why 2 was invisible) | scored the wrong code from 2 as `EXACT` — the comparison was over UB |

Defect 5 is the one worth dwelling on. Gate 2 is the safety property of the
whole track — *no accepted candidate is ever incorrect* — and it was quietly
weaker than advertised, because a loop touching `arr[i+24]` with `N`-sized rows
ran off the end of the object. Buffers are now padded by the largest offset the
loop touches, **and the pad is compared**, since a tail difference is exactly
what this class of bug produces. All ten none60 loops remain EXACT under the
strictly stronger test.

Defect 1 is the one that matches the project's own record: it is the *fourth*
wrong-code emission caught by the correctness gate, and the first found on code
from outside this repository. Fixtures and witnesses:
`conformance/lift/repo-pins/`.

## What the scan found second: nothing to contribute

With all five fixed, across **5,147 distinct loops** in ten repositories —
audio/ML on the left of the rule, scientific/HPC below it:

| repo | domain | `.c` files | loops | fully affine | profitable-shaped |
|---|---|---|---|---|---|
| xiph/opus | audio codec | 238 | 1018 | 397 (39%) | **0** |
| xiph/vorbis | audio codec | 33 | 335 | 87 (26%) | **0** |
| xiph/speexdsp | DSP | 16 | 141 | 62 (44%) | **0** |
| libsndfile/libsamplerate | resampler | 4 | 22 | 8 (36%) | **0** |
| pjreddie/darknet | neural nets | 46 | 335 | 103 (31%) | **0** |
| codeplea/genann | neural nets | 6 | 20 | 15 (75%) | **0** |
| **PolyBench/C 4.2.1** | *the* affine benchmark | 33 | 174 | **12 (7%)** | **0** |
| NPB3.0-omp-C | NAS parallel benchmarks | 14 | 269 | 48 (18%) | **0** |
| milc-qcd/milc_qcd | lattice QCD | 600 | 2003 | 604 (30%) | **0** |
| GSL | scientific library | 600 | 830 | **757 (91%)** | **0** |
| **total** | | **1590** | **5147** | **2093 (41%)** | **0** |

The HPC half was added specifically to test the assumption this document
carried in its first draft — that scientific codebases, where large affine loop
nests are the idiom, would look different. **They do not.** They look different
in *reach*, and identically in *yield*.

PolyBench is the sharpest single row. It is the canonical affine benchmark, the
corpus polyhedral compilers are evaluated on — and it lifts at **7%**, the worst
of all ten, because its loops are multi-dimensional (`A[i][j]`) and this
analyser is single-index by declaration. GSL is the mirror image: **91%**
affine, the best of all ten, and still zero.

That pairing is the finding. Reach and yield are independent here. Being able to
analyse a loop says nothing about there being a transformation worth making.

*Profitable-shaped* is Allen & Kennedy's case, and the only shape worth a
stopwatch: a **recurrence pins the loop** and distribution lets a
dependence-free statement escape it — or a non-`distribute` family fires at all.

Before the fixes the same scan reported six such candidates in opus and one in
NPB. All seven were artifacts of defects 1–4. The corrected count is zero, in
every repository, across all 5,147 loops.

### The filter is not the reason the count is zero

Run against `optimizer/probe/none60/k.c`, the same ranker flags **9 of 10**
loops — every one for which a transformation was found and measured, excluding
only `s261`, which the chooser correctly calls `none`. The filter lights up
where the wins are. It does not light up in production C.

### What the in-family candidates actually look like

```c
error[i] = -t*log(p) - (1-t)*log(1-p);      /* darknet src/blas.c:279 */
delta[i] = t - p;
```

Two independent statements, no recurrence pinning either. Distribution is legal
and pointless: it doubles loop overhead and halves locality. That is the shape
of essentially all 91.

## Reading

The transformations in this track — distribution, dead-store elimination,
preloading, wrap-around peeling — target a specific pathology: **a recurrence
sharing a loop body with vectorizable work**. TSVC contains that pathology by
construction; it is a benchmark built from the loops that defeated 1980s
vectorizers. Maintained numeric C mostly does not, and the reason is not
mysterious: where such a loop existed and mattered, someone already split it by
hand, or wrote the intrinsics.

This does not retract anything measured at G17–G22. The 10 kernels are real, and
the 42.4% -> 49.0% on TSVC is real. It bounds the claim's **reach**: the win rate
on a benchmark of hard loops is not the win rate on a repository, and this run
puts a measured number on the gap rather than an estimate.

`RESOLVED 2026-08-25.` The first draft of this document marked as untested the
assumption that scientific/HPC codebases would look different. Four were added —
PolyBench/C, NPB, milc_qcd (lattice QCD), GSL — and the yield is the same zero.
The assumption is answered, not still open.

`ASSUMPTION:` still untested — Fortran-dominated scientific code (climate, CFD:
Nek5000, Quantum ESPRESSO, NWChem), which this C-only lifter cannot read at all,
and which is where the largest affine loop nests actually live.

## What the capability model says to build, priced on a held-out corpus

`docs/design/limit-study-angle.md` records, citing Wall 1993, that every price in
this project was measured on TSVC2 alone and that a narrow benchmark misleads.
These 5,147 loops are the held-out corpus that was missing. G21's pricing,
re-run over them (`repo_scan.py` calls `capability_ceiling.features()` directly,
so the vocabulary is the same one the gate uses):

```
analysable under declared capabilities : 2073 (40.3%)

MARGINAL (each capability alone)
  +599   body.control_flow           -> 51.9%   (blocks 2108 loops)
  +415   subscript.indirect          -> 48.3%   (blocks 1695 loops)
  +98    access.multi_dimensional    -> 42.2%   (blocks 1419 loops)
  +55    iteration.unparsed_header   -> 41.3%   (blocks  204 loops)
  +23    subscript.wraparound        -> 40.7%   (blocks  526 loops)
  +19    dep.recurrence_cycle        -> 40.6%   (blocks   38 loops)

JOINT
  +3074  all six                     -> 100.0%  (marginals say +1209, UNDER by 1865)
  +2832  multi_dimensional + control_flow + indirect + wraparound -> 95.3%
```

Two results, and the second is the one that matters.

**First: the ranking is different from TSVC's.** On TSVC the subscript
capabilities lead. On real code the top capability by a wide margin is
`body.control_flow` — an `if` inside the loop body — which blocks 2,108 of 5,147
loops on its own. A build order chosen from the TSVC prices would have started
in the wrong place. That is precisely the failure Wall warns about, now measured
rather than cited.

**Second: supermodularity is enormous here.** The six capabilities price at
+1,209 summed and +3,074 together — marginal pricing under-values them by
**1,865 loops**, more than the total gain it predicts. A loop blocked by two
features is unlocked by neither alone, and most real loops are blocked by
several. On TSVC the same effect was +43 summed vs +68 joint; on a real corpus
it is more than 2.5x rather than 1.6x.

**And a caveat that outranks both.** What is priced here is analysis REACH, not
wins. This corpus already gives 2,073 analysable loops and **zero** worth
transforming. Buying reach up to 100% buys the right to analyse 3,074 more loops
of the same kind. Nothing in this measurement suggests the yield on them would
be different, and the null result above is direct evidence that it would not be.
The binding constraint is not what the analyser can *see*. It is that the
transformation catalogue — distribution, dead-store, preload, peel — targets a
pathology that maintained numeric C does not contain.

That is a more useful answer than a speedup would have been, and it was not
knowable without pointing the tools at code they did not author.

## Method, for reproduction

`optimizer/probe/repo_scan.py`, run as `python3 optimizer/probe/repo_scan.py
<repo-dir> [out.json]`. Deliberately not in `tools/`: it measures REACH, which is
a property of whatever it is pointed at, not a repo invariant, so it is advisory
and ungated. What it found IS gated, in `conformance/lift/repo-pins/`. It does
four things: glob `.c` (excluding tests/examples/vendored trees), lift each with the
directory's headers on `-I`, dedupe by `(func, line, body)`, and rank. The
per-repo JSON it emits is the input to any follow-up.

No measurement was run on repository loops, deliberately. `tools/c_choose.py`'s
stopwatch benchmarks an **extracted loop shape** — retyped to `float`, fed
fabricated inputs, run 200x over 32000 elements. A speedup there is evidence
about the shape, not about the repository's workload. Contributing upstream
would require the project's own benchmark, which is the correct next step for
any candidate that survives this filter — and none did.


---

# G23 — building the capability the probe priced, and what the price was worth

Written 2026-08-25, immediately after the above. The probe said `body.control_flow`
was the top declared refusal on real code at **+599 loops**. This section records
what building it actually delivered.

## First: the corpus above was undercounted

Fixing the lifter to REFUSE rather than assume (defect 4) exposed a counting bug
in the same place. `collect()` returns before recording accesses when it refuses,
and loops were admitted to the corpus only if they had accesses — so **every
loop refused early was silently dropped from every count in this document's
first version.**

Corrected, on the identical ten repositories:

| | loops | fully affine |
|---|---|---|
| as first reported | 5,147 | 2,093 (41%) |
| **corrected** | **10,777** | **2,107 (19.6%)** |

The affine *count* barely moves; the *rate* halves, because the denominator was
missing more than half the loops. Every percentage in the section above should
be read as "of loops the analyser got far enough to record accesses for", which
is not what it claimed to be. The zero-yield conclusion is unaffected — the
loops that reappeared are all refused ones.

## The prediction, and the measured answer

| | loops |
|---|---|
| `body.control_flow` blocks, in total | 2,108 |
| priced marginal unlock for admitting the GENUS | **+599** |
| guarded assignments the built capability NORMALISES | 47 |
| **realized unlock — loops analysable BECAUSE of it** | **+14** |

**+14 against +599: the price overstates by a factor of 43.**

The arithmetic was never wrong. `+599` is the correct answer to "how many loops
become analysable if all control flow is admitted". It is the wrong answer to
"how many become analysable if I build a capability", because nobody builds a
genus. The species that is buildable — `if (P) lhs = rhs;`, side-effect-free
predicate, non-trapping guarded work — is a thin slice of it, and the rest of
the genus decomposes into species that are each separately expensive:

```
+2888  body.nested_loop              (blocks 3004)   <- loop NESTS, not `if`s
+544   body.guarded_nonassignment    (blocks  556)
+371   body.guarded_alternative      (blocks  394)   <- if/else
+357   body.unsafe_speculation       (blocks  372)
+327   body.nested_guard             (blocks  347)
+240   body.early_exit               (blocks  259)
```

The bulk of "control flow blocks this loop" was never conditionals at all. It
was **nested loops** — loop nests, at +2,888, which is a different capability
entirely and a much larger one.

**The methodological finding, stated as a rule:** a capability price computed at
genus level is not a forecast of what building a capability delivers. It is an
upper bound on the whole genus, and the buildable species may be — here, is —
two orders of magnitude smaller. Prices must be quoted for the species that will
actually be implemented, or they mislead in the direction of overwork.

This is the first **prospective** test of the pricing instrument in this repo.
Every earlier price was computed against a corpus already understood. The
instrument's arithmetic survived; its interpretation did not.

## What the capability does deliver

Two loops in **xiph/vorbis** convert, bit-exactly, and measure faster:

```c
/* lib/psy.c:71 — min_curve */
for (i = 0; i < EHMER_MAX; i++) if (c2[i] < c[i]) c[i] = c2[i];
->  for (i = 0; i < EHMER_MAX; i++) c[i] = (c2[i] < c[i]) ? (c2[i]) : (c[i]);
```

`1.53x` and `1.57x`, EXACT. This is the first time in this project that the
pipeline has taken a loop from a repository it did not author, transformed it,
proved it bit-identical, and measured a gain end to end.

**It is not an upstream contribution, and the reason matters.** `EHMER_MAX` is
**56**, and both functions are called from `_vp_psy_init` — encoder setup, once
per stream. The measured 1.53x is the shape benchmarked at 32,000 elements by a
harness that normalises the trip count. At 56 elements, cold, the gain is
neither measurable nor worth a patch.

That is gap #2 from this document's own list arriving on schedule: **the rig
measures shapes, and a shape's speedup does not transfer to a repository without
the trip count and the profile.** Ten of the twelve convertible loops could not
be measured at all — they reference file-scope constants and enclosing locals
the harness cannot supply.

## Two wrong-code classes found while building it

Both by pointing the new capability at real repositories, both now refused:

1. **Pointer-validity guards.** `if (da) da[i] += dc[i]*s[i];` (darknet
   `src/blas.c:61`) converts to a select that subscripts `da` on **both** arms —
   a null dereference on exactly the iterations the guard existed to prevent.

   The correctness gate **cannot** catch this class: the differential harness
   only ever passes valid, non-null arrays, so the input that would expose it is
   not in the test distribution. This is G22's test-case validity problem one
   level up — the harness is not wrong, its *input distribution* is incomplete —
   and it makes refusal an ANALYSIS obligation rather than something the
   stopwatch can be trusted to find.

2. **Trapping guarded expressions.** `if (c[i] != 0) a[i] = b[i]/c[i];` converts
   to a division by zero for the same reason.

Pinned as `r007_nullguard_v0` and `r001_trap_v0` in
`conformance/lift/predication/cases.c`.

## Where this leaves the ledger

The catalogue is no longer four families; it is five, and the fifth was chosen
by measurement. The measurement that chose it has now been calibrated, and says
its own prices need re-quoting at species level. Both of those are worth more
than the 1.53x.
