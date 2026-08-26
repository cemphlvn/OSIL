#!/usr/bin/env python3
"""Point the G19 lifter + G20 chooser at a repository it did not author.

    python3 optimizer/probe/repo_scan.py <repo-dir> [out.json]

ADVISORY — not a gate, and deliberately not in tools/. It measures REACH, which
is a property of the code it is pointed at, not a repo invariant. The four bugs
it found on xiph/opus ARE gated, in conformance/lift/repo-pins/.
See docs/design/repo-scale-probe.md.

Two things the TSVC-scale tools did not have to do, and repo-scale does:
  1. DEDUPE. libclang walks the whole translation unit, so a static-inline loop
     in a header is lifted once per TU that includes it. Counting those as
     distinct loops inflated opus by ~10x on the first run.
  2. RANK. `distribute` fires on ANY loop with two SCCs -- which is most loops,
     and almost always pointless. The interesting case is Allen & Kennedy's:
     a RECURRENCE pins the loop, and distribution lets a dependence-free
     statement escape it. That is the only shape worth a stopwatch.
"""
import json, sys, hashlib
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import c_lift, c_choose, capability_ceiling

SKIP_PARTS = ("test", "tests", "examples", "example", "doc", "win32",
              "dump_modes", "demo", "contrib", "third_party")
FAMILIES = {"distribute", "dead-store", "preload", "peel-wraparound",
            "if-convert"}


def includes(repo: Path, cap=60):
    ds = {str(p.parent) for p in repo.rglob("*.h")}
    return [f"-I{d}" for d in sorted(ds)[:cap]] + [f"-I{repo}"]


def scan(repo: Path, limit=600):
    flags = includes(repo) + ["-w"]
    cfiles = [p for p in sorted(repo.rglob("*.c"))
              if not any(x in p.parts for x in SKIP_PARTS)][:limit]
    seen, loops = {}, []
    for f in cfiles:
        try:
            ls = c_lift.lift_file(f, flags)
        except Exception:
            continue
        for l in ls:
            d = asdict(l)
            key = hashlib.sha1(
                (d["func"] + str(d["line"]) + "|".join(d["stmts"])).encode()).hexdigest()
            if key in seen:
                seen[key]["_tus"] += 1
                continue
            d["_tu"] = str(f.relative_to(repo)); d["_tus"] = 1
            seen[key] = d
            loops.append(d)
    return cfiles, loops


def recurrence_shape(d):
    """Allen & Kennedy's profitable case: >=2 SCCs, at least one carrying a true
    loop-carried dependence (the recurrence that pins the loop), and at least one
    OTHER SCC entirely free of carried dependences (the statement that escapes)."""
    n = len(d["stmts"])
    edges = set()
    for dep in d["deps"]:
        a, b = dep["src"], dep["dst"]
        if not (0 <= a < n and 0 <= b < n):
            continue
        edges.add((a, b))
        if dep["array"].startswith("$"):
            edges.add((b, a))
    comps = c_choose.sccs(n, edges)
    if len(comps) < 2:
        return None
    pinned, free = [], []
    for comp in comps:
        cs = set(comp)
        carried = [dep for dep in d["deps"]
                   if dep["carried"] and not dep["breakable"]
                   and dep["src"] in cs and dep["dst"] in cs]
        (pinned if carried else free).append(comp)
    if pinned and free:
        return {"pinned": pinned, "free": free}
    return None


def price(all_loops, refused):
    """G21 capability pricing, run on a HELD-OUT corpus instead of TSVC.

    `docs/design/limit-study-angle.md` records the gap this closes: every price
    in this project was measured on TSVC2 alone, and Wall 1993 warns in as many
    words that a narrow benchmark misleads.

    What is priced here is ANALYSIS REACH -- how many loops the analyser could
    admit -- and NOT how many would yield a transformation. Those are different
    questions, and on this corpus they have very different answers.
    """
    feats = [capability_ceiling.features(d) for d in all_loops]
    n = len(feats)
    analysable = sum(1 for f in feats if not (f & refused))
    live = sorted({f for ft in feats for f in ft if f in refused})

    def reach(admit):
        r = refused - admit
        return sum(1 for f in feats if not (f & r))

    print(f"\n  === capability pricing on {n} loops (analysis REACH, not wins) ===")
    print(f"  analysable under declared capabilities : {analysable} "
          f"({100*analysable/max(n,1):.1f}%)")
    marg = {f: reach({f}) - analysable for f in live}
    print("  MARGINAL (each capability alone):")
    for f in sorted(live, key=lambda f: -marg[f]):
        blocked = sum(1 for ft in feats if f in ft)
        print(f"    +{marg[f]:<5} {f:<28} -> {100*(analysable+marg[f])/n:5.1f}%"
              f"   (blocks {blocked} loops in total)")
    import itertools
    rows = []
    for k in range(2, len(live) + 1):
        for combo in itertools.combinations(live, k):
            g = reach(set(combo)) - analysable
            rows.append((g - sum(marg[f] for f in combo), g, combo))
    if rows:
        print("  JOINT (complementary, so gains exceed the sum of marginals):")
        for excess, g, combo in sorted(rows, key=lambda r: -r[1])[:4]:
            name = " + ".join(c.split(".")[1] for c in combo)
            print(f"    +{g:<5} {name:<44} -> {100*(analysable+g)/n:5.1f}%"
                  f"   (marginals say +{g-excess}"
                  f"{', UNDER by ' + str(excess) if excess else ''})")


def main():
    repo = Path(sys.argv[1])
    cfiles, loops = scan(repo)
    handled = [d for d in loops if not d["unhandled"]]
    fam, rows = {}, []
    for d in loops:
        try:
            ps = c_choose.plans(d)
        except Exception:
            ps = [{"kind": "error"}]
        ks = sorted({p["kind"] for p in ps})
        for k in ks:
            fam.setdefault(k, 0)
            fam[k] += 1
        rows.append((d, ks))
    print(f"\n=== {repo.name} ===")
    print(f"  .c files {len(cfiles)} · distinct loops with array accesses {len(loops)}"
          f" · fully affine {len(handled)} "
          f"({100*len(handled)/max(len(loops),1):.0f}%)")
    for k in sorted(fam, key=lambda k: -fam[k]):
        print(f"    {k:<16} {fam[k]}")
    ranked = []
    for d, ks in rows:
        if not (set(ks) & FAMILIES):
            continue
        shape = recurrence_shape(d) if "distribute" in ks else None
        other = [k for k in ks if k in FAMILIES and k != "distribute"]
        if shape or other:
            ranked.append((d, ks, shape))
    print(f"  candidates in a family : {sum(1 for d,k in rows if set(k)&FAMILIES)}")
    print(f"  PROFITABLE-SHAPED      : {len(ranked)}"
          f"   (recurrence pins the loop, or a non-distribute family fires)")
    for d, ks, shape in ranked:
        tag = "recurrence+free" if shape else "+".join(k for k in ks if k in FAMILIES)
        print(f"    {d['_tu']}:{d['line']:<6} {d['func']:<26} {tag:<18} "
              f"stmts={len(d['stmts'])} tus={d['_tus']}")
    caps = capability_ceiling.read_capabilities(capability_ceiling.CORPUS)
    refused = set().union(*(c["refuses"] for c in caps.values())) if caps else set()
    price(loops, refused)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(
            [{"loop": d, "kinds": k, "shape": s} for d, k, s in ranked], indent=1))
        print(f"  -> {sys.argv[2]}")


if __name__ == "__main__":
    main()
