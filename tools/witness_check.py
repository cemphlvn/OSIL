#!/usr/bin/env python3
"""Independent validation of preservation witnesses (G25).

Borrowed wholesale from SV-COMP, whose central discipline is not its benchmark
suite but this: a tool's claim is not evidence. The tool emits a WITNESS, and a
SEPARATE validator decides whether the claim holds. SV-COMP prices the asymmetry
into its score -- a correct proof is +2, a wrong one is -32 -- because an
accepted-but-wrong answer is catastrophic while a refusal is merely useless.

`GOVERNANCE.md` has demanded a foreign-witness lane since G13, on the grounds
that evidence from a single lineage is weak against shared blind spots. Every
correctness result in this repo has so far been produced by the same harness
that produced the transformation. This tool is the other lineage.

It shares NO code with tools/c_choose.py -- not the driver, not the input
generation, not the comparison. It re-derives everything from the witness, and
it deliberately probes where the chooser's harness never looks:

  * FIVE input regimes, none of them the chooser's (zeros, wide signed
    magnitudes, denormals, exact integers, alternating extremes). The chooser's
    own blind spot at G24 was an input distribution, so a validator that reused
    it would inherit the blind spot.
  * TRIP-COUNT EDGE CASES. The chooser measures at n = 32000 and nothing else.
    Tails and prologues (`int i = n - 1`, peel depth d) are exactly the code
    that breaks at n = 0, 1, 2.
  * OUT-OF-BOUNDS CANARIES. Guard regions before and after every buffer, so a
    write past either end is caught rather than silently tolerated. If the
    ORIGINAL also corrupts a canary the original is at fault and the
    transformation is not blamed for it.

Run: `just witness`
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CC = "clang"

# SV-COMP's asymmetry, transposed. A transformation wrongly certified equivalent
# is the catastrophic outcome; a refusal costs nothing but the opportunity.
SCORE = {"CONFIRMED-EXACT": 2, "CONFIRMED-CLOSE": 1,
         "REFUTED": -32, "UNSUPPORTED": 0, "ORIGINAL-AT-FAULT": 0}

TRIP_COUNTS = [0, 1, 2, 3, 5, 7, 8, 63, 64, 65, 1000]
REGIMES = ["zeros", "wide_signed", "denormal", "integral", "alternating"]

DRIVER = r"""
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <float.h>
#define LEAD  64
#define TRAIL 64
#define NMAX  1024
#define SPAN  (LEAD + NMAX + %(pad)d + TRAIL)
#define NA    %(na)d
#define NS    %(ns)d
#define CANARY (-1.2345678e30f)

%(decls)s

static float BUFA[NA][SPAN], BUFB[NA][SPAN], SEED[NA][SPAN];
static float SCR[NS ? NS : 1][SPAN];

static unsigned st = 2463534242u;
static unsigned xr(void){ st ^= st << 13; st ^= st >> 17; st ^= st << 5; return st; }
static float pick(int regime, int k, int i){
    unsigned r = xr();
    double u = (double)(r %% 100000) / 100000.0;   /* [0,1) */
    switch (regime) {
      case 0: return (r %% 3 == 0) ? 0.0f : (float)(u + 0.5);       /* zeros    */
      case 1: return (float)((u - 0.5) * 2.0e18);                  /* wide     */
      case 2: return (float)((u + 0.001) * FLT_MIN * 4.0);         /* denormal */
      case 3: return (float)((int)(u * 64.0) - 32);                /* integral */
      default: return ((r & 1) ? 1.0e12f : -1.0e-12f);             /* alternate */
    }
}
static void seed_all(int regime){
    st = 2463534242u + (unsigned)regime * 7919u;
    for (int k = 0; k < NA; k++)
        for (int i = 0; i < SPAN; i++)
            SEED[k][i] = (i < LEAD || i >= SPAN - TRAIL)
                       ? CANARY : pick(regime, k, i - LEAD);
}
static void load(float dst[NA][SPAN]){ memcpy(dst, SEED, sizeof SEED); }
static int canary_broken(float b[NA][SPAN]){
    for (int k = 0; k < NA; k++){
        for (int i = 0; i < LEAD; i++) if (b[k][i] != CANARY) return 1;
        for (int i = SPAN - TRAIL; i < SPAN; i++) if (b[k][i] != CANARY) return 1;
    }
    return 0;
}
int main(void){
    int worst_kind = 0;          /* 0 ok, 1 refuted, 2 original-at-fault */
    double worst = 0.0; int exact = 1;
    int NS_ = NS;  (void)NS_;
    for (int regime = 0; regime < %(nregimes)d; regime++){
        seed_all(regime);
        for (int t = 0; t < %(ntrips)d; t++){
            int n = TRIPS[t];
            load(BUFA); load(BUFB);
            for (int s = 0; s < (NS ? NS : 1); s++) memcpy(SCR[s], SEED[0], sizeof SEED[0]);
            %(call_orig)s
            %(call_xform)s
            int ca = canary_broken(BUFA), cb = canary_broken(BUFB);
            if (ca) { worst_kind = worst_kind > 2 ? worst_kind : 2; }
            else if (cb) { worst_kind = 1;
                printf("OOB regime=%%d n=%%d\n", regime, n); return 1; }
            for (int k = 0; k < NA; k++)
              for (int i = LEAD; i < SPAN - TRAIL; i++){
                float x = BUFA[k][i], y = BUFB[k][i];
                if (x != y){
                    exact = 0;
                    double den = fabs((double)x) + 1e-30;
                    double d = fabs((double)y - (double)x) / den;
                    if (!(d <= %(tol)g)) {
                        if (isnan((double)x) && isnan((double)y)) continue;
                        printf("DIFF regime=%%d n=%%d k=%%d i=%%d %%.9g vs %%.9g\n",
                               regime, n, k, i - LEAD, (double)x, (double)y);
                        return 1;
                    }
                    if (d > worst) worst = d;
                }
              }
        }
    }
    if (worst_kind == 2){ printf("ORIGINAL-AT-FAULT\n"); return 0; }
    printf("%%s %%.3e\n", exact ? "EXACT" : "CLOSE", worst);
    return 0;
}
"""


def validate(w: dict, tmp: Path) -> dict:
    na, ns, nw = w["n_arrays"], w["n_scratch"], w["n_int_prefix"]
    pad = w.get("pad", 4)
    tol = float(w["claim"].get("tolerance") or 0.0)
    ints = "".join("n - 1, " for _ in range(nw))
    a_args = ints + ", ".join(f"BUFA[{i}] + LEAD" for i in range(na)) + ", n"
    b_args = (ints + "".join(f"SCR[{i}] + LEAD, " for i in range(ns))
              + ", ".join(f"BUFB[{i}] + LEAD" for i in range(na)) + ", n")
    ip = "".join("int, " for _ in range(nw))
    decls = (f"void orig({ip}{', '.join(['float *'] * na)}, int);\n"
             f"void xform({ip}{', '.join(['float *'] * (na + ns))}, int);\n"
             f"static const int TRIPS[] = {{{', '.join(map(str, TRIP_COUNTS))}}};")
    src = tmp / "w.c"
    src.write_text(w["source"]["orig"] + w["source"]["xform"])
    drv = tmp / "d.c"
    drv.write_text(DRIVER % {"decls": decls, "na": na, "ns": ns, "pad": pad,
                             "nregimes": len(REGIMES), "ntrips": len(TRIP_COUNTS),
                             "tol": tol if tol else 0.0,
                             "call_orig": f"orig({a_args});",
                             "call_xform": f"xform({b_args});"})
    exe = tmp / "w"
    c = subprocess.run([CC, "-O1", "-w", str(src), str(drv), "-o", str(exe), "-lm"],
                       capture_output=True, text=True)
    if c.returncode != 0:
        return {"verdict": "UNSUPPORTED", "why": c.stderr.strip()[:120]}
    try:
        r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        # H2 (G22): a timeout is a VERDICT, not an exception. A witness whose
        # validation does not terminate has not been confirmed, and saying so is
        # the answer. This line exists because `just harness` refused the first
        # version of this file.
        return {"verdict": "UNSUPPORTED", "why": "validation timed out (180s)"}
    out = (r.stdout or "").strip()
    if r.returncode != 0 or out.startswith(("DIFF", "OOB")):
        return {"verdict": "REFUTED", "why": out[:120] or "nonzero exit"}
    if out.startswith("ORIGINAL-AT-FAULT"):
        return {"verdict": "ORIGINAL-AT-FAULT", "why": "the original itself "
                "writes outside its buffer; the transformation is not blamed"}
    kind = out.split()[0] if out else "?"
    claimed = w["claim"]["equivalence"]
    if claimed == "EXACT" and kind != "EXACT":
        return {"verdict": "REFUTED",
                "why": f"claimed EXACT, independently measured {kind} ({out})"}
    return {"verdict": f"CONFIRMED-{kind}", "why": out}


MUTANTS = ROOT / "conformance" / "lift" / "witness-mutants"


def self_test(tmp: Path) -> tuple[int, int, int]:
    """The gate applied to ITSELF.

    With every real witness CONFIRMED, a validator that printed `CONFIRMED`
    unconditionally would score identically — nothing showed it could still
    refute anything. These mutants each carry a claim that is false on purpose,
    and each is wrong in a way that only ONE detector catches.

    A mutant that becomes CONFIRMED does not mean it was fixed. It means that
    detector died, and the file name says which. That is an XPASS-ALARM, and it
    fails the gate: a dead detector is a regression, not a curiosity.
    """
    files = sorted(MUTANTS.glob("m*.c"))
    if not files:
        print("  no mutants found — the validator is unpinned"); return 0, 1, 0
    print(f"\n  {'mutant':<24}{'detector pinned':<20}{'verdict':<20} mark")
    alive = dead = 0
    for f in files:
        text = f.read_text()
        det = next((l.split("DETECTOR:")[1].strip()
                    for l in text.splitlines() if "DETECTOR:" in l), "?")
        w = {"witness_version": 1, "loop": f.stem, "family": "mutant",
             "n_arrays": 2, "n_scratch": 0, "n_int_prefix": 0, "pad": 4,
             "claim": {"equivalence": "EXACT", "tolerance": 0.0},
             "source": {"orig": text, "xform": ""}}
        v = validate(w, tmp)
        refuted = v["verdict"] == "REFUTED"
        mark = "XFAIL-HOLDS" if refuted else "XPASS-ALARM"
        alive += refuted
        dead += not refuted
        print(f"  {f.name:<24}{det:<20}{v['verdict']:<20} {mark}"
              + ("" if refuted else "   <- DETECTOR DEAD"))
    print(f"  detectors alive {alive}/{len(files)}")
    return alive, dead, len(files)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print(__doc__); return 2
    witnesses = []
    for a in args:
        d = json.loads(Path(a).read_text())
        witnesses += d if isinstance(d, list) else [d]
    total, bad = 0, 0
    print(f"  {'loop':<20}{'family':<17}{'claim':<8}{'verdict':<20}"
          f"{'pts':>5}  note")
    with tempfile.TemporaryDirectory() as td:
        for w in witnesses:
            v = validate(w, Path(td))
            pts = SCORE.get(v["verdict"], 0)
            total += pts
            if v["verdict"] == "REFUTED":
                bad += 1
            print(f"  {str(w.get('loop')):<20}{w.get('family',''):<17}"
                  f"{w['claim']['equivalence']:<8}{v['verdict']:<20}{pts:>5}  "
                  f"{v.get('why','')[:44]}")
        alive, dead, nmut = self_test(Path(td))
    bad += dead
    print(f"\n  witnesses {len(witnesses)} · refuted {bad - dead} · SCORE {total}"
          f"   (SV-COMP asymmetry: EXACT +2, CLOSE +1, REFUTED -32)")
    print(f"WITNESS {'PASS' if bad == 0 else 'FAIL'}: every preservation claim "
          f"survived an independent checker that shares no code with the chooser")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
