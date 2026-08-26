# ADR-0017: preservation witnesses, validated by an independent checker
Date: 2026-08-26 · Status: accepted (G25)

## Context

`GOVERNANCE.md` has required a **foreign-witness lane** since G13, on the
grounds that "evidence from a single parser/linter lineage is weak against
shared blind spots" — the SIR/CIR definition hole was found by an external
reading while every internal loop was green.

The optimizer track never had one. Every correctness result was produced by the
**same harness that produced the transformation**: `tools/c_choose.py` emits the
candidate, generates the inputs, runs the comparison, and declares the verdict.
When that harness has a blind spot, nothing sees it. Three of the last four
sessions' findings were exactly that — the buffer-bounds defect (G22), the
converged-input defect (G24), and the null-guard class that is *structurally
invisible* to a harness which only passes valid pointers (G23).

SV-COMP solves this and has for years. Its central discipline is not the
benchmark suite; it is that **a tool's claim is not evidence**. The tool emits a
witness, a separate validator decides whether the claim holds, and the score
prices the asymmetry: a correct proof is +2, a wrong one is −32.

## Decision

### 1. Every candidate emits a preservation witness

`tools/c_choose.py::evaluate` returns a `witness` carrying everything an
independent checker needs to re-decide the equivalence claim without trusting
the chooser: both C functions in full, the signature shape (array count, scratch
count, integer prefix, pad), the claimed equivalence and its tolerance, and the
profile the verdict was measured under.

### 2. A validator that shares no code with the chooser

`tools/witness_check.py` imports nothing from `c_choose`. It writes its own
driver, generates its own inputs, and does its own comparison. Producer and
validator live in separate files (`witness_emit.py` / `witness_check.py`) so the
independence is true by construction rather than by care.

It deliberately probes where the chooser never looks:

| probe | why |
|---|---|
| **five input regimes** — zeros, wide signed magnitudes, denormals, exact integers, alternating extremes | the chooser's blind spot at G24 *was* an input distribution; a validator reusing it would inherit the blind spot |
| **trip-count edge cases** — n ∈ {0, 1, 2, 3, 5, 7, 8, 63, 64, 65, 1000} | the chooser measures at n = 32000 and nothing else, and tails/prologues are exactly the code that breaks at small n |
| **out-of-bounds canaries** — guard regions before and after every buffer | a write past either end is caught rather than silently tolerated |

If the **original** also corrupts a canary, the original is at fault and the
transformation is not blamed — reported as `ORIGINAL-AT-FAULT`, scored 0.

### 3. SV-COMP's scoring asymmetry, transposed

| outcome | points |
|---|---|
| `CONFIRMED-EXACT` | +2 |
| `CONFIRMED-CLOSE` | +1 |
| `REFUTED` | **−32** |
| `UNSUPPORTED` / `ORIGINAL-AT-FAULT` | 0 |

A transformation wrongly certified equivalent is the catastrophic outcome; a
refusal costs only the opportunity. This is the same ordering the chooser's three
gates already encode — the score just makes it a number, and makes regressions
visible as a magnitude rather than a boolean.

## What it found on its first run

**Dead-store elimination was wrong at n = 0.** The emitted tail was

```c
{ int i = (n) - 1; a[i+1] = ...; }      /* n == 0  ->  i == -1 */
```

which replays the removed store at index −1, writing outside the array. Caught
by the LEAD canary on `s244_v0` and as a value difference on `asc_v0`. Four
witnesses REFUTED, score **−86**.

The chooser's own harness could not have found this: it measures at n = 32000,
so the guarded path never executes there. Two independent lineages, one blind
spot each, and only their disagreement exposes it — which is the entire argument
`GOVERNANCE.md` makes.

Fixed by guarding the replay and computing the last executed index correctly for
any step, rather than assuming `up - 1`:

```c
if ((up) > (lo)) { int i = (lo) + ((((up) - 1 - (lo)) / s) * s); ... }
```

After the fix: **25 witnesses, 0 refuted, score +50.**

### 4. The gate applied to itself — mutant pins for the validator

With every real witness CONFIRMED, a validator that printed `CONFIRMED`
unconditionally would score identically. Nothing in the gate showed it could
still refute anything.

`conformance/lift/witness-mutants/` closes that. Each file is an `orig`/`xform`
pair carrying a claim that is **false on purpose**, and each is wrong in a way
that only ONE detector catches:

| mutant | detector pinned | wrong how |
|---|---|---|
| `m001-offbyone` | `value_comparison` | reads `b[i+1]`; wrong at every n, every regime |
| `m002-zero-trip` | `trip_count` | correct for all n > 0, wrong ONLY at n == 0 |
| `m003-oob-write` | `canary` | writes `a[-1]`; every in-range value correct |
| `m004-not-exact` | `exactness` | off by ~2.5e-7 — inside a 1e-6 tolerance, but the claim is EXACT |
| `m005-negative-only` | `regime_diversity` | correct for positive inputs, wrong for negative ones |

Expectations use the same vocabulary as every other pin here: **XFAIL-HOLDS**
when the mutant is refuted (the detector is alive), **XPASS-ALARM** when it is
CONFIRMED. An XPASS-ALARM **fails the gate** — a mutant that starts passing does
not mean it was fixed, it means that detector died, and the file name says which.

`m002` is the load-bearing one: it is the shape of the bug this validator
actually found (a replayed store at `int i = n - 1`, i.e. index −1). `m005` is
the second: the chooser's harness seeds strictly positive data and could never
catch a negative-input bug, which is the blind spot this validator exists not to
share.

**The pins are discriminating, checked by perturbation.** Restricting the
validator to a single trip count — exactly how the chooser measures — flips
`m002` to CONFIRMED and moves *nothing else*:

```
all detectors ON              trip-count probe DISABLED
  m001  REFUTED                 m001  REFUTED
  m002  REFUTED                 m002  CONFIRMED-EXACT   <- and only this one
  m003  REFUTED                 m003  REFUTED
  m004  REFUTED                 m004  REFUTED
  m005  REFUTED                 m005  REFUTED
```

## Consequences

- `just witness` joins the gatekeeper. A REFUTED witness fails `just test`.
- The duplicate-candidate wart is closed as a side effect: `_distribute()` was
  re-offering `dead-store` alongside `plans()`, so every such loop was measured
  twice and counted twice in the score.
- This is the first result in the repo produced by a lineage that did not also
  produce the thing it was checking.
- The validator's own capabilities are now enumerable and individually pinned —
  the same move the capability model makes for the analyser, applied to the
  checker.
- `just harness` (G22) refused the first version of this file, for a timed
  subprocess call with no `TimeoutExpired` handler. H2 — *a timeout is a
  verdict* — caught new code written minutes earlier.

## Ratification act recorded

Adding `stage witness` to `conformance/corpus/023-stage-toolchain.osil` (required
by the standing 1:1 agreement between the `justfile` `test:` line and the corpus
stage declarations) changed the derived governed views, and G16 correctly refused
the stale goldens. `just views-bless` was run for that reason and no other: the
only change is the new stage's read-set and the pair count moving 78 -> 91
(commuting 75 -> 88). No existing stage's declaration was altered.

## What is NOT closed

The validator is independent in *code*, not in *authorship* — same session, same
model. That is a weaker independence than SV-COMP's (different teams, different
tools, adversarial incentives) and is recorded as such rather than claimed away.
The strongest available next step is a second implementation of the validator by
a different author or model, checked against this one.
