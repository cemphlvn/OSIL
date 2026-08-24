# `optimizer/` — OSIL semantic optimizer (Rust)

| | |
|---|---|
| **Owner** | maintainer (unratified — no actor declared in `repo-policy.osil` yet) |
| **Status** | **PROBE.** N=1 vertical slice. Not gated, not in `just test`. |
| **Ground truth class** | empirical (measured against clang/GCC on this machine) |
| **Invariants** | correctness gates performance; realization must be licensed by a declared guard; output byte-deterministic |
| **Verbs** | probe, measure, report |

## What this is

A Rust optimizer testing one claim:

> A vectorization that LLVM must **refuse** for lack of a proof becomes legal
> when OSIL-SIR **declares** the semantic regime. The optimizer never
> rediscovers the loop's structure; it selects a realization from the declared
> semantic optimization space.

This is the constitutional equation from `spec/core.md` made executable:
`semantic optimization space = valid realizations(SIR, constraints, invariants)`.

## Why it does not unroll

Diospyros (ASPLOS'21) reaches ground terms by fully unrolling the loop nest —
see `docs/research/U6-egraph-vectorization-prior-art.md`. At TSVC's
`LEN_1D = 32000` that is 32,000 e-nodes for one loop, and Diospyros already
reports a 509 MB intermediate term at a 4×4 problem size.

This slice does **not** unroll. `(reduce mul a 32000)` is already a ground term
because the extent is a *literal*, not a *binder*. The e-graph stays constant
in the loop extent — measured at **8 classes / 13 nodes** for n=32000.

The cost: this cannot *discover* vectorizability the way Diospyros does. It can
only select among realizations of a reduction the SIR already declares. That is
a strictly weaker claim, and an honest statement of the trade.

## Status

Three of the five TSVC_2 kernels where Apple clang 17 `-O3` refuses with
*"cannot prove it is safe to reorder floating-point operations"*. Bucket chosen
from a measured survey of all 151 TSVC_2 kernels (70 are never vectorized; ~55
of those refuse for reasons a semantic declaration could discharge).

| kernel | clang -O3 | clang -ffast-math | best licensed | vs -ffast-math | realization | model right? |
|---|---|---|---|---|---|---|
| `s312` | 49.5 ms | 3.3 ms | **32x** | 2.10x | Lanes { w: 4, i: 8 } | **no** |
| `s317` | 24.7 ms | 1.7 ms | **6164x** | 431.01x | PowI | yes |
| `s352` | 31.5 ms | 4.1 ms | **8x** | 0.97x | Lanes { w: 4, i: 4 } | yes |

`s317` is an **asymptotic** result, not a constant factor: `closed_form`
licenses collapsing a 16,000-long multiply chain to one `powf` call. Verified a
real libm call (`b _powf` in the emitted assembly), and isolated `powf`
throughput on this machine is 3.00 ns/call — consistent with the measurement.
TSVC's own source comment for `s317` names the closed form; no compiler takes it.

`s352` (dot product) is the **lane where we lose**: it ties `-ffast-math` and
does not beat it. Two loads per multiply make it bandwidth-bound, so extra
accumulator chains stop paying. Reported, not hidden.

### Guard selectivity

Two independent guards, each gating a different class of rewrite:

| case | guards | space collapses to |
|---|---|---|
| `s312` | `numeric_semantics = reassociable` | `Lanes {w:4,i:4}` |
| `s312-exact` | `numeric_semantics = exact` | `Chain` (1 realization only) |
| `s317` | `reassociable` + `closed_form` | `PowI` (O(1)) |
| `s317-noclosed` | `reassociable` only | `Lanes {w:4,i:8}` |

Withdrawing `closed_form` drops `s317` from O(1) to vectorized-O(n) while
leaving reassociation intact — the guards gate independently.

Run it:

```
cargo build
./target/debug/osil-opt cases/s312.osil        # the licensed space
./target/debug/osil-opt cases/s312-exact.osil  # same kernel, 1 realization
cd bench && python3 run.py                     # ledger: correctness + timing
```

## Calibration loop

The two microarchitectural constants are **data**, not code: `src/main.rs`
reads them from `calibration/constants.toml`. The model's *form* stays
hand-written and auditable. Design follows `docs/research/U10`.

```
bench/run.py                      measure every licensed realization
  -> calibration/measurements.jsonl   append-only ledger (never rewritten)
calibration/fit.py                weighted least squares, held-out gate
  -> calibration/constants.toml       the only thing that changes
  -> calibration/HISTORY.md           append-only audit trail
```

Split declared up front: fit on `s312` + `s317-noclosed`, **hold out `s352`**.
Two gates, per U10 — pick-correctness is **blocking**, fit quality is
informational only (TenSet documents models with great R² making worse picks).

**The held-out gate has already earned its keep.** The first calibration fixed
the training kernel and *broke* the held-out one — net 0 improvement — and
promotion was refused. Textbook overfitting, caught mechanically:

```
s312   train      lanes w4 i8   lanes w4 i8   ok  (fixed)
s352   HELD-OUT   lanes w4 i8   lanes w4 i4   WRONG  (BROKE)
HELD-OUT GATE: FAIL — do not promote
```

Investigating that failure showed the s352 i4-vs-i8 gap is **noise**: repeated
runs gave deltas of 0.5% / 2.4% / 0.0% with the sign flipping. Both gates now
use a 5% noise band, justified by that measurement rather than chosen to pass.
Calibrated: `mul_latency` 4.0 -> 3.27, `lanes_per_cycle` 8.0 -> **18.44** (the
original guess was off by 2.3x). Agreement 2/3 -> 3/3.

Recalibration is **event-triggered**, not continuous (new machine, new
compiler, or a held-out failure) — per MLGO's own reported experience.

## Energy as a second objective — hypothesis FALSIFIED

We measured per-realization energy to test whether the *fastest* realization
differs from the most *energy-efficient* one. If it did, "best" would have no
answer independent of the declared objective — which a semantic optimizer could
exploit and a fixed compiler heuristic could not.

**It does not. Objectives agreed on 3/3 kernels.** The data says why:

| s312 realization | ms | nJ/call | cyc/call | IPC | nJ/cycle |
|---|---|---|---|---|---|
| Chain | 49.6 | 95475 | 109065 | 1.17 | 0.875 |
| Lanes w4 i8 | 1.8 | 5548 | 3663 | 4.38 | **1.515** |

Energy *per cycle* rises 1.7x with the fast realization — higher IPC means more
units switching, i.e. more watts. But cycles fall 30x. **Race-to-idle dominates
overwhelmingly**: power goes up, energy goes down. An energy objective would
select the same realization as a time objective, so it buys nothing here.

Scope of the refutation: one machine, plugged in, P-cores, compute-bound
reductions. It does *not* refute the idea for E-cores, for DVFS at low
frequencies, or for memory-stalled workloads. It does refute it for this class.

Measurement is per-process and needs **no sudo** — `proc_pid_rusage` with
`RUSAGE_INFO_V6` gives `ri_energy_nj`, `ri_cycles`, `ri_instructions`.

### What the energy lane found anyway

`s352` was spending **10% more energy than `-ffast-math`** at equal speed. Cause
was in our own emitter: multiply and accumulate sat in separate statements,
which blocks FP contraction, so we emitted `fmul`+`fadd` where clang emitted
`fmla`. Fixed via a new `fp_contraction` guard. IPC 3.55 -> 2.59, energy
14628 -> 13111 nJ, gap closed.

The guard is emitted as a **scope-local `#pragma clang fp contract(fast)`**,
not a `-ffp-contract` flag: the flag is per-translation-unit, the declared
licence is per-realization. That granularity is not expressible as a compiler
flag at all.

### And it fixed the cost model's physics

`ri_cycles` reports cycles; the model is *written* in cycles. Fitting against
measured cycles instead of wall time removed the clock nuisance parameter
entirely, and the constants became physically plausible for the first time:

| | guessed | fitted (wall time) | fitted (cycles) |
|---|---|---|---|
| `mul_latency` | 4.0 | 3.27 | **3.20** (NEON fp mul: 3-4) |
| `lanes_per_cycle` | 8.0 | 18.44 | **17.99** (= 4.5 x 4-wide ops/cyc) |
| implied clock | - | 4.5 GHz *at the rail* | *parameter eliminated* |

The earlier "model form suspect" warning was wrong about the cause: the form
was fine, the **measurement** was — wall time conflates frequency scaling and
preemption with the work being modeled.

## Two classes of declaration (learned the hard way)

The `probe/s1113` result forced a distinction the first four kernels had hidden:

**Class 1 — numeric licences** (`reassociable`, `closed_form`, `fp_contraction`).
They *change the result*, and a global compiler flag can grant the same
permission. `s312`'s code is reachable with `-ffast-math` plus an interleave
pragma. Our advantage here is **scope and auditability, not reach**.

**Class 2 — dependence facts** (`s1113`'s single crossing point). Bit-identical,
zero semantic cost, and **no compiler flag or pragma reaches them**: `-Ofast`,
`vectorize(enable)`, and clang's own suggested `distribute(enable)` all refuse.

Class 2 is the actual thesis. Class 1 is what was demonstrated first — because
it reused machinery that already existed — and it is the class most exposed to
the "that's just fast-math" objection. **The bucket priority was backwards.**

## Known gaps

- **`cases/*.osil` are not grammar-legal.** `sir { (reduce mul a 32000) }` uses
  an application form the ratified grammar v0.6 has no production for
  (`factor = identifier | number | "(" expr ")"`). `src/sir.rs` is a throwaway
  reader; delete it when the spec catches up. Triple representation is **owed**.
- **The cost model ranks correctly but is physically mis-specified.** After
  calibration it agrees 3/3, but the fit can only match the data by pinning
  the implied clock at its 4.5 GHz upper bound. It predicts *order*, not
  *magnitude*. Ranking is what selection needs (Halide/AutoTVM/TenSet all
  report the same priority — see U10), so it is fit for purpose while still
  being wrong about the machine. Fixing the FORM is open work.
- **`egg`, not `egglog`.** ADR-0009 binds the *spec's* equivalence projection to
  egglog. This probe uses `egg` (Diospyros precedent, mature extraction API,
  `deterministic` feature). It does **not** rebind ADR-0009.
- **n=1.** One kernel, one operator, one width. Nothing here generalizes yet.
