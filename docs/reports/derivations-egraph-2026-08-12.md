# Derivation scan — 2026-08-12
Loop: derivation scan over all corpus equivalences, one e-graph per world, saturate(8). ADVISORY — not a gate; every verdict is a mechanical egraph.check.
Suite: 6 declared equivalences · 7 candidate derivations · 5 worlds

| candidate equality | exact | integer | regime-name-only | exact+expansion-applied | integer+regime-name |
|---|---|---|---|---|---|
| chain shift_zero∘strength_reduction: `(x * 2) >> 0` ≡ `x << 1` | not derived | **DERIVED** | not derived | not derived | **DERIVED** |
| inverse_add at a COMPOSITE instance: `((a * c) + (b * c)) - (b * c)` ≡ `a * c` | **DERIVED** | not derived | not derived | **DERIVED** | not derived |
| distributivity (declared: 003): `(a * c) + (b * c)` ≡ `(a + b) * c` | **DERIVED** | not derived | not derived | **DERIVED** | not derived |
| associativity (declared: 020): `(a + b) + c` ≡ `a + (b + c)` | not derived | not derived | **DERIVED** | **DERIVED** | **DERIVED** |
| two-rule chain identity_div∘inverse_add: `(((a * c) + (b * c)) - (b * c)) / 1` ≡ `a * c` | **DERIVED** | not derived | not derived | **DERIVED** | not derived |
| distributivity at a SUBTERM (congruence; first guess mislabeled this as needing assoc — the scan corrected it): `((a * c) + (b * c)) + d` ≡ `((a + b) * c) + d` | **DERIVED** | not derived | not derived | **DERIVED** | not derived |
| genuinely TWO-regime chain strength_reduction+assoc: `(x * 2) + ((y * 2) + z)` ≡ `((x << 1) + (y << 1)) + z` | not derived | not derived | not derived | not derived | **DERIVED** |

## world-relative extraction of `(((a * c) + (b * c)) - (b * c)) / 1`
- exact: `Num.var("a") * Num.var("c")`
- integer: `(Num.var("a") * Num.var("c") + Num.var("b") * Num.var("c") - Num.var("b") * Num.var("c")) / Num(1)`
- regime-name-only: `(Num.var("a") * Num.var("c") + Num.var("b") * Num.var("c") - Num.var("b") * Num.var("c")) / Num(1)`
- exact+expansion-applied: `Num.var("a") * Num.var("c")`
- integer+regime-name: `(Num.var("a") * Num.var("c") + Num.var("b") * Num.var("c") - Num.var("b") * Num.var("c")) / Num(1)`

## honest notes
- Worlds assert guard FACTS by hand; none is a claim of domain truth. `exact+expansion-applied` simulates ADR-0007's declared expansion as data; ES003 pins that no machinery performs it.
- Non-derivations are load-bearing: a guarded rule withholding its merge in the wrong world is the guard system working.
- .flow files are OUT of scope: no flow-level equivalences are declared anywhere in the corpus, so composition equivalence has nothing to compute over yet (candidate future gate: a stage-composition term language + declared commutation guards).
- Advisory tool: `just derive` is NOT part of `just test`; the gate suite stays the ratchet, this scan is the telescope.
