"""Case: ONNX Constant nodes (input-less, value in the `value` attribute) — a 1-D
i64 shape feeding Reshape and a rank-0 f32 scale, placed between other nodes so
node order matters. torch.onnx emits these instead of initializers. Exercises the
export of a Constant node as a flow `const` and its restoration as a node, in its
original position, on import (onto↔osil↔flow loop, wave 3, 2026-09-27; source:
deneme/birim_lm.onnx, 91 Constant nodes)."""
from onnx import helper, TensorProto


def make_model():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2, 6])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [3, 4])
    shape = helper.make_node("Constant", [], ["shape"], value=helper.make_tensor(
        "shape_value", TensorProto.INT64, [2], [3, 4]))
    reshape = helper.make_node("Reshape", ["X", "shape"], ["R"])
    scale = helper.make_node("Constant", [], ["scale"], value=helper.make_tensor(
        "scale_value", TensorProto.FLOAT, [], [0.5]))
    mul = helper.make_node("Mul", ["R", "scale"], ["Y"])
    graph = helper.make_graph([shape, reshape, scale, mul], "constant_case", [X], [Y])
    return helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
