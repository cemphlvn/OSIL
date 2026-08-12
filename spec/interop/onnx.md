# ONNX Interop Contract
Status: stub (draft-0). ONNX contributes EXECUTABLE GRAPH INTERCHANGE; the ONNX
projection preserves computation. Native identities keep ONNX versioned semantics
(onnx::MatMul@13). Round-trip: .onnx -> OAAS -> .onnx with ONNX metadata surviving;
unknown fields become opaque namespaced annotations. Machine-readable contract:
profiles/ecosystem/onnx/CONTRACT.oaas. Corpus: 001, 002.
