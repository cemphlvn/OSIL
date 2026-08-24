#!/usr/bin/env python3
"""Derive the analysis ceiling from DECLARED capabilities (G21).

The architecture describing its own reach. `conformance/corpus/026` declares
which loop FEATURES the analyser admits and refuses; this derives, from those
declarations plus a lifted corpus, the ceiling on what ANY chooser of this kind
could ever recover.

Why it matters: the ceiling was first computed by an ad-hoc script that happened
to know the capabilities. That number (51.0%) sat BELOW the record being chased
(56.0%) — and was knowable before the attempt started. Making it derived means
the next such question is answered by declaration, not by an afternoon.

    --what-if <feature>   admit a currently-refused feature and recompute.
                          This is the design instrument: it prices a capability
                          BEFORE it is built.

Run: `just ceiling`
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from osil_check import tokenize            # reference lexer — dogfood

CORPUS = ROOT / "conformance" / "corpus" / "026-capability-analysis.osil"
KERNEL = re.compile(r'^(s\d|vif|vpv|vtv|vpvtv|vpvts|vpvpv|vtvtv|vsumr|vdotr|vbor)')


def read_capabilities(path: Path) -> dict:
    """Parse `capability X { admits {...} refuses {...} }` with the reference lexer.

    The lexer splits `subscript.affine` into three tokens, so dotted ids are
    rejoined here rather than letting `subscript` and `affine` both enter the
    feature set as separate names -- which they did in the first version, and
    produced four phantom features priced at +0."""
    toks = [t.text for t in tokenize(path.read_text()) if t.kind != "eof"]
    # rejoin dotted qualified ids into single tokens
    merged, i = [], 0
    while i < len(toks):
        if (i + 2 < len(toks) and toks[i + 1] == "."
                and toks[i] not in "{}" and toks[i + 2] not in "{}"):
            merged.append(f"{toks[i]}.{toks[i+2]}")
            i += 3
        else:
            merged.append(toks[i])
            i += 1
    toks = merged

    caps, i = {}, 0
    while i < len(toks):
        if toks[i] == "capability":
            name, i = toks[i + 1], i + 2
            caps[name] = {"admits": set(), "refuses": set()}
            depth, cur = 0, None
            while i < len(toks):
                t = toks[i]
                if t == "{":
                    depth += 1
                elif t == "}":
                    depth -= 1
                    if depth == 0:
                        break
                    cur = None
                elif t in ("admits", "refuses"):
                    cur = t
                elif cur:
                    caps[name][cur].add(t)
                i += 1
        i += 1
    return caps


def features(lp: dict) -> set[str]:
    """The features a lifted loop exhibits, in the capabilities' vocabulary."""
    f = set()
    for u in lp["unhandled"]:
        if "control flow" in u:
            f.add("body.control_flow")
        elif "non-affine" in u:
            f.add("subscript.wraparound" if "(wraparound)" in u
                  else "subscript.indirect")
    arrays = {a["array"] for a in lp["accesses"]}
    if arrays & {"aa", "bb", "cc", "tt", "flat_2d_array"}:
        f.add("access.multi_dimensional")
    # An irreducible recurrence is a dependence CYCLE — a statement that
    # depends on itself across iterations. A carried flow dependence BETWEEN
    # different statements is not that: distribution breaks it, and this repo
    # already recovered s211 (1.66x) and s1213 (1.67x) that way, bit-identical,
    # with no scan and no licence.
    #
    # The first version of this feature tested "has a true carried dependence"
    # and so charged the scan capability for 3 kernels distribution had ALREADY
    # won (U14 named them: s211, s1213, s261). That inflated the price of work
    # not yet done. Ask the chooser's own SCC analysis instead.
    carried = [d for d in lp["deps"] if d["carried"] and not d["breakable"]]
    if carried:
        import c_choose
        n = len(lp["stmts"])
        edges = set()
        for d in lp["deps"]:
            a, b = d["src"], d["dst"]
            if 0 <= a < n and 0 <= b < n:
                edges.add((a, b))
                if d["array"].startswith("$"):
                    edges.add((b, a))
        comps = c_choose.sccs(n, edges)
        multi = any(len(c) > 1 for c in comps)
        selfdep = any(d["src"] == d["dst"] for d in carried)
        if multi or selfdep:
            f.add("dep.recurrence_cycle")      # irreducible: needs a scan
        else:
            f.add("dep.carried_separable")     # distribution breaks it
    return f


def main() -> int:
    caps = read_capabilities(CORPUS)
    refused = set().union(*(c["refuses"] for c in caps.values())) if caps else set()
    whatif = None
    if "--what-if" in sys.argv:
        whatif = sys.argv[sys.argv.index("--what-if") + 1]
        refused = refused - {whatif}

    src = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].endswith(".c") else None
    if src is None:
        print("usage: capability_ceiling.py <corpus.c> [-I dir] [--what-if feature]")
        return 2
    inc = src.parent
    with tempfile.TemporaryDirectory() as td:
        js = Path(td) / "l.json"
        subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"), str(src),
                        "--flags", f"-I{inc}", "--json", str(js)],
                       capture_output=True, text=True)
        loops = json.loads(js.read_text())
    import tsvc_rate
    vec, allk = tsvc_rate.baseline(src, inc)

    byfn: dict[str, set] = {}
    for lp in loops:
        if not KERNEL.match(lp["func"] or ""):
            continue
        byfn.setdefault(lp["func"], set()).update(features(lp))

    analysable = {f for f, ft in byfn.items() if not (ft & refused)}
    n = len(allk)
    ceiling = len(vec | analysable)

    print(f"  declared capabilities ({len(caps)}): {', '.join(sorted(caps))}")
    print(f"  features REFUSED: {', '.join(sorted(refused)) or '(none)'}"
          + (f"   [what-if: admitting `{whatif}`]" if whatif else ""))
    print()
    print(f"  kernels                      : {n}")
    print(f"  clang -O3 already vectorizes : {len(vec)}  ({100*len(vec)/n:.1f}%)")
    print(f"  analysable under these caps  : {len(analysable)}")
    print(f"  ...not already vectorized    : {len(analysable - vec)}   <- the headroom")
    print(f"  DERIVED CEILING              : {ceiling}/{n} = {100*ceiling/n:.1f}%")
    print()
    print(f"  published record (GCC, SVE)  : 85/151 = 56.0%")
    print(f"  {'ABOVE' if ceiling >= 85 else 'BELOW'} the record by "
          f"{abs(ceiling-85)} kernels")
    if not whatif:
        import itertools
        live = [f for f in sorted(refused)
                if any(f in ft for ft in byfn.values())]

        def ceil_with(admit: set) -> int:
            r = refused - admit
            return len(vec | {f for f, ft in byfn.items() if not (ft & r)})

        marg = {f: ceil_with({f}) - ceiling for f in live}
        print()
        print("  MARGINAL price (each capability alone) — MISLEADING ON ITS OWN:")
        for f in live:
            print(f"    +{marg[f]:<3} {f:<28} -> {100*(ceiling+marg[f])/n:.1f}%")
        print()
        print("  JOINT price — capabilities here are COMPLEMENTARY, not")
        print("  substitutable: a loop blocked by two features is unlocked by")
        print("  NEITHER alone, so joint gains EXCEED the sum of marginals and")
        print("  marginal pricing systematically under-values a capability that")
        print("  only pays in company. Choose a build ORDER from this table.")
        rows = []
        for k in range(2, len(live) + 1):
            for combo in itertools.combinations(live, k):
                g = ceil_with(set(combo)) - ceiling
                rows.append((g - sum(marg[f] for f in combo), g, combo))
        for excess, g, combo in sorted(rows, key=lambda r: -r[1])[:6]:
            name = " + ".join(c.split(".")[1] for c in combo)
            print(f"    +{g:<3} {name:<44} -> {100*(ceiling+g)/n:5.1f}%"
                  f"   (marginals would say +{g-excess}"
                  f"{', UNDER by ' + str(excess) if excess else ''})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
