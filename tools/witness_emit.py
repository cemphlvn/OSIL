#!/usr/bin/env python3
"""Emit preservation witnesses for every candidate the chooser evaluates (G25).

The PRODUCER side. Kept in its own file so `tools/witness_check.py` — the
validator — imports nothing from the chooser and the independence claim stays
true by construction rather than by care.

Run: `just witness` (emits, then validates)
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import c_choose

SOURCES = [
    ROOT / "optimizer" / "probe" / "none60" / "k.c",
    ROOT / "conformance" / "lift" / "predication" / "cases.c",
    ROOT / "conformance" / "lift" / "repo-pins" / "step.c",
    ROOT / "conformance" / "lift" / "repo-pins" / "replay.c",
    ROOT / "conformance" / "lift" / "repo-pins" / "iteration.c",
]


def main() -> int:
    out = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for src in SOURCES:
            if not src.exists():
                continue
            js = tmp / (src.stem + ".json")
            r = subprocess.run([sys.executable, str(ROOT / "tools" / "c_lift.py"),
                                str(src), "--json", str(js)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  lift failed: {src.name}"); continue
            for lp in json.loads(js.read_text()):
                for cand in c_choose.plans(lp):
                    if cand["kind"] not in c_choose.CANDIDATE_KINDS:
                        continue
                    e = c_choose.evaluate(lp, cand, tmp)
                    w = e.get("witness")
                    if w:
                        w["origin"] = src.name
                        w["chooser_verdict"] = e.get("verdict")
                        out.append(w)
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "witnesses.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"  emitted {len(out)} witness(es) -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
