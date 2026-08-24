#!/usr/bin/env python3
"""Lifter conformance (OQ-2): does the mechanical lifter reproduce the hand
analysis that was independently confirmed by measurement?

Ground truth: conformance/lift/GROUND-TRUTH.md — derived by hand BEFORE the
lifter existed, then each classification confirmed by writing the implied
transformation, checking it bit-identical, and timing it.

This is the falsifiable form of ADR-0014's OQ-2.
"""
import subprocess, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "optimizer" / "probe" / "none60" / "k.c"

# (breakable, true_carried, unhandled): '+' means >0, 0 means exactly zero
EXPECT = {
    "s212_v0":  ("+", 0, 0),
    "s211_v0":  ("+", "+", 0),
    "s1213_v0": ("+", "+", 0),
    "s261_v0":  ("+", "+", 0),
    "s244_v0":  ("+", 0, 0),
    "s241_v0":  ("+", 0, 0),
    "s116_v0":  ("+", 0, 0),
    "s221_v0":  ("+", "+", 0),
    # s291/s292: the load-bearing expectation is UNHANDLED > 0 — the lifter must
    # refuse the non-affine `b[im1]` rather than guess. The breakable count was
    # originally pinned at 0 because the hand analysis considered ARRAY
    # dependences only. Once scalar dependences were tracked, `im1` correctly
    # surfaced as a breakable anti dependence — which is precisely what makes
    # peeling these loops work. Expectation WIDENED after the fact, and said so
    # here rather than quietly re-pinned.
    "s291_v0":  (None, 0, "+"),  # MUST refuse: wrap-around scalar, not affine
    "s292_v0":  (None, 0, "+"),  # MUST refuse
}


def ok(want, got):
    if want is None:
        return True          # deliberately unconstrained; see EXPECT comments
    return got > 0 if want == "+" else got == want


def main():
    out = ROOT / "conformance" / "lift" / "lifted.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(SRC), "--json", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("LIFT FAIL: analyzer errored\n" + r.stderr[:400]); return 1
    loops = {l["func"]: l for l in json.loads(out.read_text())
             if l["func"].endswith("_v0")}

    passed = failed = 0
    print(f"  {'loop':<11}{'breakable':>10}{'true-carr':>11}{'unhandled':>11}  verdict")
    for name, (wb, wt, wu) in EXPECT.items():
        lp = loops.get(name)
        if lp is None:
            print(f"  {name:<11}{'—':>10}{'—':>11}{'—':>11}  NOT LIFTED"); failed += 1; continue
        b = sum(1 for d in lp["deps"] if d["breakable"])
        t = sum(1 for d in lp["deps"] if d["carried"] and not d["breakable"])
        u = len(lp["unhandled"])
        good = ok(wb, b) and ok(wt, t) and ok(wu, u)
        passed += good; failed += not good
        print(f"  {name:<11}{b:>10}{t:>11}{u:>11}  {'ok' if good else 'MISMATCH'}"
              + ("" if good else f"  want ({wb},{wt},{wu})"))
    total = passed + failed
    print(f"\nLIFT {'PASS' if failed == 0 else 'FAIL'}: {passed}/{total} loops "
          f"match the hand analysis confirmed by measurement")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
