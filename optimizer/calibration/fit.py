#!/usr/bin/env python3
"""Calibrate the cost model's constants against measured ground truth.

NOT a training loop. The model's FORM (`max(latency, throughput) + combine`)
stays hand-written and auditable in src/main.rs; only its two physical
constants are data, fitted here. Per U10: at a 5-candidate search space there
is nothing for a learned model to amortize, and the constants are physically
meaningful quantities that can be measured directly.

Two gates, per U10 (and per the convergent finding across Halide/AutoTVM/TenSet
that RANK accuracy, not regression accuracy, is what matters):
  1. PICK-CORRECTNESS (blocking) — on HELD-OUT kernels, the realization the
     model ranks first must be the one measured fastest.
  2. Fit quality (informational only, never gates promotion).

Usage:  uv run --with scipy --with numpy python3 fit.py [--promote]
"""
import json, pathlib, sys, datetime, subprocess
import numpy as np
from scipy.optimize import least_squares

HERE = pathlib.Path(__file__).resolve().parent

# Split declared UP FRONT, not chosen after seeing results.
TRAIN   = {"s312", "s317-noclosed"}
HELDOUT = {"s352"}

# A pick counts as correct if it is within the MEASUREMENT NOISE of the best.
# Justified, not chosen to pass: repeating the s352 benchmark three times gave
# i4-vs-i8 deltas of 0.5% / 2.4% / 0.0%, with the sign FLIPPING between runs —
# those two realizations are statistically indistinguishable on that kernel.
# Gating at 1.00x would be gating on thermal noise. 5% is conservative
# relative to the 2.4% worst observed spread.
NOISE_TOL = 0.05

def parse_kind(k):
    if k.startswith("Chain"): return ("chain", None, None)
    if k.startswith("Lanes"):
        import re
        m = re.search(r"w:\s*(\d+),\s*i:\s*(\d+)", k)
        return ("lanes", int(m.group(1)), int(m.group(2)))
    return (None, None, None)   # PowI/Scale: O(1), exercise neither constant

# Per-element source cost, mirroring src_cost() in src/main.rs.
SRC_COST = {"s312": 1.0, "s317-noclosed": 0.0, "s317": 0.0, "s352": 2.0}

def model_cycles(kind, w, i, n, per, mul_lat, lanes_per_cyc):
    """Mirror of model() in src/main.rs. Keep these two in sync BY HAND —
    if they drift, the calibration is fitting a formula the optimizer does
    not use, which is worse than not calibrating at all."""
    if kind == "chain":
        return n * (mul_lat + per)
    chains = w * i
    latency    = (n / chains) * mul_lat
    throughput = n * (1.0 + per) / lanes_per_cyc
    combine    = (chains - 1) * mul_lat
    return max(latency, throughput) + combine

def load():
    rows = []
    for line in open(HERE / "measurements.jsonl"):
        d = json.loads(line)
        kind, w, i = parse_kind(d["kind"])
        if kind is None:            # closed-form rows carry no constant info
            continue
        if not d.get("cyc_per_call"):
            continue           # pre-counter rows: no cycle data, skip
        rows.append(dict(kernel=d["kernel"], n=d["extent"], kind=kind, w=w, i=i,
                         ns=d["measured_ms"] * 1e6 / d["reps"],
                         cyc=d["cyc_per_call"],
                         per=SRC_COST.get(d["kernel"], 1.0)))
    return rows

def residuals(p, rows):
    mul_lat, lanes_per_cyc = p
    out = []
    for r in rows:
        pred_ns = model_cycles(r["kind"], r["w"], r["i"], r["n"], r["per"],
                               mul_lat, lanes_per_cyc)
        # Weight toward the FAST candidates (Halide's throughput-weighted loss,
        # Ansor's w_p = y): a model that ranks the slow ones perfectly and the
        # fast ones badly picks wrong, which is the only failure that matters.
        out.append((pred_ns - r["cyc"]) / r["cyc"])   # cycles vs cycles
    return out

def picks(rows, p):
    """Model's pick vs measured-fastest, per kernel."""
    mul_lat, lanes_per_cyc = p
    by = {}
    for r in rows:
        by.setdefault(r["kernel"], []).append(r)
    out = {}
    for k, rs in by.items():
        pick = min(rs, key=lambda r: model_cycles(r["kind"], r["w"], r["i"],
                    r["n"], r["per"], mul_lat, lanes_per_cyc))
        best = min(rs, key=lambda r: r["ns"])
        label = lambda r: r["kind"] if r["kind"] == "chain" else f"lanes w{r['w']} i{r['i']}"
        ratio = pick["ns"] / best["ns"]
        out[k] = (label(pick), label(best), ratio <= 1.0 + NOISE_TOL, ratio)
    return out

def main():
    rows = load()
    train = [r for r in rows if r["kernel"] in TRAIN]
    held  = [r for r in rows if r["kernel"] in HELDOUT]
    if not train:
        sys.exit("no training rows — run bench/run.py first")

    p0 = [4.0, 8.0]          # the uncalibrated ASSUMPTION constants
    print(f"  training rows: {len(train)} from {sorted(TRAIN)}")
    print(f"  held-out rows: {len(held)} from {sorted(HELDOUT)}  (never fitted)")

    before = picks(rows, p0)
    fit = least_squares(residuals, p0, args=(train,),
                        bounds=([0.5, 1.0], [32.0, 64.0]))
    mul_lat, lanes_per_cyc = fit.x
    after = picks(rows, fit.x)

    print(f"\n  {'constant':<20}{'before':>10}{'after':>10}")
    print(f"  {'mul_latency':<20}{p0[0]:>10.2f}{mul_lat:>10.2f}")
    print(f"  {'lanes_per_cycle':<20}{p0[1]:>10.2f}{lanes_per_cyc:>10.2f}")
    # No clock parameter any more: ri_cycles is measured in the model's own
    # unit. The physical sanity check is now on the constants themselves.
    lat_ok  = 2.0 <= mul_lat <= 6.0        # NEON fp multiply latency
    thru_ok = 4.0 <= lanes_per_cyc <= 32.0 # f32 lanes retired per cycle
    print(f"  mul_latency    {'plausible' if lat_ok else 'IMPLAUSIBLE'} for NEON fp multiply")
    print(f"  lanes_per_cyc  {'plausible' if thru_ok else 'IMPLAUSIBLE'} "
          f"(= {lanes_per_cyc/4:.1f} x 4-wide NEON ops/cycle)")

    print(f"\n  {'kernel':<16}{'split':<10}{'model pick':<16}{'measured best':<16}{'':<3}")
    ok_held = True
    for k in sorted(after):
        split = "train" if k in TRAIN else ("HELD-OUT" if k in HELDOUT else "-")
        pick, best, hit, cost = after[k]
        b_hit = before[k][2]
        arrow = "" if b_hit == hit else ("  (fixed)" if hit else "  (BROKE)")
        print(f"  {k:<16}{split:<10}{pick:<16}{best:<16}{'ok' if hit else f'WRONG {cost:.2f}x'}{arrow}")
        if k in HELDOUT and not hit:
            ok_held = False

    n_before = sum(1 for k in before if before[k][2])
    n_after  = sum(1 for k in after  if after[k][2])
    print(f"\n  pick-correctness: {n_before}/{len(before)} -> {n_after}/{len(after)}")
    print(f"  HELD-OUT GATE: {'PASS' if ok_held else 'FAIL — do not promote'}")

    if "--promote" not in sys.argv:
        print("\n  (dry run — pass --promote to write constants.toml)")
        return
    if not ok_held:
        sys.exit("\n  refusing to promote: held-out pick-correctness FAILED")

    sha = subprocess.run(["git","rev-parse","--short","HEAD"],
                         capture_output=True, text=True).stdout.strip() or "uncommitted"
    date = datetime.date.today().isoformat()
    (HERE/"constants.toml").write_text(f'''# Calibrated {date} on Apple M4, clang 17 -O3 -march=native.
# Fitted by calibration/fit.py against measurements.jsonl (weighted least
# squares, weight = 1/measured, per Halide/Ansor's throughput-weighted loss).
# These are DATA. The model's FORM lives in src/main.rs and is not fitted.
version = "v1"
mul_latency_cycles = {mul_lat:.4f}   # was 4.0, an unmeasured ASSUMPTION
lanes_per_cycle    = {lanes_per_cyc:.4f}   # was 8.0, an unmeasured ASSUMPTION
fit_target         = "measured cycles (ri_cycles), not wall time"
machine     = "Apple-M4"
git_sha     = "{sha}"
fit_train   = {sorted(TRAIN)}
fit_heldout = {sorted(HELDOUT)}
''')
    with open(HERE/"HISTORY.md", "a") as fh:
        fh.write(f"- {date} `v1` sha={sha} | train={sorted(TRAIN)} heldout={sorted(HELDOUT)} "
                 f"| mul_latency {p0[0]}->{mul_lat:.2f}, lanes_per_cycle {p0[1]}->{lanes_per_cyc:.2f} "
                 f"| pick-correctness {n_before}/{len(before)}->{n_after}/{len(after)} "
                 f"| held-out gate PASS\n")
    print(f"\n  promoted -> calibration/constants.toml")

if __name__ == "__main__":
    main()
