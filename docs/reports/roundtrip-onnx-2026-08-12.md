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
# 2026-08-12: transcript-inherited ASSUMPTION pins (ir 11 / opset 24) were
# mechanically falsified by the first G3 run and corrected to observed values.
# Evidence: docs/reports/roundtrip-onnx-2026-08-12.md
ir_version = 13        # observed: onnx 1.22.0
opset ai.onnx = 27     # observed: onnx.defs.onnx_opset_version(), onnx 1.22.0
```
observed: IR 13, lib opset 27
