#!/usr/bin/env python3
"""Reproduce arXiv:2502.11906's TSVC vectorization-rate methodology.

Paper's metric (Sec. II.B / III): 151 loop nests, one per function; a loop
counts as vectorized if the COMPILER REPORTS it so. Clang reports via
-Rpass=loop-vectorize. "we use the name of the containing function to refer
to a loop nest."

Paper's ARM setup: Clang 18.1.8 on Fujitsu A64FX, -O3 -mcpu=a64fx+sve
-msve-vector-bits=512  -> Clang vectorized 47% (GCC 56%, ACFL 54%; 60 loops
vectorized by NO compiler).

We cannot match that hardware: this M4 is NEON-128 with no SVE (verified).
So this reproduces the METHOD and yields OUR baseline, not their number.
"""
import re, subprocess, sys, pathlib, collections

KERNEL = re.compile(r'^(s\d|vif|vpv|vtv|vpvtv|vpvts|vpvpv|vtvtv|vsumr|vdotr|vbor)')

def rate(src, incs, flags, label, cc="clang"):
    cmd = [cc, "-O3", "-std=c99", "-w", *flags, "-c", str(src), "-o", "/dev/null",
           *[f"-I{i}" for i in incs],
           "-Rpass=loop-vectorize", "-Rpass-missed=loop-vectorize"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  {label}: BUILD FAILED\n{r.stderr[:400]}"); return None
    # Map each remark to the enclosing kernel function by scanning source lines.
    lines = src.read_text(errors="replace").splitlines()
    fn_at = {}
    cur = None
    for n, ln in enumerate(lines, 1):
        m = re.match(r'^(?:real_t|void|int)\s+(\w+)\s*\(', ln)
        if m: cur = m.group(1)
        fn_at[n] = cur
    vec, missed = set(), set()
    for line in r.stderr.splitlines():
        m = re.search(r':(\d+):\d+: remark: (vectorized loop|loop not vectorized)', line)
        if not m: continue
        fn = fn_at.get(int(m.group(1)))
        if not fn or not KERNEL.match(fn): continue
        (vec if m.group(2) == "vectorized loop" else missed).add(fn)
    total = len({f for f in fn_at.values() if f and KERNEL.match(f)})
    return dict(label=label, vec=len(vec), total=total,
                pct=100*len(vec)/total if total else 0,
                vecset=vec, missset=missed - vec)

STOCK = pathlib.Path("TSVC_2/src")
MOD   = pathlib.Path("tsvc_withArgs/tsvc")

# Apple M4: NEON only. `-mcpu=native` is the closest analogue to their
# -mcpu=a64fx+sve on hardware that has no SVE.
FLAGS = ["-mcpu=native"]

runs = []
for src, incs, label in [
    (STOCK/"tsvc.c", [STOCK], "stock TSVC_2 (compile-time constant sizes)"),
    (MOD/"loops.c",  [MOD],   "tsvc_withArgs (info withdrawn - paper's variant)"),
]:
    if not src.exists():
        print(f"  missing {src}"); continue
    res = rate(src, incs, FLAGS, label)
    if res: runs.append(res)

print(f"  {'variant':<50}{'vectorized':>12}{'of':>5}{'rate':>8}")
for r in runs:
    print(f"  {r['label']:<50}{r['vec']:>12}{r['total']:>5}{r['pct']:>7.1f}%")
print(f"\n  paper, Clang 18.1.8 on A64FX (SVE-512), info withdrawn:      71  151   47.0%")
print(f"  paper, GCC 14.1.1 same setup:                                85  151   56.0%")
print(f"  paper, ACFL 22.2 same setup:                                 82  151   54.0%")

if len(runs) == 2:
    a, b = runs
    delta = a['pct'] - b['pct']
    print(f"\n  === COST OF WITHDRAWING COMPILE-TIME INFORMATION ===")
    print(f"  {a['pct']:.1f}% -> {b['pct']:.1f}%   ({delta:+.1f} points, "
          f"{a['vec']-b['vec']} loops lost)")
    lost = sorted(a['vecset'] - b['vecset'])
    print(f"  loops that STOPPED vectorizing when the information was withdrawn ({len(lost)}):")
    print("    " + " ".join(lost[:40]))
    pathlib.Path("repro_lost.txt").write_text("\n".join(lost))
