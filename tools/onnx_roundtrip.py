#!/usr/bin/env python3
"""ONNX round-trip harness (G3): computes the system's own testing metric.

Metric — PRESERVATION SCORE (spec/conformance.md): the fraction of the ONNX
projection's CONTRACT.oaas `preserves` fields mechanically verified on a round
trip  .onnx -> .flow text -> .onnx  over every case in
conformance/interop/onnx/cases/. Gate G3 requires score = 1.0 (scope = the
suite's case list, reported alongside).

The projection image is real OAAS text, lexed back with the reference lexer
from oaas_check (dogfooding). Native data the text does not model (initializer
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
from oaas_check import tokenize  # reference lexer — dogfood, do not fork

ELEM_TO_TEXT = {TensorProto.FLOAT: "f32", TensorProto.FLOAT16: "f16",
                TensorProto.BFLOAT16: "bf16", TensorProto.DOUBLE: "f64",
                TensorProto.INT8: "i8", TensorProto.INT32: "i32",
                TensorProto.INT64: "i64", TensorProto.BOOL: "bool_"}
TEXT_TO_ELEM = {v: k for k, v in ELEM_TO_TEXT.items()}


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


# --------------------------------------------------- projection: model -> text
def export_flow(model):
    """ModelProto -> (.flow text, passthrough). Text carries what OAAS models;
    passthrough carries the rest, opaquely."""
    g = model.graph
    opset = main_opset(model)
    init_names = {i.name for i in g.initializer}
    lines = ["use ecosystem.onnx", ""]
    for vi in g.input:
        if vi.name in init_names:
            continue
        t = ELEM_TO_TEXT[vi.type.tensor_type.elem_type]
        lines.append(f"input {vi.name} : Tensor<{t}>[{','.join(map(str, dims_of(vi)))}]")
    for init in g.initializer:
        t = ELEM_TO_TEXT[init.data_type]
        lines.append(f"const {init.name} : Tensor<{t}>[{','.join(map(str, init.dims))}]")
    for vi in g.output:
        t = ELEM_TO_TEXT[vi.type.tensor_type.elem_type]
        lines.append(f"output {vi.name} : Tensor<{t}>[{','.join(map(str, dims_of(vi)))}]")
    lines.append("")
    for node in g.node:
        since = op_since_version(node.op_type, opset)
        outs = node.output[0] if len(node.output) == 1 \
            else "(" + ", ".join(node.output) + ")"       # positional, D3/G6
        lines.append(f"{', '.join(node.input)} -> onnx::{node.op_type}@{since} -> {outs}")
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

    def vi(name, elem, dims):
        return helper.make_tensor_value_info(name, TEXT_TO_ELEM[elem], dims)

    inputs = [vi(n, e, d) for (r, n, b, e, d) in ios if r == "input"]
    outputs = [vi(n, e, d) for (r, n, b, e, d) in ios if r == "output"]
    inits = []
    for (r, n, b, e, d) in ios:
        if r != "const":
            continue
        tp = TensorProto()
        tp.ParseFromString(bytes.fromhex(passthrough["initializers"][n]))
        # cross-check: passthrough tensor must match the text's declaration
        assert tp.name == n and list(tp.dims) == d and tp.data_type == TEXT_TO_ELEM[e], \
            f"passthrough/text mismatch for const {n}"
        inits.append(tp)
    nodes = []
    protos = passthrough.get("node_protos")
    for idx, (srcs, op, dsts) in enumerate(edges):
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
