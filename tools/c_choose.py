#!/usr/bin/env python3
"""Transformation chooser (OQ-2, second half): decide WHAT to do with the
dependence facts the lifter recovers, apply it, and prove it paid.

The lifter answers "is this dependence false?". This answers "so what?".

ALGORITHM — loop distribution by strongly-connected components (Allen &
Kennedy). Build the statement-level dependence graph, find SCCs, emit one loop
per SCC in topological order:
  * statements in the SAME SCC form a recurrence and MUST stay together;
  * distinct SCCs may be split, and splitting is what lets a vectorizable
    statement escape a loop pinned by a neighbouring recurrence.
A single SCC means the loop is indivisible -- reported, not forced.

THREE GATES, in this order. A candidate must clear all three:
  1. LEGAL      — the topological order exists (no cycle spanning the split)
  2. CORRECT    — differential test against the original, on the same inputs
  3. FASTER     — measured, by a margin wider than run-to-run noise
Gate 3 is not optional. `optimizer/probe/none60/` produced an exact
transformation that was 0.33x -- three times SLOWER. Correct-but-slower is a
regression, and a chooser without a stopwatch would ship it.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CC = "clang"
CANDIDATE_KINDS = ("distribute", "dead-store", "preload", "peel-wraparound")
NOISE_MARGIN = 1.05      # must beat the original by >5%: the measured spread
                         # in optimizer/probe/none60 reached 2.4% run-to-run


def sccs(n: int, edges: set[tuple[int, int]]) -> list[list[int]]:
    """Tarjan. Returns SCCs in reverse topological order."""
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        if a != b:
            adj[a].append(b)
    idx, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]

    def strong(v):
        idx[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); on.add(v)
        for w in adj[v]:
            if w not in idx:
                strong(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            out.append(sorted(comp))
    for v in range(n):
        if v not in idx:
            strong(v)
    return out


def dead_stores(loop: dict) -> list[int]:
    """Statements whose ONLY effect is a store overwritten at a later iteration.

    Legality, all four required:
      1. the statement writes exactly one array element, arr[i+k];
      2. a carried OUTPUT dependence covers it — some statement writes the same
         location at a later iteration;
      3. nothing READS that location between the two writes;
      4. the statement has no other effect (no second store, no scalar write).
    Fails any of them -> not eliminated. Refuse, never approximate.
    """
    n = len(loop["stmts"])
    out = []
    for si in range(n):
        writes = [a for a in loop["accesses"] if a["stmt"] == si and a["is_write"]]
        if len(writes) != 1:
            continue                                   # (1) and (4)
        w = writes[0]
        if w["coeff"] != 1:
            continue
        if any(nm for nm, is_w, st in loop["scalars"] if is_w and st == si):
            continue                                   # (4) also writes a scalar
        # (2) a later-iteration write to the same location
        overwriter = None
        for a in loop["accesses"]:
            if (a["is_write"] and a["array"] == w["array"] and a["coeff"] == 1
                    and a["stmt"] != si and a["offset"] < w["offset"]):
                overwriter = a
                break
        if overwriter is None:
            continue
        # (3) no read of that location between the two writes
        gap = w["offset"] - overwriter["offset"]        # iterations apart
        blocked = False
        for a in loop["accesses"]:
            if a["is_write"] or a["array"] != w["array"] or a["coeff"] != 1:
                continue
            if a["stmt"] == si:
                continue                # the statement's own read is consumed here
            if overwriter["offset"] <= a["offset"] <= w["offset"]:
                blocked = True
                break
        if blocked:
            continue
        out.append(si)
    return out


ASSIGN = re.compile(r"(?<![=!<>+\-*/])(\+=|-=|\*=|/=|=)(?!=)")


def _rhs_sub(stmt: str, old: str, new: str) -> str:
    """Replace `old` with `new` only to the RIGHT of the assignment operator."""
    m = ASSIGN.search(stmt)
    if not m:
        return stmt.replace(old, new)
    head, tail = stmt[:m.end()], stmt[m.end():]
    return head + tail.replace(old, new)


def preloadable(loop: dict) -> list[dict]:
    """Carried ANTI dependences that a preload would break.

    `b[i] = a[i] * a[i+1] * d[i]` reads a[i+1] BEFORE the iteration that writes
    it, so the value read is the pre-loop one. Copying that array once up front
    and redirecting only those reads makes the loop dependence-free.

    Only reads at the offsets actually overwritten are redirected. Redirecting
    every read of the array would be WRONG: in the same statement `a[i]` is the
    value just written this iteration, and must stay live."""
    out = []
    for d in loop["deps"]:
        if d["kind"] != "anti" or not d["carried"] or d["array"].startswith("$"):
            continue
        arr = d["array"]
        reads = sorted({a["offset"] for a in loop["accesses"]
                        if a["array"] == arr and not a["is_write"]
                        and a["coeff"] == 1 and a["offset"] > 0})
        writes = {a["offset"] for a in loop["accesses"]
                  if a["array"] == arr and a["is_write"] and a["coeff"] == 1}
        # only offsets that are BOTH read ahead and written later need saving
        need = [o for o in reads if any(o > w for w in writes)]
        if need:
            out.append({"array": arr, "offsets": need})
    # de-duplicate by array
    seen, uniq = set(), []
    for x in out:
        if x["array"] in seen:
            continue
        seen.add(x["array"]); uniq.append(x)
    return uniq


# `j = i`, `j = k`, and also `j = i + 1` / `j = k - 2`. The first version
# matched only bare identifiers, which covered s291/s292 and missed s121, s128
# and s4116 — the price said +3 and the recogniser could only reach +2.
SCALAR_ASSIGN = re.compile(r"^\s*(\w+)\s*=\s*(\w+)\s*(?:([+-])\s*(\d+)\s*)?$")


def wraparound(loop: dict) -> dict | None:
    """Recognise wrap-around subscript scalars and solve their steady state.

    `im1 = n-1; for i { a[i] = b[i] + b[im1]; im1 = i; }` — `im1` equals `i-1`
    on every iteration except the first. Symbolic simulation finds the offsets:
    each scalar holds either an integer offset from `i` or UNKNOWN, the body is
    replayed until offsets stabilise, and the number of replays needed is the
    PEEL DEPTH.

    This is a NORMALISATION, not a new analysis: once the subscripts are affine
    the existing machinery applies unchanged. U13's verdict — wrap-around needs
    no declaration, only induction-variable substitution.
    """
    subs = {u.split("[")[-1].rstrip("]") for u in loop["unhandled"]
            if "(wraparound)" in u}
    if not subs:
        return None
    assigns = []                      # (target, source) in program order
    for st in loop["stmts"]:
        m = SCALAR_ASSIGN.match(st.strip())
        if m:
            k = int(m.group(4)) * (1 if m.group(3) == "+" else -1) if m.group(3) else 0
            assigns.append((m.group(1), m.group(2), k))
    if not assigns:
        return None

    # A WRAP-AROUND scalar is assigned AFTER its use, so the value read is the
    # previous iteration's. A scalar assigned BEFORE its use (`j = i+1; a[j]`)
    # is a same-iteration ALIAS — a different pattern needing plain
    # substitution, no peeling. Modelling the second as the first produced
    # silently wrong code for s121, caught by the differential gate.
    idx = loop["index"]
    use_at = {}
    for n, st in enumerate(loop["stmts"]):
        for sc in subs:
            if f"[ {sc} ]" in st:
                use_at.setdefault(sc, n)
    assign_at = {t: n for n, st in enumerate(loop["stmts"])
                 for t, _, _ in assigns if SCALAR_ASSIGN.match(st.strip())
                 and SCALAR_ASSIGN.match(st.strip()).group(1) == t}
    for sc in subs:
        if sc in use_at and sc in assign_at and assign_at[sc] < use_at[sc]:
            return None            # forward alias, not a wrap-around: refuse

    state: dict[str, int | None] = {t: None for t, _, _ in assigns}
    seen, depth = [], 0
    for step in range(1, 9):
        nxt = dict(state)
        for tgt, src, k in assigns:
            # `im2 = im1` copies the CURRENT value: the offset is unchanged.
            # Subtracting 1 here as well as in the ageing step below double-aged
            # every chained scalar — `im2` solved to -3 instead of -2, and the
            # emitted code was silently wrong. The differential gate caught it.
            base = 0 if src == idx else state.get(src)
            nxt[tgt] = None if base is None else base + k
        # entering the NEXT iteration every offset ages by one
        state = {k: (None if v is None else v - 1) for k, v in nxt.items()}
        key = tuple(sorted(state.items(), key=lambda kv: kv[0]))
        if key in seen:
            break
        seen.append(key)
        depth = step
        if all(v is not None for v in state.values()):
            break
    if any(state.get(sc) is None for sc in subs):
        return None                   # never stabilises: refuse
    return {"kind": "peel-wraparound", "offsets": state, "depth": depth,
            "why": f"wrap-around scalars {dict((k, state[k]) for k in sorted(subs))}"
                   f" stabilise after {depth} iteration(s): peel then substitute"}


def plans(loop: dict) -> list[dict]:
    """Every applicable family, not the first one that matches.

    Choosing by a fixed priority was wrong: preload fired before distribute on
    s212/s211/s1213 and measured WORSE (1.13x where distribute got 2.11x). The
    stopwatch exists precisely so the order does not have to be guessed --
    propose them all, measure, keep the winner."""
    n = len(loop["stmts"])
    if n < 2:
        return [{"kind": "none", "why": "single statement"}]
    if loop["unhandled"]:
        w = wraparound(loop)
        if w and all("(wraparound)" in u for u in loop["unhandled"]):
            return [w]
        return [{"kind": "refuse",
                 "why": f"non-affine access: {loop['unhandled'][0]}"}]
    out = []
    dead = dead_stores(loop)
    if dead and len(dead) < n:
        out.append({"kind": "dead-store", "dead": dead,
                    "live": [i for i in range(n) if i not in dead],
                    "why": f"S{dead} overwritten later with no intervening read"})
    pre = preloadable(loop)
    if pre:
        out.append({"kind": "preload", "preload": pre,
                    "why": "carried anti dependence: preload the pre-loop values"})
    d = _distribute(loop)
    if d:
        out.append(d)
    return out or [{"kind": "none",
                    "why": "one SCC: the statements form a recurrence, indivisible"}]


def _distribute(loop: dict) -> dict | None:
    n = len(loop["stmts"])
    """Choose a transformation from the recovered facts."""
    dead = dead_stores(loop)
    live = [i for i in range(n) if i not in dead]
    if dead and len(live) >= 1:
        return {"kind": "dead-store", "dead": dead, "live": live,
                "why": f"S{dead} store(s) overwritten a later iteration with no "
                       f"intervening read: dead except on the final iteration"}

    edges = set()
    for d in loop["deps"]:
        a, b = d["src"], d["dst"]
        if not (0 <= a < n and 0 <= b < n):
            continue
        edges.add((a, b))
        if d["array"].startswith("$"):
            # A SCALAR is one memory cell reused every iteration. Splitting the
            # statements that share it would leave the reader seeing the LAST
            # iteration's value instead of its own -- silently wrong. Doing it
            # legally requires scalar EXPANSION (promote to an array), which is
            # not implemented, so the edge is made bidirectional: the two
            # statements are forced into one SCC and never separated.
            edges.add((b, a))
    comps = sccs(n, edges)          # reverse topological
    order = list(reversed(comps))   # topological: producers first
    if len(order) < 2:
        return None
    return {"kind": "distribute", "groups": order,
            "why": f"{len(order)} SCCs -> {len(order)} loops, "
                   f"topological order {[g for g in order]}"}


def emit(loop: dict, p: dict, suffix: str) -> tuple[str, str]:
    """Emit (original, transformed) as two C functions with identical signatures."""
    arrays = sorted({a["array"] for a in loop["accesses"]})
    params = ", ".join(f"float * restrict {a}" for a in arrays) + ", int n"
    # A wrap-around scalar is initialised BEFORE the loop, outside what the
    # lifter sees. Both functions therefore take it as a parameter, and the
    # harness hands both the SAME value — so the differential test still
    # compares like with like, for that initial state.
    wscalars = sorted(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else []
    if wscalars:
        params = ", ".join(f"int {w}_init" for w in wscalars) + ", " + params
    hdr = loop["header"]
    body_all = "\n".join(f"        {s};" for s in loop["stmts"])
    wdecl = "".join(f"    int {w} = {w}_init;\n" for w in wscalars)
    orig = (f"void orig{suffix}({params}) {{\n{wdecl}"
            f"    {hdr} {{\n{body_all}\n    }}\n}}\n")
    if p["kind"] == "dead-store":
        live = "\n".join(f"        {loop['stmts'][i]};" for i in p["live"])
        # the removed store still has to happen once, for the final iteration
        last = f"({loop['upper']}) - 1"
        tail = "\n".join(
            f"    {{ int {loop['index']} = {last}; {loop['stmts'][i]}; }}"
            for i in p["dead"])
        xf = (f"void xform{suffix}({params}) {{\n"
              f"    {hdr} {{\n{live}\n    }}\n{tail}\n}}\n")
        return orig, xf
    if p["kind"] == "peel-wraparound":
        idx, d = loop["index"], p["depth"]
        lo, up = loop["lower"], loop["upper"]
        # The peeled prologue is the ORIGINAL loop restricted to its first
        # `depth` iterations. Reusing the body verbatim means the pre-loop
        # initialisation of the scalars (which lives OUTSIDE the loop and the
        # lifter never sees) is never needed.
        body = "\n".join(f"        {st};" for st in loop["stmts"])
        steady = list(loop["stmts"])
        for sc, off in p["offsets"].items():
            steady = [st.replace(f"[ {sc} ]", f"[ {idx} {off:+d} ]") for st in steady]
        sbody = "\n".join(f"        {st};" for st in steady)
        xf = (f"void xform{suffix}({params}) {{\n{wdecl}"
              f"    int {idx};\n"
              f"    for ({idx} = ({lo}); {idx} < ({lo}) + {d} && {idx} < ({up}); ++{idx}) {{\n"
              f"{body}\n    }}\n"
              f"    for (; {idx} < ({up}); ++{idx}) {{\n{sbody}\n    }}\n}}\n")
        return orig, xf
    if p["kind"] == "preload":
        idx = loop["index"]
        tmps, saves, body = [], [], list(loop["stmts"])
        for x in p["preload"]:
            arr, t = x["array"], f"__pre_{x['array']}"
            tmps.append(t)
            saves.append(f"    for (int {idx} = ({loop['lower']}); "
                         f"{idx} < ({loop['upper']}) + {max(x['offsets'])}; ++{idx}) "
                         f"{t}[{idx}] = {arr}[{idx}];")
            for off in x["offsets"]:
                # RHS ONLY. `a[i+1] = a[i+2] * a[i+1]` has the same array and
                # offset on BOTH sides; rewriting the left one would redirect
                # the STORE into the scratch buffer and never write the real
                # array. The differential test caught exactly that.
                body = [_rhs_sub(st, f"{arr} [ {idx} + {off} ]",
                                 f"{t} [ {idx} + {off} ]") for st in body]
        decl = "".join(f"float * restrict {t}, " for t in tmps)
        allb = "\n".join(f"        {st};" for st in body)
        xf = (f"void xform{suffix}({decl}{params}) {{\n"
              + "\n".join(saves) + f"\n    {hdr} {{\n{allb}\n    }}\n}}\n")
        return orig, xf
    if p["kind"] != "distribute":
        return orig, ""
    loops = []
    for g in p["groups"]:
        b = "\n".join(f"        {loop['stmts'][i]};" for i in g)
        loops.append(f"    {hdr} {{\n{b}\n    }}")
    xf = (f"void xform{suffix}({params}) {{\n" + "\n".join(loops) + "\n}\n")
    return orig, xf


HARNESS = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 32000
%(decls)s
static float REF[%(na)d][N], WRK[%(na)d][N], SAV[%(na)d][N];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
  return t.tv_sec*1e3+t.tv_nsec/1e6;}
static void seed(void){srand(7);
  for(int k=0;k<%(na)d;k++) for(int i=0;i<N;i++)
      SAV[k][i]=(float)rand()/RAND_MAX+0.5f;}
static void reset(float dst[%(na)d][N]){memcpy(dst,SAV,sizeof SAV);}
int main(void){
  seed();
  reset(REF); %(call_ref)s
  reset(WRK); %(call_xf)s
  int exact=1; double worst=0;
  for(int k=0;k<%(na)d;k++) for(int i=0;i<N;i++){
    if(WRK[k][i]!=REF[k][i]) exact=0;
    double d=fabs((double)WRK[k][i]-REF[k][i])/(fabs((double)REF[k][i])+1e-30);
    if(d>worst) worst=d; }
  if(!exact && worst>1e-6){ printf("INCORRECT %%.3e\n",worst); return 1; }
  double t0=1e18,t1=1e18;
  for(int t=0;t<11;t++){reset(REF); double s=ms();
    for(int r=0;r<%(reps)d;r++) %(call_ref)s ; double d=ms()-s; if(d<t0)t0=d;}
  for(int t=0;t<11;t++){reset(WRK); double s=ms();
    for(int r=0;r<%(reps)d;r++) %(call_xf)s ; double d=ms()-s; if(d<t1)t1=d;}
  printf("%%s %%.4f %%.4f %%.4f\n", exact?"EXACT":"CLOSE", t0, t1, t0/t1);
  return 0; }
"""


def evaluate(loop: dict, p: dict, tmp: Path) -> dict:
    arrays = sorted({a["array"] for a in loop["accesses"]})
    orig, xf = emit(loop, p, "")
    if not xf:
        return {"verdict": "no-candidate"}
    na = len(arrays)
    npre = len(p.get("preload", []))
    # wrap-around scalars are parameters of BOTH functions; the harness gives
    # both the same initial values (TSVC's own idiom: n-1, n-2, ...)
    winit = "".join(f"N-{k+1}, " for k in
                    range(len(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else 0))
    args_ref = winit + ", ".join(f"REF[{i}]" for i in range(na)) + ", N"
    pre_args = "".join(f"SCRATCH[{i}], " for i in range(npre))
    args_xf = winit + pre_args + ", ".join(f"WRK[{i}]" for i in range(na)) + ", N"
    nw = len(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else 0
    wp = "".join("int, " for _ in range(nw))
    decls = (f"void orig({wp}{', '.join(['float * restrict']*na)}, int);\n"
             f"void xform({wp}{', '.join(['float * restrict']*(na+npre))}, int);\n"
             f"static float SCRATCH[{max(npre,1)}][32000];")
    src = tmp / "cand.c"
    src.write_text(orig + xf)
    run = tmp / "run.c"
    run.write_text(HARNESS % {"decls": decls, "na": na, "reps": 200,
                              "call_ref": f"orig({args_ref});",
                              "call_xf": f"xform({args_xf});"})
    exe = tmp / "cand"
    c = subprocess.run([CC, "-O3", "-mcpu=native", "-w", str(src), str(run),
                        "-o", str(exe), "-lm"], capture_output=True, text=True)
    if c.returncode != 0:
        return {"verdict": "compile-fail", "err": c.stderr[:160]}
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return {"verdict": "INCORRECT", "err": r.stdout.strip()[:80]}
    parts = r.stdout.split()
    if parts[0] == "INCORRECT":
        return {"verdict": "INCORRECT", "err": parts[1]}
    eq, t0, t1, sp = parts[0], float(parts[1]), float(parts[2]), float(parts[3])
    ok = sp >= NOISE_MARGIN
    return {"verdict": "ACCEPT" if ok else "REJECT-not-faster",
            "equivalence": eq, "orig_ms": t0, "xform_ms": t1, "speedup": sp}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__); return 2
    lifted = json.loads(Path(sys.argv[1]).read_text())
    loops = [l for l in lifted if l["func"].endswith("_v0")] or lifted
    print(f"  {'loop':<11}{'decision':<13}{'orig':>8}{'xform':>8}"
          f"{'speedup':>9}  verdict")
    acc = rej = skip = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for lp in loops:
            cands = [c for c in plans(lp) if c["kind"] in CANDIDATE_KINDS]
            if not cands:
                skip += 1
                q = plans(lp)[0]
                print(f"  {lp['func']:<11}{q['kind']:<13}{'—':>8}{'—':>8}"
                      f"{'—':>9}  {q['why'][:44]}")
                continue
            results = [(c, evaluate(lp, c, tmp)) for c in cands]
            good = [(c, e) for c, e in results if e.get("verdict") == "ACCEPT"]
            if good:
                p, e = max(good, key=lambda ce: ce[1]["speedup"])
            else:
                p, e = max(results, key=lambda ce: ce[1].get("speedup", 0))
            v = e["verdict"]
            acc += v == "ACCEPT"; rej += v.startswith(("REJECT", "INCORRECT"))
            if "speedup" in e:
                print(f"  {lp['func']:<11}{p['kind']:<13}{e['orig_ms']:>8.3f}"
                      f"{e['xform_ms']:>8.3f}{e['speedup']:>8.2f}x  {v}"
                      f"  [{e['equivalence']}]")
            else:
                print(f"  {lp['func']:<11}{p['kind']:<13}{'—':>8}{'—':>8}"
                      f"{'—':>9}  {v} {e.get('err','')[:40]}")
    print(f"\n  accepted {acc} · rejected {rej} · no-candidate {skip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
