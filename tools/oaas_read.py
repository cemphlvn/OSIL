#!/usr/bin/env python3
"""Shared OAAS readers (G12) — the anti-fifth-reader module.

Built for the resolver, designed for reuse: these are the symbol-table
readers a future LSP needs (g12-resolver-plan.md, perspective 2). Migration
target for the four older inline readers (oaas_check fire-only excepted —
it is the reference parser; roundtrip/render/policy readers are follow-ups).
Reuses the reference lexer; never forks tokenization.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oaas_check import tokenize


def _toks(text):
    return [t for t in tokenize(text) if t.kind != "eof"]


def read_flow(text):
    """Full-fidelity flow reader: keeps namespaces, versions, multi-outputs.
    Returns dict(uses, ios, edges, has_layout). Edge = (srcs, ns, op, ver, dsts);
    ns/ver are None when absent. Layout blocks are skipped (render_check owns
    layout)."""
    toks, i = _toks(text), 0
    out = {"uses": [], "ios": [], "edges": [], "has_layout": False}

    def at_op(op, k=0):
        t = toks[i + k] if i + k < len(toks) else None
        return t is not None and t.kind == "op" and t.text == op

    def ident():
        nonlocal i
        t = toks[i]
        assert t.kind == "ident", f"line {t.line}: expected identifier, got {t.text!r}"
        i += 1
        return t.text

    def op(o):
        nonlocal i
        t = toks[i]
        assert t.kind == "op" and t.text == o, f"line {t.line}: expected {o!r}"
        i += 1

    while i < len(toks):
        t = toks[i]
        if t.kind == "ident" and t.text == "use":
            i += 1
            parts = [ident()]
            while at_op("."):
                i += 1
                parts.append(ident())
            out["uses"].append(".".join(parts))
        elif t.kind == "ident" and t.text in ("input", "const", "output"):
            role = t.text
            i += 1
            name = ident()
            op(":")
            base = ident()
            elem = None
            if at_op("<"):
                i += 1
                elem = ident()
                op(">")
            dims = []
            if at_op("["):
                i += 1
                while not at_op("]"):
                    if at_op(","):
                        i += 1
                        continue
                    d = toks[i]
                    dims.append(int(d.text) if d.kind == "number" else d.text)
                    i += 1
                i += 1
            out["ios"].append((role, name, base, elem, dims))
        elif t.kind == "ident" and t.text == "layout" and at_op("{", 1):
            out["has_layout"] = True
            i += 1
            depth = 0
            while i < len(toks):
                if toks[i].kind == "op" and toks[i].text == "{":
                    depth += 1
                elif toks[i].kind == "op" and toks[i].text == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                i += 1
        else:
            srcs = [ident()]
            while at_op(","):
                i += 1
                srcs.append(ident())
            op("->")
            first = ident()
            ns = opname = None
            if at_op("::"):
                i += 1
                ns, opname = first, ident()
            else:
                opname = first
            ver = None
            if at_op("@"):
                i += 1
                ver = int(toks[i].text)
                i += 1
            op("->")
            if at_op("("):
                i += 1
                dsts = [ident()]
                while at_op(","):
                    i += 1
                    dsts.append(ident())
                op(")")
            else:
                dsts = [ident()]
            out["edges"].append((srcs, ns, opname, ver, dsts))
    return out


def read_stage_decls(text):
    """Stage declarations (G15): {name: {"reads": set, "writes": set}}."""
    toks, i = _toks(text), 0
    out = {}

    def qualified(j):
        parts = [toks[j].text]
        j += 1
        while j < len(toks) and toks[j].kind == "op" and toks[j].text == ".":
            parts.append(toks[j + 1].text)
            j += 2
        return ".".join(parts), j

    while i < len(toks):
        t = toks[i]
        if t.kind == "ident" and t.text == "stage" and i + 2 < len(toks) \
                and toks[i + 1].kind == "ident" and toks[i + 2].text == "{":
            name, i = toks[i + 1].text, i + 3
            rw = {"reads": set(), "writes": set()}
            while toks[i].text != "}":
                word = toks[i].text
                if word == "runs":
                    _, i = qualified(i + 2)
                elif word in rw:
                    i += 2
                    while toks[i].text != "}":
                        res, i = qualified(i)
                        rw[word].add(res)
                    i += 1
                else:
                    raise SyntaxError(f"unexpected {word!r} in stage {name}")
            i += 1
            out[name] = rw
        else:
            i += 1
    return out


def read_contract_fields(text):
    """Top-level preserves{}/may_lose{} id lists (the CONTRACT.oaas shape):
    {"preserves": [...], "may_lose": [...]}. Role-bound `preserves:` inside
    operator blocks is NOT matched (no following brace)."""
    toks, i = _toks(text), 0
    out = {"preserves": [], "may_lose": []}
    while i < len(toks):
        t = toks[i]
        if t.kind == "ident" and t.text in out and i + 1 < len(toks) \
                and toks[i + 1].kind == "op" and toks[i + 1].text == "{":
            key, i = t.text, i + 2
            while toks[i].text != "}":
                out[key].append(toks[i].text)
                i += 1
            i += 1
        else:
            i += 1
    return out


def read_vocab(text):
    """Vocabulary reader for .oaas files: profile ids (+ pins), operator /
    concept / invariant names. Other declarations are brace-skipped."""
    toks, i = _toks(text), 0
    out = {"profiles": [], "operators": [], "concepts": [], "invariants": [],
           "pins": {}, "projections": []}

    def skip_block():
        nonlocal i
        depth = 0
        while i < len(toks):
            if toks[i].kind == "op" and toks[i].text == "{":
                depth += 1
            elif toks[i].kind == "op" and toks[i].text == "}":
                depth -= 1
                if depth == 0:
                    i += 1
                    return
            i += 1

    while i < len(toks):
        t = toks[i]
        if t.kind == "ident" and t.text == "profile":
            i += 1
            parts = [toks[i].text]
            i += 1
            while i < len(toks) and toks[i].kind == "op" and toks[i].text == ".":
                i += 1
                parts.append(toks[i].text)
                i += 1
            out["profiles"].append(".".join(parts))
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "{":
                i += 1
                while not (toks[i].kind == "op" and toks[i].text == "}"):
                    if toks[i].kind == "ident":
                        key = toks[i].text
                        i += 1
                        if toks[i].kind == "string":
                            key += " " + toks[i].text.strip('"')
                            i += 1
                        if toks[i].kind == "op" and toks[i].text == "=":
                            i += 1
                            out["pins"][key] = toks[i].text
                            i += 1
                    else:
                        i += 1
                i += 1
        elif t.kind == "ident" and t.text in ("operator", "concept"):
            kind = t.text
            i += 1
            out[kind + "s"].append(toks[i].text)
            i += 1
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "{":
                skip_block()
        elif t.kind == "ident" and t.text == "invariant":
            i += 1
            out["invariants"].append(toks[i].text)
            i += 1
        elif t.kind == "ident" and t.text == "projection":
            i += 1
            name = toks[i].text
            i += 1
            src, pres = None, []
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "{":
                i += 1
                while not (toks[i].kind == "op" and toks[i].text == "}"):
                    if toks[i].kind == "ident" and toks[i].text == "from":
                        i += 1
                        src = toks[i].text
                        i += 1
                    elif toks[i].kind == "ident" and toks[i].text == "preserve":
                        i += 1
                        while toks[i].kind == "ident" or \
                                (toks[i].kind == "op" and toks[i].text == ","):
                            if toks[i].kind == "ident":
                                pres.append(toks[i].text)
                            i += 1
                    else:
                        i += 1
                i += 1
            out["projections"].append((name, src, pres))
        elif t.kind == "ident" and t.text in ("actor", "equivalence", "model"):
            i += 2  # keyword + name
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "{":
                skip_block()
        elif t.kind == "ident" and t.text in ("preserves", "may_lose"):
            i += 1
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "{":
                skip_block()
        else:
            i += 1
    return out
