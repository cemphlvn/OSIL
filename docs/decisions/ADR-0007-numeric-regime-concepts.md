# ADR-0007: Numeric regimes as named concepts (`domain.numeric`)

Date: 2026-08-12 · Status: **RATIFIED** (maintainer instruction, same day) —
applied: profiles/domain/numeric/ · corpus 020 · spec/TERMS.md first entry ·
re-baseline. Gate G5 closed by this application.
Origin: compression-scout name-direction finding (docs/reports/
compression-2026-08-12.md): `guards { numeric_semantics = … }` recurs across
5 of 6 equivalence fixtures — the first mechanically-detected naming
opportunity in the corpus.

## What the concept IS (the analysis, not just the block)

A numeric regime is an equivalence's **validity domain**: distributivity holds
under exact arithmetic and silently breaks under floating point; strength
reduction (`x*2 <=> x<<1`) holds only for integers. Today each equivalence
re-declares its regime as a raw key/value pair. The proposal names the regimes
as concepts — and the fit with the existing `concept` production is exact,
because a regime has *realizations*: concrete arithmetics that carry it. This
is the transcript's own category-substitution pattern (AuthenticatedEncryption
→ {AES-GCM, ChaCha20}) applied to numerics: regime → {carriers}.

## Proposed vocabulary (lands as `profiles/domain/numeric/numeric.oaas`)

```
// profiles/domain/numeric/numeric.oaas (created by ratifying ADR-0007)
// provenance: compression-scout naming finding, 2026-08-12
profile domain.numeric {
    version = 0
}

concept ExactArithmetic {
    equivalent_under { numeric_semantics = exact }
    to { rational_arithmetic, arbitrary_precision, symbolic }
}

concept IntegerArithmetic {
    equivalent_under { numeric_semantics = integer }
    to { int32_wrapping, int64_wrapping, arbitrary_precision_integer }
}
```

(Realization lists are ILLUSTRATIVE — to be curated when the egg adapter
lands, U5. `equivalent_under` here reads: the regime's identity holds under
this condition; `to` lists carriers realizing it. New directory
`profiles/domain/numeric/` gets a standard subtree card.)

## Usage form (parses under grammar v0.3 TODAY — no grammar change)

```
equivalence distributivity {
    (a * c) + (b * c) <=> (a + b) * c
    guards { regime = ExactArithmetic }
}
```

## Univocity handling (two forms = tracked synonym, not silent drift)

- `regime = <ConceptName>` becomes the CANONICAL guard form for new content.
- `numeric_semantics = exact|integer` remains valid as the declared EXPANSION
  of the named form (existing fixtures 003/009/013/014/015 keep their
  transcript-faithful raw guards — no corpus rewrite).
- univocity-lint records the pair in spec/TERMS.md with the canonical choice.
- One new corpus fixture demonstrates the named form (added on ratification).

## Compression claim, rung-honest

- **Token rung: NEUTRAL.** `regime = ExactArithmetic` is the same 3 tokens as
  `numeric_semantics = exact`; the concept blocks ADD ~30 tokens. Naming does
  not pay here and this ADR does not claim it does.
- **Concept rung: the actual gain.** (a) single point of meaning — refining
  what `exact` means happens once, not per-equivalence; (b) substitution
  reasoning — carriers are enumerable and swappable per target, the crypto
  pattern; (c) **search-space compression** — the egg projection can export
  rewrite-rule sets *keyed by regime* (all ExactArithmetic rules as one
  family), which is the transcript's "equivalence classes grouped by semantic
  family" made concrete.

## On ratification (one instruction applies all of this)

1. Create `profiles/domain/numeric/` (card + numeric.oaas as above).
2. Add corpus fixture: equivalence using `regime = ExactArithmetic`.
3. Record the synonym pair for univocity-lint's first TERMS.md entry.
4. `just check` + `just compress` re-baseline (expect: +1 fixture, covering
   set unchanged, naming candidate resolved).
