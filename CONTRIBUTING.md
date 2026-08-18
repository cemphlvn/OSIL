# Contributing to OAAS

Thanks for your interest. OAAS is an open specification for a semantic
architecture layer — start with `README.md` for what it is and the gate table
for where it stands.

## License and sign-off (DCO)

Contributions are accepted under **Apache-2.0** (inbound = outbound). Every
commit must carry a Developer Certificate of Origin sign-off:

    git commit -s

which appends `Signed-off-by: Your Name <you@example.com>`, certifying
https://developercertificate.org/. No CLA.

## How this repository works (read before your first PR)

This repo is unusual: it is designed to be operated by humans AND agents, and
its rules are mechanical, not stylistic. `just test` must be green — it runs
the corpus contract, ONNX round-trip, golden render, policy agreement,
resolution, e-graph, stage, and view gates. CI runs the same suite.

The rules that will actually affect your PR:

1. **Triple representation**: a change that adds or renames a language
   construct ships its spec prose, grammar production, and ≥1 corpus example
   in the same PR. The validator enforces production coverage mechanically.
2. **Corpus discipline** (`conformance/corpus/`): one construct per file,
   `//` provenance header, stable ids — additions are free, deletions require
   maintainer ratification.
3. **Negative fixtures**: `EXPECTED-FAIL:` pins mark open gaps and are closed
   only through the documented XPASS ritual; `MUST-FAIL:` rejections are
   permanent and are NEVER flipped — a rejection that starts parsing is a
   regression, not an opportunity.
4. **Boundary obligation**: a PR that enlarges the grammar ships at least one
   rejection fixture pinning the new construct's boundary (or justifies "no
   new boundary"). See `spec/conformance.md` §2.
5. **Ratification points** (maintainer sign-off required): grammar changes,
   normative MUST/SHOULD spec text, skill frontmatter, corpus deletions,
   golden blessings. Everything else flows through ordinary review.
6. **Agent contributors** are first-class: `AGENTS.md` is the operating
   manual; your diff must stay within the scope of the skill you operate
   under (`improvable/`), and `tools/policy_check.py` must stay green.

## Good first contributions

- ONNX suite cases (`conformance/interop/onnx/cases/` — one generator per
  file; each grows the preservation-score scope honestly).
- Curriculum paths (`curriculum/paths/` — views over the corpus, ids only).
- Ecosystem profiles (MLIR and WASM are stubs awaiting their G3-style gates).
- Reading `docs/reports/` and filing issues where a claim seems overstated —
  witness diversity is a governance requirement here (GOVERNANCE.md).

## Naming note

"OAAS" carries a known collision risk with an existing LF AI & Data project
(OAAX); a rename is expected before any foundation submission. Build against
the repo, not the name.
