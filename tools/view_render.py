#!/usr/bin/env python3
"""Governed vocabulary views (G16, ADR-0011): diagrams as conformance artifacts.

A view is a DETERMINISTIC FUNCTION of declarations — never an authored
drawing. This tool reads the same ground truth the harnesses read (shared
readers, tools/osil_read.py), computes canonical view DATA, renders an
austere advisory SVG, and gates with the G4 three-tier verdict: data
zero-diff GATES against blessed goldens, SVG byte-diff ADVISES, pixels
never. Blessing (`just views-bless`) is a ratification act.

Two witnesses run inside every gate pass:
  DETERMINISM  — the views are built twice; any byte difference fails.
  LIE-DETECT   — the views are rebuilt from deliberately perturbed copies of
                 the declarations; if the data does NOT change, the view is
                 decorative rather than derived, and the run fails.

Views:
  projection-map     strata -> ecosystems, preserved dimension + contract
                     fields + verification score (matrix.yaml; dates excluded)
  stage-commutation  declared stages, computed write-disjointness, the
                     withheld pairs (only constraints are drawn)

Run: `just views` (gate) · `just views-bless` (ratification act).
Reads only; goldens live in conformance/golden-render/views/.
"""
from __future__ import annotations

import copy
import json
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from osil_read import read_contract_fields, read_stage_decls, read_vocab

VIEWS = ROOT / "conformance" / "golden-render" / "views"

# a view must grow deliberately: unknown projections fail loudly, never guess
ECOSYSTEM_OF = {"EGraph": "egglog", "ONNX": "onnx", "MLIR": "mlir",
                "Identity": "native"}
ADAPTER_OF = {"EGraph": "egglog-roundtrip", "ONNX": "onnx-roundtrip"}
STRATA_ORDER = ["OSIL-SIR", "OSIL-CIR", "OSIL-NATIVE"]


# ------------------------------------------------------------- ground truth
def scan():
    files = sorted((ROOT / "conformance" / "corpus").glob("*.osil")) + \
            sorted((ROOT / "profiles").rglob("*.osil"))
    projections, stages = {}, {}
    for path in files:
        text = path.read_text()
        rel = str(path.relative_to(ROOT))
        vocab = read_vocab(text)
        for name, src, pres in vocab["projections"]:
            row = projections.setdefault(name, {
                "from": src, "preserve": pres, "declared_in": [],
                "preserves": [], "may_lose": []})
            if row["from"] != src or row["preserve"] != pres:
                raise SystemExit(f"FAIL: projection {name} disagrees across "
                                 f"declarations ({rel})")
            row["declared_in"].append(rel)
            if len(vocab["projections"]) == 1:  # the CONTRACT.osil shape
                fields = read_contract_fields(text)
                row["preserves"] = sorted(set(fields["preserves"]))
                row["may_lose"] = sorted(set(fields["may_lose"]))
        stages.update(read_stage_decls(text))
    for row in projections.values():
        row["declared_in"].sort()
    return projections, stages


def read_matrix_scores():
    scores, adapter = {}, None
    for line in (ROOT / "conformance" / "matrix" / "matrix.yaml").read_text().splitlines():
        s = line.strip()
        if s.startswith("adapter:"):
            adapter = s.split('"')[1].split(" ")[0]
        elif s.startswith("status:") and adapter:
            scores.setdefault(adapter, {})["status"] = s.split(":", 1)[1].strip()
        elif s.startswith("preservation_score:") and adapter:
            scores[adapter]["score"] = s.split('"')[1]
    return scores


# ------------------------------------------------------------- view data
def data_projection_map(projections, scores):
    rows = []
    for name in sorted(projections):
        pj = projections[name]
        if name not in ECOSYSTEM_OF:
            raise SystemExit(f"FAIL: projection {name} has no ecosystem "
                             "mapping — grow the view deliberately")
        cell = scores.get(ADAPTER_OF.get(name))
        rows.append({
            "projection": name, "from": pj["from"],
            "preserve": pj["preserve"], "ecosystem": ECOSYSTEM_OF[name],
            "declared_in": pj["declared_in"],
            "preserves": pj["preserves"], "may_lose": pj["may_lose"],
            "score": cell["score"] if cell else None,
            "status": cell["status"] if cell else "uncontracted",
        })
    seen = [s for s in STRATA_ORDER if any(r["from"] == s for r in rows)]
    seen += sorted({r["from"] for r in rows} - set(seen))
    return {"view": "projection-map", "strata": seen, "projections": rows}


def data_stage_commutation(stages):
    withheld = []
    pairs = list(combinations(sorted(stages), 2))
    for a, b in pairs:
        clash = sorted(stages[a]["writes"] & stages[b]["writes"])
        if clash:
            withheld.append({"a": a, "b": b, "collision": clash})
    return {"view": "stage-commutation",
            "stages": {n: {"reads": sorted(stages[n]["reads"]),
                           "writes": sorted(stages[n]["writes"])}
                       for n in sorted(stages)},
            "pairs_total": len(pairs),
            "commuting": len(pairs) - len(withheld),
            "withheld": withheld}


# ------------------------------------------------------------- advisory SVG
def svg_projection_map(d):
    n = len(d["projections"])
    h = 40 + max(len(d["strata"]) * 120, n * 90)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {h}" '
           'font-family="monospace" font-size="13">',
           "<title>projection-map</title>"]
    sy = {s: 30 + i * 120 for i, s in enumerate(d["strata"])}
    for s, y in sy.items():
        out.append(f'<rect x="20" y="{y}" width="190" height="54" fill="none" stroke="#000"/>')
        out.append(f'<text x="34" y="{y + 33}">{s}</text>')
    for i, r in enumerate(sorted(d["projections"], key=lambda r: r["projection"])):
        y = 30 + i * 90
        dash = ' stroke-dasharray="5 4"' if r["status"] == "uncontracted" else ""
        out.append(f'<rect x="630" y="{y}" width="230" height="54" fill="none" stroke="#000"{dash}/>')
        out.append(f'<text x="644" y="{y + 24}">{r["ecosystem"]}</text>')
        out.append(f'<text x="644" y="{y + 42}" font-size="11">via {r["projection"]}</text>')
        y0, y1 = sy[r["from"]] + 27, y + 27
        out.append(f'<polyline points="210,{y0} 630,{y1}" fill="none" stroke="#000"{dash}/>')
        verdict = f'{r["score"]} {r["status"]}' if r["score"] else r["status"]
        ly = (y0 + y1) // 2 - 6
        out.append(f'<text x="240" y="{ly}" font-size="11">preserve '
                   f'{",".join(r["preserve"])} · {verdict}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def svg_stage_commutation(d):
    names = sorted(d["stages"])
    rows = (len(names) + 3) // 4
    h = 60 + rows * 80 + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 880 {h}" '
           'font-family="monospace" font-size="13">',
           "<title>stage-commutation</title>"]
    center = {}
    for i, nname in enumerate(names):
        x, y = 20 + (i % 4) * 215, 30 + (i // 4) * 80
        center[nname] = (x + 90, y + 20)
        out.append(f'<rect x="{x}" y="{y}" width="180" height="40" fill="none" stroke="#000"/>')
        out.append(f'<text x="{x + 14}" y="{y + 25}">{nname}</text>')
    for w in d["withheld"]:
        (x0, y0), (x1, y1) = center[w["a"]], center[w["b"]]
        out.append(f'<polyline points="{x0},{y0} {x1},{y1}" fill="none" '
                   'stroke="#000" stroke-dasharray="3 3"/>')
        mx, my = (x0 + x1) // 2, (y0 + y1) // 2 - 6
        out.append(f'<text x="{mx}" y="{my}" font-size="11">'
                   f'{",".join(w["collision"])}</text>')
    out.append(f'<text x="20" y="{h - 16}" font-size="11">'
               f'{d["commuting"]}/{d["pairs_total"]} pairs commute; '
               'only constraints drawn (dashed = shared write)</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def build(projections, stages, scores):
    pm = data_projection_map(projections, scores)
    sc = data_stage_commutation(stages)
    canon = lambda d: json.dumps(d, indent=1, sort_keys=True) + "\n"
    return {"projection-map.json": canon(pm),
            "projection-map.svg": svg_projection_map(pm),
            "stage-commutation.json": canon(sc),
            "stage-commutation.svg": svg_stage_commutation(sc)}


# ------------------------------------------------------------- gate
def main():
    bless = "--bless" in sys.argv
    projections, stages = scan()
    scores = read_matrix_scores()

    built = build(projections, stages, scores)
    if build(projections, stages, scores) != built:
        print("FAIL: non-deterministic build (two passes differ)")
        sys.exit(1)

    # lie-detect: perturbed declarations MUST change the derived data
    p_st = copy.deepcopy(stages)
    p_st["roundtrip"]["writes"].discard("conformance.matrix.matrix_yaml")
    p_pj = copy.deepcopy(projections)
    egraph_fields = p_pj["EGraph"]["preserves"]
    egraph_fields.pop()  # drop one contracted field
    lies = [
        ("stage-commutation.json",
         build(projections, p_st, scores)["stage-commutation.json"]),
        ("projection-map.json",
         build(p_pj, stages, scores)["projection-map.json"]),
    ]
    for fname, perturbed in lies:
        if perturbed == built[fname]:
            print(f"FAIL: LIE-DETECT — perturbing declarations did not "
                  f"change {fname}; the view is decorative, not derived")
            sys.exit(1)
    print("LIE-DETECT ok (2/2 perturbations change view data) · "
          "DETERMINISM ok (double build identical)")

    if bless:
        VIEWS.mkdir(parents=True, exist_ok=True)
        for fname, content in sorted(built.items()):
            (VIEWS / fname).write_text(content)
            print(f"BLESSED  views/{fname}")
        print("blessing is a RATIFICATION ACT — record who/why in the PR")
        sys.exit(0)

    failures = 0
    for fname, content in sorted(built.items()):
        golden = VIEWS / fname
        gate = fname.endswith(".json")
        if not golden.exists():
            print(f"FAIL     views/{fname}: no golden "
                  "(run `just views-bless` in a ratified change)")
            failures += 1
        elif golden.read_text() != content:
            if gate:
                print(f"FAIL     views/{fname}: derived data diverged from "
                      "blessed golden — a declaration changed; re-bless "
                      "in a ratified change")
                failures += 1
            else:
                print(f"ADVISORY views/{fname}: svg differs (renderer "
                      "constants changed?) — data gate is authoritative")
        else:
            print(f"VIEW-OK  views/{fname}")
    if failures:
        sys.exit(1)
    print("Governed-views contract satisfied: derived data matches "
          "blessed goldens; diagrams are coupled to ground truth.")


if __name__ == "__main__":
    main()
