# ONNX round-trip report — 2026-08-12
Metric: preservation score = 4/4 -> PASS
Upstream actually tested: onnx 1.22.0, IR 13, lib opset 27 (cases pinned at opset 13)

## case add: tensor_types=ok, operator_versions=ok, graph_topology=ok, constants=ok
projection image (.flow):
```
use ecosystem.onnx

input A : Tensor<f32>[N,8]
input B : Tensor<f32>[N,8]
output Y : Tensor<f32>[N,8]

A, B -> onnx::Add@13 -> Y
```
## case matmul: tensor_types=ok, operator_versions=ok, graph_topology=ok, constants=ok
projection image (.flow):
```
use ecosystem.onnx

input X : Tensor<f32>[N,4]
const W : Tensor<f32>[4,8]
output Y : Tensor<f32>[N,8]

X, W -> onnx::MatMul@13 -> Y
```
## pins vs observed (drift-watch input, no auto-bump)
pinned:
```
# upstream pins (drift-watch reads this; bumps are propose-only)
ir_version = 11        # ASSUMPTION: inherited from intake transcript, unverified
opset ai.onnx = 24     # ASSUMPTION: inherited from intake transcript, unverified
```
observed: IR 13, lib opset 27
