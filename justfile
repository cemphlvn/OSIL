# OAAS command menu (`just` lists these)

# G1 validator: parse corpus + profiles, check production coverage
check:
    python3 tools/oaas_check.py

# G3 ONNX round-trip suite: preservation score + matrix cell (uv supplies onnx)
roundtrip:
    uv run --with onnx python3 tools/onnx_roundtrip.py

# full gatekeeper: grammar/corpus contract + interop round-trip
test: check roundtrip

# show corpus inventory with document kinds
corpus:
    @ls -1 conformance/corpus/

# show gate status (grep the README table)
gates:
    @grep -A2 '^| G' README.md | head -20
