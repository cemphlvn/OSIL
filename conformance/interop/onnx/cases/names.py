"""Case: ONNX value names that are not OSIL identifiers ('.', '/', ':'), a value named
like a flow keyword, and a rank-0 initializer — the shapes real exporters (torch.onnx)
emit. Exercises the export-side renaming and its exact restoration on import
(onto↔osil↔flow loop, wave 2, 2026-09-27; source: deneme/birim_lm.onnx)."""
from onnx import helper, TensorProto


def make_model():
    X = helper.make_tensor_value_info("model.embed/x:0", TensorProto.FLOAT, ["N", 4])
    Y = helper.make_tensor_value_info("output", TensorProto.FLOAT, ["N", 4])
    W = helper.make_tensor("layer.0.weight", TensorProto.FLOAT, [4, 4], [0.5] * 16)
    s = helper.make_tensor("/scale", TensorProto.FLOAT, [], [2.0])
    mm = helper.make_node("MatMul", ["model.embed/x:0", "layer.0.weight"], ["/layer.0/MatMul_output_0"])
    mul = helper.make_node("Mul", ["/layer.0/MatMul_output_0", "/scale"], ["output"])
    graph = helper.make_graph([mm, mul], "names_case", [X], [Y], initializer=[W, s])
    return helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
