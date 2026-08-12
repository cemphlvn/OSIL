# U1 — Linux Foundation Onboarding Paths for OAAS (2026)

**Date:** 2026-08-12
**Researcher:** research-agent
**Question:** What are the realistic Linux Foundation onboarding paths for a brand-new open-specification project in 2026, and what does each concretely require?
**Feeds:** `docs/intake/synthesis-repo-organization.md` → Gate **G5 LF readiness** ("charter, license pairing, governance, contribution ladder... submission checklist for the chosen LF path satisfied").

All sources below were fetched live (WebFetch/WebSearch, several via raw GitHub content) on **2026-08-12**. Where a claim is a summary produced by the fetch tool rather than a verbatim quote from the primary document, that is noted. Nothing here is drawn from model memory of pre-cutoff training data — every load-bearing claim below traces to a URL fetched this session.

---

## TL;DR Recommendation

**Two-phase path, not a single choice:**

**Phase 0 (now, day 0, zero gatekeeping, zero cost):** Self-serve adopt the **Community Specification** license/template (governed by the Joint Development Foundation, an LF entity) directly into `spec/` — no membership, no LF contact, no vote required. This is the only path that is literally usable *today* and is a legitimate, LF-branded way to say "developed with Linux Foundation legal/process infrastructure" before OAAS has adopters, maintainers-plural, or a sponsor.

**Phase 1 (once the repo's own G1–G4 gates are met — grammar+corpus, self-description, ONNX round-trip, visual identity projection):** Apply to **LF AI & Data Foundation's Sandbox stage**. This is literally ONNX's home foundation, the entry bar is comparatively low (fit-of-mission + one sponsoring member org + governance docs + OSI-approved license + Technical Charter — no stars/badge/multi-org requirement at Sandbox), and there is a direct, verified precedent for a *specification-only* project succeeding there end-to-end: **Bitol / Open Data Contract Standard**, Sandbox (Sept 2023) → Incubation (Nov 2024) → Graduated (2026), using Apache-2.0 for the spec text, not the Community Specification License.

**OpenSSF is not a plausible host** — its ~22 current projects are exclusively supply-chain-security tooling (SBOM, VEX, signing, scorecards); OAAS's security-invariants angle should aim to **cross-reference or align with OpenSSF outputs (e.g., OSPS Baseline, Gemara)**, not seek hosting there.

**Do not pursue full Joint Development Foundation (JDF) *formation*** (a standalone legal entity with dues, a Project Charter, a Funding Agreement) at this stage — that machinery exists for multi-company consortia that need international standards-body escalation (ISO/IEC JTC1 PAS), which is years away for OAAS, if ever relevant.

**Naming flag (see §5):** "OAAS" has no strong prior trademark claim, but **"OAAX" — Open AI Accelerator eXchange — is an existing LF AI & Data *Sandbox* project** (donated by Network Optix, Jan 2025, github.com/OAAX-standard) in the *same foundation*, same "open standard for AI interop" space, one character off from OAAS. This is the single highest-priority naming risk found and should be resolved (or explicitly accepted) before any LF-facing announcement.

**Confidence:** HIGH on the LF AI & Data lifecycle mechanics and the Community Specification mechanics (both verified against primary/raw-source repo files). MEDIUM on OpenSSF exclusion (scope statement is clear; no exhaustive precedent search of every historical OpenSSF project was done). MEDIUM-LOW on trademark clearance (search-engine-based only; no formal USPTO/EUIPO search was run — see ASSUMPTION flags in §5 and §6).

---

## 1. LF AI & Data Foundation — Project Lifecycle (ONNX's home)

**Primary source:** `LF AI & Data Project Lifecycle Document.md`, approved and in effect since **June 1, 2023**, fetched verbatim via raw GitHub content.
https://github.com/lfai/foundation/blob/main/LF%20AI%20&%20Data%20Project%20Lifecycle%20Document.md (accessed 2026-08-12, full text retrieved)

### Four stages: Sandbox → Incubation → Graduation → Emeritus

**Sandbox stage — entry requirements (exact, quoted from source):**
1. "Fit the scope and mission of LF AI & Data"
2. "Have a sponsor who is an existing LF AI & Data member. Alternatively, a new organization would join LF AI & Data and sponsor the project's incubation application."
3. "Have an open and documented technical governance. The Linux Foundation team can help set this up as part of the onboarding process."
4. "Have an OSI-approved license."
5. Adopt open governance documented in a **Technical Charter**; execute the **Project Contribution Agreement** transferring the project's assets to the Linux Foundation.

Plus a task list to actually execute: submit a **Project Contribution Proposal via GitHub PR** to `lfai/proposing-projects/proposals/`; move code into its own GitHub org (not the founder's); enable 2FA org-wide; install the GitHub DCO app; add `@thelinuxfoundation` as GitHub org co-owner; achieve OpenSSF Best Practices Badge **Passing**; name a security-issue handler; and have **9 mandatory files**: `LICENSE.md`, `README.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `CODE_OF_CONDUCT.md`, `RELEASE.md`, `GOVERNANCE.md`, `SUPPORT.md`, `SECURITY.md`. Entry is by **majority TAC vote**.

**Incubation stage** — Sandbox requirements plus: ≥3 orgs actively contributing, a defined TSC with named chair, **≥500 GitHub stars**, OpenSSF Badge **Silver**. Majority TAC vote.

**Graduation stage** — Incubation requirements plus: "healthy number of code contributions from at least five organizations," **≥1000 GitHub stars**, OpenSSF Badge **Gold**, 12 months of substantial ongoing commit flow, at least one completed collaboration with another LF AI & Data project. Requires **affirmative vote of both the TAC and the Governing Board**. The document explicitly notes: "Since some of these criteria can vary depending on a project's type, scope, and size, the TAC has final judgment over the activity level adequate to meet these criteria" — i.e., stars/commits are TAC-interpreted, not hard-coded, for non-standard project shapes.

**Emeritus/Archived** — inactive projects; trademarks and assets remain with LF AI & Data/Linux Foundation permanently.

**No explicit minimum dwell time** is stated for Sandbox before applying to Incubation (contradicts a plausible assumption of a fixed "12–18 months" floor — that number, found in a secondary summary early in this research, is the *expected* Incubation→Graduation window, not a Sandbox floor; the primary doc only says a **rejected** stage-transition request may be **re-submitted after 6 months**).

### The proposal document itself — verified via a real example

Fetched the actual accepted proposal: `lfai/proposing-projects/proposals/onnx.adoc` (raw, 68 lines, accessed 2026-08-12). ONNX entered *requesting maturity level: Graduated* directly (not Sandbox) in 2019, backed by "138 contributors, over 7K stars and over 1K forks," 30+ registered supporting companies, and an existing CII/OpenSSF Best Practices badge — i.e., ONNX did not bootstrap inside LF AI & Data, it arrived already mature and asked to be graded in at the top. This means **ONNX's own history is not a template for how a brand-new project like OAAS enters** — the Bitol precedent (below) is the relevant one.

The proposal `.adoc` covers: project name/description, requested maturity level, license, source control location, initial committers/governance model, infrastructure requests, existing sponsorship (list of supporting companies), and CII Best Practices Badge link. This is the actual shape of the document OAAS would eventually have to write.

### Charter template — verified via `lfai/tsc-template`

`https://github.com/lfai/tsc-template` (accessed 2026-08-12) is the literal fill-in-the-blanks charter repo LF AI & Data projects use. Its `tsc/CHARTER.md` (fetched raw) is titled *"Technical Charter... for [PROJECT NAME] a Series of LF Projects, LLC"* and is a boilerplate shared across multiple LF sub-foundations (this specific copy still contains un-replaced text referencing "the Academy Software Foundation," confirming it is a shared LF Projects template, lightly re-skinned per foundation). Notably, **Section 7 (Intellectual Property Policy)** hard-codes a license *pairing*:
> "7.b.i. All new inbound code contributions... **Apache License, Version 2.0**... 7.b.iv. Documentation will be received and made available by the Project under the **Creative Commons Attribution 4.0 International License**."

This is a directly relevant, primary-sourced data point for **U2 (license pairing)**: the standard LF Projects charter *already* encodes an Apache-2.0 (code) / CC-BY-4.0 (docs) split as its default — matching the ASSUMPTION already logged in `synthesis-repo-organization.md`. Flagging for U2, not resolving it here.

### Precedent: a specification-only project completing the full lifecycle — Bitol / Open Data Contract Standard

This is the single most load-bearing finding for OAAS. Bitol (produces the Open Data Contract Standard, ODCS, and Open Data Product Standard, ODPS — YAML/text specifications, not primarily a codebase) went:
- **Sandbox: September 2023**
- **Incubation: November 2024**
- **Graduated: 2026** (exact month not resolved in the fetched source; blog post itself is undated beyond year)

Source: https://bitol.io/bitol-graduates/ (accessed 2026-08-12, summarized by fetch tool — treat quoted numbers as tool-summarized, not hand-verified against the raw HTML).

How a non-code project satisfied code-shaped graduation metrics, per that post: GitHub stars **counted across the multiple spec repos** (ODCS + ODPS combined, reported ~1,053 + 113); "contributions from ≥11 organizations" counted via **RFC participation**, not commits; **480+ commits/year** counted spec-text and documentation edits across `bitol-io` repos; OpenSSF Badge **Gold** achieved despite being governance/process documentation rather than software; **59 RFCs decided by public debate over 3 years** was the actual work product. This confirms the TAC's own stated discretion ("criteria can vary depending on a project's type... TAC has final judgment") is exercised in practice for spec-shaped projects, and gives OAAS a concrete existence proof that the LF AI & Data track is navigable without being a traditional codebase.

**License used by Bitol/ODCS:** confirmed via `github.com/bitol-io/open-data-contract-standard` README (accessed 2026-08-12) — **Apache 2.0**, explicitly, not the Community Specification License. This matters for the tension noted in §2 below.

**Current roster (accessed 2026-08-12, via lfaidata.foundation/projects/):** 12 Graduated (incl. ONNX, Bitol, Milvus, Horovod...), 18 Incubating (incl. OAAX — see §5), 16 Sandbox (incl. Feathr, IREE, Open Model Initiative, Open Platform for Enterprise AI...). Note: **OAAX has already moved from Sandbox to Incubation** in the roster snapshot taken today, despite entering Sandbox in January 2025 — i.e., under 18 months Sandbox→Incubation is achievable in practice, consistent with (if faster than) the general "12–18 months Incubation→Graduation" expectation reported for the overall lifecycle in secondary sources.

---

## 2. Community Specification / Joint Development Foundation — the spec-specific track

**Primary sources, all fetched raw from `CommunitySpecification/Community_Specification` and `jointdevelopment.org` (accessed 2026-08-12):**
- https://github.com/CommunitySpecification/Community_Specification (repo root, `Readme.md`)
- `getting-started.md`, `05-governance.md`, `02-scope.md`, `04-license.md`, `01-community-specification-license-v1.md` (all fetched in full or near-full)
- https://jointdevelopment.org/get-started/ and https://jointdevelopment.org/faq/

### What it is, ontologically

The Community Specification is explicitly **not** an open-source software license repackaged for specs — the getting-started doc argues the two are categorically different: "Open source is collaboration around a specific codebase, while specifications provide a blueprint developers implement in different ways in many different codebases... open source licenses provide terms to use and modify a particular codebase and specification licenses are designed to provide terms for **separate independent implementations of the specification**." It was developed by the **Joint Development Foundation** (a Linux Foundation entity), drawing on the Open Web Foundation agreements and the AOMedia Patent License 1.0.

### How a brand-new spec project actually adopts it — verified, concrete, two options

From `getting-started.md` (fetched verbatim, quoted):

> **Option 1 — Reference the official repo:** create a new repo, copy in the Community Specification **Contributor License Agreement**, **Scope.md**, **Notices.md**, **License.md** from `github.com/CommunitySpecification/1.0`, fill in Scope/Notices/License, then "Develop your specification in that repository."
> **Option 2 — Clone the repo** directly and do the same.

**No membership, no fee, no LF contact, no vote is required to do this.** It is literally a fork-and-fill-in-the-blanks operation. Best-practices notes in the same doc: use a CLA bot (EasyCLA or cla-bot) once contributions start; **use CS License for specs, not code**; keep spec and reference code in **separate repos** with the code under a normal OSI license; one spec per repo if there are multiple specs.

**Live proof this is used exactly this way, with zero formal LF affiliation implied by the repo itself:** `finos/standards-project-blueprint` (FINOS = Fintech Open Source Foundation, itself an LF entity, but the blueprint repo is literally the CS template forked and re-skinned) — confirms real-world adoption pattern, accessed 2026-08-12.

### Governance model imposed by the License/Process (`05-governance.md`, quoted)

Defines three roles per "Working Group": **Maintainer** (determines consensus, coordinates appeals), **Editor** (keeps the doc faithful to decisions), **Participants** (anyone who has contributed under the CS License). Decision-making is **consensus-based**, explicitly modeled on ANSI's Essential Requirements for Due Process (openness, no dominance by one party, balance of interests, documented objections, written procedures). A 4-stage spec lifecycle is defined: **Pre-Draft → Draft Specification (Working Group Approval) → Approved Specification → Publication**, with a further optional step of Working-Group-approved **submission to an external standards body** (this is the ISO/IEC PAS-submitter escalation path, gated behind Working Group consensus, not automatic).

### License text itself (`01-community-specification-license-v1.md`, fetched, 99 lines)

Grants (1) an irrevocable copyright license to reproduce/modify/distribute Working Group materials with attribution, and (2) a **patent non-assertion/licensing framework** scoped to "Necessary Claims" within the declared Scope, with a **45-day patent-exclusion window** per contribution and defensive-termination clauses if a licensee sues over the spec. This is materially different in shape from a normal OSS license (MIT/Apache-2.0) — it's a patent-pool-style specification license, which is *the point*: it exists because OSS licenses don't grant the right kind of protection for independent implementers of a spec.

**Formalizing further (full JDF project, not just borrowing the License template):** per `jointdevelopment.org/get-started/` and `/faq/` — email `formation@jointdevelopment.org`; JDF assesses fit and stands up a legal entity; the group customizes a Project Charter / Working Group Charter(s) / optional Funding Agreement; then launches. Membership dues are **per-project, not mandated by JDF**: "Each Project makes its own decision about whether to charge Membership dues and how much to charge." Non-members can still participate as contributors, forum participants, or invited experts. **This heavier path is not needed just to use the License/template** — it is only relevant if OAAS wants a dues-collecting legal entity, formal international standards submission rights, or multi-company governance infrastructure beyond what a GitHub-hosted consensus process provides.

### Tension worth flagging for U2

The Community Specification License is **listed by SPDX** as `Community-Spec-1.0` (spdx.org/licenses/Community-Spec-1.0.html, accessed 2026-08-12) but was **not found among OSI-approved licenses** in this session's searches — and its own documentation argues it is deliberately *not* an open-source software license (it's a specification/patent-pool license, a different category by design). LF AI & Data's Sandbox stage requires "an OSI-approved license." **If OAAS's spec text were licensed solely under the Community Specification License, it is unclear whether that would satisfy LF AI & Data's Sandbox license gate** — no primary source directly addresses this interaction. Precedent (Bitol using plain Apache-2.0 for spec text, not the CS License) suggests LF AI & Data projects that are "specifications" in practice still use ordinary OSI-approved licenses (Apache-2.0) rather than the CS License. **ASSUMPTION: if/when OAAS pursues LF AI & Data hosting, the spec text should be Apache-2.0 or CC-BY-4.0 (both OSI/Creative-Commons standard, both used elsewhere in the LF ecosystem — see charter template §7 above), not the Community Specification License** — this needs explicit confirmation from LF AI & Data staff before G5, not assumed silently. Cross-reference: U2.

---

## 3. OpenSSF — alignment target, not a plausible host

**Source:** https://openssf.org/projects/ (accessed 2026-08-12) and https://github.com/ossf/tac/blob/main/process/project-lifecycle.md (accessed 2026-08-12).

Current roster (as fetched today): **3 Graduated** (Best Practices Badge, Sigstore, SLSA), **5 Incubating** (gittuf, GUAC, OpenSSF Scorecard, OSPS Baseline, Repository Service for TUF), **10 Sandbox** (Bomctl, Gemara, Minder, OpenBao, OpenSSF Model Signing, OpenVEX, OSS-CRS, Protobom, SBOMit, Security Insights, Zarf), plus 4 "TBD status" incubating-adjacent efforts. Every one of these is **supply-chain-security tooling**: SBOM/VEX formats, artifact signing, vulnerability scoring, secrets/dependency tooling. The lifecycle doc's scope test is: "Projects must be aligned with the OpenSSF mission *and* either be a novel approach for existing areas or address an unfulfilled need" — where "the OpenSSF mission" is explicitly the security of open source software supply chains.

A **semantic-architecture DSL for compiler/toolchain intent and invariants is not supply-chain security tooling**, even though it has a "security invariants" angle. Sandbox-stage OpenSSF entry requires only 1+ maintainer and passing the Best Practices badge (comparatively low bar, similar shape to LF AI & Data), so the bar itself isn't the blocker — **mission fit is**.

**Two OpenSSF projects worth watching as *alignment* targets, not hosts:** **OSPS Baseline** (Incubating) and **Gemara** (Sandbox) are themselves specification/requirements-shaped efforts inside OpenSSF (baseline security requirements, and a common requirements-and-evidence framework respectively) — these are exactly the kind of things OAAS's security-invariants profile (`profiles/domain/crypto/` per the repo tree) should cite or interoperate with, the same way `profiles/ecosystem/onnx/` cites ONNX. **No evidence found** that OpenSSF has ever hosted a project whose primary output is a general-purpose semantic/interop DSL rather than a security artifact format or security tool — this was not found because it plausibly does not exist, not because the search was shallow.

**Conclusion: OpenSSF is a downstream-consumer/alignment relationship (cite their security-requirements formats from `profiles/domain/crypto/` or similar), not a submission target.**

---

## 4. What "with the help of LF" can mean at day 0, before any formal submission

Four concrete, verified mechanisms, from lightest-touch to heaviest:

1. **Community Specification template adoption (§2)** — zero contact, zero cost, zero vote. Fork/copy the CS License + Scope/Notices/License files into `spec/`. This is the only mechanism that requires **literally nothing** from the Linux Foundation and is usable this week. It is a legitimate, foundation-backed process (JDF-authored), even though no human at LF is involved unless/until OAAS chooses to formalize.

2. **LFX tools** — `https://lfx.linuxfoundation.org/tools/` (accessed 2026-08-12) is the Foundation's SaaS suite (Insights, Mentorship, EasyCLA, Security, Project Control Center, etc.). LFX Mentorship explicitly lists **participating projects that mentees can apply to work with** — implying the tool surface, in that specific corner, is scoped to already-hosted LF projects, not open to any GitHub repo. I attempted to verify whether **LFX Project Control Center** allows unaffiliated projects to self-register (a plausible "use the tooling before formal hosting" path) via `docs.linuxfoundation.org/lfx/project-control-center/adding-a-main-project`, but that specific doc page **returned a dead link** during this session (moved/removed) — **could not verify**. **ASSUMPTION: most LFX tooling (Mentorship, EasyCLA, Insights dashboards, Project Control Center) requires the project to already be formally hosted by an LF entity; treat LFX access as a Phase-1-or-later benefit, not a day-0 one, until directly confirmed with LF staff.**

3. **LF Charities** (`lf-charities.org`, accessed 2026-08-12) — a separate Delaware nonprofit, tax-exempt under **IRC 509(a)(3)/501(c)(3)**, distinct from the Linux Foundation itself (which is a 501(c)(6)). It provides **fiscal sponsorship** (accepting donations, holding funds) for open-technology projects; current examples cited on the page include Tazama, Jupyter, and Moja Global as "Hosted by," and Jenkins/OS-Climate as "Supported by." **This is a funding/legal-entity mechanism, not a project-lifecycle mechanism** — it doesn't grant TAC standing, a charter, or trademark hosting the way LF AI & Data does. It requires direct email contact (`contribute@lf-charities.dev`), so it is not a zero-touch day-0 option either, just a *lighter-weight* one than a full sub-foundation TAC vote. **Relevant only if OAAS needs to receive/hold money before it has a formal governance home — not otherwise load-bearing for U1.**

4. **Informal engagement before a PR to `lfai/proposing-projects`** — the lifecycle doc itself invites this: "Have an open and documented technical governance. **The Linux Foundation team can help set this up as part of the onboarding process.**" I.e., LF AI & Data staff (`info@lfaidata.foundation`) will informally help a not-yet-proposed project shape its governance docs ahead of a PR — this is a real, sourced "help before submission" channel, but it's advisory, not a tool or legal structure, and it presupposes intent to submit to LF AI & Data specifically.

**Synthesis: the only mechanism that is literally usable with zero LF contact today is #1 (Community Specification).** Everything else (#2–#4) either requires direct outreach or (per the LFX Mentorship evidence) appears scoped to already-hosted projects.

---

## 5. Trademark / naming — "OAAS" collision risk

**Method note:** this was done via web search and a blocked direct USPTO fetch (see below), **not a formal USPTO TESS / EUIPO / WIPO clearance search**. Treat this section as a first-pass screen, not legal clearance. **ASSUMPTION: a proper trademark clearance search (ideally by counsel, at minimum a manual TESS search across relevant Nice classes for software/standards) has not been performed and is a hard prerequisite before any public LF-facing announcement of the name "OAAS."**

### What was found

- **No live, dominant US federal trademark registration for "OAAS."** One historical application was found — e-Magic Inc., serial referenced via `uspto.report/TM/88305896`, for cloud/edge process-control software services — reported by search-engine summary as **refused/abandoned, no longer active** (accessed 2026-08-12; the direct `uspto.report` page itself returned HTTP 403 and could not be fetched directly in this session, so this is a **secondary, unverified** data point — re-check directly on USPTO TESS at uspto.gov/trademarks/search before relying on it).
- **"OAAS" as a bare acronym is heavily overloaded but not trademark-owned by any single party**: AcronymFinder lists "Office as a Service" as a top hit (acronymfinder.com/Office-as-a-Service-(OAAS).html); other loose usages found include "Outsourcing-as-a-Service," "Offshoring-as-a-Service." None of these appear to be registered marks, just descriptive industry shorthand — **low risk from this cluster**.
- **Lowercase "OaaS" is used by at least two unrelated open-source/academic projects**: `hpcclab/OaaS` ("Object as a Service," a serverless-paradigm research project) and `solowan/OaaS` / `carlosv5/OaaS-network` ("Optimizer as a Service" for OpenStack). Neither is trademarked; both are small GitHub research repos. **Low-to-moderate risk** — mostly a discoverability/SEO collision, not a legal one.
- **Highest risk found — "OAAX" (Open AI Accelerator eXchange)**, an **existing LF AI & Data project**, currently at **Incubation** stage per today's roster fetch (entered Sandbox January 2025, donated by Network Optix — https://lfaidata.foundation/projects/oaax/, https://github.com/OAAX-standard, https://www.networkoptix.com/blog/2025/01/29-oaax-joins-lf-ai-data, all accessed 2026-08-12). OAAX defines "a standard runtime API that all AI accelerators can implement" for ML model portability across hardware — i.e., **an open interop *standard*, in the *same foundation*, in the *same general domain* (ML/AI toolchain interoperability adjacent to ONNX)**, with a name that differs from "OAAS" by exactly one letter (X vs S) and is phonetically near-identical. This is not a legal trademark blocker (different letter, different registered/claimed scope), but it is a **severe practical confusability risk** specifically because both projects could plausibly sit in the *same LF AI & Data project directory* someday, get mentioned in the same TAC meeting, or be conflated in search/community discussion. **This is the single most important naming finding of this research.**

### Recommendation on naming

Given OAAX's existence inside the exact target foundation, in an adjacent problem space, **the "OAAS" name should be treated as a live risk, not a settled choice** — this reinforces (independent of this research) that the "OAAS acronym expansion is still undecided" note in the task framing is well-founded caution. If the project proceeds toward LF AI & Data, expect this to surface explicitly during the TAC review/proposal process (naming collisions with existing projects are exactly the kind of thing a TAC would flag). Recommend resolving the expansion/name **before** any LF-facing document is drafted, and running an actual USPTO/EUIPO search (not just web search) as part of that resolution.

**LF's own naming/trademark process itself:** no dedicated "name-clearance checklist" document was found on linuxfoundation.org (the Trademark Usage page, https://www.linuxfoundation.org/legal/trademark-usage, accessed 2026-08-12, covers *using* LF's own marks correctly, not clearing a new project's name). General LF project-hosting guidance (https://www.linuxfoundation.org/projects/hosting, accessed 2026-08-12) confirms trademark transfer is structurally required once hosted ("Any trademark, git repo accounts, or community assets should be owned neutrally by the foundation entity"), and this is echoed in the charter template itself (§5.a, quoted above: "LF Projects shall hold title to all trade or service marks used by the Project"). **ASSUMPTION: LF/TAC performs its own informal collision check during proposal review (as a practical matter, given the OAAX proximity) but no documented, self-serve pre-check tool was found; direct contact (`trademarks@linuxfoundation.org`) is the only verified channel for an explicit LF-side check, and this session did not contact them.**

---

## 6. Hard requirements checklist for the recommended (two-phase) path

### Phase 0 — Community Specification adoption (do now)
- [ ] Fork/copy `Contributor License Agreement`, `Scope.md`, `Notices.md`, `License.md` from `github.com/CommunitySpecification/1.0` into `spec/` (or a dedicated location — repo tree already has `spec/` as its own P1-owned subtree, so this fits cleanly).
- [ ] Fill in `Scope.md` carefully (sets the outer bound of patent commitments — CS docs explicitly warn against drafting it too narrow *or* too broad).
- [ ] Fill in `Notices.md` with a named code-of-conduct/security contact.
- [ ] Decide the reference-code license in `License.md` (default MIT; repo's existing convention should decide, resolve jointly with U2).
- [ ] Once external contributions start: enable a CLA bot (EasyCLA or cla-bot) to require the CS CLA before merge.
- [ ] Keep spec (`spec/`) and any reference code (`tools/`) in separate license domains, per CS best practice.
- [ ] **Explicitly decide and document** whether the *published spec text itself* will ultimately be Apache-2.0/CC-BY-4.0 (LF AI & Data-compatible, precedent: Bitol) vs. the Community Specification License (patent-pool-shaped, uncertain LF AI & Data compatibility) — do not silently default; this is a direct input to U2.

### Phase 1 — LF AI & Data Sandbox proposal (once G1–G4 gates pass)
- [ ] A **sponsor**: an existing LF AI & Data member organization willing to back the proposal, or an org willing to join LF AI & Data to sponsor it. (**Practical gate, not just paperwork** — identify a candidate sponsor early; this is likely the longest-lead-time item.)
- [ ] Project's repo(s) moved into their **own GitHub org** (not a personal/founder org).
- [ ] Org-wide **2FA** enabled; **GitHub DCO app** installed on all repos.
- [ ] `@thelinuxfoundation` added as GitHub org co-owner.
- [ ] **OpenSSF Best Practices Badge: Passing** achieved before Sandbox entry.
- [ ] A named **security issue handler**.
- [ ] All **9 mandatory files** present: `LICENSE.md`, `README.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `CODE_OF_CONDUCT.md`, `RELEASE.md`, `GOVERNANCE.md`, `SUPPORT.md`, `SECURITY.md`.
- [ ] An **OSI-approved license** for the spec/code (Apache-2.0 recommended per Bitol precedent + charter-template default).
- [ ] A completed **Technical Charter** (template: `lfai/tsc-template`), adopted by founding committers.
- [ ] A **Project Contribution Proposal** (`.adoc`, per `lfai/proposing-projects` template — see the fetched ONNX example for exact shape) submitted as a **GitHub PR** to `lfai/proposing-projects/proposals/`.
- [ ] Execute the **Project Contribution Agreement** (transfers project assets to the Linux Foundation).
- [ ] Pass a **majority TAC vote**.
- [ ] (Naming) resolve the OAAX-collision question (§5) before this PR is opened — a TAC reviewer will almost certainly notice.

---

## 7. Realistic timeline

- **Phase 0 (Community Specification adoption):** days, not weeks — it is a file-copy-and-fill-in operation. No external dependency.
- **Time to Phase-1-readiness (G1–G4 in the repo's own gate sequence — grammar+corpus, self-description, ONNX round-trip, visual identity projection, plus finding a sponsor org and assembling the 9 governance files):** not estimable from this research alone; depends entirely on OAAS's own build velocity and — critically — on **finding a sponsoring LF AI & Data member organization**, which is a relationship/BD problem, not a documentation problem, and has no fixed timeline in any source found.
- **Sandbox proposal → TAC vote:** no fixed SLA found in the primary lifecycle doc; existing onboarding-tracker GitHub issues (`lfai/foundation` issues #15, #22, #45, #71, #80 — titles only, not opened in depth this session) suggest a tracked, multi-step onboarding checklist process handled issue-by-issue, implying **weeks to a few months** is plausible once a PR is filed, but this is **inferred, not directly sourced** — flag as ASSUMPTION.
- **Sandbox → Incubation:** OAAX went from Sandbox (Jan 2025) to Incubation within the ~18-month window observed in today's roster snapshot (accessed 2026-08-12) — consistent with, but somewhat faster than, the oft-cited "12–18 months Incubation→Graduation" figure (which is a *different* transition and was found in a secondary/summarized source, not the primary lifecycle doc itself — the primary doc states no fixed interval, only a 6-month reapplication cooldown after a failed vote).
- **Incubation → Graduation:** Bitol took **~14 months** (Nov 2024 → sometime in 2026) for this specific transition, and **~3 years total** (Sept 2023 Sandbox entry → 2026 Graduation) end-to-end — this is the single most relevant real timeline data point available, given Bitol is the closest analog (spec-only project) found.

**Bottom line: Phase 0 is immediate. Phase 1 entry (Sandbox) is realistically 6+ months out at minimum (driven by the sponsor-org search and G1–G4 technical gates, not by LF process speed), and full Graduation, if pursued, is a 2–4 year horizon based on the one directly comparable precedent (Bitol).**

---

## 8. Open questions (not resolved by this research)

1. **Does LF AI & Data's "OSI-approved license" Sandbox requirement accept spec text under the Community Specification License, or does it require Apache-2.0/CC-BY-4.0-style licensing even for pure specification content?** No primary source directly addresses this; Bitol's use of plain Apache-2.0 (not CS License) is suggestive but not conclusive. **Needs a direct question to `info@lfaidata.foundation` or TAC.** (Feeds U2.)
2. **Is there a documented, self-serve trademark/name pre-check tool at LF**, or is `trademarks@linuxfoundation.org` genuinely the only channel? Not found either way conclusively.
3. **What exactly does LFX Project Control Center require for a project to appear/self-register** — could not verify (dead doc link, `docs.linuxfoundation.org/lfx/project-control-center/adding-a-main-project`, accessed 2026-08-12, returned "page no longer exists").
4. **Full USPTO/EUIPO clearance for "OAAS"** has not been run in this session — the one historical filing found (`uspto.report/TM/88305896`) could not be directly fetched (403) and was only characterized via a search-engine summary. **This is the highest-priority follow-up action item**, ahead of any public naming commitment.
5. **Exact TAC review timeline** (proposal PR → vote) is inferred from GitHub issue evidence (titles only), not a documented SLA — worth asking LF AI & Data staff directly, or reading a few of the referenced `lfai/foundation` onboarding-tracker issues (#15, #22, #45, #71, #80) end-to-end for real elapsed-time data, which this pass did not do (out of scope for a first survey; flagging as a cheap, high-value follow-up if the team wants tighter Phase-1 timeline confidence).

---

## Sources (all accessed 2026-08-12)

**LF AI & Data:**
- LF AI & Data Project Lifecycle Document (raw, full text): https://github.com/lfai/foundation/blob/main/LF%20AI%20&%20Data%20Project%20Lifecycle%20Document.md
- ONNX project proposal (raw `.adoc`, full text): https://github.com/lfai/proposing-projects/blob/master/proposals/onnx.adoc
- Proposing-projects repo (process/template overview): https://github.com/lfai/proposing-projects
- TSC/Charter template repo + `tsc/CHARTER.md` (raw): https://github.com/lfai/tsc-template
- Current project roster by stage: https://lfaidata.foundation/projects/
- ONNX project page: https://lfaidata.foundation/projects/onnx/
- Bitol graduation announcement: https://bitol.io/bitol-graduates/
- Bitol/ODCS license confirmation: https://github.com/bitol-io/open-data-contract-standard
- OAAX project page: https://lfaidata.foundation/projects/oaax/ ; https://github.com/OAAX-standard ; https://www.networkoptix.com/blog/2025/01/29-oaax-joins-lf-ai-data
- LF AI & Data onboarding-tracker issues (titles only, not fully read): https://github.com/lfai/foundation/issues/15, /22, /45, /71, /80

**Community Specification / JDF:**
- Community Specification repo (root + governance/license/scope files, raw, full text): https://github.com/CommunitySpecification/Community_Specification
- Community Specification 1.0 canonical repo: https://github.com/CommunitySpecification/1.0
- FINOS live-adoption example: https://github.com/finos/standards-project-blueprint
- Joint Development Foundation — Get Started: https://jointdevelopment.org/get-started/
- Joint Development Foundation — FAQ: https://jointdevelopment.org/faq/
- Linux Foundation Standards & Specifications overview: https://www.linuxfoundation.org/projects/standards
- SPDX license entry: https://spdx.org/licenses/Community-Spec-1.0.html

**OpenSSF:**
- Projects listing: https://openssf.org/projects/
- Project lifecycle doc: https://github.com/ossf/tac/blob/main/process/project-lifecycle.md

**General LF / trademark / fiscal sponsorship:**
- LF project hosting overview: https://www.linuxfoundation.org/projects/hosting
- LF trademark usage policy: https://www.linuxfoundation.org/legal/trademark-usage
- LF Charities: https://lf-charities.org/
- LFX Tools overview: https://lfx.linuxfoundation.org/tools/
- LFX Project Control Center doc (dead link at time of access): https://docs.linuxfoundation.org/lfx/project-control-center/adding-a-main-project

**Naming/trademark screen (secondary, unverified — see §5 and §8 caveats):**
- e-Magic Inc. OAAS filing (fetch blocked, 403; characterized via search snippet only): https://uspto.report/TM/88305896
- AcronymFinder "Office as a Service": https://www.acronymfinder.com/Office-as-a-Service-(OAAS).html
- `hpcclab/OaaS` (Object as a Service): https://github.com/hpcclab/OaaS

---

**Epistemological note:** This research represents best available evidence as of 2026-08-12, gathered primarily from primary/raw-source documents (foundation lifecycle docs, license texts, an actual accepted project proposal, an actual charter template) rather than secondary summaries, per the task's instruction. The trademark section (§5) is the weakest-evidenced part of this report and is explicitly flagged as needing a real clearance search before the team relies on it. LF process details (timelines especially) can and do change; re-verify against the primary URLs above before G5 execution, not against this document alone.
