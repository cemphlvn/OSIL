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
PINS = ROOT / "conformance" / "lift" / "repo-pins"
STEP_SRC, REPLAY_SRC = PINS / "step.c", PINS / "replay.c"
MEMBER_SRC, ITER_SRC = PINS / "member.c", PINS / "iteration.c"
PRED_SRC = ROOT / "conformance" / "lift" / "predication" / "cases.c"
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


# ---------------------------------------------------------------------------
# STEP PINS. Every loop in none60 steps by 1, which makes `(q-p) % s == 0`
# collapse to `q > p` -- so the recognisers agreed with the lifter by accident
# rather than by construction. Manually unrolled loops break the accident.
# Found by pointing the shipped lifter at xiph/opus (2026-08-25); the chooser
# proposed deleting three of four LIVE stores in the SILK copy idiom.
#
# Pinned deterministically:
#   * the offered SET on each pin;
#   * `preload` redirects ONLY the offsets that genuinely alias;
#   * no candidate on a pin is INCORRECT.
# Plus a lie-detector: forcing step back to 1 must break both pins, or the
# fixture is not exercising the test it claims to.
EXPECT_STEP = {
    "unrolled_v0":   {"distribute"},               # NOT dead-store: 4 live stores
    "unroll_pre_v0": {"preload", "distribute"},
}
EXPECT_PRELOAD_OFFSETS = {"unroll_pre_v0": {"a": [2]}}   # not [1, 2]

# The replay pin. `dead-store` must not fire, and the plan it USED to offer must
# be rejected by the correctness gate — which is the sharper half: that plan was
# scored EXACT until the differential harness stopped indexing past its buffers.
REFUSED_PLAN = {"kind": "dead-store", "dead": [0], "live": [1, 2, 3],
                "why": "the pre-fix proposal, kept as a witness"}


# G23 predication. Four loops the analyser must NORMALISE and six it must
# REFUSE — each refusal by SPECIES, because the species is what gets priced.
# Every accepted conversion must be bit-exact; the speedup is reported, never
# gated (same rule as every other family).
EXPECT_PRED = {
    "p001_mask_v0":       "if-convert",
    "p002_accum_v0":      "if-convert",
    "p003_twoarray_v0":   "if-convert",
    "p004_mixed_v0":      "if-convert",
    "r001_trap_v0":       "body.unsafe_speculation",
    "r002_indexguard_v0": "body.unsafe_speculation",
    "r003_break_v0":      "body.early_exit",
    "r004_else_v0":       "body.guarded_alternative",
    "r005_call_v0":       "body.unsafe_speculation",
    "r006_block_v0":      "body.guarded_nonassignment",
    "r007_nullguard_v0":  "body.unsafe_speculation",
}


# ---------------------------------------------------------------------------
# PROFITABILITY, reported in the four-way vocabulary this repo already uses for
# pins. ADVISORY, never gated: a speedup is machine-dependent, and gating one
# makes `just test` flaky. But an expectation that quietly stops holding is
# exactly what a pin is for, so it is declared and reported rather than
# remembered.
#
#   PASS         expected faster, measured faster
#   FAIL         expected faster, measured NOT faster   <- a documented claim died
#   XFAIL-HOLDS  expected not-faster, measured not-faster
#   XPASS-ALARM  expected not-faster, measured FASTER    <- investigate, do not bless
#   UNDECIDED    the two input regimes disagree — reported, never averaged
EXPECT_PROFIT = {
    "s212_v0": "faster", "s211_v0": "faster", "s1213_v0": "faster",
    "s241_v0": "faster", "s244_v0": "faster",
    "s291_v0": "faster", "s292_v0": "faster",
    # s116's 0.33x is the standing evidence that gate 3 is not optional
    # (CHOOSER.md); s221 is the marginal case the stopwatch keeps rejecting.
    "s116_v0": "not-faster", "s221_v0": "not-faster",
    "p001_mask_v0": "faster", "p003_twoarray_v0": "faster",
    "p002_accum_v0": "not-faster",
    # p004 was ACCEPT 1.56x under the old harness and is a 5.9x REGRESSION under
    # fresh inputs — confirmed independently outside the rig. The expectation
    # records the corrected fact, not the one that was published.
    "p004_mixed_v0": "not-faster",
}
PROFIT_LOG = []


def log_profit(name, e):
    want = EXPECT_PROFIT.get(name)
    if want is None:
        return
    v = e.get("verdict", "?")
    if v.startswith(("UNDECIDED", "UNSTABLE")):
        mark = "UNDECIDED"
    elif want == "faster":
        mark = "PASS" if v == "ACCEPT" else "FAIL"
    else:
        mark = "XPASS-ALARM" if v == "ACCEPT" else "XFAIL-HOLDS"
    PROFIT_LOG.append((name, want, v, e.get("speedup"),
                       e.get("speedup_best"), mark, e.get("profile")))


def profit_report() -> None:
    if not PROFIT_LOG:
        return
    print(f"\n  {'profitability (ADVISORY)':<20}{'expect':<12}{'worst':>7}"
          f"{'best':>7}  {'p0/p1':<12} mark")
    tally = {}
    for name, want, v, sp, spb, mark, pr in PROFIT_LOG:
        tally[mark] = tally.get(mark, 0) + 1
        ps = "—"
        if pr and pr["regime0"]["branch_probability"] >= 0:
            ps = (f"{pr['regime0']['branch_probability']:.2f}/"
                  f"{pr['regime1']['branch_probability']:.2f}")
        print(f"  {name:<20}{want:<12}{(f'{sp:.2f}x' if sp else '—'):>7}"
              f"{(f'{spb:.2f}x' if spb else '—'):>7}  {ps:<12} {mark}")
    print("  " + " · ".join(f"{k} {v}" for k, v in sorted(tally.items())))
    if tally.get("XPASS-ALARM"):
        print("  XPASS-ALARM: a transformation declared unprofitable measured "
              "faster. Re-read the declaration before blessing it.")
    if tally.get("FAIL"):
        print("  FAIL: a documented speedup claim no longer holds on this "
              "machine. Advisory — but it is a claim, and claims are checked.")


def predication(c_choose, td: Path) -> int:
    lifted = td / "pred.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(PRED_SRC), "--json", str(lifted)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  predication: lifter errored"); return 1
    loops = {l["func"]: l for l in json.loads(lifted.read_text())}
    bad = 0
    print(f"\n  {'predication':<20}{'verdict':<26}{'correct':<10} note")
    for name, want in EXPECT_PRED.items():
        lp = loops.get(name)
        if lp is None:
            print(f"  {name:<20}{'NOT LIFTED':<26}"); bad += 1; continue
        ps = c_choose.plans(lp)
        kinds = {q["kind"] for q in ps}
        correctness, note = "n/a", ""
        if want == "if-convert":
            got = "+".join(sorted(kinds))
            if kinds != {"if-convert"}:
                note = f"expected if-convert, got {got}"; bad += 1
            else:
                e = c_choose.evaluate(lp, ps[0], td)
                log_profit(name, e)
                v = e.get("verdict", "?")
                # SAFETY: a predicated store must be bit-identical. Anything
                # else means the false arm is not writing back what was there.
                if e.get("equivalence") != "EXACT":
                    note = f"NOT EXACT: {v} {e.get('err','')[:30]}"; bad += 1
                correctness = e.get("equivalence", v)
                note = note or (f"{e['speedup']:.2f}x  {v}"
                                if "speedup" in e else v)
            print(f"  {name:<20}{got:<26}{correctness:<10} {note}")
        else:
            got = (lp["unhandled"] or ["(none)"])[0].split()[0]
            if kinds != {"refuse"} or got != want:
                note = f"expected refuse/{want}"; bad += 1
            print(f"  {name:<20}{('refuse: ' + got):<26}{'n/a':<10} {note}")
    return bad


def step_pins(c_choose, td: Path) -> int:
    """Returns the number of problems found."""
    lifted = td / "step.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(STEP_SRC), "--json", str(lifted)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  step-pins: lifter errored"); return 1
    loops = {l["func"]: l for l in json.loads(lifted.read_text())}
    bad = 0
    print(f"\n  {'step pin':<16}{'step':>5}  {'offered':<24}{'correct':<10} note")
    for name, want in EXPECT_STEP.items():
        lp = loops.get(name)
        if lp is None:
            print(f"  {name:<16}{'—':>5}  NOT LIFTED"); bad += 1; continue
        ps = c_choose.plans(lp)
        got = {q["kind"] for q in ps}
        note, ok = "", got == want
        if not ok:
            note = f"DECISION MISMATCH — expected {'+'.join(sorted(want))}"
            bad += 1
        # the offsets preload redirects are the precise property under test
        for q in ps:
            if q["kind"] == "preload":
                offs = {x["array"]: x["offsets"] for x in q["preload"]}
                if offs != EXPECT_PRELOAD_OFFSETS.get(name, offs):
                    note = f"PRELOAD OFFSETS {offs} — expected " \
                           f"{EXPECT_PRELOAD_OFFSETS[name]}"
                    bad += 1
        correctness = "n/a"
        for q in ps:
            if q["kind"] not in c_choose.CANDIDATE_KINDS:
                continue
            e = c_choose.evaluate(lp, q, td)
            if e.get("verdict") == "INCORRECT":
                correctness = "INCORRECT"; bad += 1
                note = note or f"{q['kind']} emitted wrong code"
            elif correctness == "n/a":
                correctness = e.get("equivalence", "?")
        print(f"  {name:<16}{lp['step']:>5}  {'+'.join(sorted(got)):<24}"
              f"{correctness:<10} {note}")

    # --- replay pin -------------------------------------------------------
    lifted2 = td / "replay.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(REPLAY_SRC), "--json", str(lifted2)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  replay-pin: lifter errored"); return bad + 1
    rl = {l["func"]: l for l in json.loads(lifted2.read_text())}["shift_v0"]
    kinds = {q["kind"] for q in c_choose.plans(rl)}
    if "dead-store" in kinds:
        print(f"  {'shift_v0':<16}{rl['step']:>5}  {'+'.join(sorted(kinds)):<24}"
              f"{'—':<10} dead-store fired: the store is read before it is "
              f"overwritten"); bad += 1
    else:
        # WITNESS: the plan the chooser used to offer here is wrong code, and
        # the gate must say so. If this ever comes back EXACT, the differential
        # harness has stopped comparing the tail again.
        e = c_choose.evaluate(rl, REFUSED_PLAN, td)
        ok = e.get("verdict") == "INCORRECT"
        bad += 0 if ok else 1
        print(f"  {'shift_v0':<16}{rl['step']:>5}  {'+'.join(sorted(kinds)):<24}"
              f"{'n/a':<10} witness: refused plan scores "
              f"{e.get('verdict')} {e.get('err','')[:18]}"
              + ("" if ok else "  — EXPECTED INCORRECT"))

    # --- member pin -------------------------------------------------------
    lifted3 = td / "member.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(MEMBER_SRC), "--json", str(lifted3)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  member-pin: lifter errored"); return bad + 1
    ml = {l["func"]: l for l in json.loads(lifted3.read_text())}["member_v0"]
    names = sorted({a["array"] for a in ml["accesses"]})
    kinds = {q["kind"] for q in c_choose.plans(ml)}
    note = ""
    if ml["deps"]:
        note = f"INVENTED {len(ml['deps'])} dependence(s) between disjoint members"
        bad += 1
    elif kinds != {"refuse"}:
        note = f"expected refuse, got {'+'.join(sorted(kinds))}"
        bad += 1
    else:
        # WITNESS: collapse each qualified name back to its first identifier —
        # the pre-fix naming — and dead-store must fire on a store that is live.
        merged = json.loads(json.dumps(ml))
        for a in merged["accesses"]:
            a["array"] = a["array"].split("->")[0].split(".")[0]
        fires = c_choose.dead_stores(merged)
        note = (f"witness: merged names -> dead_stores{fires}"
                if fires else "witness INERT — merged names no longer fire")
        if not fires:
            bad += 1
    print(f"  {'member_v0':<16}{ml['step']:>5}  {'+'.join(sorted(kinds)):<24}"
          f"{'n/a':<10} {names} {note}")

    # --- iteration pin ----------------------------------------------------
    lifted4 = td / "iteration.json"
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                        str(ITER_SRC), "--json", str(lifted4)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("  iteration-pin: lifter errored"); return bad + 1
    il = {l["func"]: l for l in json.loads(lifted4.read_text())}
    asc = {q["kind"] for q in c_choose.plans(il["asc_v0"])}
    desc = {q["kind"] for q in c_choose.plans(il["desc_v0"])}
    # The WITNESS is the contrast: identical bodies, opposite directions. If the
    # lifter ever stops distinguishing them, both answers converge and this
    # fails — no monkeypatching required.
    ok = ("dead-store" in asc and desc == {"refuse"}
          and any("iteration.unparsed_header" in u
                  for u in il["desc_v0"]["unhandled"]))
    bad += 0 if ok else 1
    print(f"  {'asc/desc_v0':<16}{'1/-1':>5}  {'+'.join(sorted(asc)):<24}"
          f"{'n/a':<10} descending -> {'+'.join(sorted(desc))}"
          + ("" if ok else "  — EXPECTED dead-store vs refuse"))

    # LIE-DETECTION: the pins must be load-bearing. Forcing step to 1 restores
    # the pre-fix assumption, and BOTH pins must then change.
    #
    # Comparing the offered SET alone is too weak, and this detector said so on
    # its first run: `unroll_pre_v0` offers {preload, distribute} either way —
    # what the step test changes is WHICH OFFSETS preload redirects. The
    # signature therefore carries the plan's payload, not just its kind.
    def signature(lp):
        out = []
        for q in c_choose.plans(lp):
            out.append((q["kind"], json.dumps(q.get("preload", q.get("dead", "")),
                                              sort_keys=True)))
        return sorted(out)

    moved = 0
    for name in EXPECT_STEP:
        lp = dict(loops[name]); lp["step"] = 1
        if signature(lp) != signature(loops[name]):
            moved += 1
    if moved != len(EXPECT_STEP):
        print(f"  lie-detection: only {moved}/{len(EXPECT_STEP)} pins move when "
              f"the step test is removed — fixture is not exercising it")
        bad += 1
    else:
        print(f"  lie-detection ok ({moved}/{len(EXPECT_STEP)} pins break when "
              f"the step test is removed)")
    return bad


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
                # log the candidate the gate actually SELECTED. Logging the
                # first one instead reported `preload` for s211/s1213, whose
                # winner is `distribute` — and turned two PASSes into FAILs.
                log_profit(name, e)
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
        bad += step_pins(c_choose, Path(td))
        bad += predication(c_choose, Path(td))
        profit_report()
    print(f"\nCHOOSE {'PASS' if bad == 0 else 'FAIL'}: decisions follow the "
          f"dependence graph; no accepted candidate is incorrect"
          + ("" if bad == 0 else f" ({bad} problem(s))"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
