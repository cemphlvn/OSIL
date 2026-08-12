#!/usr/bin/env python3
"""Stage commutation harness (G15): the pipeline tests itself.

The repo's own architecture is the test object. Corpus 023 declares the
`just test` stages with file-granular read/write resource sets; corpus 024
declares commutation GENERICALLY (`a then b <=> b then a` under
`writes_disjoint = true`). This harness:

  1. computes the binary relation writes_disjoint(A, B) from DECLARED
     write-sets — the first guard that is derived from architecture, not
     hand-asserted (both orders registered: symmetry is asserted, not
     assumed);
  2. registers the generic commutation rule with that relation as its
     condition (guard mapping v0: `writes_disjoint = true` on a two-variable
     generic rule binds the rule's two pattern variables, in LHS order);
  3. checks the FULL pairwise matrix: every write-disjoint pair must DERIVE
     as commuting, every colliding pair must be WITHHELD — both directions
     of the expectation are gated;
  4. holds the pins in conformance/equivalence/ tagged `// SUITE: stages`:
     ES004 pins roundtrip/egraph non-commutation (the shared matrix_yaml
     write — the G14 wart made normative). XPASS = the collision was fixed;
     ALARM and demand ratification (pin lifecycle, G10), never flip silently.

Operand disambiguation (ADR-0010): an identifier naming a declared stage is
a ground stage constant; any other identifier is a pattern variable.

Run: `just stages`. Writes: docs/reports/stage-commute-<date>.md
"""
from __future__ import annotations

import datetime
import sys
from itertools import combinations
from pathlib import Path

from egglog import EGraph, Expr, StringLike, birewrite, relation, vars_

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from egraph_roundtrip import holds, read_directives
from oaas_check import tokenize

SATURATION_STEPS = 5


class Stage(Expr):
    @classmethod
    def named(cls, name: StringLike) -> Stage: ...
    def then(self, other: Stage) -> Stage: ...


writes_disjoint = relation("writes_disjoint", Stage, Stage)


# ------------------------------------------------------------- corpus readers
def read_stages():
    """stage blocks from corpus (reference lexer — dogfood)."""
    stages = {}
    for path in sorted((ROOT / "conformance" / "corpus").glob("*.oaas")):
        toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
        i = 0
        while i < len(toks):
            if toks[i].kind == "ident" and toks[i].text == "stage" \
                    and i + 2 < len(toks) and toks[i + 1].kind == "ident" \
                    and toks[i + 2].text == "{":
                name, i = toks[i + 1].text, i + 3
                rw = {"reads": set(), "writes": set()}
                def qualified(j):
                    parts = [toks[j].text]
                    j += 1
                    while toks[j].kind == "op" and toks[j].text == ".":
                        parts.append(toks[j + 1].text)
                        j += 2
                    return ".".join(parts), j

                while toks[i].text != "}":
                    word = toks[i].text
                    if word == "runs":
                        _, i = qualified(i + 2)  # skip 'runs' '=' qualified_id
                    elif word in rw:
                        i += 2  # reads|writes {
                        while toks[i].text != "}":
                            res, i = qualified(i)
                            rw[word].add(res)
                        i += 1  # }
                    else:
                        raise SyntaxError(f"{path.name}: unexpected {word!r} in stage {name}")
                i += 1
                stages[name] = rw
            else:
                i += 1
    return stages


def read_compose_equivalences(root_dir):
    """compose-shaped equivalences: (name, lhs_ids, rhs_ids, guards, path)."""
    out = []
    for path in sorted(root_dir.glob("*.oaas")):
        toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
        i = 0
        while i < len(toks):
            if toks[i].kind == "ident" and toks[i].text == "equivalence" \
                    and i + 2 < len(toks) and toks[i + 2].text == "{":
                name, i = toks[i + 1].text, i + 3
                if not (toks[i + 1].kind == "ident" and toks[i + 1].text == "then"):
                    i -= 1  # not compose-shaped: leave for the arithmetic suite
                    while toks[i].text != "}":
                        i += 1
                    i += 1
                    continue

                def chain(j):
                    ids = [toks[j].text]
                    j += 1
                    while j + 1 < len(toks) and toks[j].kind == "ident" \
                            and toks[j].text == "then":
                        ids.append(toks[j + 1].text)
                        j += 2
                    return ids, j

                lhs, i = chain(i)
                assert toks[i].text == "<=>", f"{path.name}: expected <=> in {name}"
                rhs, i = chain(i + 1)
                guards = []
                if toks[i].kind == "ident" and toks[i].text == "guards":
                    i += 2
                    while toks[i].text != "}":
                        guards.append((toks[i].text, toks[i + 2].text))
                        i += 3
                    i += 1
                assert toks[i].text == "}", f"{path.name}: unclosed {name}"
                i += 1
                out.append((name, lhs, rhs, guards, path))
            else:
                i += 1
    return out


# --------------------------------------------------------------- translation
def compose(ids, leaf):
    node = leaf(ids[0])
    for s in ids[1:]:
        node = node.then(leaf(s))
    return node


def main():
    stages = read_stages()
    if not stages:
        print("FAIL: no stage declarations found in corpus/")
        sys.exit(1)

    disjoint = {}
    for a, b in combinations(sorted(stages), 2):
        disjoint[(a, b)] = not (stages[a]["writes"] & stages[b]["writes"])

    generics = read_compose_equivalences(ROOT / "conformance" / "corpus")
    if len(generics) != 1:
        print(f"FAIL: expected exactly one generic commutation rule, "
              f"found {len(generics)}")
        sys.exit(1)
    gname, glhs, grhs, gguards, _ = generics[0]
    gvars = [x for x in glhs if x not in stages]
    if sorted(gvars) != sorted(x for x in grhs if x not in stages) \
            or len(gvars) != 2 or dict(gguards) != {"writes_disjoint": "true"}:
        print(f"FAIL: {gname}: v0 supports exactly the two-variable "
              "writes_disjoint-guarded commutation form")
        sys.exit(1)

    eg = EGraph()
    for (a, b), d in disjoint.items():
        if d:  # symmetry asserted, not assumed
            eg.register(writes_disjoint(Stage.named(a), Stage.named(b)))
            eg.register(writes_disjoint(Stage.named(b), Stage.named(a)))
    pv = dict(zip(gvars, vars_(" ".join(gvars), Stage)))
    leaf = lambda x: Stage.named(x) if x in stages else pv[x]
    eg.register(birewrite(compose(glhs, leaf)).to(
        compose(grhs, leaf), writes_disjoint(pv[gvars[0]], pv[gvars[1]])))

    grounds = {}
    for a, b in disjoint:
        grounds[(a, b)] = (
            eg.let(f"c_{a}_{b}", Stage.named(a).then(Stage.named(b))),
            Stage.named(b).then(Stage.named(a)))
    eg.run(SATURATION_STEPS)

    today = datetime.date.today().isoformat()
    rows, mismatches = [], []
    for (a, b), expected in sorted(disjoint.items()):
        l, r = grounds[(a, b)]
        derived = holds(eg, l, r)
        ok = derived == expected
        verdict = ("COMMUTE" if derived else "WITHHELD")
        if not ok:
            mismatches.append((a, b, expected, derived))
        collision = stages[a]["writes"] & stages[b]["writes"]
        why = f"collision: {', '.join(sorted(collision))}" if collision \
            else "writes disjoint"
        rows.append((a, b, verdict, why, ok))
        print(f"{verdict:9s} {a} then {b}  ({why})" + ("" if ok else "  << MISMATCH"))

    # pins (SUITE: stages) — instance fixtures with governance semantics
    pin_rows, pin_ok = [], True
    for path in sorted((ROOT / "conformance" / "equivalence").glob("*.oaas")):
        expects, _, suite = read_directives(path)
        if suite != "stages":
            continue
        for name, lhs, rhs, guards, _ in read_compose_equivalences(path.parent):
            if name != tokenize_first_equiv_name(path):
                continue
            undeclared = [x for x in lhs + rhs if x not in stages]
            if undeclared:
                pin_rows.append((path.name, "MALFORMED", False,
                                 f"undeclared stages {undeclared} in a pin instance"))
                pin_ok = False
                continue
            l = eg.let(f"pin_{name}_l", compose(lhs, Stage.named))
            r = compose(rhs, Stage.named)
            eg.run(SATURATION_STEPS)
            merged = holds(eg, l, r)
            if expects == "fail" and not merged:
                pin_rows.append((path.name, "XFAIL-HOLDS", True,
                                 "no commutation without disjoint writes"))
            elif expects == "fail":
                pin_rows.append((path.name, "XPASS-ALARM", False,
                                 "collision gone — RATIFY before accepting (G10)"))
                pin_ok = False
            else:
                pin_rows.append((path.name, "MALFORMED", False,
                                 "stage-suite fixture without EXPECTED-FAIL"))
                pin_ok = False
    for fname, verdict, _, detail in pin_rows:
        print(f"{verdict:12s} {fname} — {detail}")

    status = "pass" if not mismatches and pin_ok else "fail"
    report = [f"# Stage commutation report — {today}",
              f"Metric: pair matrix {len(rows) - len(mismatches)}/{len(rows)} "
              f"as declared + {sum(ok for _, _, ok, _ in pin_rows)}/{len(pin_rows)}"
              f" pins hold -> {status.upper()}",
              "The architecture under test is this repository's own pipeline "
              "(corpus 023/024).", "",
              "| composition | verdict | why |", "|---|---|---|"]
    for a, b, verdict, why, ok in rows:
        report.append(f"| `{a} then {b}` | {verdict}{'' if ok else ' MISMATCH'} | {why} |")
    report += ["", "## pins"]
    for fname, verdict, _, detail in pin_rows:
        report.append(f"- {fname}: **{verdict}** — {detail}")
    report += ["", "## honest notes",
               "- Write-sets are DECLARED (self-class truth); mechanical "
               "extraction from tool source is future work (ADR-0010).",
               "- Guard is write-write disjointness only; the Bernstein "
               "read-write refinement is recorded, not implemented — egraph "
               "READS matrix_yaml, so the refinement would also pin "
               "roundtrip-then-egraph ordering, not just the write collision.",
               "- Undeclared identifiers in the GENERIC rule become pattern "
               "variables silently; pins reject undeclared stages loudly."]
    (ROOT / "docs" / "reports" / f"stage-commute-{today}.md").write_text(
        "\n".join(report) + "\n")

    print(f"stage commutation: {len(rows) - len(mismatches)}/{len(rows)} pairs "
          f"as declared; pins {'hold' if pin_ok else 'ALARM'} ({status.upper()})")
    print(f"report: docs/reports/stage-commute-{today}.md")
    sys.exit(0 if status == "pass" else 1)


def tokenize_first_equiv_name(path):
    toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
    for i, t in enumerate(toks):
        if t.kind == "ident" and t.text == "equivalence":
            return toks[i + 1].text
    return None


if __name__ == "__main__":
    main()
