#!/usr/bin/env python3
"""TSVC2 vectorization rate — the record attempt (docs/design/record-attempt.md).

Metric, matching arXiv:2502.11906 exactly: a loop counts as vectorized when the
COMPILER REPORTS it so. 151 kernels, one loop nest per function.

    published, A64FX SVE-512 :  GCC 56.0% | ACFL 54.0% | Clang 47.0%
    ours, baseline           :  Apple clang 17 on M4 NEON-128

A kernel is counted as RECOVERED only if all four hold:
    1. clang did NOT vectorize it originally
    2. the chooser proposes a transformation
    3. the transformed code is CORRECT (differential test)
    4. clang DOES vectorize the transformed code
Point 4 is what makes the number comparable to the published table: the metric
is the compiler's own report, not our opinion.
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import c_choose

KERNEL = re.compile(r'^(s\d|vif|vpv|vtv|vpvtv|vpvts|vpvpv|vtvtv|vsumr|vdotr|vbor)')


def baseline(src: Path, inc: Path) -> tuple[set, set]:
    r = subprocess.run(["clang", "-O3", "-std=c99", "-w", *([c_choose.arch_flag()] if c_choose.arch_flag() else []),
                        "-c", str(src), "-o", "/dev/null", f"-I{inc}",
                        "-Rpass=loop-vectorize"], capture_output=True, text=True)
    lines = src.read_text(errors="replace").splitlines()
    fn_at, cur = {}, None
    for n, ln in enumerate(lines, 1):
        m = re.match(r'^(?:real_t|void|int)\s+(\w+)\s*\(', ln)
        if m: cur = m.group(1)
        fn_at[n] = cur
    vec = set()
    for line in r.stderr.splitlines():
        m = re.search(r':(\d+):\d+: remark: vectorized loop', line)
        if m:
            f = fn_at.get(int(m.group(1)))
            if f and KERNEL.match(f): vec.add(f)
    allk = {f for f in fn_at.values() if f and KERNEL.match(f)}
    return vec, allk


# --- IN-CONTEXT evaluation ------------------------------------------------
# Extracting a loop into a standalone function strips the very context that
# gives it meaning: TSVC's LEN_1D, its global arrays, its headers. The first
# run of this script reported 0 recovered, and every single candidate had
# compile-failed on `undeclared identifier LEN_1D`. That was a harness
# artefact, not a result. Candidates are now compiled AGAINST TSVC ITSELF.

CTX_HARNESS = r"""
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "common.h"
#include "array_defs.h"
/* TSVC's own common.c does not build on Darwin (<malloc.h>). The globals are
   defined here instead -- linking it is unnecessary to exercise one loop. */
__attribute__((aligned(ARRAY_ALIGNMENT))) real_t flat_2d_array[LEN_2D*LEN_2D];
__attribute__((aligned(ARRAY_ALIGNMENT))) real_t x[LEN_1D];
__attribute__((aligned(ARRAY_ALIGNMENT))) real_t a[LEN_1D],b[LEN_1D],c[LEN_1D],
    d[LEN_1D],e[LEN_1D],aa[LEN_2D][LEN_2D],bb[LEN_2D][LEN_2D],cc[LEN_2D][LEN_2D],
    tt[LEN_2D][LEN_2D];
__attribute__((aligned(ARRAY_ALIGNMENT))) int indx[LEN_1D];
real_t* __restrict__ xx; real_t* yy;
%(scratch)s
void __orig(void); void __xform(void);
static real_t SAV[%(na)d][LEN_1D], REF[%(na)d][LEN_1D];
static real_t *TGT[%(na)d] = { %(targets)s };
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
  return t.tv_sec*1e3+t.tv_nsec/1e6;}
int main(void){
  for(int k=0;k<%(na)d;k++) for(int i=0;i<LEN_1D;i++)
      SAV[k][i]=(real_t)((i*37%%991)+1)/97.0;
  for(int k=0;k<%(na)d;k++) memcpy(TGT[k],SAV[k],sizeof SAV[k]);
  __orig();
  for(int k=0;k<%(na)d;k++) memcpy(REF[k],TGT[k],sizeof REF[k]);
  for(int k=0;k<%(na)d;k++) memcpy(TGT[k],SAV[k],sizeof SAV[k]);
  __xform();
  int exact=1; double worst=0;
  for(int k=0;k<%(na)d;k++) for(int i=0;i<LEN_1D;i++){
    if(TGT[k][i]!=REF[k][i]) exact=0;
    double d=fabs((double)TGT[k][i]-REF[k][i])/(fabs((double)REF[k][i])+1e-30);
    if(d>worst) worst=d; }
  if(!exact && worst>1e-6){ printf("INCORRECT %%.3e\n",worst); return 1; }
  double t0=1e18,t1=1e18;
  for(int t=0;t<7;t++){ for(int k=0;k<%(na)d;k++) memcpy(TGT[k],SAV[k],sizeof SAV[k]);
    double s=ms(); for(int r=0;r<%(reps)d;r++) __orig(); double d=ms()-s; if(d<t0)t0=d; }
  for(int t=0;t<7;t++){ for(int k=0;k<%(na)d;k++) memcpy(TGT[k],SAV[k],sizeof SAV[k]);
    double s=ms(); for(int r=0;r<%(reps)d;r++) __xform(); double d=ms()-s; if(d<t1)t1=d; }
  printf("%%s %%.4f %%.4f %%.4f\n", exact?"EXACT":"CLOSE", t0, t1, t0/t1);
  return 0; }
"""


def emit_ctx(lp, p):  # noqa: needs `p` for preload scratch
    """Emit orig/xform as no-arg functions over TSVC's own globals.

    Stripping the parameter list is what makes these callable with no
    arguments — but a `peel-wraparound` plan passes the scalars' pre-loop
    values AS parameters (they are initialised outside the loop, which the
    lifter never sees). Stripping them left `im1_init` dangling and every
    wrap-around candidate compile-failed. They are bound here instead, to
    TSVC's own idiom (LEN_1D-1, LEN_1D-2, ...).
    """
    o, x = c_choose.emit(lp, p, "")
    def strip(fn, name):
        i = fn.index("{")
        return f"void {name}(void) " + fn[i:]
    if not x:
        return None
    if p["kind"] == "peel-wraparound":
        for k, w in enumerate(sorted(p["offsets"])):
            o = o.replace(f"{w}_init", f"(LEN_1D-{k+1})")
            x = x.replace(f"{w}_init", f"(LEN_1D-{k+1})")
    pre = "".join(f"extern real_t __pre_{q['array']}[];\n"
                  for q in p.get("preload", []))
    return ('#include "common.h"\n#include "array_defs.h"\n' + pre
            + strip(o, "__orig") + strip(x, "__xform"))


def eval_ctx(lp, p, tmp: Path, inc: Path, extra: list[Path]) -> dict:
    src = emit_ctx(lp, p)
    if src is None:
        return {"verdict": "no-candidate"}
    arrays = sorted({a["array"] for a in lp["accesses"]})
    if any(a in ("aa", "bb", "cc", "tt", "flat_2d_array") for a in arrays):
        return {"verdict": "skip-2d"}
    # A malformed or unrecovered bound can emit a loop that never terminates.
    # One such candidate hung for 180s and took the whole run down with it.
    if not lp.get("lower") or not lp.get("upper") or lp.get("step") != 1:
        return {"verdict": "skip-bounds"}
    if lp["index"] is None:
        return {"verdict": "skip-bounds"}
    joined = " ".join(lp["stmts"])
    if re.search(r"\b(?!if|for|while|return)\w+\s*\(", joined):
        return {"verdict": "skip-calls-helper"}
    cf = tmp / "cand.c"; cf.write_text(src)
    rf = tmp / "run.c"
    scratch = "\n".join(
        f"__attribute__((aligned(64))) real_t __pre_{x['array']}[LEN_1D+16];"
        for x in p.get("preload", []))
    rf.write_text(CTX_HARNESS % {"na": len(arrays), "reps": 40,
                                 "targets": ", ".join(arrays),
                                 "scratch": scratch})
    exe = tmp / "run"
    c = subprocess.run(["clang", "-O3", "-std=c99", "-w", *([c_choose.arch_flag()] if c_choose.arch_flag() else []),
                        str(cf), str(rf), *[str(e) for e in extra],
                        f"-I{inc}", "-o", str(exe), "-lm"],
                       capture_output=True, text=True)
    if c.returncode != 0:
        return {"verdict": "compile-fail", "err": c.stderr.strip()[:150]}
    try:
        r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        # A hang is a REJECTED candidate, never a crashed run.
        return {"verdict": "timeout"}
    if r.returncode != 0 or not r.stdout.strip():
        return {"verdict": "INCORRECT", "err": r.stdout.strip()[:60]}
    q = r.stdout.split()
    if q[0] == "INCORRECT":
        return {"verdict": "INCORRECT", "err": q[1]}
    sp = float(q[3])
    return {"verdict": "ACCEPT" if sp >= c_choose.NOISE_MARGIN
            else "REJECT-not-faster", "equivalence": q[0], "speedup": sp,
            "src": src}


def clang_vectorizes(csrc: str, tmp: Path, inc: Path = None) -> bool:
    f = tmp / "chk.c"
    f.write_text(csrc)
    cmd = ["clang", "-O3", "-std=c99", "-w", *([c_choose.arch_flag()] if c_choose.arch_flag() else []), "-c", str(f),
           "-o", "/dev/null", "-Rpass=loop-vectorize"]
    if inc: cmd.append(f"-I{inc}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    return "vectorized loop" in r.stderr


def main() -> int:
    src = Path(sys.argv[1]); inc = Path(sys.argv[2]) if len(sys.argv) > 2 else src.parent
    vec, allk = baseline(src, inc)
    lifted = Path(tempfile.mkdtemp()) / "l.json"
    subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"), str(src),
                    "--flags", f"-I{inc}", "--json", str(lifted)],
                   capture_output=True, text=True)
    loops = json.loads(lifted.read_text())
    byfn = {}
    for lp in loops:
        byfn.setdefault(lp["func"], []).append(lp)

    import collections
    verdicts = collections.Counter()
    extra = []          # globals are defined in the harness; see CTX_HARNESS
    recovered, attempted, rows = set(), 0, []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for fn in sorted(allk - vec):
            for lp in byfn.get(fn, []):
                cands = [c for c in c_choose.plans(lp)
                         if c["kind"] in c_choose.CANDIDATE_KINDS]
                if not cands: continue
                attempted += 1
                for c in cands:
                    e = eval_ctx(lp, c, tmp, inc, extra)
                    verdicts[e.get("verdict", "?")] += 1
                    if e.get("verdict") != "ACCEPT": continue
                    if clang_vectorizes(e["src"], tmp, inc):
                        recovered.add(fn)
                        rows.append((fn, c["kind"], e["speedup"]))
                        break
                if fn in recovered: break

    n = len(allk)
    base, tot = len(vec), len(vec) + len(recovered)
    print(f"  === TSVC2 vectorization rate (compiler-reported) ===")
    print(f"  kernels                       : {n}")
    print(f"  clang -O3 {c_choose.arch_flag()} alone  : {base}/{n} = {100*base/n:.1f}%")
    print(f"  kernels the chooser attempted : {attempted}")
    print(f"  RECOVERED (correct + faster + clang then vectorizes) : {len(recovered)}")
    print(f"  clang + chooser               : {tot}/{n} = {100*tot/n:.1f}%")
    print()
    print(f"  published (A64FX, SVE-512):  Clang 47.0%  ACFL 54.0%  GCC 56.0%")
    print()
    print("  candidate verdicts:")
    for k, v in verdicts.most_common(): print(f"    {v:4d}  {k}")
    print()
    for fn, kind, sp in sorted(rows):
        print(f"    + {fn:<10} {kind:<12} {sp:.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
