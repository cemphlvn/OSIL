#!/usr/bin/env python3
"""Capability-ceiling conformance (G21).

The architecture analysing its own reach. `conformance/corpus/026` declares
which loop features the analyser admits and refuses; the analysable set is
DERIVED from those declarations. This gate checks two properties, both in the
G16 governed-views spirit:

  1. AGREEMENT — the derived classification matches the hand analysis that
     `conformance/lift/GROUND-TRUTH.md` already pins and measurement already
     confirmed.
  2. LIE-DETECTION — perturbing a capability MUST move the derived set. A
     ceiling that does not respond to its own declarations is decoration.

Runs on `optimizer/probe/none60/k.c`, which is in-repo, so the gate is
self-contained (the TSVC corpus is external and not vendored).
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import capability_ceiling as cc

SRC = ROOT / "optimizer" / "probe" / "none60" / "k.c"

# Cross-checked against conformance/lift/GROUND-TRUTH.md.
#
# NOTE the model is deliberately CONSERVATIVE. `dep.true_carried` disqualifies a
# loop here, but distribution can PARTIALLY recover such loops by isolating the
# recurrence so the rest vectorizes — s1213 (1.67x) and s211 (1.66x) were both
# recovered despite carrying a true dependence. So the derived ceiling
# UNDERSTATES what is reachable. Understating is the safe direction for a
# ceiling; overstating one would have justified work that cannot pay.
EXPECT_RECOVERABLE = {"s212_v0", "s241_v0", "s244_v0", "s116_v0",
                      "s211_v0", "s1213_v0"}   # separable, not recurrences
# NOTE s291/s292 remain REFUSED by the capability model (`subscript.wraparound`
# is still a declared refusal) even though the chooser now normalises them.
# That divergence is deliberate and is the point of this gate: the capability
# declaration states what the ANALYSER admits, and normalisation happens
# upstream of it. When `026` is updated to admit wrap-around, this set must
# grow to match — and the vocabulary-coverage check will catch it if it does not.


def classify(refused: set) -> tuple[set, dict]:
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "l.json"
        subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(SRC), "--json", str(js)], capture_output=True)
        loops = json.loads(js.read_text())
    feats = {}
    for lp in loops:
        if not lp["func"].endswith("_v0"):
            continue
        # A loop with NO accesses affine in its own index is scaffolding, not a
        # kernel: in k.c that is the outer `for (nl = 0; nl < reps; nl++)`
        # repeat loop, whose body's subscripts are affine in `i`, not `nl`.
        # These are keyed by FUNCTION, so unioning the scaffolding's features
        # into the kernel's makes every kernel look blocked by
        # `body.nested_loop` — which it is not. The scaffolding used to be
        # dropped for having no accesses; it now survives so that refused loops
        # are counted at repo scale, so the exclusion has to be stated here
        # instead of happening by accident.
        if not lp["accesses"]:
            continue
        feats.setdefault(lp["func"], set()).update(cc.features(lp))
    ok = {f for f, ft in feats.items() if not (ft & refused)}
    return ok, feats


def main() -> int:
    caps = cc.read_capabilities(ROOT / "conformance" / "corpus"
                                / "026-capability-analysis.osil")
    refused = set().union(*(c["refuses"] for c in caps.values()))
    print(f"  declared capabilities : {', '.join(sorted(caps))}")
    print(f"  features refused      : {', '.join(sorted(refused))}")

    # --- VOCABULARY COVERAGE: every declared feature must be REACHABLE.
    # G21's lie-detection checks that declarations move the derived set — but
    # only for features the classifier actually emits. A feature named in a
    # declaration that no classifier path can produce is unreachable
    # vocabulary: it prices at +0 BY CONSTRUCTION, and that +0 reads as
    # "worthless" rather than "never measured". `subscript.wraparound` was
    # exactly this, and was reported as worthless on that basis. The bug was
    # found by outside review, not by this gate — so the gate now checks it.
    import inspect
    # Any dotted string literal in features() is a feature the classifier can
    # emit. Matching only `f.add("X")` missed the conditional form
    # `f.add("A" if cond else "B")` and reported BOTH branches unreachable.
    emitted = {m for m in re.findall(r'"([a-z_]+\.[a-z_]+)"',
                                     inspect.getsource(cc.features))}
    # Only REFUSES must be emittable: `features()` reports blockers, so an
    # `admits` feature is the COMPLEMENT of a blocker and is legitimately never
    # emitted. A refused feature the classifier cannot produce, however, is
    # unreachable vocabulary that prices at +0 by construction.
    declared = set()
    for c in caps.values():
        declared |= c["refuses"]
    unreachable = {d for d in declared if d not in emitted}

    ok, feats = classify(refused)
    bad = 0
    print(f"\n  {'loop':<11}{'recoverable':<13} features")
    for fn in sorted(feats):
        a = fn in ok
        want = fn in EXPECT_RECOVERABLE
        if a != want: bad += 1
        print(f"  {fn:<11}{'yes' if a else 'no':<13}"
              f"{', '.join(sorted(feats[fn])) or '(none)'}"
              f"{'' if a == want else '   MISMATCH'}")

    # --- LIE-DETECTION: every refused feature that any loop exhibits must,
    # when admitted, change the derived set. A feature nothing exhibits is
    # inert here and is reported rather than silently counted as a pass.
    print(f"\n  vocabulary coverage (every REFUSED feature must be reachable):")
    for d in sorted(declared):
        mark = "emitted by classifier" if d in emitted else "UNREACHABLE — priced +0 by construction"
        if d in unreachable:
            bad += 1
        print(f"    {d:<32} {mark}")

    print(f"\n  lie-detection (admitting each refused feature must move the set):")
    exhibited = set().union(*feats.values()) if feats else set()
    moved = inert = 0
    for f in sorted(refused):
        alt, _ = classify(refused - {f})
        delta = len(alt) - len(ok)
        if f not in exhibited:
            inert += 1
            print(f"    {f:<28} inert here (no loop exhibits it)")
        elif delta == 0:
            bad += 1
            print(f"    {f:<28} NO EFFECT — declaration is decoration")
        else:
            moved += 1
            print(f"    {f:<28} +{delta} recoverable  ok")

    print(f"\nCEILING {'PASS' if bad == 0 else 'FAIL'}: derived classification "
          f"matches the hand analysis; {moved} declaration(s) demonstrably move "
          f"the set, {inert} inert on this corpus (model is conservative — see "
          f"EXPECT_RECOVERABLE)")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
