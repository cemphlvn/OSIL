# OSIL command menu (`just` lists these)

# G1 validator: parse corpus + profiles, check production coverage
check:
    python3 tools/osil_check.py

# G3 ONNX round-trip suite: preservation score + matrix cell (uv supplies onnx)
roundtrip:
    uv run --with onnx python3 tools/onnx_roundtrip.py

# G14 egglog round-trip suite: equivalence preservation score (uv supplies egglog)
egraph:
    uv run --with 'egglog==13.2.0' python3 tools/egraph_roundtrip.py

# G4 golden-render loop: layout data gate + SVG advisory
render:
    python3 tools/render_check.py

# render one .flow (with layout block) to SVG: just draw FILE [OUT]
draw FILE *OUT:
    python3 tools/render_check.py --draw {{FILE}} {{OUT}}

# bless goldens (RATIFICATION ACT - record who/why in the PR)
render-bless:
    python3 tools/render_check.py --bless

# policy agreement: self-hosted actors vs skill frontmatter (G8)
policy:
    python3 tools/policy_check.py

# G12 resolver: references find their universals; refusals REJECT
resolve:
    python3 tools/osil_resolve.py

# G17 C projection: the lowering-ecosystem contract (needs a C compiler)
cproj:
    python3 tools/c_roundtrip.py

# G19 C lifter (OQ-2): does mechanical lifting reproduce the hand analysis?
lift:
    uv run --with libclang python3 tools/lift_check.py

# G20 transformation chooser (OQ-2): decisions follow the dependence graph,
# and no accepted candidate is ever semantically wrong
choose:
    uv run --with libclang python3 tools/choose_check.py

# G21 capability ceiling: the architecture analysing its own reach
ceiling:
    uv run --with libclang python3 tools/ceiling_check.py

# price a capability BEFORE building it: just price <corpus.c>
price FILE:
    uv run --with libclang python3 tools/capability_ceiling.py {{FILE}}

# G22 harness discipline: the test-case validity problem, made mechanical
harness:
    uv run --with libclang python3 tools/harness_check.py

# G25 witness validation: an INDEPENDENT checker re-decides every preservation
# claim (SV-COMP's discipline; shares no code with the chooser)
witness:
    uv run --with libclang python3 tools/witness_emit.py /tmp/osil-witnesses.json
    python3 tools/witness_check.py /tmp/osil-witnesses.json

# full gatekeeper: contract + round-trips + render + policy + resolution + stages + views
test: check roundtrip egraph cproj lift choose ceiling harness witness render policy resolve stages views

# G15 stage commutation: the pipeline tests itself (uv supplies egglog)
stages:
    uv run --with 'egglog==13.2.0' python3 tools/stage_commute.py

# G16 governed views: vocabulary diagrams as conformance artifacts
views:
    python3 tools/view_render.py

# bless view goldens (RATIFICATION ACT — record who/why in the PR)
views-bless:
    python3 tools/view_render.py --bless

# derivation scan (ADVISORY): what the declared equivalences jointly entail
derive:
    uv run --with 'egglog==13.2.0' python3 tools/egraph_derive.py

# compression ladder scan: covering set, naming candidates, interop ratios
compress:
    uv run --with onnx python3 tools/compression_scan.py

# show corpus inventory with document kinds
corpus:
    @ls -1 conformance/corpus/

# show gate status (grep the gate ledger)
gates:
    @grep -E '^\| G' docs/GATES.md
