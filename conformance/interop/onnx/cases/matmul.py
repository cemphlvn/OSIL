"""Case: MatMul with a symbolic batch dim and a constant weight initializer.
Mirrors corpus fixture 002. Deterministic: fixed opset, fixed weight values."""
import numpy as np
from onnx import helper, numpy_helper, TensorProto


def make_model():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, ["N", 4])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, ["N", 8])
    W = numpy_helper.from_array(
        np.arange(32, dtype=np.float32).reshape(4, 8), name="W")
    node = helper.make_node("MatMul", ["X", "W"], ["Y"])
    graph = helper.make_graph([node], "matmul_case", [X], [Y], initializer=[W])
    return helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", 13)])
