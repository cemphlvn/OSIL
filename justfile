# OAAS command menu (`just` lists these)

# G1 validator: parse corpus + profiles, check production coverage
check:
    python3 tools/oaas_check.py

# G3 ONNX round-trip suite: preservation score + matrix cell (uv supplies onnx)
roundtrip:
    uv run --with onnx python3 tools/onnx_roundtrip.py

# G4 golden-render loop: layout data gate + SVG advisory
render:
    python3 tools/render_check.py

# render one .flow (with layout block) to SVG: just draw FILE [OUT]
draw FILE *OUT:
    python3 tools/render_check.py --draw {{FILE}} {{OUT}}

# bless goldens (RATIFICATION ACT - record who/why in the PR)
render-bless:
    python3 tools/render_check.py --bless

# full gatekeeper: grammar/corpus contract + interop round-trip + golden render
test: check roundtrip render

# show corpus inventory with document kinds
corpus:
    @ls -1 conformance/corpus/

# show gate status (grep the README table)
gates:
    @grep -A2 '^| G' README.md | head -20
