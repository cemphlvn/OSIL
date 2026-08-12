# EGraph round-trip report — 2026-08-12
Metric: preservation score = 4/4 -> PASS
Upstream actually tested: egglog 13.2.0 (PyPI)
Loop: OAAS-SIR -> egglog -> saturate(5) -> extract -> OAAS-SIR
Suite: 6 equivalence declarations (corpus IS the rule set)

## case add_associativity (020-equivalence-associativity.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `((a + b) + c) <=> (a + (b + c))` · guards: regime = ExactArithmetic · realized rule: `<=>`
extraction image (re-lexed by reference lexer): `((a + b) + c)`

## case distributivity (003-equivalence-distributivity.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `((a * c) + (b * c)) <=> ((a + b) * c)` · guards: numeric_semantics = exact · realized rule: `<=>`
extraction image (re-lexed by reference lexer): `((a + b) * c)`

## case identity_div (014-equivalence-identity-div.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `(x / 1) <=> x` · guards: numeric_semantics = exact · realized rule: `->`
extraction image (re-lexed by reference lexer): `x`

## case inverse_add (013-equivalence-inverse-add.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `((a + b) - b) <=> a` · guards: numeric_semantics = exact · realized rule: `->`
extraction image (re-lexed by reference lexer): `a`

## case shift_zero (015-equivalence-shift-zero.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `(x >> 0) <=> x` · guards: numeric_semantics = integer · realized rule: `->`
extraction image (re-lexed by reference lexer): `x`

## case strength_reduction (009-equivalence-strength-reduction.oaas): equivalence=ok, guard_selectivity=ok, term_extraction=ok
declared: `(x * 2) <=> (x << 1)` · guards: numeric_semantics = integer · realized rule: `<=>`
extraction image (re-lexed by reference lexer): `(x * 2)`

## pins vs observed (drift-watch input, no auto-bump)
pinned:
```
# upstream pins (drift-watch reads this; bumps are propose-only)
# 2026-08-12: pinned at G14 per research U5 §5. The PyPI wheel vendors the
# Rust core at an exact git rev; crates.io egglog (2.0.0) numbering is
# provably DECOUPLED from PyPI egglog (13.2.0) — never cross-check the two.
# Evidence: docs/research/U5-egg-vs-egglog.md
egglog pypi = 13.2.0            # harness dependency (just egraph); published 2026-06-03
egglog core git rev = 2e5657b   # vendored inside the 13.2.0 wheel; opaque/transitive
egg crates.io = 0.11.0          # citation/foreign-witness reference only — never executed
```
observed: egglog 13.2.0 (PyPI)
