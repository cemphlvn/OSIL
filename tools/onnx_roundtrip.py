#!/usr/bin/env python3
"""ONNX round-trip harness (G3): computes the system's own testing metric.

Metric — PRESERVATION SCORE (spec/conformance.md): the fraction of the ONNX
projection's CONTRACT.osil `preserves` fields mechanically verified on a round
trip  .onnx -> .flow text -> .onnx  over every case in
conformance/interop/onnx/cases/. Gate G3 requires score = 1.0 (scope = the
suite's case list, reported alongside).

The projection image is real OSIL text, lexed back with the reference lexer
from osil_check (dogfooding). Native data the text does not model (initializer
values, ir_version, producer) survives via OPAQUE PASSTHROUGH, the mechanism
spec/interop/ecosystem-contract.md §3 sanctions. may_lose fields
(ontology_annotations, visual_layout) are excluded from the score by definition.

Run: `just roundtrip`  (uv supplies onnx ephemerally).
Writes: conformance/matrix/matrix.yaml cell + docs/reports/roundtrip-onnx-<date>.md
"""
import datetime
import importlib.util
import sys
from pathlib import Path

import numpy as np
import onnx
from onnx import helper, numpy_helper, TensorProto

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from osil_check import Parser, tokenize  # reference lexer/parser — dogfood, do not fork

ELEM_TO_TEXT = {TensorProto.FLOAT: "f32", TensorProto.FLOAT16: "f16",
                TensorProto.BFLOAT16: "bf16", TensorProto.DOUBLE: "f64",
                TensorProto.INT8: "i8", TensorProto.INT32: "i32",
                TensorProto.INT64: "i64", TensorProto.BOOL: "bool_"}
TEXT_TO_ELEM = {v: k for k, v in ELEM_TO_TEXT.items()}

# statement-leading words of a flow document; a value spelled like one would be
# read as the statement, so it is renamed like any non-identifier
FLOW_KEYWORDS = {"use", "input", "const", "output", "layout"}


def is_flow_ident(name):
    """True iff the reference lexer reads `name` as exactly one identifier."""
    try:
        toks = [t for t in tokenize(name) if t.kind not in ("ws", "comment")]
    except Exception:
        return False
    return len(toks) == 1 and toks[0].kind == "ident" and toks[0].text == name \
        and name not in FLOW_KEYWORDS


def flow_names(model):
    """ONNX value name -> flow identifier, for the names that are not already one.
    Deterministic (first occurrence order) and collision-free; the inverse rides
    the passthrough so import restores the original names exactly (wave 2)."""
    g = model.graph
    names = [v.name for v in g.input] + [i.name for i in g.initializer] + [v.name for v in g.output]
    for n in g.node:
        names += list(n.input) + list(n.output)
    names = [n for n in dict.fromkeys(names) if n]
    taken = {n for n in names if is_flow_ident(n)}
    ren = {}
    for n in names:
        if n in taken:
            continue
        base = "v_" + ("".join(c if c.isascii() and (c.isalnum() or c == "_") else "_" for c in n)
                       .strip("_") or "x")
        cand, k = base, 1
        while cand in taken:
            cand, k = f"{base}_{k}", k + 1
        taken.add(cand)
        ren[n] = cand
    return ren


def dims_of(vi):
    out = []
    for d in vi.type.tensor_type.shape.dim:
        out.append(d.dim_param if d.dim_param else int(d.dim_value))
    return out


def op_since_version(op_type, opset):
    try:
        return onnx.defs.get_schema(op_type, opset).since_version
    except Exception:
        return opset


def main_opset(model):
    for o in model.opset_import:
        if o.domain in ("", "ai.onnx"):
            return o.version
    raise RuntimeError("no default-domain opset")


def constant_value(node):
    """The tensor of an input-less Constant node carried in `value`, else None.
    Such a node IS a constant: it projects to a flow `const`, not to an edge with
    no sources (which the grammar rightly has no form for). Wave 3."""
    if node.op_type == "Constant" and not node.input and len(node.output) == 1 \
            and len(node.attribute) == 1 and node.attribute[0].name == "value":
        return node.attribute[0].t
    return None


# --------------------------------------------------- projection: model -> text
def export_flow(model):
    """ModelProto -> (.flow text, passthrough). Text carries what OSIL models;
    passthrough carries the rest, opaquely."""
    g = model.graph
    opset = main_opset(model)
    init_names = {i.name for i in g.initializer}
    ren = flow_names(model)

    def f(name):
        return ren.get(name, name)

    lines = ["use ecosystem.onnx", ""]
    for vi in g.input:
        if vi.name in init_names:
            continue
        t = ELEM_TO_TEXT[vi.type.tensor_type.elem_type]
        lines.append(f"input {f(vi.name)} : Tensor<{t}>[{','.join(map(str, dims_of(vi)))}]")
    for init in g.initializer:
        t = ELEM_TO_TEXT[init.data_type]
        lines.append(f"const {f(init.name)} : Tensor<{t}>[{','.join(map(str, init.dims))}]")
    constant_nodes = []   # (node index, ONNX output name): restored as nodes, in place
    for idx, node in enumerate(g.node):
        cv = constant_value(node)
        if cv is None:
            continue
        constant_nodes.append((idx, node.output[0]))
        t = ELEM_TO_TEXT[cv.data_type]
        lines.append(f"const {f(node.output[0])} : Tensor<{t}>[{','.join(map(str, cv.dims))}]")
    for vi in g.output:
        t = ELEM_TO_TEXT[vi.type.tensor_type.elem_type]
        lines.append(f"output {f(vi.name)} : Tensor<{t}>[{','.join(map(str, dims_of(vi)))}]")
    lines.append("")
    for node in g.node:
        if constant_value(node) is not None:
            continue
        since = op_since_version(node.op_type, opset)
        outs = f(node.output[0]) if len(node.output) == 1 \
            else "(" + ", ".join(map(f, node.output)) + ")"       # positional, D3/G6
        lines.append(f"{', '.join(map(f, node.input))} -> onnx::{node.op_type}@{since} -> {outs}")
    passthrough = {
        # full NodeProtos ride the sanctioned opaque passthrough (attributes,
        # names, domains); the text stays authoritative for the modeled
        # fields and import cross-checks them against these protos
        "node_protos": [n.SerializeToString().hex() for n in g.node],
        "ir_version": model.ir_version,
        "producer_name": model.producer_name,
        "producer_version": model.producer_version,
        "graph_name": g.name,
        "opset_import": [(o.domain, o.version) for o in model.opset_import],
        "initializers": {i.name: i.SerializeToString().hex() for i in g.initializer},
        "flow_names": {v: k for k, v in ren.items()},   # flow identifier -> ONNX name
        "constant_nodes": constant_nodes,
    }
    return "\n".join(lines) + "\n", passthrough


# ------------------------------------------------- flow text -> structure
def read_flow(text):
    """Minimal structural reader over the reference lexer's token stream."""
    toks = [t for t in tokenize(text) if t.kind != "eof"]
    i, uses, ios, edges = 0, [], [], []

    def expect(kind, val=None):
        nonlocal i
        t = toks[i]
        if t.kind != kind or (val is not None and t.text != val):
            raise SyntaxError(f"line {t.line}: expected {val or kind}, got {t.text!r}")
        i += 1
        return t

    while i < len(toks):
        t = toks[i]
        if t.kind == "ident" and t.text == "use":
            i += 1
            parts = [expect("ident").text]
            while i < len(toks) and toks[i].kind == "op" and toks[i].text == ".":
                i += 1
                parts.append(expect("ident").text)
            uses.append(".".join(parts))
        elif t.kind == "ident" and t.text in ("input", "const", "output"):
            role = t.text
            i += 1
            name = expect("ident").text
            expect("op", ":")
            base = expect("ident").text
            elem = None
            if toks[i].kind == "op" and toks[i].text == "<":
                i += 1
                elem = expect("ident").text
                expect("op", ">")
            dims = []
            if i < len(toks) and toks[i].kind == "op" and toks[i].text == "[":
                i += 1
                while not (toks[i].kind == "op" and toks[i].text == "]"):
                    if toks[i].kind == "op" and toks[i].text == ",":
                        i += 1
                        continue
                    d = toks[i]
                    dims.append(int(d.text) if d.kind == "number" else d.text)
                    i += 1
                i += 1
            ios.append((role, name, base, elem, dims))
        else:
            srcs = [expect("ident").text]
            while toks[i].kind == "op" and toks[i].text == ",":
                i += 1
                srcs.append(expect("ident").text)
            expect("op", "->")
            ns = expect("ident").text
            op_name = ns
            if toks[i].kind == "op" and toks[i].text == "::":
                i += 1
                op_name = expect("ident").text
            if toks[i].kind == "op" and toks[i].text == "@":
                i += 1
                expect("number")
            expect("op", "->")
            if toks[i].kind == "op" and toks[i].text == "(":
                i += 1
                dsts = [expect("ident").text]
                while toks[i].kind == "op" and toks[i].text == ",":
                    i += 1
                    dsts.append(expect("ident").text)
                expect("op", ")")
            else:
                dsts = [expect("ident").text]
            edges.append((srcs, op_name, dsts))
    return uses, ios, edges


# ------------------------------------------------- structure -> model
def import_model(text, passthrough):
    uses, ios, edges = read_flow(text)
    assert "ecosystem.onnx" in uses, "flow must `use ecosystem.onnx`"
    back = passthrough.get("flow_names", {})   # absent in pre-wave-2 passthroughs

    def o(name):
        return back.get(name, name)

    ios = [(r, o(n), b, e, d) for (r, n, b, e, d) in ios]
    edges = [([o(s) for s in srcs], op, [o(d) for d in dsts]) for (srcs, op, dsts) in edges]

    def vi(name, elem, dims):
        return helper.make_tensor_value_info(name, TEXT_TO_ELEM[elem], dims)

    inputs = [vi(n, e, d) for (r, n, b, e, d) in ios if r == "input"]
    outputs = [vi(n, e, d) for (r, n, b, e, d) in ios if r == "output"]
    const_at = {idx: name for idx, name in passthrough.get("constant_nodes", [])}
    decl = {n: (e, d) for (r, n, b, e, d) in ios if r == "const"}
    inits = []
    for (r, n, b, e, d) in ios:
        if r != "const" or n in const_at.values():
            continue
        tp = TensorProto()
        tp.ParseFromString(bytes.fromhex(passthrough["initializers"][n]))
        # cross-check: passthrough tensor must match the text's declaration
        assert tp.name == n and list(tp.dims) == d and tp.data_type == TEXT_TO_ELEM[e], \
            f"passthrough/text mismatch for const {n}"
        inits.append(tp)
    nodes = []
    protos = passthrough.get("node_protos")
    edge_it = iter(edges)
    for idx in range(len(protos) if protos else len(edges)):
        if idx in const_at:   # a flow `const` that was a Constant node: back in place
            np_ = onnx.NodeProto()
            np_.ParseFromString(bytes.fromhex(protos[idx]))
            cv, (e, d) = constant_value(np_), decl.get(const_at[idx], (None, None))
            assert cv is not None and np_.output[0] == const_at[idx] \
                and list(cv.dims) == d and cv.data_type == TEXT_TO_ELEM.get(e), \
                f"passthrough/text mismatch for Constant node {idx} ({const_at[idx]})"
            nodes.append(np_)
            continue
        srcs, op, dsts = next(edge_it)
        if protos:
            np_ = onnx.NodeProto()
            np_.ParseFromString(bytes.fromhex(protos[idx]))
            # text is authoritative for modeled fields; passthrough must agree
            assert np_.op_type == op and list(np_.input) == srcs \
                and list(np_.output) == dsts, \
                f"passthrough/text mismatch on node {idx} ({op})"
            nodes.append(np_)
        else:
            nodes.append(helper.make_node(op, srcs, dsts))
    assert next(edge_it, None) is None, "flow has more edges than the passthrough has nodes"
    graph = helper.make_graph(nodes, passthrough["graph_name"],
                              inputs, outputs, initializer=inits)
    model = helper.make_model(graph, opset_imports=[
        helper.make_opsetid(dom, ver) for dom, ver in passthrough["opset_import"]])
    model.ir_version = passthrough["ir_version"]
    model.producer_name = passthrough["producer_name"]
    model.producer_version = passthrough["producer_version"]
    return model


# ------------------------------------------------- contract verification
def sig_tensor_types(model):
    g = model.graph
    return (
        [(v.name, v.type.tensor_type.elem_type, dims_of(v)) for v in g.input],
        [(v.name, v.type.tensor_type.elem_type, dims_of(v)) for v in g.output],
        [(t.name, t.data_type, list(t.dims)) for t in g.initializer],
    )


def verify(original, rebuilt):
    opset_o = main_opset(original)
    results = {}
    results["tensor_types"] = sig_tensor_types(original) == sig_tensor_types(rebuilt)
    results["operator_versions"] = (
        sorted((o.domain, o.version) for o in original.opset_import)
        == sorted((o.domain, o.version) for o in rebuilt.opset_import)
        and [op_since_version(n.op_type, opset_o) for n in original.graph.node]
        == [op_since_version(n.op_type, main_opset(rebuilt)) for n in rebuilt.graph.node])
    results["graph_topology"] = (
        [(n.op_type, list(n.input), list(n.output)) for n in original.graph.node]
        == [(n.op_type, list(n.input), list(n.output)) for n in rebuilt.graph.node])
    results["constants"] = all(
        np.array_equal(numpy_helper.to_array(a), numpy_helper.to_array(b))
        and a.name == b.name
        for a, b in zip(original.graph.initializer, rebuilt.graph.initializer)
    ) and len(original.graph.initializer) == len(rebuilt.graph.initializer)
    return results


PRESERVES = ["tensor_types", "operator_versions", "graph_topology", "constants"]


def main():
    cases_dir = ROOT / "conformance" / "interop" / "onnx" / "cases"
    today = datetime.date.today().isoformat()
    per_case, all_field = {}, {f: True for f in PRESERVES}

    for case_path in sorted(cases_dir.glob("*.py")):
        spec = importlib.util.spec_from_file_location(case_path.stem, case_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        model = mod.make_model()
        onnx.checker.check_model(model)

        text, passthrough = export_flow(model)
        # the projection's output must itself be OSIL: a round-trip that preserves
        # everything through text the reference parser rejects proves nothing (GAP-6)
        Parser(tokenize(text), set(), set()).parse_flow_document()
        rebuilt = import_model(text, passthrough)
        onnx.checker.check_model(rebuilt)

        results = verify(model, rebuilt)
        per_case[case_path.stem] = (results, text)
        for f in PRESERVES:
            all_field[f] &= results[f]

    verified = sum(all_field[f] for f in PRESERVES)
    score = verified / len(PRESERVES)
    status = "pass" if score == 1.0 else "fail"
    upstream = (f"onnx {onnx.__version__}, IR {onnx.IR_VERSION}, "
                f"lib opset {onnx.defs.onnx_opset_version()} "
                f"(cases pinned at opset 13)")

    # matrix cell — the only sanctioned way a cell reaches `pass`
    (ROOT / "conformance" / "matrix" / "matrix.yaml").write_text(f"""\
# Compatibility matrix: spec version x adapter x upstream version.
# Cells are agent-maintained (matrix-refresh). A cell may reach `pass` only on
# mechanical round-trip evidence — never by inference.
dimensions: [spec, adapter, upstream]
cells:
  - spec: "0.0.0-draft (grammar v0.2)"
    adapter: "onnx-roundtrip v0 (tools/onnx_roundtrip.py)"
    upstream: "{upstream}"
    status: {status}
    preservation_score: "{verified}/{len(PRESERVES)}"
    fields: {{tensor_types: {str(all_field['tensor_types']).lower()}, operator_versions: {str(all_field['operator_versions']).lower()}, graph_topology: {str(all_field['graph_topology']).lower()}, constants: {str(all_field['constants']).lower()}}}
    cases: [{', '.join(sorted(per_case))}]
    checked: {today}
""")

    report = [f"# ONNX round-trip report — {today}",
              f"Metric: preservation score = {verified}/{len(PRESERVES)} -> {status.upper()}",
              f"Upstream actually tested: {upstream}", ""]
    for name, (results, text) in sorted(per_case.items()):
        report.append(f"## case {name}: " + ", ".join(
            f"{f}={'ok' if results[f] else 'FAIL'}" for f in PRESERVES))
        report.append("projection image (.flow):\n```\n" + text + "```")
    # honest scope + drift lines
    pins = (ROOT / "profiles" / "ecosystem" / "onnx" / "VERSIONS").read_text()
    report.append("## pins vs observed (drift-watch input, no auto-bump)")
    report.append("pinned:\n```\n" + pins + "```")
    report.append(f"observed: IR {onnx.IR_VERSION}, lib opset {onnx.defs.onnx_opset_version()}")
    (ROOT / "docs" / "reports" / f"roundtrip-onnx-{today}.md").write_text(
        "\n".join(report) + "\n")

    print(f"preservation score: {verified}/{len(PRESERVES)} ({status.upper()}) "
          f"over cases: {', '.join(sorted(per_case))}")
    print(f"matrix cell written; report: docs/reports/roundtrip-onnx-{today}.md")
    sys.exit(0 if status == "pass" else 1)


if __name__ == "__main__":
    main()
