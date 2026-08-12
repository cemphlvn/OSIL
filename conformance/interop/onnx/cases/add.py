"""Case: elementwise Add, two runtime inputs, no initializers — exercises the
no-constants path and a second operator identity."""
from onnx import helper, TensorProto


def make_model():
    A = helper.make_tensor_value_info("A", TensorProto.FLOAT, ["N", 8])
    B = helper.make_tensor_value_info("B", TensorProto.FLOAT, ["N", 8])
    Y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, ["N", 8])
    node = helper.make_node("Add", ["A", "B"], ["Y"])
    graph = helper.make_graph([node], "add_case", [A, B], [Y])
    return helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", 13)])
