#!/usr/bin/env python3
"""G4 harness: golden-render loop for the visual identity projection.

Three-tier verdict (spec/visual.md; research U4):
  1. GATE, zero tolerance — structural diff of the layout-as-data model:
     parse -> canonical structure -> exact match against the golden JSON.
     Viewport is EXCLUDED (non-normative session state).
  2. ADVISORY — deterministic SVG byte-diff. The renderer builds SVG as pure
     strings with fixed-metrics monospace text (char-count x constant width),
     never measuring system fonts — U4's #1 flakiness source is deleted by
     construction, not mitigated. A mismatch warns (the renderer changed);
     only the data gate fails the build.
  3. NEVER — pixel diff.

Also enforced per file:
  - anchoring: every layout node/label references a semantic identifier; every
    layout edge (src -> dst) matches a semantic edge (D2 working decision).
  - round-trip: structure -> emitted layout text -> reparse -> identical
    structure (the identity projection's zero-diff invariant, mechanically).

--bless writes/updates goldens. Blessing is a ratification act: record who/why
in the PR (GOVERNANCE.md — goldens update only via human-ratified change).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from oaas_check import tokenize  # reference lexer — dogfood, do not fork

GOLD = ROOT / "conformance" / "golden-render"
CHAR_W = 8  # fixed text metrics: no font measurement anywhere


class Cur:
    def __init__(self, toks):
        self.t = [x for x in toks if x.kind != "eof"]
        self.i = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def next(self):
        t = self.t[self.i]
        self.i += 1
        return t

    def eat_op(self, op):
        t = self.next()
        assert t.kind == "op" and t.text == op, f"line {t.line}: want {op!r} got {t.text!r}"

    def eat_word(self, w=None):
        t = self.next()
        assert t.kind == "ident" and (w is None or t.text == w), \
            f"line {t.line}: want {w or 'identifier'} got {t.text!r}"
        return t

    def at_op(self, op):
        t = self.peek()
        return t is not None and t.kind == "op" and t.text == op

    def at_word(self, *ws):
        t = self.peek()
        return t is not None and t.kind == "ident" and t.text in ws


def number(cur):
    neg = cur.at_op("-")
    if neg:
        cur.next()
    t = cur.next()
    assert t.kind == "number", f"line {t.line}: want number got {t.text!r}"
    v = float(t.text)
    return -v if neg else v


def bounds(cur):
    cur.eat_op("[")
    x = number(cur); cur.eat_op(",")
    y = number(cur); cur.eat_op(",")
    w = number(cur); cur.eat_op(",")
    h = number(cur); cur.eat_op("]")
    return [x, y, w, h]


def read(text):
    """Flow text -> (io names, semantic edges, layout structure, viewport)."""
    cur = Cur(tokenize(text))
    ios, sem_edges = [], []
    layout = {"nodes": {}, "edges": [], "labels": {}}
    viewport = None
    while cur.peek():
        if cur.at_word("use"):
            cur.next(); cur.eat_word()
            while cur.at_op("."):
                cur.next(); cur.eat_word()
        elif cur.at_word("input", "const", "output"):
            cur.next()
            name = cur.eat_word().text
            cur.eat_op(":"); cur.eat_word()
            if cur.at_op("<"):
                cur.next(); cur.eat_word(); cur.eat_op(">")
            if cur.at_op("["):
                cur.next()
                while not cur.at_op("]"):
                    cur.next()
                cur.eat_op("]")
            ios.append(name)
        elif cur.at_word("layout") and cur.peek(1) is not None \
                and cur.peek(1).kind == "op" and cur.peek(1).text == "{":
            cur.next(); cur.eat_op("{")
            while not cur.at_op("}"):
                if cur.at_word("node"):
                    cur.next()
                    n = cur.eat_word().text
                    b = bounds(cur)
                    coll = z = None
                    if cur.at_word("collapsed"):
                        cur.next(); cur.eat_op("=")
                        coll = cur.eat_word().text == "true"
                    if cur.at_word("z"):
                        cur.next(); cur.eat_op("=")
                        z = int(number(cur))
                    layout["nodes"][n] = {"bounds": b, "collapsed": coll, "z": z}
                elif cur.at_word("edge"):
                    cur.next()
                    s = cur.eat_word().text
                    cur.eat_op("->")
                    d = cur.eat_word().text
                    cur.eat_word("waypoints"); cur.eat_op("[")
                    pts = []
                    while cur.at_op("("):
                        cur.next()
                        x = number(cur); cur.eat_op(",")
                        y = number(cur); cur.eat_op(")")
                        pts.append([x, y])
                    cur.eat_op("]")
                    layout["edges"].append({"src": s, "dst": d, "waypoints": pts})
                elif cur.at_word("label"):
                    cur.next()
                    o = cur.eat_word().text
                    layout["labels"][o] = bounds(cur)
                elif cur.at_word("viewport"):
                    cur.next(); cur.eat_op("[")
                    x = number(cur); cur.eat_op(",")
                    y = number(cur); cur.eat_op(",")
                    zm = number(cur); cur.eat_op("]")
                    viewport = [x, y, zm]
                else:
                    t = cur.peek()
                    raise AssertionError(f"line {t.line}: bad layout stmt {t.text!r}")
            cur.eat_op("}")
        else:
            srcs = [cur.eat_word().text]
            while cur.at_op(","):
                cur.next()
                srcs.append(cur.eat_word().text)
            cur.eat_op("->")
            cur.eat_word()
            if cur.at_op("::"):
                cur.next(); cur.eat_word()
            if cur.at_op("@"):
                cur.next(); cur.next()
            cur.eat_op("->")
            if cur.at_op("("):                     # multi-output (D3/G6)
                cur.next()
                dsts = [cur.eat_word().text]
                while cur.at_op(","):
                    cur.next()
                    dsts.append(cur.eat_word().text)
                cur.eat_op(")")
            else:
                dsts = [cur.eat_word().text]
            sem_edges.append((srcs, dsts))
    return ios, sem_edges, layout, viewport


def canonical(layout):
    return {
        "nodes": {n: layout["nodes"][n] for n in sorted(layout["nodes"])},
        "edges": sorted(layout["edges"], key=lambda e: (e["src"], e["dst"])),
        "labels": {o: layout["labels"][o] for o in sorted(layout["labels"])},
    }


def fmt(v):
    return f"{v:g}"


def emit(layout, viewport):
    lines = ["layout {"]
    for n in sorted(layout["nodes"]):
        e = layout["nodes"][n]
        line = f"    node {n} [{', '.join(fmt(v) for v in e['bounds'])}]"
        if e["collapsed"] is not None:
            line += f" collapsed = {'true' if e['collapsed'] else 'false'}"
        if e["z"] is not None:
            line += f" z = {e['z']}"
        lines.append(line)
    for e in sorted(layout["edges"], key=lambda e: (e["src"], e["dst"])):
        pts = " ".join(f"({fmt(x)},{fmt(y)})" for x, y in e["waypoints"])
        lines.append(f"    edge {e['src']} -> {e['dst']} waypoints [{pts}]")
    for o in sorted(layout["labels"]):
        lines.append(f"    label {o} [{', '.join(fmt(v) for v in layout['labels'][o])}]")
    if viewport is not None:
        lines.append(f"    viewport [{', '.join(fmt(v) for v in viewport)}]")
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_svg(layout, title):
    xs, ys = [], []
    for e in layout["nodes"].values():
        x, y, w, h = e["bounds"]
        xs += [x, x + w]; ys += [y, y + h]
    for b in layout["labels"].values():
        xs += [b[0], b[0] + b[2]]; ys += [b[1], b[1] + b[3]]
    for e in layout["edges"]:
        for x, y in e["waypoints"]:
            xs.append(x); ys.append(y)
    minx, miny = min(xs) - 20, min(ys) - 20
    vw, vh = max(xs) - minx + 20, max(ys) - miny + 20
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="{fmt(minx)} {fmt(miny)} {fmt(vw)} {fmt(vh)}" '
             f'font-family="monospace" font-size="13">',
             f'<title>{title}</title>']
    for n in sorted(layout["nodes"], key=lambda n: (layout["nodes"][n]["z"] or 0, n)):
        x, y, w, h = layout["nodes"][n]["bounds"]
        parts.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" '
                     f'height="{fmt(h)}" fill="none" stroke="#000"/>')
        parts.append(f'<text x="{fmt(x + 8)}" y="{fmt(y + h / 2 + 4)}" '
                     f'textLength="{len(n) * CHAR_W}">{n}</text>')
    for e in sorted(layout["edges"], key=lambda e: (e["src"], e["dst"])):
        pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in e["waypoints"])
        parts.append(f'<polyline points="{pts}" fill="none" stroke="#000"/>')
    for o in sorted(layout["labels"]):
        x, y, w, h = layout["labels"][o]
        parts.append(f'<text x="{fmt(x)}" y="{fmt(y + h - 4)}" '
                     f'textLength="{len(o) * CHAR_W}">{o}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    if "--draw" in sys.argv:
        # user-facing verb: render one .flow (with a layout block) to SVG.
        # No auto-layout engine exists BY DESIGN (layout is data, the Mermaid
        # trade was rejected) — a flow without a layout block cannot render.
        i = sys.argv.index("--draw")
        src = Path(sys.argv[i + 1])
        out = Path(sys.argv[i + 2]) if len(sys.argv) > i + 2 else \
            Path.cwd() / (src.stem + ".svg")
        _, _, layout, _ = read(src.read_text())
        if not layout["nodes"]:
            sys.exit(f"{src}: no layout block — layout is data; add one "
                     "(there is deliberately no auto-layout engine)")
        out.write_text(render_svg(layout, src.stem))
        print(f"wrote {out}")
        return

    bless = "--bless" in sys.argv
    targets = [p for p in sorted((ROOT / "conformance" / "corpus").glob("*.flow"))
               if "layout {" in p.read_text()]
    if not targets:
        print("no .flow corpus files carry a layout block yet")
        return
    failed = []
    for p in targets:
        ios, sem_edges, layout, viewport = read(p.read_text())
        universe = set(ios) \
            | {d for _, dsts in sem_edges for d in dsts} \
            | {s for srcs, _ in sem_edges for s in srcs}
        problems = [f"layout node {n!r} not a semantic identifier"
                    for n in layout["nodes"] if n not in universe]
        problems += [f"label owner {o!r} not a semantic identifier"
                     for o in layout["labels"] if o not in universe]
        problems += [
            f"layout edge {e['src']} -> {e['dst']} matches no semantic edge"
            for e in layout["edges"]
            if not any(e["dst"] in dsts and e["src"] in srcs
                       for srcs, dsts in sem_edges)]

        # identity round-trip: structure -> text -> structure, zero diff
        _, _, relayout, reviewport = read(emit(layout, viewport))
        if canonical(relayout) != canonical(layout) or reviewport != viewport:
            problems.append("round-trip: re-parsed structure differs")

        canon = canonical(layout)
        svg = render_svg(layout, p.stem)
        gj, gs = GOLD / f"{p.stem}.layout.json", GOLD / f"{p.stem}.svg"

        if bless:
            gj.write_text(json.dumps(canon, indent=1, sort_keys=True) + "\n")
            gs.write_text(svg)
            verdict = "BLESSED"
        elif problems:
            verdict = "FAIL"
        elif not gj.exists():
            problems.append("no golden (run --bless in a ratified change)")
            verdict = "FAIL"
        elif json.loads(gj.read_text()) != canon:
            problems.append("layout-data diff vs golden (GATE)")
            verdict = "FAIL"
        else:
            verdict = "PASS"
            if not gs.exists() or gs.read_text() != svg:
                verdict = "PASS (svg ADVISORY mismatch — renderer changed?)"
        if problems and not bless:
            failed.append(p.stem)
        print(f"{verdict:8} {p.relative_to(ROOT)}"
              + ("".join(f"\n         - {m}" for m in problems) if problems and not bless else ""))
    if failed:
        sys.exit(1)
    print("\nGolden-render contract satisfied (data gate; svg advisory; pixels never).")


if __name__ == "__main__":
    main()
