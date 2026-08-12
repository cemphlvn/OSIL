# Compression report — 2026-08-12
Rung discipline: every claim names its ladder rung (bytes -> tokens -> productions -> concepts).

## B. Corpus ladder
- 22 fixtures (2 expected-fail, excluded from parse rungs)
- bytes: 8383 · tokens: 779 · productions: 60 (all fired)

## C. Cover direction — the corpus's 'books'
Greedy covering set: 9 fixtures cover all 60 productions:
- 019-toolchain-render  (+21: bounds, coord, dim, dim_list, edge_layout, edge_stmt…)
- 007-invariants-operator  (+11: constraint, invariant_decl, literal, number, oaas_declaration, oaas_document…)
- 010-actor-policy  (+8: actor_decl, actor_field, invariants_block, path_list, path_ref, ratify_block…)
- 003-equivalence-distributivity  (+7: add_op, equivalence_decl, expr, factor, guards_block, mul_op…)
- 008-concept-equivalent-under  (+4: arg, arg_list, boolean, concept_decl)
- 005-preservation-contract  (+3: contract_decl, may_lose_block, preserves_block)
- 006-model-intent-constraints  (+3: constraints_block, model_decl, model_field)
- 001-profile-ecosystem-onnx  (+2: profile_decl, profile_field)
- 004-projections  (+1: projection_decl)

Redundancy: fattest productions [('oaas_document', 14), ('oaas_declaration', 14), ('literal', 11), ('id_list', 10), ('qualified_id', 7)]; single-witness productions (31): actor_decl, actor_field, arg, arg_list, boolean, bounds, concept_decl, constraints_block, contract_decl, coord, edge_layout, invariant_decl…

## D. Name direction — unnamed recurring patterns (PROPOSE-ONLY)
- `guards { numeric_semantics = exact } }` — 3 fixtures (003-equivalence-distributivity, 013-equivalence-inverse-add, 014-equivalence-identity-div)
- `use domain . toolchain input` — 4 fixtures (016-toolchain-check, 017-toolchain-roundtrip, 018-multi-output-edge, 019-toolchain-render)
- `guards { numeric_semantics =` — 5 fixtures (003-equivalence-distributivity, 009-equivalence-strength-reduction, 013-equivalence-inverse-add, 014-equivalence-identity-div…)
- `( a + b )` — 3 fixtures (003-equivalence-distributivity, 013-equivalence-inverse-add, 020-equivalence-associativity)
- `ecosystem . onnx` — 3 fixtures (001-profile-ecosystem-onnx, 002-graph-onnx-matmul, 011-flow-matmul-roundtrip)

## E. Curriculum views (resolution + reachability)
- paths resolve: yes
- unreachable corpus items (8): 009-equivalence-strength-reduction, 011-flow-matmul-roundtrip, 013-equivalence-inverse-add, 014-equivalence-identity-div, 015-equivalence-shift-zero, 020-equivalence-associativity, 021-colon-binding, 022-file-scoped-actor — report-only; pedagogy is ratified
- minimal-spine.yaml regenerated from the covering set

## A. Interop axis (native vs projection, per ONNX case)
- add: native 102B | flow text 129B / 51 tokens | passthrough 186B | text/native = 1.26, (text+passthrough)/native = 3.09
- matmul: native 230B | flow text 132B / 51 tokens | passthrough 482B | text/native = 0.57, (text+passthrough)/native = 2.67
- split: native 123B | flow text 138B / 53 tokens | passthrough 222B | text/native = 1.12, (text+passthrough)/native = 2.93

Reading (rung honesty): the identity-bearing text is what OAAS
owns; constants ride the sanctioned passthrough, so tiny graphs
pay a byte-rung premium. The representational claim lives at the
concept rung (naming subgraphs), exactly as the founding text's
caveat states — byte ratios are reported, never headlined.
