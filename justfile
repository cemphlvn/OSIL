# OAAS command menu (`just` lists these)

# G1 validator: parse corpus + profiles, check production coverage
check:
    python3 tools/oaas_check.py

# show corpus inventory with document kinds
corpus:
    @ls -1 conformance/corpus/

# show gate status (grep the README table)
gates:
    @grep -A2 '^| G' README.md | head -20
