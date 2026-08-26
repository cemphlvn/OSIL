# Witness mutants — pinning the VALIDATOR's detectors (G25)

`tools/witness_check.py` exists to refute false preservation claims. With every
real witness CONFIRMED, a validator that simply printed `CONFIRMED` would score
identically. Nothing in the gate demonstrated that it can still refute anything.

These are the negative fixtures for the validator itself. Each file is a pair —
`orig` and a **deliberately wrong** `xform` — that the validator MUST refute,
and each is wrong in a way that only ONE detector catches. A mutant that starts
being CONFIRMED does not mean the mutant was fixed; it means that detector died,
and the file name says which.

This is the gate applied to itself: the same witness format, carrying claims that
are false on purpose.

| mutant | detector pinned | wrong how |
|---|---|---|
| `m001-offbyone.c` | `value_comparison` | reads `b[i+1]`; wrong at every n, in every regime |
| `m002-zero-trip.c` | `trip_count` | correct for all n > 0, wrong ONLY at n == 0 |
| `m003-oob-write.c` | `canary` | writes `a[-1]`, outside the buffer, value-correct otherwise |
| `m004-not-exact.c` | `exactness` | off by ~2.5e-7 — inside a 1e-6 tolerance, but the claim is EXACT |
| `m005-negative-only.c` | `regime_diversity` | correct for positive inputs, wrong for negative ones |

`m002` is the one that matters most: it is the bug the validator actually found
on its first run (dead-store's `int i = n - 1` replaying at index −1). It is
pinned here so the trip-count probe can never be quietly dropped.

`m005` is the second: the chooser's own harness seeds strictly positive data, so
it could never catch a negative-input bug. That is the blind spot this validator
exists to not share.

Expectation vocabulary, as everywhere else in this repo:

- **XFAIL-HOLDS** — the mutant is refuted, as declared. The detector is alive.
- **XPASS-ALARM** — the mutant was CONFIRMED. A detector has died. Gate fails.
