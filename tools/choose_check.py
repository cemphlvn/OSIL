#!/usr/bin/env python3
"""Chooser conformance (OQ-2, second half).

WHAT IS GATED (deterministic, machine-independent):
  * the DECISION per loop — distribute / none / refuse — follows from the
    dependence graph alone;
  * no accepted candidate is ever INCORRECT. This is the safety property: a
    chooser that emits wrong code is worse than no chooser.

WHAT IS NOT GATED (machine-dependent, reported only):
  * the measured speedup, and therefore ACCEPT vs REJECT-not-faster. Those
    depend on the machine, its load and its thermal state. Gating on them would
    make `just test` flaky, and a flaky gate is worse than an honest report.
    The stopwatch still runs on every invocation of `tools/c_choose.py`; it is
    just not a repo invariant.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "optimizer" / "probe" / "none60" / "k.c"
sys.path.insert(0, str(ROOT / "tools"))

# Decisions implied by the dependence graph. Derived by hand in
# optimizer/probe/none60/README.md, each confirmed by measurement.
# The chooser proposes EVERY applicable family and keeps the best measured, so
# the expectation is the SET of families offered, not a single pick.
EXPECT = {
    "s212_v0":  {"distribute", "preload"},
    "s211_v0":  {"distribute", "preload"},
    "s1213_v0": {"distribute", "preload"},
    "s221_v0":  {"distribute"},        # legal; the stopwatch then rejects it
    "s241_v0":  {"preload"},           # carried anti dep on a[i+1]
    # s244 also has a carried anti dep on a[i+1], so preload is genuinely
    # applicable too — expectation widened after the chooser was right and
    # this line was wrong.
    "s244_v0":  {"dead-store", "preload"},
    "s116_v0":  {"preload"},           # exact, but measured slower -> rejected
    "s261_v0":  {"none"},              # scalar `t` welds the statements together
    # G22: wrap-around is now NORMALISED (induction-variable substitution)
    # rather than refused — the subscripts become affine and the existing
    # machinery applies unchanged.
    "s291_v0":  {"peel-wraparound"},
    "s292_v0":  {"peel-wraparound"},
}


def main() -> int:
    import c_choose
    with tempfile.TemporaryDirectory() as td:
        lifted = Path(td) / "l.json"
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                            str(SRC), "--json", str(lifted)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("CHOOSE FAIL: lifter errored\n" + r.stderr[:300]); return 1
        loops = {l["func"]: l for l in json.loads(lifted.read_text())
                 if l["func"].endswith("_v0")}

        bad = 0
        print(f"  {'loop':<11}{'offered':<24}{'expected':<24}"
              f"{'correct':<10}  note")
        for name, want in EXPECT.items():
            lp = loops.get(name)
            if lp is None:
                print(f"  {name:<11}{'—':<24}{'+'.join(sorted(want)):<24}{'—':<10}  NOT LIFTED")
                bad += 1; continue
            ps = c_choose.plans(lp)
            got_set = {q["kind"] for q in ps}
            ok_decision = got_set == want
            p = next((q for q in ps if q["kind"] in c_choose.CANDIDATE_KINDS),
                     ps[0])
            got = "+".join(sorted(got_set))
            correctness, note = "n/a", p["why"][:34]
            if p["kind"] in c_choose.CANDIDATE_KINDS:
                cands = [q for q in ps if q["kind"] in c_choose.CANDIDATE_KINDS]
                res = [(q, c_choose.evaluate(lp, q, Path(td))) for q in cands]
                # SAFETY: not one candidate may be incorrect, even a losing one
                if any(r.get("verdict") == "INCORRECT" for _, r in res):
                    correctness = "INCORRECT"; bad += 1
                    print(f"  {name:<11}{got:<24}{'':<24}{correctness:<10}"
                          f"  a candidate emitted wrong code"); continue
                good = [(q, r) for q, r in res if r.get("verdict") == "ACCEPT"]
                p, e = (max(good, key=lambda qr: qr[1]["speedup"]) if good
                        else max(res, key=lambda qr: qr[1].get("speedup", 0)))
                v = e.get("verdict", "?")
                if v == "INCORRECT":
                    correctness = "INCORRECT"; bad += 1
                elif v == "compile-fail":
                    correctness = "COMPILE-FAIL"; bad += 1
                    note = e.get("err", "")[:34]
                else:
                    correctness = e.get("equivalence", "?")
                    note = (f"{e['speedup']:.2f}x  {v}"
                            if "speedup" in e else v)
            if not ok_decision:
                bad += 1
            print(f"  {name:<11}{got:<24}{"+".join(sorted(want)):<24}{correctness:<10}"
                  f"  {'' if ok_decision else 'DECISION MISMATCH — '}{note}")
    print(f"\nCHOOSE {'PASS' if bad == 0 else 'FAIL'}: decisions follow the "
          f"dependence graph; no accepted candidate is incorrect"
          + ("" if bad == 0 else f" ({bad} problem(s))"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
