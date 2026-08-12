# Grammar gaps (filed by corpus-gardener; grammar changes need ratification)

| # | Construct | Needed by | Notes |
|---|---|---|---|
| GAP-1 | `actor` / `scope` / `verbs` / `ratify` blocks | profiles/domain/agent/repo-policy.oaas (conformance test #0) | Deliberate: closing this gap IS gate G2. |
| GAP-2 | `privacy: local_only` colon-form inside operator blocks | 007 (normalized to `=` for now) | Decide `:` vs `=` assignment univocity — flagged for univocity-lint. |
| GAP-3 | `quantity` lexing underspecified: `number identifier` juxtaposition needs a boundary rule. v0 parser rule: same line. Proper fix: no-whitespace adjacency or unit suffix set — needs ratified grammar text. Found mechanically by first G1 run on corpus 007. | 006, 007 | Discovered by tools/oaas_check.py 2026-08-12. |
