#!/usr/bin/env python3
"""Does the FASTEST realization differ from the most ENERGY-EFFICIENT one?

If it never does, an energy objective buys nothing and the idea is dead.
If it does, then "which realization is best" has no answer independent of
the declared objective — which is precisely what a semantic optimizer with
declared intent is positioned to exploit, and what a fixed compiler heuristic
cannot express.
"""
import json, pathlib
d = json.load(open(pathlib.Path(__file__).parent / "results.json"))

disagree = 0
for k, kd in d.items():
    vs = [v for v in kd["variants"] if v["ok"] and v.get("nj_per_call")]
    if not vs:
        continue
    fastest = min(vs, key=lambda v: v["ms"])
    greenest = min(vs, key=lambda v: v["nj_per_call"])
    # energy-delay product: the standard joint metric when neither dominates
    edp = min(vs, key=lambda v: v["nj_per_call"] * v["ms"])

    print(f"\n=== {k} ===")
    print(f"  {'realization':<22}{'ms':>8}{'nJ/call':>11}{'uW·s':>9}"
          f"{'cyc/call':>11}{'IPC':>6}{'nJ/cyc':>9}")
    for v in sorted(vs, key=lambda v: v["ms"]):
        ipc = v["ins_per_call"] / v["cyc_per_call"] if v["cyc_per_call"] else 0
        njc = v["nj_per_call"] / v["cyc_per_call"] if v["cyc_per_call"] else 0
        tag = ""
        if v is fastest:  tag += " FASTEST"
        if v is greenest: tag += " GREENEST"
        print(f"  {v['kind']:<22}{v['ms']:>8.2f}{v['nj_per_call']:>11.0f}"
              f"{v['nj_per_call']/1000:>9.1f}{v['cyc_per_call']:>11.0f}"
              f"{ipc:>6.2f}{njc:>9.3f}{tag}")

    same = fastest["kind"] == greenest["kind"]
    if not same:
        disagree += 1
        pen_t = greenest["ms"] / fastest["ms"]
        pen_e = fastest["nj_per_call"] / greenest["nj_per_call"]
        print(f"  -> OBJECTIVES DISAGREE")
        print(f"     fastest  : {fastest['kind']}  costs {pen_e:.2f}x the energy of the greenest")
        print(f"     greenest : {greenest['kind']}  costs {pen_t:.2f}x the time of the fastest")
        print(f"     best EDP : {edp['kind']}")
    else:
        print(f"  -> objectives agree ({fastest['kind']} wins both)")

    # totals vs the two compiler baselines
    print(f"     clang -O3        {kd['ref_ms']:>7.2f} ms {kd['ref_nj']:>10.0f} nJ")
    print(f"     clang -ffast-math{kd['rival_ms']:>7.2f} ms {kd['rival_nj']:>10.0f} nJ")
    best_e = greenest["nj_per_call"]
    print(f"     best licensed    {greenest['ms']:>7.2f} ms {best_e:>10.0f} nJ"
          f"   ({kd['ref_nj']/best_e:.1f}x less energy than -O3,"
          f" {kd['rival_nj']/best_e:.2f}x vs -ffast-math)")

print(f"\n== objectives disagreed on {disagree}/{len(d)} kernels ==")
