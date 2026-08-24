#!/usr/bin/env python3
"""Ledger generator: measure EVERY licensed realization, per kernel.

Two jobs, in this order:
  1. CORRECTNESS GATE. Each realization is differentially tested against a
     declaration-order scalar reference. A realization that fails is never
     timed and never enters the ledger as a speedup.
  2. COST MODEL vs GROUND TRUTH. osil-opt picks a realization from its own
     analytical model. This measures all of them and records whether the pick
     was the empirical best. A model that never meets a measured outcome is
     unfalsified taste.

Writes results.json (the ledger) and prints a table.
"""
import json, re, subprocess, sys, pathlib

# A pick counts as correct if it is within MEASUREMENT NOISE of the best.
# Same constant, same justification, as calibration/fit.py — repeating the
# s352 benchmark gave i4-vs-i8 deltas of 0.5%/2.4%/0.0% with the sign
# FLIPPING between runs. Gating at 1.00x gates on thermal noise.
# These two gates MUST agree; if you change one, change the other.
NOISE_TOL = 0.05

HERE = pathlib.Path(__file__).resolve().parent
OPT  = HERE.parent / "target" / "debug" / "osil-opt"
CC   = ["clang", "-O3", "-march=native"]
N_DEFAULT = 32000

# Per-kernel: the reference (declaration order), the call shape, and the
# harness setup. `ref` is verbatim TSVC loop structure.
CASES = {
    "s312": dict(
        case="s312.osil", n=32000,
        sig="const float * restrict a, int n",
        ref="float acc = 1.0f;\n    for (int i = 0; i < 32000; ++i) acc *= a[i];\n    return acc;",
        call="A, 32000", bench_call="A, 32000",
        rival=True,
    ),
    "s317": dict(
        case="s317.osil", n=16000,
        sig="float k, int n",
        ref="float acc = 1.0f;\n    for (int i = 0; i < 16000; ++i) acc *= k;\n    return acc;",
        # args MUST vary per rep or the whole call is loop-invariant and
        # gets hoisted — that is what produced a bogus 6000x first pass.
        call="0.9999f, 16000", bench_call="0.9999f + r*1e-9f, 16000",
        rival=True,
    ),
    "s317-noclosed": dict(
        case="s317-noclosed.osil", n=16000,
        sig="float k, int n",
        ref="float acc = 1.0f;\n    for (int i = 0; i < 16000; ++i) acc *= k;\n    return acc;",
        call="0.9999f, 16000", bench_call="0.9999f + r*1e-9f, 16000",
        rival=True,
    ),
    "s352": dict(
        case="s352.osil", n=32000,
        sig="const float * restrict a, const float * restrict b, int n",
        ref="float acc = 0.0f;\n    for (int i = 0; i < 32000; ++i) acc += a[i] * b[i];\n    return acc;",
        call="A, B, 32000", bench_call="A, B, 32000",
        rival=True,
    ),
}

def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)

def realizations(case):
    """Ask osil-opt for the licensed space; return [(kind_token, modeled)]."""
    out = sh([str(OPT), str(HERE.parent / "cases" / case)]).stdout
    rs = []
    for line in out.splitlines():
        m = re.match(r"\s*(?:->|\s)\s*(\w+(?: \{ w: \d+, i: \d+ \})?)\s+modeled cost\s+([\d.]+)", line)
        if m:
            rs.append((m.group(1), float(m.group(2))))
    pick = next((k for k, _ in rs), None)
    m = re.search(r"selected: (.+)", out)
    if m: pick = m.group(1).strip()
    return rs, pick

def tok(kind):
    """Stable identifier for a realization kind."""
    return kind.replace(" ", "").replace("{", "_").replace("}", "") \
               .replace(":", "").replace(",", "_")

def main():
    sh(["cargo", "build", "-q"], cwd=HERE.parent)
    ledger = {}

    for name, cfg in CASES.items():
        rs, pick = realizations(cfg["case"])
        variants = []
        for kind, modeled in rs:
            t = tok(kind)
            src = HERE / f"v_{name}_{t}.c"
            r = sh([str(OPT), str(HERE.parent / "cases" / cfg["case"]),
                    "--pick", kind.replace(" ", ""), "--emit", str(src)])
            if r.returncode != 0:
                print(f"  ! emit failed for {name}/{kind}: {r.stderr.strip()[:120]}")
                continue
            src.write_text(src.read_text().replace(
                f"osil_{name}(", f"osil_{name}_{t}("))
            variants.append((kind, t, modeled))

        if not variants:
            continue

        decls = "\n".join(
            f"float osil_{name}_{t}({cfg['sig']});" for _, t, _ in variants)
        entries = ",\n".join(
            f'    {{ "{k}", osil_{name}_{t}, {m} }}' for k, t, m in variants)

        harness = f"""
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <libproc.h>
#define N {max(cfg['n'], N_DEFAULT)}
#define TARGET_MS 250.0        /* per-realization measurement window */
#define TRIALS 7
static float A[N], B[N];
static volatile float sink;
typedef float (*kern)({cfg['sig']});
typedef struct {{ const char *name; kern f; double modeled; }} entry;
{decls}
float ref_{name}({cfg['sig']}) {{ (void)n;
    {cfg['ref']}
}}
float rival_{name}({cfg['sig']});
static void fill(unsigned s) {{ srand(s);
    for (int i = 0; i < N; i++) {{
        A[i] = 1.0f + ((float)rand()/RAND_MAX - 0.5f) * 0.002f;
        B[i] = 1.0f + ((float)rand()/RAND_MAX - 0.5f) * 0.002f;
    }} }}
static double ms(void) {{ struct timespec t; clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3 + t.tv_nsec/1e6; }}

/* Per-process energy and hardware cycle counters. No sudo required, unlike
   powermetrics; RUSAGE_INFO_V6 exposes ri_energy_nj and ri_cycles directly. */
static void rusage_now(uint64_t *nj, uint64_t *cyc, uint64_t *ins) {{
    struct rusage_info_v6 r; memset(&r, 0, sizeof r);
    proc_pid_rusage(getpid(), RUSAGE_INFO_V6, (rusage_info_t*)&r);
    *nj = r.ri_energy_nj; *cyc = r.ri_cycles; *ins = r.ri_instructions;
}}

typedef struct {{ double ms; double nj; double cyc; double ins; long reps; }} meas;

/* Calibrate reps so every realization gets a comparable ~TARGET_MS window.
   A fixed rep count would give the fast realizations too short a window for
   the energy counter to resolve. */
static long calibrate(kern f) {{
    long reps = 256;
    for (;;) {{
        double t0 = ms();
        for (long r = 0; r < reps; r++) {{ A[r % N] += 1e-9f; sink = f({cfg['bench_call']}); }}
        double dt = ms() - t0;
        if (dt > 40.0) return (long)(reps * (TARGET_MS / dt)) + 1;
        reps *= 4;
        if (reps > (1L<<30)) return reps;
    }}
}}

static meas measure(kern f) {{
    long reps = calibrate(f);
    meas best; best.ms = 1e18; best.reps = reps;
    for (int t = 0; t < TRIALS; t++) {{
        uint64_t nj0, c0, i0, nj1, c1, i1;
        rusage_now(&nj0, &c0, &i0);
        double t0 = ms();
        for (long r = 0; r < reps; r++) {{ A[r % N] += 1e-9f; sink = f({cfg['bench_call']}); }}
        double dt = ms() - t0;
        rusage_now(&nj1, &c1, &i1);
        /* Keep the trial with the least wall time: least preemption and least
           thermal interference, so its energy figure is the cleanest too. */
        if (dt < best.ms) {{
            best.ms = dt;
            best.nj  = (double)(nj1 - nj0);
            best.cyc = (double)(c1 - c0);
            best.ins = (double)(i1 - i0);
        }}
    }}
    return best;
}}

static void emit(const char *label, meas m, double modeled) {{
    printf("%s{{\\"kind\\":\\"%s\\",\\"modeled\\":%g,\\"ok\\":1,\\"rel\\":0,"
           "\\"ms\\":%g,\\"reps\\":%ld,\\"nj_per_call\\":%g,\\"cyc_per_call\\":%g,"
           "\\"ins_per_call\\":%g}}", label[0]?"":"", label, modeled,
           m.ms * 2000.0 / m.reps,   /* normalized to the old 2000-rep scale */
           m.reps, m.nj / m.reps, m.cyc / m.reps, m.ins / m.reps);
}}

int main(void) {{
    entry V[] = {{
{entries}
    }};
    int NV = sizeof(V)/sizeof(V[0]);
    fill(1);
    float truth = ref_{name}({cfg['call']});
    printf("{{\\"kernel\\":\\"{name}\\",\\"variants\\":[");
    meas m_ref = measure(ref_{name}), m_riv = measure(rival_{name});
    for (int i=0;i<NV;i++) {{
        fill(1);
        double v = V[i].f({cfg['call']});
        double rel = fabs(v-truth)/fabs(truth);
        int ok = rel < 1e-3;
        printf("%s{{\\"kind\\":\\"%s\\",\\"modeled\\":%g,\\"ok\\":%d,\\"rel\\":%g",
               i?",":"", V[i].name, V[i].modeled, ok, rel);
        if (ok) {{ meas m = measure(V[i].f);
            printf(",\\"ms\\":%g,\\"reps\\":%ld,\\"nj_per_call\\":%g,"
                   "\\"cyc_per_call\\":%g,\\"ins_per_call\\":%g}}",
                   m.ms*2000.0/m.reps, m.reps, m.nj/m.reps, m.cyc/m.reps, m.ins/m.reps);
        }} else printf(",\\"ms\\":0}}");
    }}
    printf("],\\"ref_ms\\":%g,\\"ref_nj\\":%g,\\"rival_ms\\":%g,\\"rival_nj\\":%g}}\\n",
        m_ref.ms*2000.0/m_ref.reps, m_ref.nj/m_ref.reps,
        m_riv.ms*2000.0/m_riv.reps, m_riv.nj/m_riv.reps);
    return 0; }}
"""
        (HERE / f"h_{name}.c").write_text(harness)
        # the rival: identical source to the reference, built with -ffast-math
        (HERE / f"r_{name}.c").write_text(
            f"float rival_{name}({cfg['sig']}) {{ (void)n;\n    {cfg['ref']}\n}}\n")

        objs = []
        for _, t, _ in variants:
            o = HERE / f"v_{name}_{t}.o"
            sh(CC + ["-c", str(HERE / f"v_{name}_{t}.c"), "-o", str(o)])
            objs.append(str(o))
        sh(CC + ["-ffast-math", "-c", str(HERE/f"r_{name}.c"), "-o", str(HERE/f"r_{name}.o")])
        sh(CC + ["-c", str(HERE/f"h_{name}.c"), "-o", str(HERE/f"h_{name}.o")])
        link = sh(CC + [str(HERE/f"h_{name}.o"), str(HERE/f"r_{name}.o")] + objs
                  + ["-o", str(HERE/f"b_{name}"), "-lm"])
        if link.returncode != 0:
            print(f"  ! link failed for {name}: {link.stderr.strip()[:300]}"); continue
        out = sh([str(HERE/f"b_{name}")]).stdout.strip()
        try:
            ledger[name] = json.loads(out)
        except Exception:
            print(f"  ! bad output for {name}: {out[:200]}"); continue
        ledger[name]["model_pick"] = pick

    (HERE/"results.json").write_text(json.dumps(ledger, indent=2))

    # ---- append to the calibration ledger (append-only, never rewritten) ----
    import datetime, os
    cal = HERE.parent / "calibration"
    cal.mkdir(exist_ok=True)
    sha = sh(["git", "rev-parse", "--short", "HEAD"]).stdout.strip() or "uncommitted"
    date = datetime.date.today().isoformat()
    with open(cal / "measurements.jsonl", "a") as fh:
        for name, d in ledger.items():
            n = CASES[name]["n"]
            for v in d["variants"]:
                if not v["ok"]:
                    continue
                row = {"date": date, "kernel": name, "extent": n,
                       "kind": v["kind"], "measured_ms": v["ms"],
                       "cyc_per_call": v.get("cyc_per_call"),
                       "nj_per_call": v.get("nj_per_call"),
                       "ins_per_call": v.get("ins_per_call"),
                       "reps": 2000, "modeled_at_measure": v["modeled"],
                       "machine": "Apple-M4", "cc": "clang-17",
                       "cflags": "-O3 -march=native", "git_sha": sha}
                fh.write(json.dumps(row) + "\n")
    print(f"\n  ledger: appended to {cal/'measurements.jsonl'}")

    # ---- report ----
    agree = total = 0
    for name, d in ledger.items():
        ok = [v for v in d["variants"] if v["ok"]]
        if not ok: continue
        best = min(ok, key=lambda v: v["ms"])
        pick = next((v for v in d["variants"] if v["kind"].replace(" ","")
                     == d["model_pick"].replace(" ","")), None)
        total += 1
        hit = pick is not None and pick["ms"] <= best["ms"] * (1 + NOISE_TOL)
        agree += hit
        print(f"\n=== {name} ===  baseline clang -O3: {d['ref_ms']:.2f} ms"
              f"   |  rival clang -ffast-math: {d['rival_ms']:.2f} ms "
              f"({d['ref_ms']/d['rival_ms']:.2f}x)")
        print(f"  {'realization':<22}{'ms':>8}{'vs -O3':>9}{'vs f-m':>9}{'modeled':>10}  ok")
        for v in sorted(d["variants"], key=lambda v: (not v["ok"], v["ms"] or 9e9)):
            if not v["ok"]:
                print(f"  {v['kind']:<22}{'--':>8}{'--':>9}{'--':>9}{v['modeled']:>10.0f}  FAIL rel={v['rel']:.1e}")
                continue
            mark = " <- model pick" if pick and v["kind"]==pick["kind"] else ""
            print(f"  {v['kind']:<22}{v['ms']:>8.2f}{d['ref_ms']/v['ms']:>8.2f}x"
                  f"{d['rival_ms']/v['ms']:>8.2f}x{v['modeled']:>10.0f}  ok{mark}")
        within = f" (within {NOISE_TOL:.0%} noise band)" if hit and pick["kind"] != best["kind"] else ""
        print(f"  measured best: {best['kind']}   model picked: {d['model_pick']}"
              f"   -> {'AGREES' if hit else 'MODEL WRONG'}{within}")
        if not hit and pick:
            print(f"     cost of model error: {pick['ms']/best['ms']:.2f}x slower than best licensed")
    print(f"\n== cost model agreement: {agree}/{total} kernels ==")

if __name__ == "__main__":
    main()
