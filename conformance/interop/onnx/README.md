# ONNX interop suite — subtree card

The project's first REGISTERED LF interop: ONNX is a Linux Foundation (LF AI &
Data) graduated project; registration binding lives in `registry/entries/onnx.yaml`
(`interop:` block), contract in `profiles/ecosystem/onnx/CONTRACT.oaas`.

ground-truth: FOREIGN (ONNX semantics) exercised against SHARED claims (our contract)
loops: round-trip harness (`just roundtrip`) — computes the PRESERVATION SCORE
       (spec/conformance.md) and writes the matrix cell + a dated report
cases: one generator per file in `cases/` (`def make_model()`), deterministic,
       no stored binaries — the pattern ONNX itself uses (research U3)
invariants: a cell reaches `pass` only on mechanical evidence · suite grows
       monotonically · case files never renumber/rename once referenced
policy: agents may add cases freely; harness changes follow tools/ review
