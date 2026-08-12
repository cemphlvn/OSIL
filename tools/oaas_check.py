#!/usr/bin/env python3
"""G1 validator: parse the conformance corpus (and all .oaas/.flow files in
profiles/) against grammar/oaas.ebnf v0.1, tracking production coverage.

Contract (gate G1): every corpus file parses; every grammar production fired
by >=1 corpus file. Files whose header contains EXPECTED-FAIL must NOT parse
(their parsing would mean a gap silently closed without ratification).

Stdlib only, by design: the parser is the reference implementation of the
grammar, and the grammar is small enough that a dependency would cost more
than it saves. Keywords are CONTEXTUAL (see grammar note): matched by
position, never reserved — `equivalence` is a valid id_list member.
"""
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- tokenizer
TOKEN_RE = re.compile(r"""
    (?P<comment>//[^\n]*)
  | (?P<string>"[^"\n]*")
  | (?P<number>\d+\.\d+|\d+)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_]*(?:-[A-Za-z0-9_]+)*)
  | (?P<op><=>|->|::|<<|>>|<=|>=|==|[{}()\[\]<>,:=@+\-*/.])
  | (?P<ws>\s+)
""", re.VERBOSE)


class Tok:
    __slots__ = ("kind", "text", "line", "start", "end")
    def __init__(self, kind, text, line, start, end):
        self.kind, self.text, self.line = kind, text, line
        self.start, self.end = start, end
    def __repr__(self):
        return f"{self.kind}({self.text!r})@{self.line}"


def tokenize(src: str):
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise ParseError(f"line {line}: unexpected character {src[pos]!r}")
        kind = m.lastgroup
        text = m.group()
        if kind not in ("ws", "comment"):
            toks.append(Tok(kind, text, line, m.start(), m.end()))
        line += text.count("\n")
        pos = m.end()
    toks.append(Tok("eof", "<eof>", line, len(src), len(src)))
    return toks


class ParseError(Exception):
    pass


# ------------------------------------------------------------------ parser
class Parser:
    def __init__(self, toks, coverage: set, alts: set):
        self.toks, self.i, self.cov, self.alts = toks, 0, coverage, alts

    # -- helpers ----------------------------------------------------------
    def peek(self, k=0):
        return self.toks[min(self.i + k, len(self.toks) - 1)]

    def at_word(self, *words):
        t = self.peek()
        return t.kind == "ident" and t.text in words

    def take(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect_op(self, op):
        t = self.take()
        if t.kind != "op" or t.text != op:
            raise ParseError(f"line {t.line}: expected {op!r}, got {t.text!r}")
        return t

    def expect_word(self, word):
        t = self.take()
        if t.kind != "ident" or t.text != word:
            raise ParseError(f"line {t.line}: expected keyword {word!r}, got {t.text!r}")
        return t

    def expect_ident(self):
        t = self.take()
        if t.kind != "ident":
            raise ParseError(f"line {t.line}: expected identifier, got {t.text!r}")
        return t

    def fire(self, production):
        self.cov.add(production)

    def alt(self, name):
        self.alts.add(name)

    # -- entry points ------------------------------------------------------
    def parse_oaas_document(self):
        self.fire("oaas_document")
        while self.peek().kind != "eof":
            self.oaas_declaration()

    def parse_flow_document(self):
        self.fire("flow_document")
        while self.peek().kind != "eof":
            self.flow_statement()

    # -- .oaas declarations -------------------------------------------------
    def oaas_declaration(self):
        self.fire("oaas_declaration")
        t = self.peek()
        if t.kind != "ident":
            raise ParseError(f"line {t.line}: expected declaration, got {t.text!r}")
        dispatch = {
            "profile": self.profile_decl, "projection": self.projection_decl,
            "equivalence": self.equivalence_decl, "model": self.model_decl,
            "invariant": self.invariant_decl, "operator": self.operator_decl,
            "preserves": self.contract_decl, "concept": self.concept_decl,
            "actor": self.actor_decl,
        }
        fn = dispatch.get(t.text)
        if fn is None:
            raise ParseError(
                f"line {t.line}: {t.text!r} does not start any .oaas declaration")
        fn()

    def profile_decl(self):
        self.fire("profile_decl")
        self.expect_word("profile")
        self.qualified_id()
        self.expect_op("{")
        while not self.at_op("}"):
            self.profile_field()
        self.expect_op("}")

    def profile_field(self):
        self.fire("profile_field")
        self.expect_ident()
        if self.peek().kind == "string":
            self.alt("profile_field:string-keyed")
            self.take()
        else:
            self.alt("profile_field:plain")
        self.expect_op("=")
        self.literal()

    def projection_decl(self):
        self.fire("projection_decl")
        self.expect_word("projection")
        self.expect_ident()
        self.expect_op("{")
        self.expect_word("from")
        self.expect_ident()
        self.expect_word("preserve")
        self.id_list(stop_words={"}"})
        self.expect_op("}")

    def equivalence_decl(self):
        self.fire("equivalence_decl")
        self.expect_word("equivalence")
        self.expect_ident()
        self.expect_op("{")
        self.expr()
        self.expect_op("<=>")
        self.expr()
        if self.at_word("guards"):
            self.guards_block()
        self.expect_op("}")

    def guards_block(self):
        self.fire("guards_block")
        self.expect_word("guards")
        self.expect_op("{")
        while not self.at_op("}"):
            self.expect_ident()
            self.expect_op("=")
            self.literal()
        self.expect_op("}")

    def model_decl(self):
        self.fire("model_decl")
        self.expect_word("model")
        self.expect_ident()
        self.expect_op("{")
        while not self.at_op("}"):
            self.model_field()
        self.expect_op("}")

    def model_field(self):
        self.fire("model_field")
        if self.at_word("purpose"):
            self.alt("model_field:purpose")
            self.take()
            self.expect_op(":")
            self.expect_ident()
        elif self.at_word("constraints"):
            self.alt("model_field:constraints")
            self.constraints_block()
        elif self.at_word("ecosystem"):
            self.alt("model_field:ecosystem")
            self.take()
            self.expect_ident()
        else:
            t = self.peek()
            raise ParseError(f"line {t.line}: bad model field {t.text!r}")

    def constraints_block(self):
        self.fire("constraints_block")
        self.expect_word("constraints")
        self.expect_op("{")
        while not self.at_op("}"):
            self.constraint()
        self.expect_op("}")

    def constraint(self):
        self.fire("constraint")
        self.expect_ident()
        self.rel_op()
        self.value()

    def invariant_decl(self):
        self.fire("invariant_decl")
        self.expect_word("invariant")
        self.expect_ident()

    def operator_decl(self):
        self.fire("operator_decl")
        self.expect_word("operator")
        self.expect_ident()
        self.expect_op("{")
        while not self.at_op("}"):
            self.operator_field()
        self.expect_op("}")

    def operator_field(self):
        self.fire("operator_field")
        if self.at_word("goal"):
            self.alt("operator_field:goal")
            self.take()
            self.expect_op(":")
            self.expect_ident()
        elif self.at_word("preserves") and self.peek(1).kind == "op" \
                and self.peek(1).text == ":":
            self.alt("operator_field:preserves")
            self.take()
            self.expect_op(":")
            self.constraint()
        else:
            self.alt("operator_field:constraint")
            self.constraint()

    def contract_decl(self):
        self.fire("contract_decl")
        self.fire("preserves_block")
        self.expect_word("preserves")
        self.expect_op("{")
        self.id_list(stop_words={"}"})
        self.expect_op("}")
        if self.at_word("may_lose"):
            self.fire("may_lose_block")
            self.take()
            self.expect_op("{")
            self.id_list(stop_words={"}"})
            self.expect_op("}")

    def concept_decl(self):
        self.fire("concept_decl")
        self.expect_word("concept")
        self.expect_ident()
        self.expect_op("{")
        self.expect_word("equivalent_under")
        self.expect_op("{")
        self.arg_list()
        self.expect_op("}")
        self.expect_word("to")
        self.expect_op("{")
        self.id_list(stop_words={"}"})
        self.expect_op("}")
        self.expect_op("}")

    # -- actors: operating policy as vocabulary (GAP-1, closed at G2) ----------
    def actor_decl(self):
        self.fire("actor_decl")
        self.expect_word("actor")
        self.expect_ident()
        self.expect_op("{")
        while not self.at_op("}"):
            self.actor_field()
        self.expect_op("}")

    def actor_field(self):
        self.fire("actor_field")
        if self.at_word("scope"):
            self.alt("actor_field:scope")
            self.scope_block()
        elif self.at_word("verbs"):
            self.alt("actor_field:verbs")
            self.word_id_block("verbs", "verbs_block")
        elif self.at_word("invariants"):
            self.alt("actor_field:invariants")
            self.word_id_block("invariants", "invariants_block")
        elif self.at_word("ratify"):
            self.alt("actor_field:ratify")
            self.word_id_block("ratify", "ratify_block")
        else:
            t = self.peek()
            raise ParseError(f"line {t.line}: bad actor field {t.text!r}")

    def word_id_block(self, word, production):
        self.fire(production)
        self.expect_word(word)
        self.expect_op("{")
        self.id_list(stop_words={"}"})
        self.expect_op("}")

    def scope_block(self):
        self.fire("scope_block")
        self.expect_word("scope")
        self.expect_op("{")
        self.fire("path_list")
        self.path_ref()
        while True:
            if self.at_op(","):
                self.take()
                self.path_ref()
                continue
            if self.peek().kind == "ident":
                self.path_ref()
                continue
            break
        self.expect_op("}")

    def path_ref(self):
        # components ADJACENT (no whitespace); whitespace separates sibling
        # paths — the juxtaposition rule ratified at G2
        self.fire("path_ref")
        last = self.expect_ident()
        while self.at_op("/") and self.peek().start == last.end:
            last = self.take()
            if self.peek().kind == "ident" and self.peek().start == last.end:
                last = self.take()
            else:
                break

    # -- .flow statements -----------------------------------------------------
    def flow_statement(self):
        self.fire("flow_statement")
        if self.at_word("use"):
            self.use_decl()
        elif self.at_word("input", "const", "output"):
            self.io_decl()
        else:
            self.edge_stmt()

    def use_decl(self):
        self.fire("use_decl")
        self.expect_word("use")
        self.qualified_id()

    def io_decl(self):
        self.fire("io_decl")
        kw = self.take()  # input | const | output (checked by caller)
        self.alt(f"io_decl:{kw.text}")
        self.expect_ident()
        self.expect_op(":")
        self.type_ref()

    def type_ref(self):
        self.fire("type")
        self.expect_ident()
        if self.at_op("<"):
            self.take()
            self.expect_ident()
            self.expect_op(">")
        if self.at_op("["):
            self.take()
            self.fire("dim_list")
            self.dim()
            while self.at_op(","):
                self.take()
                self.dim()
            self.expect_op("]")

    def dim(self):
        self.fire("dim")
        t = self.take()
        if t.kind not in ("ident", "number"):
            raise ParseError(f"line {t.line}: bad dimension {t.text!r}")

    def edge_stmt(self):
        self.fire("edge_stmt")
        self.id_list(stop_ops={"->"})
        self.expect_op("->")
        self.op_ref()
        self.expect_op("->")
        self.expect_ident()

    def op_ref(self):
        self.fire("op_ref")
        self.expect_ident()
        if self.at_op("::"):
            self.take()
            self.expect_ident()
        if self.at_op("@"):
            self.take()
            t = self.take()
            if t.kind != "number" or "." in t.text:
                raise ParseError(f"line {t.line}: expected integer after @")

    # -- expressions -----------------------------------------------------------
    def expr(self):
        self.fire("expr")
        self.term()
        while self.at_op("+", "-"):
            self.fire("add_op")
            self.alt("add_op:" + self.take().text)
            self.term()

    def term(self):
        self.fire("term")
        self.factor()
        while self.at_op("*", "/", "<<", ">>"):
            self.fire("mul_op")
            self.alt("mul_op:" + self.take().text)
            self.factor()

    def factor(self):
        self.fire("factor")
        t = self.peek()
        if t.kind == "op" and t.text == "(":
            self.alt("factor:paren")
            self.take()
            self.expr()
            self.expect_op(")")
        elif t.kind in ("ident", "number"):
            self.alt("factor:identifier" if t.kind == "ident" else "factor:number")
            self.take()
        else:
            raise ParseError(f"line {t.line}: bad factor {t.text!r}")

    # -- shared small productions -----------------------------------------------
    def qualified_id(self):
        self.fire("qualified_id")
        self.expect_ident()
        while self.at_op("."):
            self.take()
            self.expect_ident()

    def id_list(self, stop_words=frozenset(), stop_ops=frozenset()):
        self.fire("id_list")
        def at_stop():
            t = self.peek()
            if t.kind == "op" and (t.text in stop_ops or t.text in stop_words):
                return True
            return t.kind == "ident" and t.text in stop_words
        self.expect_ident()
        while True:
            if self.at_op(","):
                self.take()
                self.expect_ident()
                continue
            t = self.peek()
            if t.kind == "ident" and not at_stop():
                self.take()
                continue
            break

    def arg_list(self):
        self.fire("arg_list")
        self.arg()
        while self.at_op(","):
            self.take()
            self.arg()

    def arg(self):
        self.fire("arg")
        self.expect_ident()
        if self.at_op("="):
            self.take()
            self.literal()

    def rel_op(self):
        self.fire("rel_op")
        t = self.take()
        if not (t.kind == "op" and t.text in ("<", "<=", ">", ">=", "=", "==")):
            raise ParseError(f"line {t.line}: expected relational op, got {t.text!r}")
        self.alt("rel_op:" + t.text)

    def value(self):
        self.fire("value")
        t = self.peek()
        if t.kind == "number":
            num = self.take()
            nxt = self.peek()
            # quantity = number ADJACENT to unit (no whitespace) — juxtaposition
            # rule ratified at G2, closing GAP-3: `20ms` is a quantity,
            # `>= 0.997\nmemory` is not
            if nxt.kind == "ident" and nxt.start == num.end:
                self.fire("quantity")
                self.take()
            else:
                self.fire("number")
        else:
            self.literal()

    def literal(self):
        self.fire("literal")
        t = self.take()
        if t.kind == "ident" and t.text in ("true", "false"):
            self.fire("boolean")
            self.alt("literal:boolean")
        elif t.kind == "number":
            self.fire("number")
            self.alt("literal:number")
        elif t.kind == "ident":
            self.alt("literal:identifier")
        elif t.kind == "string":
            self.alt("literal:string")
        else:
            raise ParseError(f"line {t.line}: bad literal {t.text!r}")

    def at_op(self, *ops):
        t = self.peek()
        return t.kind == "op" and t.text in ops


ALL_PRODUCTIONS = [
    "oaas_document", "flow_document", "oaas_declaration", "flow_statement",
    "profile_decl", "profile_field", "projection_decl", "equivalence_decl",
    "guards_block", "model_decl", "model_field", "constraints_block",
    "constraint", "invariant_decl", "operator_decl", "operator_field",
    "contract_decl", "preserves_block", "may_lose_block", "concept_decl",
    "use_decl", "io_decl", "type", "dim_list", "dim", "edge_stmt", "op_ref",
    "expr", "term", "factor", "add_op", "mul_op", "qualified_id", "id_list",
    "arg_list", "arg", "rel_op", "value", "quantity", "literal", "boolean",
    "number",
    "actor_decl", "actor_field", "scope_block", "verbs_block",
    "invariants_block", "ratify_block", "path_list", "path_ref",
]


# Alternative-level coverage is INFORMATIONAL: G1's gate is production-level.
# These are the alternatives inside productions where a gap is meaningful.
ALT_EXPECTED = sorted(
    f"{prod}:{alt}" for prod, alt_names in {
        "io_decl": ["input", "const", "output"],
        "add_op": ["+", "-"],
        "mul_op": ["*", "/", "<<", ">>"],
        "rel_op": ["<", "<=", ">", ">=", "=", "=="],
        "factor": ["identifier", "number", "paren"],
        "literal": ["identifier", "number", "string", "boolean"],
        "model_field": ["purpose", "constraints", "ecosystem"],
        "operator_field": ["goal", "preserves", "constraint"],
        "profile_field": ["plain", "string-keyed"],
        "actor_field": ["scope", "verbs", "invariants", "ratify"],
    }.items() for alt in alt_names
)


def parse_file(path: Path, coverage: set, alts: set):
    src = path.read_text()
    p = Parser(tokenize(src), coverage, alts)
    if path.suffix == ".flow":
        p.parse_flow_document()
    else:
        p.parse_oaas_document()


def main():
    root = Path(__file__).resolve().parent.parent
    corpus = sorted((root / "conformance" / "corpus").glob("*.oaas")) + \
             sorted((root / "conformance" / "corpus").glob("*.flow"))
    extra = sorted((root / "profiles").rglob("*.oaas")) + \
            sorted((root / "profiles").rglob("*.flow"))

    coverage, alts, failures, results = set(), set(), [], []
    for path in corpus + extra:
        head = "\n".join(path.read_text().splitlines()[:12])
        # marker is SYNTACTIC (`// EXPECTED-FAIL: <gap>` at line start), not a
        # substring — prose that merely mentions the marker must not trigger it
        expect_fail = re.search(r"^// EXPECTED-FAIL\b", head, re.M) is not None
        try:
            # coverage is a corpus-only claim; profiles/ files parse but don't count
            in_corpus = path in corpus
            parse_file(path, coverage if in_corpus else set(),
                       alts if in_corpus else set())
            if expect_fail:
                failures.append(f"XPASS {path.relative_to(root)} — expected to fail "
                                f"(a GAP closed without ratification?)")
                results.append(("XPASS", path))
            else:
                results.append(("PASS", path))
        except ParseError as e:
            if expect_fail:
                results.append(("XFAIL", path))
            else:
                failures.append(f"FAIL  {path.relative_to(root)}: {e}")
                results.append(("FAIL", path))

    for status, path in results:
        print(f"{status:6} {path.relative_to(root)}")

    # The denominator is derived from the EBNF itself, never self-asserted:
    # the validator's instrumented inventory must equal the grammar's rule set.
    ebnf = (root / "grammar" / "oaas.ebnf").read_text()
    declared = set(re.findall(r"^([a-z_]+)\s*=", ebnf, re.M)) - {"comment"}
    inventory = set(ALL_PRODUCTIONS)
    if declared != inventory:
        failures.append(
            "grammar<->validator inventory mismatch: "
            f"only-in-ebnf={sorted(declared - inventory)} "
            f"only-in-validator={sorted(inventory - declared)}")

    uncovered = [p for p in ALL_PRODUCTIONS if p not in coverage]
    print(f"\ninventory: {len(declared)} productions declared in oaas.ebnf, "
          f"{len(inventory)} instrumented in validator "
          + ("[MISMATCH]" if declared != inventory else "[match]"))
    print(f"coverage (GATE, production level): "
          f"{len(ALL_PRODUCTIONS) - len(uncovered)}/{len(ALL_PRODUCTIONS)} fired")
    if uncovered:
        print("uncovered:", ", ".join(uncovered))
    missing_alts = [a for a in ALT_EXPECTED if a not in alts]
    print(f"coverage (informational, alternative level): "
          f"{len(ALT_EXPECTED) - len(missing_alts)}/{len(ALT_EXPECTED)} exemplified")
    if missing_alts:
        print("alternative gaps (corpus wishlist; do NOT fail the gate):")
        for a in missing_alts:
            print(f"  - {a}")

    if failures or uncovered:
        for f in failures:
            print(f, file=sys.stderr)
        sys.exit(1)
    print("\nCorpus contract satisfied: all files parse as expected; all productions exemplified.")


if __name__ == "__main__":
    main()
