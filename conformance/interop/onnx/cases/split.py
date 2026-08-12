"""Case: Split — the first MULTI-OUTPUT operator (D3/G6 revisit trigger).
One input splits equally into two outputs along axis 1; carries a node
attribute (axis), which rides the node-proto passthrough."""
from onnx import helper, TensorProto


def make_model():
    X = helper.make_tensor_value_info("X", TensorProto.FLOAT, ["N", 8])
    Y1 = helper.make_tensor_value_info("Y1", TensorProto.FLOAT, ["N", 4])
    Y2 = helper.make_tensor_value_info("Y2", TensorProto.FLOAT, ["N", 4])
    node = helper.make_node("Split", ["X"], ["Y1", "Y2"], axis=1)
    graph = helper.make_graph([node], "split_case", [X], [Y1, Y2])
    return helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", 13)])
