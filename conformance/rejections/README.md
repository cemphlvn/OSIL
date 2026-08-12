# rejections/ — what the language REFUSES (subtree card)

Fixtures that must NEVER parse. Every file carries a syntactic
`// MUST-FAIL: <rule>` marker naming the normative refusal it pins; the
validator turns any parse success here into a build failure (XPASS) — and
unlike corpus gap-pins, these markers NEVER flip: an XPASS in this directory
is always a parser/spec regression, not a ritual step.

Selection principle (what makes an XFAIL smart): ONE fixture per normative
refusal, anchored to the rule/ADR that forbids it. Random syntax errors are
noise — the parser rejects infinitely many strings; we pin only the
boundaries that carry policy weight:
- R001/R002 — document-kind purity (ADR-0005: the policy-inside-the-language
  boundary; agents scoped to flows structurally cannot mint vocabulary)
- R003 — adjacency/juxtaposition (G2 ratification, ex-GAP-3)
- R004 — output arity (G6, out_spec)

Taxonomy (spec/conformance.md §2): temporal pins (`EXPECTED-FAIL: GAP-n`,
closable via the XPASS ritual) live in corpus/; permanent rejections
(`MUST-FAIL:`) live here.
invariants: marker-required · never-flipped · one-fixture-per-rule
policy: agents add freely with rule anchors; deletions propose-only
