#!/usr/bin/env python3
"""Derivation scan (ADVISORY — not a gate): what do the corpus's declared
equivalences JOINTLY entail that no fixture states?

Method: load every declared corpus equivalence into ONE e-graph per WORLD
(a set of asserted guard facts), saturate, then check candidate equalities
the corpus never declares. Every verdict is mechanical (egraph.check); the
non-derivations are knowledge too — they show what a guard regime withholds.

Worlds are FACT ASSERTIONS, not domain truths: the `exact+expansion-applied`
world asserts both `numeric_semantics__exact` and `regime__ExactArithmetic`
BY HAND — it demonstrates what ADR-0007's declared expansion would buy as
machinery, without pretending the machinery exists (ES003 pins that it
doesn't). Scope: .oaas equivalence declarations only; .flow files carry no
declared equivalences yet, so flows are OUT of this scan's reach by
construction — composition-level equivalence needs its own declared term
language before anything can compute over it.

Run: `just derive`. Writes: docs/reports/derivations-egraph-<date>.md
"""
import datetime
import sys
from pathlib import Path

from egglog import EGraph

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from egraph_roundtrip import (Num, build, holds, parse_expr, read_equivalences,
                              rel_for, to_text, translate)
from oaas_check import tokenize

STEPS = 8  # deeper than the gate's 5: chains need headroom

WORLDS = [
    ("exact", [("numeric_semantics", "exact")]),
    ("integer", [("numeric_semantics", "integer")]),
    ("regime-name-only", [("regime", "ExactArithmetic")]),
    ("exact+expansion-applied", [("numeric_semantics", "exact"),
                                 ("regime", "ExactArithmetic")]),
    ("integer+regime-name", [("numeric_semantics", "integer"),
                             ("regime", "ExactArithmetic")]),
]

# candidate DERIVED equalities — none of these lhs/rhs pairs is declared
# as a fixture; each can only hold by rule composition or instantiation
QUERIES = [
    ("chain shift_zero∘strength_reduction", "(x * 2) >> 0", "x << 1"),
    ("inverse_add at a COMPOSITE instance", "((a * c) + (b * c)) - (b * c)", "a * c"),
    ("distributivity (declared: 003)", "(a * c) + (b * c)", "(a + b) * c"),
    ("associativity (declared: 020)", "(a + b) + c", "a + (b + c)"),
    ("two-rule chain identity_div∘inverse_add",
     "(((a * c) + (b * c)) - (b * c)) / 1", "a * c"),
    ("distributivity at a SUBTERM (congruence; first guess mislabeled this "
     "as needing assoc — the scan corrected it)",
     "((a * c) + (b * c)) + d", "((a + b) * c) + d"),
    ("genuinely TWO-regime chain strength_reduction+assoc",
     "(x * 2) + ((y * 2) + z)", "((x << 1) + (y << 1)) + z"),
]

SHOWCASE = "(((a * c) + (b * c)) - (b * c)) / 1"


def term(text):
    toks = [t for t in tokenize(text) if t.kind != "eof"]
    node, j = parse_expr(toks, 0)
    if j != len(toks):
        raise SyntaxError(f"probe did not consume all tokens: {text!r}")
    return node


def main():
    fixtures = []
    for path in sorted((ROOT / "conformance" / "corpus").glob("*.oaas")):
        fixtures.extend(read_equivalences(path))

    today = datetime.date.today().isoformat()
    grid = {}       # (query_label, world_name) -> bool
    images = {}     # world_name -> extraction image of SHOWCASE

    for wname, asserted in WORLDS:
        eg = EGraph()
        for k, v in asserted:
            eg.register(rel_for(k, v)())
        for fx in fixtures:
            eg.register(translate(fx))
        probes = []
        for qi, (label, lt, rt) in enumerate(QUERIES):
            l = eg.let(f"q{qi}_l", build(term(lt), Num.var))
            r = eg.let(f"q{qi}_r", build(term(rt), Num.var))
            probes.append((label, l, r))
        show = eg.let("showcase", build(term(SHOWCASE), Num.var))
        eg.run(STEPS)
        for label, l, r in probes:
            grid[(label, wname)] = holds(eg, l, r)
        images[wname] = repr(eg.extract(show))

    # ------------------------------------------------------------- report
    wnames = [w for w, _ in WORLDS]
    lines = [f"# Derivation scan — {today}",
             "Loop: derivation scan over all corpus equivalences, one e-graph "
             f"per world, saturate({STEPS}). ADVISORY — not a gate; every "
             "verdict is a mechanical egraph.check.",
             f"Suite: {len(fixtures)} declared equivalences · "
             f"{len(QUERIES)} candidate derivations · {len(WORLDS)} worlds", "",
             "| candidate equality | " + " | ".join(wnames) + " |",
             "|---|" + "---|" * len(wnames)]
    for label, lt, rt in QUERIES:
        row = [f"{label}: `{lt}` ≡ `{rt}`"]
        row += ["**DERIVED**" if grid[(label, w)] else "not derived"
                for w in wnames]
        lines.append("| " + " | ".join(row) + " |")
    lines += ["", f"## world-relative extraction of `{SHOWCASE}`"]
    for w in wnames:
        lines.append(f"- {w}: `{images[w]}`")
    lines += ["", "## honest notes",
              "- Worlds assert guard FACTS by hand; none is a claim of domain "
              "truth. `exact+expansion-applied` simulates ADR-0007's declared "
              "expansion as data; ES003 pins that no machinery performs it.",
              "- Non-derivations are load-bearing: a guarded rule withholding "
              "its merge in the wrong world is the guard system working.",
              "- .flow files are OUT of scope: no flow-level equivalences are "
              "declared anywhere in the corpus, so composition equivalence "
              "has nothing to compute over yet (candidate future gate: a "
              "stage-composition term language + declared commutation guards).",
              "- Advisory tool: `just derive` is NOT part of `just test`; the "
              "gate suite stays the ratchet, this scan is the telescope."]
    out = ROOT / "docs" / "reports" / f"derivations-egraph-{today}.md"
    out.write_text("\n".join(lines) + "\n")

    for label, _, _ in QUERIES:
        verdicts = " ".join(f"{w}:{'Y' if grid[(label, w)] else '.'}" for w in wnames)
        print(f"{label:48s} {verdicts}")
    print(f"report: {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
