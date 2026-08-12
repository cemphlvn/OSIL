# Grammar gaps ledger (grammar changes require ratification; open gaps may be
# pinned by expected-fail fixtures — marker form: `// EXPECTED-FAIL: <gap>`)

| # | Construct | Needed by | Status |
|---|---|---|---|
| GAP-1 | `actor` / `scope` / `verbs` / `ratify` blocks | repo-policy.oaas (conformance test #0) | **CLOSED at G2** (grammar v0.2, ratified by maintainer instruction 2026-08-12; XPASS guard held the build red mid-sequence, as designed) |
| GAP-2 | `:` vs `=` assignment univocity (`purpose:`/`goal:` vs `device =`) | 006, 007 | OPEN — **pinned by corpus 021** (G7): transcript's original colon form; falsifiable in both directions (ratify-colon -> XPASS ritual; ratify-`=`-only -> delete pin in same change) |
| GAP-3 | quantity juxtaposition boundary | 006, 007 | **CLOSED at G2**: adjacency rule (no whitespace between number and unit; same rule governs path components) ratified alongside GAP-1; originally discovered mechanically by the first G1 run |
| GAP-4 | multi-output edges `-> (Y, Z)` | toolchain ExportFlow; ONNX Split/Dropout | **CLOSED at G6** (grammar v0.4, ratified 2026-08-12; XPASS ritual on 018 held the build red mid-sequence; syntax ratified as positional) |
| GAP-5 | file-granular path_ref (dotted components: `spec/TERMS.md`) | repo-policy fidelity to skill frontmatter scopes | **CLOSED at G9** (grammar v0.5, ratified 2026-08-12; XPASS ritual on 022; policy scopes narrowed to skill declarations) |
