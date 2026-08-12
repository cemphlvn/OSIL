# U2 — License pairing for a mixed spec+grammar+corpus+tooling repo

**Date:** 2026-08-12
**Researcher:** research-agent
**Question:** What license pairing should OAAS (spec prose + formal grammar + conformance
corpus + JSON Schemas + eventual tooling code, destined for Linux Foundation association)
use, based on what comparable LF-associated spec projects *actually* license their files
under (verified against primary LICENSE files, not summaries)?

**Status of this research relative to the repo:** `GOVERNANCE.md` marks licensing and
DCO-vs-CLA as PENDING on this finding. `README.md` gate G5 ("LF submission checklist")
is open and explicitly depends on U1 (which foundation) and U2 (this document). This
document does not resolve U1 — the recommendation below is written to be robust to
either a plain LF AI & Data-style outcome or a JDF/Community-Specification-style outcome,
and flags where the two paths diverge.

---

## TL;DR recommendation

**Split by artifact class, not by directory-tree convenience:**

| Artifact class | Repo paths | Recommended license | Why |
|---|---|---|---|
| Normative spec prose | `spec/`, normative prose inside `profiles/domain/` | **Community Specification License 1.0** (SPDX: `Community-Spec-1.0`) | Only license in the comparison set with a patent grant explicitly scoped to *implementations of the specification* (not just copies of the document text) — see §3. |
| Grammar, JSON Schemas, conformance corpus, tooling code | `grammar/`, `conformance/` (corpus + matrix + golden-render), `registry/`, `tools/` | **Apache License 2.0** (SPDX: `Apache-2.0`) | Matches every comparable project's treatment of code-shaped artifacts; gives Apache's own (code-scoped) patent grant to tooling; matches W3C's own split of test-suite assets away from its document license (§5). |
| Patent-sensitive claims disclosure (if/when needed) | new top-level `PATENTS.md` | Companion doc, not a license | Mirrors FINOS/FDC3's `PATENTS-FDC3-1.0.md` pattern — keep exclusions/claims out of the LICENSE files themselves. |

**Contribution mechanism now: DCO (`Signed-off-by`), not a signed CLA.** Every
LF-adjacent project checked requires *at minimum* a DCO sign-off; CLA is layered on top
only by projects with an already-active foundation legal entity running LFX EasyCLA
(FINOS/FDC3, CNCF/OpenTelemetry). OAAS has no such entity yet (G5 open) — DCO is the
mechanism the SPDX project pairs with the Community Specification License too (its
CONTRIBUTING.md requires *both* the CS License's built-in "deemed" contributor grant
*and* a DCO `Signed-off-by` line, with no separately signed paperwork). Adopt that
pattern; revisit if/when a sponsoring foundation from U1 mandates EasyCLA.

**Confidence: MEDIUM.** High confidence on what the comparison projects actually license
their files under (primary-sourced, see table below). Medium confidence on the
recommendation itself, because it depends on an unresolved fact (which foundation OAAS
ends up under, from U1) that materially changes which precedent is closest — see
"Risks" and "Open questions."

---

## Evidence table (primary sources — LICENSE files read directly, access date 2026-08-12)

| Project | Host / foundation | Spec-text license | Code/tooling license | Test/corpus license | Contribution mechanism | Source |
|---|---|---|---|---|---|---|
| **ONNX** (`onnx/onnx`) | LF AI & Data | Apache-2.0 (single repo-wide `LICENSE`; spec `.md` files not split out) | Apache-2.0 | Apache-2.0 (same file) | DCO — "ONNX has adopted the DCO. All code repositories under ONNX require a DCO... DCO bot will ensure commits are signed" | `github.com/onnx/onnx/blob/main/LICENSE`, `.../CONTRIBUTING.md` |
| **StableHLO** (`openxla/stablehlo`) | **No formal foundation** — Google-led OpenXLA industry consortium; openxla.org states no LF/PyTorch Foundation governance | Apache-2.0 (single repo-wide `LICENSE`) | Apache-2.0 | Apache-2.0 (same file) | **Google CLA** (`cla.developers.google.com`), not DCO | `github.com/openxla/stablehlo/blob/main/LICENSE`, `.../CONTRIBUTING.md`, `openxla.org` |
| **OCI image-spec** (`opencontainers/image-spec`) | Linux Foundation (Open Container Initiative) | Apache-2.0 (single repo-wide `LICENSE`) | Apache-2.0 | Apache-2.0 (same file) | DCO — `CONTRIBUTING.md` requires `Signed-off-by:` line | `github.com/opencontainers/image-spec/blob/main/LICENSE`, `.../CONTRIBUTING.md` |
| **OCI distribution-spec** (`opencontainers/distribution-spec`) | Linux Foundation (OCI) | Apache-2.0 (GitHub license API confirms `Apache-2.0`) | Apache-2.0 | Apache-2.0 (assumed same, org-wide OCI pattern) | DCO — ASSUMPTION: not independently re-verified in this repo's own CONTRIBUTING.md text (checked, DCO not explicitly quoted there), inferred from OCI org-wide policy shared with image-spec | `api.github.com/repos/opencontainers/distribution-spec/license` |
| **CloudEvents spec** (`cloudevents/spec`) | CNCF (graduated 2024-01-25) | Apache-2.0 | Apache-2.0 | Apache-2.0 | DCO — `docs/CONTRIBUTING.md`: "If the Author and Signed-off-by lines don't match, your PR will be rejected by the automated DCO check" | `github.com/cloudevents/spec/blob/main/docs/CONTRIBUTING.md` |
| **OpenTelemetry spec** (`open-telemetry/opentelemetry-specification`) | CNCF | Apache-2.0 | Apache-2.0 | Apache-2.0 | **CLA** via LF EasyCLA — `CONTRIBUTING.md`: "Before you can contribute, you will need to sign the Contributor License Agreement (easycla.lfx.linuxfoundation.org)." DCO not mentioned in this file, though CNCF's charter mandates DCO sign-off foundation-wide for new inbound code contributions (ASSUMPTION: unclear whether that clause is read to cover prose-only spec PRs) | `github.com/open-telemetry/opentelemetry-specification/blob/main/CONTRIBUTING.md`, `github.com/cncf/foundation/blob/main/charter.md` §11(b) |
| **W3C Trace Context** (`w3c/trace-context`) | W3C | **W3C Software and Document License** (SPDX: `W3C`) for "Reports" | (no separate code) | **W3C 3-clause BSD** (SPDX: `W3C-3-clause-BSD`) for "Tests" — explicit dual-license split by artifact class in one `LICENSE.md` | W3C's own Community Group patent/copyright process (not DCO/CLA in the LF sense) | `raw.githubusercontent.com/w3c/trace-context/main/LICENSE.md` |
| **FINOS FDC3** (`finos/FDC3`) | Linux Foundation (FINOS) | **Community Specification License 1.0** (`LICENSE.md`, SPDX-adjacent `Community-Spec-1.0`), plus a standalone `PATENTS-FDC3-1.0.md` | **Apache-2.0** for reference implementations / kits ("Reference implementations and other software contained in FDC3 repositories is licensed under the Apache License, Version 2.0") | Apache-2.0 (schemas/kits directories fall under the code license; not independently file-by-file verified — ASSUMPTION, medium confidence) | **CLA** — ICLA or CCLA executed with FINOS via LF EasyCLA; `CONTRIBUTING.md`: "Commits ... will only be accepted from those participants with an active, executed [ICLA] ... or [CCLA]," enforced by the EasyCLA bot | `github.com/finos/FDC3` root listing (`LICENSE.md`, `LICENSE.spdx`, `PATENTS-FDC3-1.0.md`), `.../CONTRIBUTING.md` |
| **SPDX spec** (`spdx/spdx-spec`) | Linux Foundation (SPDX; also ISO/IEC 5962) | **Community Specification License 1.0** — GitHub's license-detector returns `NOASSERTION` for the repo `LICENSE` file (i.e., a non-standard/non-detected license, consistent with CS License text, which is not in GitHub's common detector list), and `CONTRIBUTING.md` explicitly references "the SPDX Community Specification Contributor License Agreement 1.0" | Code lives in a **separate** repo, `spdx/tools-python`, licensed **Apache-2.0** (verified via `api.github.com/repos/spdx/tools-python/license` → `Apache-2.0`) — split-by-repo rather than split-by-directory | Not independently verified for a corpus-equivalent (spdx-spec has `examples/` — not separately license-tagged; ASSUMPTION it inherits the repo's CS License by default, which would be atypical/undesirable for an examples directory — flagged as a cautionary precedent, see "Risks") | CS License's own "deemed" grant (no signature required — "You do not need to submit a signed copy... by making a contribution... you agree to the terms") **plus** a DCO `Signed-off-by:` line required on every commit | `raw.githubusercontent.com/spdx/spdx-spec/develop/CONTRIBUTING.md`, `api.github.com/repos/spdx/spdx-spec/license`, `api.github.com/repos/spdx/tools-python/license` |

Two more CNCF/LF-adjacent data points surfaced but not deep-dived (noted for completeness,
not in the requested "2-3 W3C or CNCF" set beyond what's above): **in-toto attestation**
(`in-toto/attestation`) — Apache-2.0, "Copyright 2021 in-toto Developers"
(`github.com/in-toto/attestation/blob/main/LICENSE`) — confirms the plain-Apache-2.0
pattern extends beyond OCI/ONNX/CloudEvents into supply-chain-security spec repos too.

---

## 1. What comparable projects actually license their files under

Two clear clusters emerged, not a single norm:

- **"Just Apache-2.0 everywhere" cluster:** ONNX, StableHLO, OCI image-spec,
  OCI distribution-spec, CloudEvents, OpenTelemetry spec, in-toto attestation. All of
  these ship spec prose, schemas, and (where present) tooling code under one repo-wide
  `LICENSE` file — no split by artifact class. This is the majority pattern among the
  projects checked (5 of 7 primary comparisons technically LF/CNCF-hosted, 1 of 7 not
  foundation-hosted at all).
- **"Split spec license from code license" cluster:** W3C (document license for prose,
  BSD-3 for tests), FINOS/FDC3 (Community Specification License for the standard,
  Apache-2.0 for kits), SPDX (Community Specification License for the spec repo,
  Apache-2.0 in a *separate* tooling repo). This pattern appears specifically among
  projects that treat the artifact as a **standard with a formal specification-track
  process** (W3C Recommendation track, JDF/Community Specification process, or —
  for SPDX — an ISO/IEC standard) rather than as "an open-source project that happens to
  document a format in markdown."

The dividing line is not "LF vs not-LF" — ONNX and OCI are both squarely LF-hosted and
both just use plain Apache-2.0. The dividing line is closer to: **does the project intend
to be citable/adoptable as a standard independent of any particular reference
implementation, with a patent posture that survives the reference implementation being
abandoned or forked.** OAAS's own framing (`README.md`: "an open specification layer,"
G5 = LF submission checklist, explicit ecosystem-coordination stance toward ONNX/MLIR/WASM
rather than an implementation-first stance) reads closer to the second cluster than the
first — this is the main argument for the CS-License recommendation, not foundation
membership alone.

## 2. Community Specification License 1.0

Read directly from `CommunitySpecification/Community_Specification` (canonical source,
Copyright 2020 Joint Development Foundation, itself CC-BY-4.0-licensed as a governance
document) and cross-checked against its live use in `finos/FDC3/LICENSE.md`:

- **Scope:** "sets forth the terms under which contributors participate in and
  contribute to the development of specifications, standards, best practices,
  guidelines, and other similar materials" — and explicitly: **"is not intended for
  source code."** The license template itself directs source code to a companion
  license (its own template defaults to MIT; real adopters are free to pick differently
  — FDC3 pairs it with Apache-2.0, which the license permits).
- **Copyright grant:** contributors grant a non-sublicensable, perpetual, worldwide,
  non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce,
  prepare derivative works of, publicly display/perform, and distribute submitted
  materials.
- **Patent grant (§2.1.1.1):** "Contributor grants Licensee a non-sublicensable,
  perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable ... license
  to its Necessary Claims" — "Necessary Claims" is a defined term scoped to claims
  *necessarily infringed by an implementation of the specification*, not merely by
  copying the document text. Contributors retain a formal notice procedure to exclude
  specific claims (i.e., the grant is not unconditionally universal — mirrors
  FRAND-style carve-outs common in SDO IPR policies, though the default commitment is
  royalty-free, not merely RAND).
- **Attribution (§1.2):** derivative works must attribute "the Working Group,"
  including at minimum the material's name, version number, and source.
- **Relationship to a code license in the same repo:** the CS License and a project's
  chosen source-code license are meant to coexist file-by-file (or repo-by-repo, as
  SPDX does it) — the FDC3 precedent is a single repository with `LICENSE.md` (CS
  License, governs the standard's prose/markdown) and a separate statement that
  "Reference implementations and other software... is licensed under ... Apache License,
  Version 2.0." Neither Linux Foundation's own description of Community Specification
  (`linuxfoundation.org` blog, fetched 2026-08-12) nor the JDF FAQ (`jointdevelopment.org/faq`,
  fetched 2026-08-12) states that CS License is *required* for LF-hosted spec projects —
  it is explicitly framed as an optional offering via JDF ("We invite interested
  projects... to benefit from an organized collaboration platform"), not a mandate. This
  is consistent with the "Apache-2.0 everywhere" cluster in §1 existing as a legitimate,
  common alternative.

**ASSUMPTION:** I could not locate an explicit LF or JDF policy document stating
"spec-track projects MUST use Community Specification License" — the strongest evidence
found is that it's the *offered, purpose-built* option and is the one chosen by every
project in the comparison set that pursued genuine multi-implementer standardization
(FDC3, SPDX, and — found incidentally during search but not deep-verified —
SWHID/`swhid.org`, and Open Compute Project). Treat "required" as false and "the
JDF-recommended path for spec-track work" as true.

## 3. Patent implications: why not just Apache-2.0, why not just CC-BY-4.0

- **CC-BY-4.0 for spec text:** Creative Commons licenses are explicitly copyright-only.
  CC-BY-4.0 §2(b)(1) affirmatively states the license does not grant patent or trademark
  rights. For a specification that third parties will implement (compilers, adapters,
  toolchains — precisely OAAS's stated coordination stance toward ONNX/MLIR/WASM), this
  means CC-BY-4.0 gives you a clean, well-understood copyright license for the *document*
  but zero patent peace for *implementers* of what the document describes. This is
  **acceptable** for specs where the drafting organization/contributors credibly have no
  patent-bearing technical contributions (e.g., a pure vocabulary/glossary, a style
  guide) and **discouraged** where the spec describes non-obvious technical mechanisms
  contributors might separately patent (an IR / semantic-space specification like OAAS's
  own subject matter is exactly the discouraged case).
- **Apache-2.0's patent grant (§3) for spec text:** Apache-2.0 §3 grants a patent license
  scoped to claims "necessarily infringed by their Contribution(s) alone or by
  combination of their Contribution(s) with the Work." Read literally against a
  specification document as "the Work," this *does* extend some patent coverage to the
  document itself — which is part of why the "just Apache-2.0" cluster (ONNX, OCI,
  CloudEvents) is a defensible, not reckless, choice. The gap is that this grant is tied
  to the *contribution* (the text delta a contributor submitted), not explicitly to
  "implementations of the specification" as a general technical teaching — an
  implementer who never copies/redistributes the document text at all (e.g., writes an
  independent decoder from a third-party description of the format) sits in a legally
  less-certain position than under a purpose-built spec license. This is the concrete,
  named reason W3C, JDF/Community-Specification, and OWFa all define their patent grants
  around "Necessary Claims of implementations" rather than around "the Work" as a
  copyrightable document.
- **Net:** the choice between "plain Apache-2.0" and "CS License + Apache-2.0" is a
  real risk-tolerance judgment call, not a right-vs-wrong call — see "Risks" below.

## 4. DCO vs CLA at LF AI & Data and JDF

- **LF AI & Data:** the Project Lifecycle Document (`lfai/foundation`, fetched
  2026-08-12) lists "Install the GitHub DCO app on all repos" as a mandatory Sandbox-stage
  requirement. It separately mentions founders "execute the Project Contribution
  Agreement transferring the project's assets to the Linux Foundation" — this is an
  org-to-LF asset-transfer agreement, not a per-contributor CLA. No LF AI & Data project
  in the comparison set (ONNX) uses a per-contributor CLA; all use DCO only.
- **CNCF (relevant because CloudEvents/OpenTelemetry are the closest CNCF spec
  analogs):** the CNCF Charter (`cncf/foundation/charter.md` §11(b), fetched
  2026-08-12) states "All new inbound code contributions to the CNCF shall be
  accompanied by a Developer Certificate of Origin sign-off," and separately, "Each
  project shall determine whether it will require use of an approved CNCF CLA" — DCO is
  the floor, CLA is opt-in per project. CloudEvents opted DCO-only; OpenTelemetry layered
  a CLA on top (via LFX EasyCLA) — showing both patterns coexist even within one
  foundation.
- **JDF:** the JDF FAQ (fetched 2026-08-12) did not itself state a DCO-vs-CLA policy in
  the content retrieved. The concrete evidence instead comes from how JDF-adjacent
  Community-Specification projects actually implement it: **SPDX pairs the CS License's
  own built-in "deemed" contributor grant (no separate signature — "by making a
  contribution... you agree to the terms") with a DCO `Signed-off-by:` line**, i.e. DCO
  is used as the provenance/attestation mechanism *underneath* a license that already
  carries its own inbound patent+copyright grant. **FINOS/FDC3 instead requires a fully
  executed ICLA/CCLA** via LFX EasyCLA on top of the CS License. Both are real,
  currently-live patterns; the difference tracks organizational maturity (FINOS is an
  established foundation with legal staff running CLA administration; SPDX's spec repo
  keeps things lighter).
- **For OAAS specifically:** given no foundation sponsor exists yet (G5 open, U1
  unresolved), the SPDX pattern (CS-License-style deemed grant + DCO) is the only one of
  the two that doesn't require infrastructure (LFX EasyCLA) that a pre-affiliation
  project doesn't have access to. **Recommendation: DCO now**, revisit if/when U1 lands
  on a foundation that mandates CLA (OpenTelemetry-style) rather than accepting DCO
  (ONNX/CloudEvents-style).

## 5. Does a conformance corpus need special licensing treatment?

Yes, on two independent grounds found in the primary sources:

1. **Precedent for splitting it out:** W3C is the one project in the comparison set that
   explicitly, structurally separates test-suite licensing from spec-text licensing in
   the same `LICENSE.md` — "Reports" (spec) under the W3C Software and Document License,
   "Tests" under the more permissive W3C 3-clause BSD License, specifically so that
   conformance-test code can be freely reused/modified inside third-party test harnesses
   without inheriting the document license's attribution-to-the-Working-Group
   requirement. This directly supports putting `conformance/corpus/` under the permissive
   code license (Apache-2.0) rather than the spec license (CS License), matching OAAS's
   own `GOVERNANCE.md` treatment of `conformance/` as **shared** (ecosystem-negotiated),
   distinct from `spec/`'s **self** class.
2. **Volume/originality mechanics specific to a corpus:** a conformance corpus by design
   accumulates many small, often near-trivial example files (a single short config or
   IR snippet is common). Two practical consequences: (a) DCO sign-off is per-commit and
   trivially satisfied even for a one-file addition, so it imposes negligible friction —
   this favors keeping the corpus under the same DCO-based contribution flow as
   everything else rather than inventing a separate lighter-weight path; (b) some
   individual corpus files may fall below the threshold of originality for copyright
   protection at all (a minimal syntactic example may be "the only way to express X"),
   meaning the license nominally attached may not even be the operative legal protection
   for that file — this is a reason to license the corpus permissively (Apache-2.0) by
   default rather than under the spec license's Working-Group-attribution regime, since
   attribution requirements on possibly-uncopyrightable trivial snippets create
   compliance questions with no clear benefit.

**Cautionary counter-example found:** `spdx/spdx-spec`'s `examples/` directory does not
appear to carry a distinct license tag from the repo's Community Specification License
— i.e., SPDX itself does *not* cleanly execute the split recommended above. This is
flagged as a real precedent for "don't bother splitting," not just a hypothetical; noted
under Risks.

---

## Risks of the recommended pairing (CS License 1.0 for spec/ + Apache-2.0 for
grammar/conformance/registry/tools/, DCO now)

- **Unfamiliarity cost.** CS License 1.0 is far less recognized than Apache-2.0 or
  CC-BY-4.0. Corporate legal/OSS-compliance teams that gate on an SPDX allow-list may
  flag it for manual review, slowing external adoption in a way plain Apache-2.0 would
  not. This is a real, named cost against a real, named benefit (§3) — not free.
- **File-boundary ambiguity in a monorepo.** Every real dual-license precedent found
  either uses a single repo-wide license (majority cluster) or puts the two artifact
  classes in **separate repos** (SPDX: spec repo vs `tools-python`). FDC3 is the only
  clean same-repo split found, and even FDC3's split is coarse (whole directories, not
  individual files) — SPDX's own `examples/` directory shows the split can slip even
  inside a project that otherwise champions the CS License. OAAS's directory layout
  (`grammar/`, `conformance/`, `spec/` all siblings, with grammar prose living partly
  *inside* `spec/`) will need an explicit, enforced convention (e.g., a `REUSE.toml` /
  per-file `SPDX-License-Identifier` header, checked in CI) or this ambiguity will
  recur — plan for that as a concrete follow-up task, not an afterthought.
- **Bet on an unresolved fact (U1).** If U1 resolves toward OAAS joining LF AI & Data as
  an ordinary hosted project (the ONNX path), the closest and most-followed precedent in
  that specific foundation uses plain Apache-2.0 with no CS License at all — adopting CS
  License now could put OAAS in the minority pattern *within its own foundation*,
  trading conformity for patent precision it may not end up needing if LF AI & Data's own
  IP policy already gives adequate patent peace at the foundation level (untested here —
  see Open Questions).
- **Patent grant isn't unconditional.** CS License 1.0's own §2.1.1.1
  Necessary Claims patent grant is contributor-scoped with an opt-out procedure, not an
  unconditional universal grant — overselling "explicit patent grant" as bulletproof
  would be dishonest. It is *stronger* than CC-BY-4.0 (which has none) and *more explicit
  for spec implementations* than Apache-2.0's contribution-scoped grant, but it is not a
  guarantee against all patent risk.
- **DCO-now-CLA-later migration cost.** If the eventual foundation sponsor (post-U1)
  mandates EasyCLA-backed CLA (OpenTelemetry/FDC3 pattern), retroactively obtaining CLA
  coverage for contributions already accepted under DCO-only is administratively
  possible but adds friction (re-affirmation requests to prior contributors, or a
  re-licensing effort). This is a known, accepted, reversible risk, not a blocker — DCO
  is still the right default now given no EasyCLA access exists pre-affiliation.

## Open questions

1. **U1 dependency:** which foundation actually hosts OAAS (LF AI & Data vs a
   JDF-chartered Community Specification project vs CNCF vs staying independent) is
   still open and directly determines whether the CS-License path (JDF/FDC3/SPDX
   precedent) or the plain-Apache-2.0 path (ONNX/OCI precedent) is the better-trodden
   road. This document's recommendation should be re-checked once U1 lands.
2. **Does OAAS intend a genuine multi-implementer standards-track outcome** (up to
   possible ISO-style submission, as SPDX pursued) or is "Linux Foundation association"
   primarily about hosting/governance/credibility rather than formal SDO IPR mechanics?
   This is the real fork identified in §1 and wasn't resolved by any document read in
   this repo (`README.md`, `GOVERNANCE.md` state the gate but not the intent behind it).
3. **Where exactly does `grammar/*.ebnf` belong** — spec-like (it defines normative
   syntax, arguably as central to "the specification" as prose) or code-like (it's a
   formal, mechanically-processed artifact)? No precedent project in the comparison set
   has an EBNF-shaped artifact split out separately from either its prose or its code;
   this recommendation defaults it to Apache-2.0 (code-like) but this is a genuine
   judgment call, not a documented convention. **ASSUMPTION**, flagged explicitly.
4. **Would LF AI & Data's or JDF's foundation-level IP/patent policy (not the
   project-level file license) already provide adequate patent peace independent of
   which file-level license OAAS picks?** Some foundations layer a membership-level
   patent non-assertion or defensive-suspension clause into their bylaws/IP policy on
   top of whatever license individual projects choose — if OAAS's eventual foundation
   does this, the marginal value of CS License's patent grant over plain Apache-2.0
   shrinks. Not investigated in this pass (would require reading the specific candidate
   foundation's IP policy, which depends on U1's outcome first).
5. **REUSE/SPDX-header tooling decision** — not really a license-choice question but a
   direct consequence of picking a two-license pairing (per "Risks" above): needs its own
   small implementation decision (e.g., adopt the `reuse.software` convention with a
   `REUSE.toml`) before G1/G5, not researched here.

---

## Sources

1. ONNX LICENSE — https://github.com/onnx/onnx/blob/main/LICENSE (accessed 2026-08-12)
2. ONNX CONTRIBUTING — https://github.com/onnx/onnx/blob/main/CONTRIBUTING.md (accessed 2026-08-12)
3. StableHLO LICENSE — https://github.com/openxla/stablehlo/blob/main/LICENSE (accessed 2026-08-12)
4. StableHLO CONTRIBUTING (Google CLA) — https://github.com/openxla/stablehlo/blob/main/CONTRIBUTING.md (accessed 2026-08-12)
5. OpenXLA governance page — https://openxla.org/ (accessed 2026-08-12)
6. OCI image-spec LICENSE — https://github.com/opencontainers/image-spec/blob/main/LICENSE (accessed 2026-08-12)
7. OCI image-spec CONTRIBUTING (DCO) — https://github.com/opencontainers/image-spec (root README/CONTRIBUTING) (accessed 2026-08-12)
8. OCI distribution-spec LICENSE (GitHub license API) — https://api.github.com/repos/opencontainers/distribution-spec/license (accessed 2026-08-12)
9. OCI distribution-spec CONTRIBUTING — https://raw.githubusercontent.com/opencontainers/distribution-spec/main/CONTRIBUTING.md (accessed 2026-08-12)
10. CloudEvents spec CONTRIBUTING (DCO) — https://github.com/cloudevents/spec/blob/main/docs/CONTRIBUTING.md (accessed 2026-08-12)
11. CloudEvents CNCF graduation — https://www.cncf.io/announcements/2024/01/25/cloud-native-computing-foundation-announces-the-graduation-of-cloudevents/ (accessed 2026-08-12)
12. OpenTelemetry specification CONTRIBUTING (CLA) — https://github.com/open-telemetry/opentelemetry-specification/blob/main/CONTRIBUTING.md (accessed 2026-08-12)
13. CNCF Charter §11(b), DCO/CLA — https://github.com/cncf/foundation/blob/main/charter.md (accessed 2026-08-12)
14. W3C Trace Context LICENSE.md (dual license) — https://github.com/w3c/trace-context/blob/main/LICENSE.md (accessed 2026-08-12)
15. W3C test suite licensing policy — https://www.w3.org/Consortium/Legal/2008/04-testsuite-copyright.html (accessed 2026-08-12)
16. FINOS FDC3 repo root (LICENSE.md, LICENSE.spdx, PATENTS-FDC3-1.0.md) — https://github.com/finos/FDC3 (accessed 2026-08-12)
17. FINOS FDC3 CONTRIBUTING (CLA/EasyCLA) — https://github.com/finos/FDC3/blob/main/CONTRIBUTING.md (accessed 2026-08-12)
18. SPDX spec CONTRIBUTING (CS License + DCO) — https://github.com/spdx/spdx-spec/blob/develop/CONTRIBUTING.md (accessed 2026-08-12)
19. SPDX spec LICENSE detector (NOASSERTION) — https://api.github.com/repos/spdx/spdx-spec/license (accessed 2026-08-12)
20. SPDX tools-python LICENSE (Apache-2.0) — https://api.github.com/repos/spdx/tools-python/license (accessed 2026-08-12)
21. Community Specification License 1.0 full text — https://github.com/CommunitySpecification/Community_Specification/blob/main/1._Community_Specification_License-v1.md (accessed 2026-08-12)
22. Community Specification License — SPDX registry entry — https://spdx.org/licenses/Community-Spec-1.0.html (accessed 2026-08-12)
23. Linux Foundation "Accelerating Open Standards development with Community Specifications" — https://www.linuxfoundation.org/blog/blog/accelerating-open-standards-development-with-community-specifications (accessed 2026-08-12)
24. Joint Development Foundation FAQ — https://jointdevelopment.org/faq/ (accessed 2026-08-12)
25. in-toto attestation LICENSE — https://github.com/in-toto/attestation/blob/main/LICENSE (accessed 2026-08-12)
26. LF AI & Data Project Lifecycle Document (DCO app mandatory) — https://github.com/lfai/foundation/blob/main/LF%20AI%20%26%20Data%20Project%20Lifecycle%20Document.md (accessed 2026-08-12)
27. W3C Patent Policy overview — https://www.w3.org/2004/02/05-patentsummary.html (accessed 2026-08-12)
28. CC-BY vs specification patent grants discussion (Open Web Foundation) — https://www.openwebfoundation.org/the-agreements/the-owf-1-0-agreements-granted-claims (accessed 2026-08-12)

---

**Epistemological note:** This research reflects primary-source LICENSE/CONTRIBUTING
file contents as of 2026-08-12. License choices at these projects can and do change
(e.g., a project could migrate from DCO to CLA or vice versa). All claims not directly
quoted from a fetched primary source are explicitly marked `ASSUMPTION:` inline above.
This document does not itself constitute legal advice; before ratifying a license
pairing, OAAS's human maintainers should have the recommendation reviewed by counsel
familiar with SDO/patent-grant licensing, particularly given the CS License's
comparatively low familiarity outside standards-body circles.
