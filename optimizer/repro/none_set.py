#!/usr/bin/env python3
"""Compute OUR analogue of the paper's "None: 60" — loops that NO compiler
vectorizes. The paper used GCC + Clang + ACFL on A64FX; we have GCC 16 and
Apple clang 17 on M4/NEON (ACFL is Linux/ARM only), so this is a two-compiler
intersection on different hardware. Directionally the same experiment.
"""
import re, subprocess, pathlib, collections, json

SRC = "tsvc_withArgs/tsvc/loops.c"
INC = "tsvc_withArgs/tsvc"
KERNEL = re.compile(r'^(s\d|vif|vpv|vtv|vpvtv|vpvts|vpvpv|vtvtv|vsumr|vdotr|vbor)')

lines = pathlib.Path(SRC).read_text(errors="replace").splitlines()
fn_at, cur = {}, None
for n, ln in enumerate(lines, 1):
    m = re.match(r'^(?:real_t|void|int)\s+(\w+)\s*\(', ln)
    if m: cur = m.group(1)
    fn_at[n] = cur
ALL = sorted({f for f in fn_at.values() if f and KERNEL.match(f)})

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stderr

# clang
cl = run(["clang","-O3","-std=c99","-w","-mcpu=native","-c",SRC,"-o","/dev/null",
          f"-I{INC}","-Rpass=loop-vectorize","-Rpass-analysis=loop-vectorize"])
clang_vec, clang_why = set(), collections.defaultdict(set)
for line in cl.splitlines():
    m = re.search(r':(\d+):\d+: remark: (.*?)(?:\[|$)', line)
    if not m: continue
    fn = fn_at.get(int(m.group(1)))
    if not fn or not KERNEL.match(fn): continue
    txt = m.group(2).strip()
    if txt.startswith("vectorized loop"): clang_vec.add(fn)
    elif txt.startswith("loop not vectorized:"):
        clang_why[fn].add(txt.replace("loop not vectorized:","").strip())

# gcc
gc = run(["gcc-16","-O3","-std=c99","-w","-mcpu=native","-c",SRC,"-o","/dev/null",
          f"-I{INC}","-fopt-info-vec-all"])
gcc_vec = set()
for line in gc.splitlines():
    m = re.search(r':(\d+):\d+: optimized: loop vectorized', line)
    if not m: continue
    fn = fn_at.get(int(m.group(1)))
    if fn and KERNEL.match(fn): gcc_vec.add(fn)

none = sorted(set(ALL) - clang_vec - gcc_vec)
print(f"  total kernels          : {len(ALL)}")
print(f"  clang vectorized       : {len(clang_vec)}  ({100*len(clang_vec)/len(ALL):.1f}%)")
print(f"  gcc-16 vectorized      : {len(gcc_vec)}  ({100*len(gcc_vec)/len(ALL):.1f}%)")
print(f"  either one vectorized  : {len(clang_vec|gcc_vec)}")
print(f"  NEITHER  ('None' set)  : {len(none)}  ({100*len(none)/len(ALL):.1f}%)")
print(f"  paper's None on A64FX  : 60  (39.7%)  [3 compilers]")

CLASS = {
 "unsafe dependent memory operations": "CLASS-2 dependence",
 "cannot identify array bounds": "CLASS-2 dependence",
 "value that could not be identified as reduction": "CLASS-2 recognition",
 "cannot prove it is safe to reorder floating-point": "CLASS-1 numeric",
 "could not determine number of loop iterations": "dynamic bounds",
 "control flow cannot be substituted": "control flow",
 "loop contains a switch": "control flow",
 "loop control flow is not understood": "control flow",
 "call instruction cannot be vectorized": "opaque call",
 "instruction cannot be vectorized": "opaque op",
}
PRIO = list(CLASS)
buckets = collections.defaultdict(list)
for fn in none:
    rs = clang_why.get(fn, set())
    pick = next((p for p in PRIO for r in rs if r.startswith(p)), None)
    buckets[CLASS.get(pick, "unattributed")].append(fn)
print(f"\n  === the None set, by clang's stated reason ===")
for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(v):3d}  {k}")
    print(f"       {' '.join(sorted(v))}")
json.dump({k: sorted(v) for k, v in buckets.items()}, open("none_set.json","w"), indent=1)
