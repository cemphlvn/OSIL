# Grammar gaps ledger (grammar changes require ratification; open gaps may be
# pinned by expected-fail fixtures — marker form: `// EXPECTED-FAIL: <gap>`)

| # | Construct | Needed by | Status |
|---|---|---|---|
| GAP-1 | `actor` / `scope` / `verbs` / `ratify` blocks | repo-policy.oaas (conformance test #0) | **CLOSED at G2** (grammar v0.2, ratified by maintainer instruction 2026-08-12; XPASS guard held the build red mid-sequence, as designed) |
| GAP-2 | `:` vs `=` assignment univocity (`purpose:`/`goal:` vs `device =`) | 006, 007 | OPEN — flagged for univocity-lint; decide one relational story for bindings |
| GAP-3 | quantity juxtaposition boundary | 006, 007 | **CLOSED at G2**: adjacency rule (no whitespace between number and unit; same rule governs path components) ratified alongside GAP-1; originally discovered mechanically by the first G1 run |
| GAP-4 | multi-output edges (`-> (Y, Z)`, D3 working proposal) | toolchain ExportFlow; ONNX Split/Dropout as the suite grows | OPEN — pinned by corpus 018 (expected-fail); ratification designs the final syntax |
