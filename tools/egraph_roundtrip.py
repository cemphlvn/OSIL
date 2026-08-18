#!/usr/bin/env python3
"""EGraph round-trip harness (G14): the search-ecosystem analog of G3.

Metric — PRESERVATION SCORE (spec/conformance.md): the fraction of the EGraph
projection's CONTRACT.osil `preserves` fields mechanically verified on the
round trip  OSIL-SIR -> e-graph -> equality saturation -> extraction ->
OSIL-SIR  over every `equivalence` declaration in conformance/corpus/.
Gate G14 requires score = 1.0 (scope = the fixture list, reported alongside).

The corpus IS the rule set: each declared equivalence is simultaneously a
conformance fixture, a rewrite rule the engine runs, and a preservation test.
Fields (profiles/ecosystem/egglog/CONTRACT.osil):
  rule_identity     — every declared equivalence translates 1:1 to a native
                      rewrite; none silently dropped. Bidirectional when BOTH
                      directions are realizable; DIRECTED otherwise. A
                      direction is realizable iff its match side (a) binds
                      every variable the other side needs — the reverse of
                      `(a + b) - b <=> a` would unbind b — and (b) is not a
                      bare variable — the reverse of `x / 1 <=> x` would
                      match every e-class. Both constraints are engine-forced
                      (egglog rejects each as ungrounded). Realized direction
                      is recorded per case; a declaration with no realizable
                      direction is untranslatable and fails loudly.
  equivalence       — under asserted guard facts, saturation merges each
                      declared lhs/rhs pair into one e-class (checked from a
                      pre-saturation DISTINCT state, so the merge is earned)
  guard_selectivity — the negative lane: with the guard fact absent, the same
                      rule must NOT merge lhs/rhs (fixture 020's regime
                      comment, made mechanical)
  term_extraction   — extraction returns a term that re-enters SIR: its text
                      re-lexes under the reference lexer (dogfood, like G3),
                      re-parses, rebuilds, and still sits in the input's class

Guards map to DATA per ADR-0009: `guards { k = v }` -> one nullary relation
`k__v`, asserted once in the positive lane, attached to the birewrite as a
condition. No code generation.

Run: `just egraph`  (uv supplies egglog, pinned per profiles/ecosystem/egglog/VERSIONS).
Writes: conformance/matrix/matrix.yaml cell (own cell only, idempotent) +
docs/reports/roundtrip-egraph-<date>.md
"""
from __future__ import annotations

import ast as pyast
import datetime
import re
import sys
from importlib.metadata import version as pkg_version
from pathlib import Path
from typing import TypeAlias

from egglog import (EGraph, Expr, String, StringLike, birewrite, converter,
                    i64, i64Like, relation, rewrite, vars_)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from osil_check import tokenize  # reference lexer — dogfood, do not fork

SATURATION_STEPS = 5
PRESERVES = ["rule_identity", "equivalence", "guard_selectivity", "term_extraction"]
BINOPS = {"+", "-", "*", "/", "<<", ">>"}


# ------------------------------------------------ SIR term language (egglog)
class Num(Expr):
    def __init__(self, value: i64Like) -> None: ...
    @classmethod
    def var(cls, name: StringLike) -> Num: ...
    def __add__(self, other: NumLike) -> Num: ...
    def __sub__(self, other: NumLike) -> Num: ...
    def __mul__(self, other: NumLike) -> Num: ...
    def __truediv__(self, other: NumLike) -> Num: ...
    def __lshift__(self, other: NumLike) -> Num: ...
    def __rshift__(self, other: NumLike) -> Num: ...


NumLike: TypeAlias = Num | StringLike | i64Like
converter(i64, Num, Num)
converter(String, Num, Num.var)

OPS = {"+": Num.__add__, "-": Num.__sub__, "*": Num.__mul__,
       "/": Num.__truediv__, "<<": Num.__lshift__, ">>": Num.__rshift__}

# one relation object per distinct guard, shared by both lanes of every fixture
_RELATIONS: dict[str, object] = {}


def rel_for(key: str, val: str):
    name = f"{key}__{val}"
    if name not in _RELATIONS:
        _RELATIONS[name] = relation(name)
    return _RELATIONS[name]


# ------------------------------------------- corpus reader (reference lexer)
class Equivalence:
    def __init__(self, name, path, lhs, rhs, guards):
        self.name, self.path = name, path
        self.lhs, self.rhs, self.guards = lhs, rhs, guards
        self.vars = sorted(walk_vars(lhs) | walk_vars(rhs))


def walk_vars(node):
    if node[0] == "var":
        return {node[1]}
    if node[0] == "num":
        return set()
    _, l, r = node
    return walk_vars(l) | walk_vars(r)


def parse_term(toks, i):
    t = toks[i]
    if t.kind == "op" and t.text == "(":
        node, i = parse_expr(toks, i + 1)
        if toks[i].text != ")":
            raise SyntaxError(f"line {toks[i].line}: expected ')'")
        return node, i + 1
    if t.kind == "number":
        return ("num", t.text), i + 1
    if t.kind == "ident":
        return ("var", t.text), i + 1
    raise SyntaxError(f"line {t.line}: unexpected {t.text!r} in expression")


def parse_expr(toks, i):
    """expr := term (binop term)? — every corpus equivalence is either a
    single binop or fully parenthesized; anything richer must FAIL here so the
    reader grows with the suite instead of guessing precedence."""
    left, i = parse_term(toks, i)
    if i < len(toks) and toks[i].kind == "op" and toks[i].text in BINOPS:
        op = toks[i].text
        right, i = parse_term(toks, i + 1)
        return (op, left, right), i
    return left, i


def read_equivalences(path):
    toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if (t.kind == "ident" and t.text == "equivalence" and i + 2 < len(toks)
                and toks[i + 1].kind == "ident" and toks[i + 2].text == "{"):
            name = toks[i + 1].text
            # compose-shaped equivalences (`a then b`) belong to the stage
            # suite (tools/stage_commute.py) — skip LOUDLY, never silently
            if (toks[i + 4].kind == "ident" and toks[i + 4].text == "then"):
                print(f"SKIP (suite: stages) {path.name}: {name}")
                depth, i = 1, i + 3
                while depth:
                    if toks[i].text == "{":
                        depth += 1
                    elif toks[i].text == "}":
                        depth -= 1
                    i += 1
                continue
            lhs, i = parse_expr(toks, i + 3)
            if toks[i].text != "<=>":
                raise SyntaxError(f"{path.name}: expected <=> in {name}")
            rhs, i = parse_expr(toks, i + 1)
            guards = []
            if toks[i].kind == "ident" and toks[i].text == "guards":
                if toks[i + 1].text != "{":
                    raise SyntaxError(f"{path.name}: expected guards block")
                i += 2
                while toks[i].text != "}":
                    key, eq, val = toks[i], toks[i + 1], toks[i + 2]
                    if eq.text != "=":
                        raise SyntaxError(f"{path.name}: guard must be k = v")
                    guards.append((key.text, val.text))
                    i += 3
                i += 1
            if toks[i].text != "}":
                raise SyntaxError(f"{path.name}: unclosed equivalence {name}")
            i += 1
            out.append(Equivalence(name, path, lhs, rhs, guards))
        else:
            i += 1
    return out


# ------------------------------------------------- OSIL AST <-> egglog term
def build(node, leaf):
    if node[0] == "var":
        return leaf(node[1])
    if node[0] == "num":
        return Num(int(node[1]))
    op, l, r = node
    return OPS[op](build(l, leaf), build(r, leaf))


def to_text(node):
    if node[0] == "var":
        return node[1]
    if node[0] == "num":
        return node[1]
    op, l, r = node
    return f"({to_text(l)} {op} {to_text(r)})"


PYOP = {pyast.Add: "+", pyast.Sub: "-", pyast.Mult: "*",
        pyast.Div: "/", pyast.LShift: "<<", pyast.RShift: ">>"}


def repr_to_ast(text):
    """Extraction image -> OSIL AST. egglog-python reprs extracted terms as a
    Python expression over Num.var("x") / Num(n) / operators — parseable with
    the stdlib ast module; anything unmappable raises (never guess)."""
    def conv(n):
        if isinstance(n, pyast.BinOp):
            return (PYOP[type(n.op)], conv(n.left), conv(n.right))
        if isinstance(n, pyast.Call):
            f = n.func
            if isinstance(f, pyast.Attribute) and f.attr == "var":
                return ("var", n.args[0].value)
            if isinstance(f, pyast.Name) and f.id == "Num":
                return ("num", str(n.args[0].value))
        if isinstance(n, pyast.Constant) and isinstance(n.value, int):
            return ("num", str(n.value))
        raise ValueError(f"unmappable extraction repr node: {pyast.dump(n)}")
    return conv(pyast.parse(text, mode="eval").body)


# --------------------------------------------------------------- lanes
def translate(fx):
    """Declared equivalence -> native rule. The REALIZABILITY rule
    (spec/core.md) lives here, once, for every tool that computes over
    declared equivalences. Sets fx.direction; raises on no realizable
    direction — refusal, never a silent drop."""
    pvs = dict(zip(fx.vars, vars_(" ".join(fx.vars), Num)))
    lp = build(fx.lhs, pvs.__getitem__)
    rp = build(fx.rhs, pvs.__getitem__)
    lv, rv = walk_vars(fx.lhs), walk_vars(fx.rhs)
    conds = [rel_for(k, v)() for k, v in fx.guards]
    # a direction is realizable iff its match side binds every variable the
    # other side needs AND is not a bare variable (a lone-var pattern matches
    # every e-class — egglog rejects it as ungrounded)
    fwd = lv >= rv and fx.lhs[0] != "var"
    bwd = rv >= lv and fx.rhs[0] != "var"
    if fwd and bwd:
        rule, fx.direction = birewrite(lp).to(rp, *conds), "<=>"
    elif fwd:
        rule, fx.direction = rewrite(lp).to(rp, *conds), "->"
    elif bwd:
        rule, fx.direction = rewrite(rp).to(lp, *conds), "<-"
    else:
        raise ValueError(f"{fx.name}: no realizable direction "
                         f"(vars {sorted(lv)} vs {sorted(rv)}) — untranslatable")
    return rule


def lane(fx, asserted_pairs):
    """Build one e-graph lane. The rule's CONDITIONS always come from the
    fixture's declared guards; `asserted_pairs` is what actually gets asserted
    as facts — the positive lane passes fx.guards, the negative lane passes
    [], and the regime-expansion pin passes a DIFFERENT fact on purpose."""
    eg = EGraph()
    for k, v in asserted_pairs:
        eg.register(rel_for(k, v)())
    eg.register(translate(fx))
    lhs = eg.let(f"lhs_{fx.name}", build(fx.lhs, Num.var))
    rhs = build(fx.rhs, Num.var)
    return eg, lhs, rhs


def holds(eg, a, b):
    try:
        eg.check(a == b)
        return True
    except Exception:
        return False


def run_fixture(fx):
    r = {}
    # positive lane: guard asserted -> merge must be EARNED across saturation
    eg, lhs, rhs = lane(fx, fx.guards)
    pre_distinct = not holds(eg, lhs, rhs)
    eg.run(SATURATION_STEPS)
    r["equivalence"] = pre_distinct and holds(eg, lhs, rhs)

    # negative lane: guard absent -> the same rule must NOT merge
    if fx.guards:
        eg2, lhs2, rhs2 = lane(fx, [])
        eg2.run(SATURATION_STEPS)
        r["guard_selectivity"] = not holds(eg2, lhs2, rhs2)
    else:  # unguarded equivalence: lane vacuous — flagged, never silent
        r["guard_selectivity"] = True
        r["selectivity_note"] = "no guards declared — negative lane vacuous"

    # extraction lane: image must re-enter SIR through the reference lexer
    extracted = eg.extract(lhs)
    image = to_text(repr_to_ast(repr(extracted)))
    retoks = [t for t in tokenize(image) if t.kind != "eof"]
    ast2, j = parse_expr(retoks, 0)
    rebuilt = build(ast2, Num.var)
    r["term_extraction"] = j == len(retoks) and holds(eg, rebuilt, lhs)
    r["image"] = image
    return r


# ----------------------------------------- adapter self-suite (refusals/pins)
def read_directives(path):
    """`//` header directives, corpus EXPECTED-FAIL style: what this fixture
    expects OF THE ADAPTER (not of the grammar)."""
    expects, pin_assert, suite = None, [], None
    for line in path.read_text().splitlines():
        if not line.startswith("//"):
            break
        body = line[2:].strip()
        if body.startswith("EXPECTED-UNTRANSLATABLE"):
            expects = "untranslatable"
        elif body.startswith("EXPECTED-FAIL"):
            expects = "fail"
        elif body.startswith("PIN-ASSERT:"):
            k, v = body.split(":", 1)[1].split("=")
            pin_assert.append((k.strip(), v.strip()))
        elif body.startswith("SUITE:"):
            suite = body.split(":", 1)[1].strip()
    return expects, pin_assert, suite


def run_adapter_suite():
    """The suite that tests the TESTER: refusal fixtures prove the adapter's
    realizability classification refuses what it must; the regime-expansion
    pin proves guard facts stay literal. An XPASS here is an ALARM (pin
    lifecycle, G10): capability arrived unratified — the run fails."""
    verdicts = []
    for path in sorted((ROOT / "conformance" / "equivalence").glob("*.osil")):
        expects, pin_assert, suite = read_directives(path)
        if suite is not None:  # foreign suite — owned by its own tool
            print(f"SKIP (suite: {suite}) {path.name}")
            continue
        fxs = read_equivalences(path)
        if expects is None or len(fxs) != 1:
            verdicts.append((path.name, "MALFORMED", False,
                             "need exactly one equivalence + an EXPECTED- header"))
            continue
        fx = fxs[0]
        if expects == "untranslatable":
            try:
                lane(fx, fx.guards)
                verdicts.append((path.name, "XPASS-ALARM", False,
                                 f"translated as {fx.direction!r} — refusal expected; "
                                 "RATIFY before accepting"))
            except ValueError as e:
                verdicts.append((path.name, "REFUSE", True, str(e)))
        else:  # expected-fail pin: assert ONLY the pin facts, expect NO merge
            eg, lhs, rhs = lane(fx, pin_assert)
            eg.run(SATURATION_STEPS)
            if holds(eg, lhs, rhs):
                verdicts.append((path.name, "XPASS-ALARM", False,
                                 "merge observed under pin-asserted facts — expansion "
                                 "machinery arrived; STOP and ratify (ADR-0007)"))
            else:
                verdicts.append((path.name, "XFAIL-HOLDS", True,
                                 "no merge without the literal guard fact"))
    return verdicts


# --------------------------------------------------------------- reporting
def write_matrix_cell(upstream, status, verified, all_field, cases, today):
    """Rewrite ONLY our own cell; other adapters' cells pass through untouched."""
    mpath = ROOT / "conformance" / "matrix" / "matrix.yaml"
    txt = mpath.read_text()
    head, *blocks = txt.split("  - spec:")
    cells = ["  - spec:" + b for b in blocks if "egglog-roundtrip" not in b]
    fields = ", ".join(f"{f}: {str(all_field[f]).lower()}" for f in PRESERVES)
    cells.append(f"""  - spec: "0.0.0-draft (grammar v0.5)"
    adapter: "egglog-roundtrip v0 (tools/egraph_roundtrip.py)"
    upstream: "{upstream}"
    status: {status}
    preservation_score: "{verified}/{len(PRESERVES)}"
    fields: {{{fields}}}
    cases: [{', '.join(cases)}]
    checked: {today}
""")
    mpath.write_text(head + "".join(cells))


def main():
    fixtures = []
    for path in sorted((ROOT / "conformance" / "corpus").glob("*.osil")):
        fixtures.extend(read_equivalences(path))
    if not fixtures:
        print("FAIL: no equivalence declarations found in corpus/")
        sys.exit(1)

    names = [fx.name for fx in fixtures]
    per_case, rules_registered = {}, 0
    all_field = {f: True for f in PRESERVES}
    for fx in fixtures:
        results = run_fixture(fx)
        rules_registered += 1  # run_fixture raises if translation fails
        per_case[fx.name] = (results, fx)
        for f in ("equivalence", "guard_selectivity", "term_extraction"):
            all_field[f] &= results[f]
    # rule_identity: every declaration discovered was translated & executed,
    # and names are unique (no silent shadowing)
    all_field["rule_identity"] = (rules_registered == len(fixtures)
                                  and len(set(names)) == len(names))

    verified = sum(all_field[f] for f in PRESERVES)
    score = verified / len(PRESERVES)
    adapter = run_adapter_suite()
    adapter_ok = all(ok for _, _, ok, _ in adapter)
    status = "pass" if score == 1.0 and adapter_ok else "fail"
    today = datetime.date.today().isoformat()

    observed = pkg_version("egglog")
    pins = (ROOT / "profiles" / "ecosystem" / "egglog" / "VERSIONS").read_text()
    pinned = re.search(r"egglog pypi = (\S+)", pins).group(1)
    drift = "" if observed == pinned else f"  [DRIFT: pinned {pinned}]"
    upstream = f"egglog {observed} (PyPI; vendored core rev 2e5657b)"

    write_matrix_cell(upstream, status, verified, all_field,
                      sorted(per_case), today)

    report = [f"# EGraph round-trip report — {today}",
              f"Metric: preservation score = {verified}/{len(PRESERVES)} -> {status.upper()}",
              f"Upstream actually tested: egglog {observed} (PyPI){drift}",
              f"Loop: OSIL-SIR -> egglog -> saturate({SATURATION_STEPS}) -> extract -> OSIL-SIR",
              f"Suite: {len(fixtures)} equivalence declarations (corpus IS the rule set)", ""]
    for name, (results, fx) in sorted(per_case.items()):
        flags = ", ".join(f"{f}={'ok' if results[f] else 'FAIL'}"
                          for f in ("equivalence", "guard_selectivity", "term_extraction"))
        report.append(f"## case {name} ({fx.path.name}): {flags}")
        guard_txt = ", ".join(f"{k} = {v}" for k, v in fx.guards) or "(none)"
        report.append(f"declared: `{to_text(fx.lhs)} <=> {to_text(fx.rhs)}`"
                      f" · guards: {guard_txt}"
                      f" · realized rule: `{fx.direction}`")
        report.append(f"extraction image (re-lexed by reference lexer): `{results['image']}`")
        if "selectivity_note" in results:
            report.append(f"NOTE: {results['selectivity_note']}")
        report.append("")
    report.append("## adapter self-suite (conformance/equivalence/ — tests the tester)")
    for fname, verdict, ok, detail in adapter:
        report.append(f"- {fname}: **{verdict}** — {detail}")
    report.append("")
    report.append("## pins vs observed (drift-watch input, no auto-bump)")
    report.append("pinned:\n```\n" + pins + "```")
    report.append(f"observed: egglog {observed} (PyPI)")
    (ROOT / "docs" / "reports" / f"roundtrip-egraph-{today}.md").write_text(
        "\n".join(report) + "\n")

    print(f"preservation score: {verified}/{len(PRESERVES)} "
          f"({'PASS' if score == 1.0 else 'FAIL'}) "
          f"over cases: {', '.join(sorted(per_case))}")
    for fname, verdict, ok, _ in adapter:
        print(f"{verdict:12s} {fname}")
    held = sum(ok for _, _, ok, _ in adapter)
    print(f"adapter self-suite: {held}/{len(adapter)} hold"
          + ("" if adapter_ok else "  << XPASS ALARM — ratification required"))
    print(f"matrix cell written; report: docs/reports/roundtrip-egraph-{today}.md")
    sys.exit(0 if status == "pass" else 1)


if __name__ == "__main__":
    main()
