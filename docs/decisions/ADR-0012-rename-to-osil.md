# ADR-0012: Rename to OSIL (Open Semantic Interoperability Layer)

Date: 2026-08-18 · Status: RATIFIED (maintainer selection via decision
dialog; full-depth rename ratified in the same dialog). Gate G17.

## Context
The working name OAAS carried a collision risk identified by research U1:
OAAX (Open AI Accelerator eXchange), an existing LF AI & Data project one
letter away in an adjacent domain. The rename was the last GX blocker.
Candidates screened against GitHub before the decision: ontoagentics (clean),
ontoflow (taken, 3 active projects), osil (minor unrelated noise), realis
(crowded), semport (weak). Maintainer selected OSIL: the conventional
descriptive-acronym path (ONNX/SPDX family), with a deliberate echo of the
OSI layer model.

## Decision
- Project and repository name: **osil** (github.com/cemphlvn/osil; old URL
  redirects). Expansion: Open Semantic Interoperability Layer.
- FULL depth: file extension `.oaas` becomes `.osil` (34 files, git mv,
  ids stable); strata tokens OAAS-SIR/CIR/NATIVE become OSIL-SIR/CIR/NATIVE
  (core symbol universe, resolver, spec, corpus, contracts, view goldens);
  tool files oaas_check/oaas_read/oaas_resolve become osil_*; grammar file
  and start-symbol production labels renamed; brand tokens swept across all
  living surfaces (64 files).
- **History is frozen**: `docs/` (intake, ADRs 0001-0011, dated reports,
  research memos) retains OAAS untouched; renaming historical records would
  falsify them. Exception: docs/GATES.md gains a header note, and this ADR.
- Sweep note: provenance path strings INSIDE living fixtures were normalized
  to `.osil` by the sweep; git history preserves the original citations.

## Consequences
- Full suite green under the new name on the first post-sweep run
  (`just test`: 8 harnesses including stage commutation 28/28 and view
  witnesses 2/2). Grammar productions added = 0; language unchanged.
- The `.flow` extension is untouched (kind-descriptive, not brand-derived).
- GX has no remaining naming blocker.
- Local working directories named `oaas` are user-side; renaming them is
  optional and does not affect the repository.
