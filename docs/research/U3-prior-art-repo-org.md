# U3 — Prior Art: How Successful Spec/Interop Projects Organize Their Repositories

**Date:** 2026-08-12
**Researcher:** research-agent
**Question:** How do successful spec/interop projects actually organize their repositories, and what does that evidence say about OAAS's proposed monorepo tree (v0)?

**Method:** Primary evidence only — GitHub API tree/content listings and raw file contents, fetched directly, not summarized from memory. All repo trees and doc excerpts below were fetched 2026-08-12 from the `main`/default branch of each repository. One claim (JSON-LD test manifest internals) is additionally cross-checked against a GitHub tree listing rather than left as a WebSearch-only claim; this is noted where relevant.

---

## TL;DR

### Patterns to adopt (evidence-backed)

1. **"One-construct-per-file" conformance corpora are real, precedented, and load-bearing.** ONNX's `onnx/backend/test/case/node/{op}.py` — 201 files, one per operator, each a *generator* of example/conformance data rather than a static fixture — is structurally identical to OAAS's proposed `conformance/corpus/`. This is the single strongest direct validation found in this survey. **Delta:** prefer generator files over static fixtures where feasible, so corpus and golden output cannot drift apart (see §Deltas #3).

2. **Never hand-maintain a derived artifact that has a ground-truth source.** ONNX generates `docs/Operators.md` and `docs/Changelog.md` from `onnx/defs/*/defs.cc` via `gen_doc.py`, with an explicit "Do not modify directly" header. Nothing in OAAS's tree currently marks which files in `registry/` or `curriculum/` are hand-authored vs. generated from `spec/`/`grammar/`/`conformance/`. **Delta:** add that marker convention now (see §Deltas #6).

3. **Version each independently-evolving axis explicitly, in one dedicated doc.** ONNX's `docs/Versioning.md` names three distinct, independently-cadenced version numbers (IR version, operator/opset version, model version) and states exactly which kinds of changes bump which. StableHLO layers a *durable compatibility guarantee* (5y backward / 2y forward) on top of its version number via `docs/compatibility.md`, backed by an RFC and enforced in code via the VHLO versioned dialect. OAAS's `spec/{core,execution,interchange,visual}` will not version in lockstep. **Delta:** add `spec/versioning.md` before the first cut (see §Deltas #1).

4. **Conformance-testing machinery should not be uniform across spec files — let it track what's actually being specified.** `opencontainers/image-spec` (a static file format) has **no** conformance directory at all; JSON Schema validation in `schema/` is sufficient. `opencontainers/distribution-spec` (an HTTP protocol) has a full executable Go conformance harness in `conformance/`. Same org, same design principles, deliberately different conformance shapes because the *kind of thing* being specified differs. **Delta:** don't build one `conformance/matrix` shape for all of `spec/*` (see §Deltas #2).

5. **A lightweight, auto-synced aggregator/mirror is a legitimate way to give consumers one place to look, without forcing all ground truth into one repo.** `WebAssembly/testsuite` is a separate, read-only, weekly-auto-updated repo that amalgamates `WebAssembly/spec/test/core` plus tests pulled from ~25 independent per-proposal repos (`simd`, `threads`, `gc`, `tail-call`, `exception-handling`, etc.), explicitly telling contributors to file issues upstream, not in the mirror. This is a template for how OAAS's `registry/` could work if `profiles/domain/{ml,crypto,agent}` ever fission into their own repos. **Delta:** design `registry/` as an aggregator-capable index now, not an implicit assumption that it always holds ground truth (see §Deltas #6).

### Anti-patterns to avoid

**A. Don't let "repo-shaped for future fission" substitute for writing down, today, who owns each subtree and what would trigger a split.** None of the five projects rely on directory shape alone. OCI's charter enumerates three legally-distinct project categories (spec / application / conformance-tool) with different backward-compat and patent-grant obligations attached. WebAssembly's own README states in prose *why* `design/` is kept separate from `spec/` ("so that this spec repository can remain focused"). ONNX's `community/repo_guidelines.md` and `sigs.md` name SIG ownership explicitly. OAAS's design principle ("subtrees cut along ground-truth ownership and version-cadence boundaries") is sound but currently lives only in the *tree shape*, not in a document. **Recommendation:** write it down (see §Deltas #5).

**B. Don't conflate "which GitHub directory this lives in" with "where the ground truth actually is."** StableHLO's own July 2026 RFC (`rfcs/20260720-repo-sot-migration.md`, approved 2026-07-21 — three weeks old at time of writing) is a live, current example of a spec project discovering that its GitHub tree was *not* actually its source of truth: changes were really landing in Google's internal monorepo first and being squash-exported to GitHub weekly, degrading version-history transparency. They are now moving canonical authorship into the internal monorepo and syncing out via Copybara. **Lesson for OAAS:** deciding "repo-shaped so it *can* fission" answers a directory-layout question, not a ground-truth question — if OAAS ever has stewarding orgs/companies contributing through internal tooling, the SoT question needs its own explicit answer, independent of the public tree.

**C. Don't apply "one-entry-per-file" registry design uniformly without checking whether the closest precedent actually uses it.** ONNX's *conformance corpus* is genuinely one-file-per-operator (201 files). But ONNX's actual **operator registry** (the thing that would map most directly to OAAS's `registry/`) is the opposite: operators are registered as *code*, batched by category (`onnx/defs/math/defs.cc`, `onnx/defs/nn/defs.cc`, …), with superseded versions appended to a sibling `old.cc` rather than filed one-per-operator. `opencontainers/distribution-spec/extensions/` is moving toward one-file-per-extension but currently has only two files — too small a sample to call validated. Treat "one-entry-per-file" as strongly validated for **corpora**, only weakly validated for **registries proper** (see §Verdict).

### Specific deltas recommended against the proposed tree

1. **Add `spec/versioning.md`** (mirroring `onnx/docs/Versioning.md` + `stablehlo/docs/compatibility.md`) naming each independently-versioned axis (`core`, `execution`, `interchange`, `visual`, `grammar`) and any durable compatibility guarantee per axis. Currently absent.
2. **Don't assume uniform conformance machinery.** Structure `conformance/` so each spec file's subtree can differ in kind — schema-validation-only for static/interchange-like constructs (image-spec precedent), a full executable harness for protocol/behavioral constructs like `execution.md` or `interop/` (distribution-spec precedent). Document this explicitly rather than letting `matrix/` imply one shape fits all.
3. **Prefer corpus *generators* over static fixtures** in `conformance/corpus/`, following ONNX's `backend/test/case/node/{op}.py` — each file *produces* its own expected output rather than shipping data that can silently drift from what golden-render expects. **ASSUMPTION:** OAAS's stated tree ("corpus/ one-construct-per-file") doesn't specify whether entries are static fixtures or generators — this delta assumes generators are preferable and should be an explicit decision, not a default.
4. **Decide, per top-level dir, whether grammar and its reference validator are colocated or split**, and document the rule. Precedent is inconsistent but never fully separated in practice: ONNX keeps `.proto` grammar files inside the `onnx/` implementation package (not a bare grammar-only dir); `image-spec/schema/` bundles JSON Schema files with a Go validator *and* its unit tests in the same directory. OAAS currently splits `grammar/` from `tools/` — not wrong, but undocumented as a deliberate choice.
5. **Write an ownership/fission-trigger doc** (e.g. `docs/governance.md` or root `ARCHITECTURE.md`) naming, per top-level dir, who owns it and what condition would trigger fission into its own repo — modeled on WebAssembly's stated design/spec split and ONNX's `community/repo_guidelines.md` + `sigs.md`.
6. **Design `registry/` to work as an aggregator, not just a store of ground truth**, following `WebAssembly/testsuite`'s auto-synced-mirror pattern — relevant if/when `profiles/domain/{ml,crypto,agent}` fission into independent repos, so `registry/` can keep indexing them without owning their content.
7. **`improvable/` (agent skills with evals) is the weakest-precedented part of the proposed tree in this sample.** ONNX recently (2026) added `.agents/skills/{name}/SKILL.md` — one directory per skill with a manifest — a partial validation of "skills as directories." But the one skill inspected (`add-function-body`) has **no colocated eval harness file**, so "skills + evals colocated" is not validated by this evidence. **ASSUMPTION:** none of the five spec/interop projects surveyed here demonstrably colocate evals with skill/agent definitions; this part of OAAS's design may be closer to eval-tooling conventions (e.g. promptfoo-style) than to spec-repo prior art, and would benefit from a separate, narrower research pass if it matters.

---

## Per-Project Findings

### 1. onnx/onnx

**Repo:** https://github.com/onnx/onnx · **Accessed:** 2026-08-12 · **Branch:** `main` (`VERSION_NUMBER` = 1.23.0-dev)

**Observed tree (relevant subset):**
```
onnx/
├── AGENTS.md, CLAUDE.md            # agent-facing instructions at repo root
├── CODEOWNERS, CONTRIBUTING.md, RELEASE-MANAGEMENT.md, ROADMAP.md
├── .agents/skills/                 # NEW (2026): one dir per skill
│   ├── add-function-body/SKILL.md
│   ├── add-op/SKILL.md
│   ├── add-shape-inference/SKILL.md
│   └── onnxtxt/SKILL.md
├── community/                      # governance in prose, not manifests
│   ├── sigs.md, working-groups.md, repo_guidelines.md, sc-election-guidelines.md
├── docs/
│   ├── IR.md, Versioning.md, ShapeInference.md, ONNXTypes.md, ...  # hand-authored spec prose
│   ├── Operators.md, Operators-ml.md      # GENERATED (gen_doc.py) — "do not modify directly"
│   ├── Changelog.md, Changelog-ml.md      # GENERATED, full historical op-version log
│   └── docsgen/, proposals/, images/
├── onnx/                           # the python package AND the canonical grammar
│   ├── onnx.proto, onnx-ml.proto, onnx-operators.proto, onnx-data.proto  # grammar lives HERE, not in a bare grammar/ dir
│   ├── defs/
│   │   ├── schema.cc, schema.h, function.cc, parser.cc, printer.cc   # registry framework (code)
│   │   ├── math/{defs.cc, old.cc}, nn/{defs.cc, old.cc}, controlflow/, image/, text/, quantization/, training/, ...
│   │   │        # operators are registered as CODE, batched by domain category — NOT one file per operator.
│   │   │        # old.cc holds every superseded schema version, append-only, per category.
│   ├── reference/                  # Python reference evaluator (in-tree, not a separate repo)
│   ├── backend/test/
│   │   ├── case/node/{op}.py       # ONE FILE PER OPERATOR (201 files) — each a generator of example/conformance data
│   │   ├── case/node/ai_onnx_ml/{op}.py  # domain-specific ops get their own subdir, same one-per-file rule
│   │   └── data/{light,pytorch-converted,pytorch-operator,real,simple}/  # derived/static fixture sets
├── tests/{cpp,python,cmake}/       # unit tests (separate from backend/test conformance corpus)
```

**Versioning (from `docs/Versioning.md`):** Three explicitly named, independently-evolving version types: **IR version** (monotonic int, for the graph/operator abstract format), **operator/opset version** (monotonic int, per `(domain, opset_version)` pair — `ModelProto.opset_import`), and **model version** (recommended SemVer, non-normative). The doc states precisely which classes of change bump which number, and gives a worked example table showing operator `since_version` evolution across four opsets. Release cadence (`RELEASE-MANAGEMENT.md`) is quarterly branch cuts, **no LTS branches** — only the latest minor receives fixes; backports are case-by-case.

**Conformance-corpus generation pattern:** `onnx/backend/test/case/node/abs.py`, `add.py`, `argmax.py`, etc. — 201 files total, one per operator (plus a nested `ai_onnx_ml/` subdir for ML-domain ops) — each a Python function that programmatically builds a minimal model + input/output example and registers it as a conformance case. This is the closest real-world analogue to OAAS's `conformance/corpus/` "one-construct-per-file" design found in this survey.

---

### 2. openxla/stablehlo

**Repo:** https://github.com/openxla/stablehlo · **Accessed:** 2026-08-12 · **Branch:** `main`

**Observed tree (relevant subset):**
```
stablehlo/
├── docs/
│   ├── spec.md                     # THE normative spec — single file, not split per construct
│   ├── compatibility.md            # compat GUARANTEES doc (see below), separate from spec.md
│   ├── bytecode.md                 # serialization/wire-format spec, separate from opset semantics
│   ├── vhlo.md, vhlo_checklist.md  # versioned dialect + process checklist for changing it
│   ├── spec_checklist.md, reference_checklist.md   # process checklists to keep spec/reference/VHLO in sync
│   ├── governance.md               # explicit near-term vs. future governance statement
│   ├── interpreter_status.md, status.md, roadmap.md, dynamism.md, type_inference.md, quantization.md
├── rfcs/                           # 29 dated RFC files, proposal-before-implementation process
│   └── 20260720-repo-sot-migration.md   # see "Notable recent finding" below
├── stablehlo/                      # the implementation tree
│   ├── dialect/                    # MLIR dialect (includes VHLO — versioned IR as CODE)
│   ├── reference/                  # reference INTERPRETER — lives inside impl tree, not a top-level dir
│   ├── conversions/, transforms/, integrations/, tools/, api/
│   ├── tests/                      # .mlir test files, colocated with dialect code (uses LLVM `lit`)
│   └── testdata/
├── examples/{c++,python}/
```

**Compatibility guarantee (from `docs/compatibility.md`):** **5 years of backward compatibility** and **2 years of forward compatibility**, defined in terms of *time between commits*, not just version numbers — "artifacts serialized by an old version ... have the same semantics when deserialized by a new version ... if these versions are built from commits which are less than 5 years apart." This guarantee is backed by an RFC (`rfcs/20230623-compatibility.md`) and *enforced mechanically* by the VHLO dialect: an add-only, versioned MLIR dialect that snapshots every op/type/attribute at every version boundary, used to downgrade/upgrade portable artifacts. This is a compatibility mechanism implemented as **code**, not just as documentation.

**Notable recent finding — ground truth is not the same question as directory layout:** `rfcs/20260720-repo-sot-migration.md` (Status: **Approved**, approved 2026-07-21 — three weeks before this research date) documents StableHLO's own team concluding that GitHub was *not actually* their source of truth: changes landed first in Google's internal monorepo ("Google3") and were squash-exported to GitHub weekly via the "Integrate LLVM at ..." PRs, degrading version-history transparency and creating maintenance overhead. The RFC proposes moving canonical authorship into Google3, syncing out to GitHub via Copybara tooling, matching how sibling OpenXLA projects (`openxla/xla`, `openxla/shardy`) already work. **Relevance to OAAS:** a public monorepo's directory tree does not by itself establish where ground truth lives; if OAAS ever has corporate/institutional stewards contributing through internal tooling, that needs an explicit, separate answer from the tree-shape decision.

---

### 3. opencontainers/image-spec and opencontainers/distribution-spec

**Repos:** https://github.com/opencontainers/image-spec · https://github.com/opencontainers/distribution-spec · **Accessed:** 2026-08-12 · **Branch:** `main` (both)

**Org-level pattern:** `opencontainers` runs image-spec, distribution-spec, and runtime-spec as **three separate top-level repos**, plus a fourth, `oci-conformance`, for the **certification program** (business/legal layer — vendor certification, branding, legal terms), which sits *on top of* distribution-spec's in-repo technical conformance harness rather than replacing it. Org repo list (partial, filtered to spec-relevant): `image-spec`, `distribution-spec`, `runtime-spec`, `oci-conformance`, `image-tools`, `runtime-tools`, plus several `wg-*` working-group repos (`wg-auth`, `wg-freebsd-runtime`, `wg-image-compatibility`, `wg-reference-types`, `wg-template`) — i.e. even *working groups* are repo-shaped.

**image-spec tree (flat — spec is a static file-format spec):**
```
image-spec/
├── spec.md                         # index/overview linking chapters
├── annotations.md, config.md, descriptor.md, image-index.md, image-layout.md,
│   manifest.md, media-types.md, conversion.md, considerations.md, artifacts-guidance.md
│                                    # one file per CHAPTER, all at repo root — no spec/ subdir wrapper
├── schema/                         # grammar (JSON Schema) + reference validator, colocated
│   ├── config-schema.json, image-index-schema.json, image-layout-schema.json, image-manifest-schema.json
│   ├── defs.json, defs-descriptor.json, content-descriptor.json
│   ├── schema.go, validator.go, doc.go            # Go reference validator lives IN schema/
│   └── *_test.go                                  # unit tests for the validator, also in schema/
├── identity/, specs-go/, img/
├── GOVERNANCE.md, RELEASES.md, EMERITUS.md, MAINTAINERS
# NOTE: no conformance/ directory exists in this repo (confirmed via 404 on GET contents/conformance).
#       Static-format conformance reduces to schema validation, provided by schema/ itself.
```

**distribution-spec tree (flat, but protocol-shaped — needs behavioral conformance):**
```
distribution-spec/
├── spec.md, content-negotiation.md
├── extensions/
│   ├── README.md
│   └── _oci.md                     # nascent one-file-per-extension registry; only 1 entry so far — too small to call validated
├── conformance/                    # FULL executable Go conformance test program
│   ├── api.go, config.go, run.go, state.go, junit.go, testdata.go, legacy_test.go, main.go, ...
│   # black-box tests HTTP registry endpoints; configured via env vars or oci-conformance.yaml;
│   # emits JUnit-format results; explicitly versioned against OCI_VERSION ("1.1", "stable", "dev")
├── GOVERNANCE.md, RELEASES.md, FAQ.md, action.yml   # ships as a reusable GitHub Action too
```

**Why the two repos differ:** image-spec specifies a **static artifact format** — conformance is "does this JSON validate against this schema," fully covered by `schema/`. distribution-spec specifies an **HTTP protocol/behavior** — conformance requires actually exercising a running registry implementation, hence the full Go program. Same org, same governance model (`RELEASES.md` is near-identical text copy-pasted across both repos: pre-1.0 monthly cadence, 3 release-candidates minimum for majors, restart the RC count if a breaking change lands mid-cycle), but **conformance-tooling shape tracks the kind of spec, not the org's house style.**

**Release/versioning governance:** Both `RELEASES.md` files explicitly tie release-category rules to the **OCI charter**, which defines three legally distinct project categories — *specifications*, *applications*, and *conformance-testing tools* — each with different backward-compatibility and patent-grant (§8.d/e) obligations. This is an explicit, written-down ownership/category taxonomy, not something left implicit in directory names.

---

### 4. w3c/json-ld-syntax and w3c/json-ld-api

**Repos:** https://github.com/w3c/json-ld-syntax · https://github.com/w3c/json-ld-api · **Accessed:** 2026-08-12 · **Branch:** `main` (both; tree confirmed via GitHub API for both repos, not just search)

**json-ld-syntax tree:**
```
json-ld-syntax/
├── index.html            # THE spec source — W3C's ReSpec toolchain authors specs as annotated HTML, not Markdown
├── common/                # shared W3C boilerplate/build scripts (submodule-like shared infra)
├── yaml/                  # structured vocabulary/context definitions referenced by the spec text
├── examples/, errata/, publication-snapshots/
├── Rakefile, Gemfile, ECHIDNA, .pr-preview.json   # W3C publication tooling
# NOTE: no test suite anywhere in this repo.
```

**json-ld-api tree (sibling repo, confirmed via GitHub API):**
```
json-ld-api/
├── index.html             # the API/algorithms spec (separate normative doc from syntax)
├── tests/                 # THE JSON-LD CONFORMANCE TEST SUITE lives here, not in json-ld-syntax
│   ├── manifest.jsonld, manifest.html               # top-level test manifest
│   ├── compact-manifest.jsonld / compact/            # one manifest + one directory per test CATEGORY
│   ├── expand-manifest.jsonld / expand/
│   ├── flatten-manifest.jsonld / flatten/
│   ├── fromRdf-manifest.jsonld / fromRdf/
│   ├── toRdf-manifest.jsonld / toRdf/
│   ├── html-manifest.jsonld / html/
│   ├── remote-doc-manifest.jsonld / remote-doc/
│   └── vocab.jsonld, vocab.ttl, context.jsonld       # shared vocab/context fixtures
├── reports/, errata/, examples/, yaml/
```

**Pattern:** the spec-text repo (`json-ld-syntax`) and the conformance-suite repo (`json-ld-api`) are **two separate GitHub repos**, split along which sub-spec owns the ground truth (syntax vs. processing-algorithm), not generically "spec vs. tests." Each test category (`compact`, `expand`, `flatten`, …) gets its own manifest file + its own directory of small numbered test-case files — effectively a one-construct-per-file corpus indexed by a manifest, structurally close to what OAAS's `conformance/corpus/` + `conformance/matrix/` combination is aiming for. **ASSUMPTION:** the internal per-test-case file structure inside `tests/compact/`, `tests/expand/`, etc. was not individually enumerated (only the directory-level listing was fetched); the "one file per test case" characterization for the innermost level follows from the well-documented W3C test-manifest convention (`manifest.jsonld` + numbered `.jsonld`/`.json` pairs) but was not independently verified file-by-file in this pass.

---

### 5. WebAssembly/spec and the WebAssembly org

**Repo:** https://github.com/WebAssembly/spec · **Accessed:** 2026-08-12 · **Branch:** `main`

**Observed tree:**
```
spec/
├── document/              # spec PROSE, itself split by which layer/host-binding it governs
│   ├── core/, js-api/, web-api/, legacy/, versions/, metadata/, util/
├── interpreter/            # OCaml REFERENCE IMPLEMENTATION (full validator/executor), in-tree
│   ├── binary/, exec/, syntax/, text/, valid/, runtime/, host/, jslib/, main/, script/, unittest/
├── test/                   # OFFICIAL TEST SUITE — committed directly, confirmed NOT a git submodule
│   ├── core/{*.wast, bulk-memory/, ...}    # hundreds of raw .wast files
│   ├── js-api/, legacy/, custom/, harness/, meta/
├── spectec/                 # newer formal-spec-as-code tool (generates/checks prose spec)
├── proposals/                # tracks proposal status within this repo
├── papers/
```
(`.gitmodules` contains exactly one entry — a KaTeX doc-rendering dependency — confirming `test/core` is directly committed, not pulled in from elsewhere.)

**Explicit, stated repo-fission rationale (from `README.md`):** *"Discussions about new features, significant semantic changes, or any specification change likely to generate substantial discussion should take place in [the WebAssembly design repository](https://github.com/WebAssembly/design) first, so that this spec repository can remain focused."* This is a written, explicit statement of *why* pre-consensus discussion is kept out of the spec monorepo — not left implicit in directory shape.

**Org-level multi-repo pattern (from `GET /orgs/WebAssembly/repos`):** ~25+ **separate, independent repos, one per proposal**, live and active while the feature is unstable: `simd`, `threads`, `gc`, `tail-call`, `exception-handling`, `memory64`, `relaxed-simd`, `stringref`, `component-model`, `multi-memory`, `function-references`, `stack-switching`, `interface-types`, `extended-const`, `branch-hinting`, `call-tags`, `memory-control`, `module-linking`, `sign-extension-ops`, `mutable-global`, `bulk-memory-operations`, `nontrapping-float-to-int-conversions`, `js-promise-integration`, `js-types`, `feature-detection`, `esm-integration`, `conditional-sections`, `flexible-vectors`, `debugging`, `instrument-tracing`, `root-scanning`, and more — each repo-shaped, and merged **into** `WebAssembly/spec` only once the proposal reaches a stable phase. `proposals` is a separate, lightweight tracking-index repo (not ground truth for any proposal's content).

**Aggregator/mirror pattern:** `WebAssembly/testsuite` (separate repo) is described in its own README as *"a mirror of the WebAssembly core testsuite which is maintained [in WebAssembly/spec], as well as the tests from the various proposals repositories... updated weekly on Wednesday via automated pull requests... To add new tests or report problems, please file issues and PRs within the spec or individual proposal repositories rather than within this mirror repository."* Ground truth for tests stays distributed across `spec` + ~25 proposal repos; a single derived, read-only, auto-synced aggregate is published for consumers who don't want to track 26 repos individually.

---

## Final Verdict on OAAS's Monorepo-with-Fission-Lines Assumption

**The evidence broadly supports the strategy, with three important refinements.**

1. **"Monorepo per artifact-type," not "monorepo for everything," is the actual dominant pattern — and OAAS's `spec/` directory currently blurs this.** ONNX (one artifact: the ONNX IR+opset format) and StableHLO (one artifact: an MLIR dialect) are each a single monorepo covering *one thing's* full stack — spec, implementation, tests, docs, process — end to end. But OCI does **not** run one monorepo for "container specs": it runs three (`image-spec`, `distribution-spec`, `runtime-spec`) plus a certification repo, precisely because image-format and registry-protocol are different *kinds* of things with different conformance needs and different versioning cadences. OAAS's `spec/{core, execution, interchange, visual}` currently nests four files that may turn out to be exactly this kind of case — candidate separate-monorepos-in-waiting, the way image-spec and distribution-spec are, not permanently sibling files under one `spec/`. Nesting them together for v0 is reasonable, but the tree should name, in advance, which of the four is likeliest to need its own conformance shape and versioning cadence first (see Deltas #1, #2, #5) — the OCI evidence says the signal to watch is *"does this spec describe a static format or a runtime behavior/protocol,"* not just "different subject matter."

2. **"Repo-shaped so it CAN fission" is validated as a design property, but the observed real-world trigger for actually fissioning runs in the opposite direction from OAAS's plan.** WebAssembly proposals live in **independent repos while unstable** and are folded **into** the monorepo (`WebAssembly/spec`) only once they reach a stability milestone — i.e., the empirically observed fission direction is *outward-then-inward* (start independent, merge in once mature), not *inward-then-outward* (start merged into one monorepo, split out later), which is what OAAS's stated design principle implies. Both directions are plausible, but the WebAssembly evidence suggests it may be cheaper to prototype new `profiles/domain/{ml,crypto,agent}` extensions as separate scratch/experimental repos first, merging only stabilized ones into the OAAS monorepo, rather than defaulting everything into the monorepo now and fissioning out later. **ASSUMPTION:** this directional argument generalizes from a single large-sample precedent (WebAssembly's ~25 proposal repos); ONNX and OCI don't provide a clean confirming or disconfirming data point either way, since neither has gone through a comparable outward-then-inward or inward-then-outward cycle in the evidence gathered here. This is worth an explicit decision by OAAS, not an inherited assumption.

3. **"Ground truth" and "directory layout" are separate questions, and the tree alone cannot answer the first one.** StableHLO's own July 2026 RFC is direct, current evidence that a project can have a well-organized public monorepo tree and *still* be wrong about where its actual source of truth lives (Google3 vs. GitHub). OAAS's design principle "subtrees cut along ground-truth ownership... boundaries" is the right instinct, but ownership needs its own document (per Anti-pattern A / Delta #5) — the tree shape documents *what exists*, not *who is authoritative for it* or *which system changes land in first*.

4. **Conformance/registry granularity should not be assumed uniform.** "One-entry-per-file" is strongly validated for **conformance corpora** (ONNX: 201 files, one per operator; JSON-LD: one manifest + directory per test category) but only weakly validated for **registries proper** — ONNX's actual operator registry is category-batched code (`defs.cc`/`old.cc` per domain), not one file per operator, and OCI's `extensions/` file-per-extension pattern has only two entries so far. If OAAS's `registry/` design depends on the one-entry-per-file assumption holding at scale, it's worth a narrower follow-up research pass against at least one more registry-shaped precedent (e.g., a package-manager or plugin-registry index) — this survey's evidence for that specific sub-claim is thinner than for the corpus claim.

---

## Sources

1. ONNX — repo root, `docs/`, `onnx/`, `onnx/defs/`, `onnx/backend/test/`, `community/`, `.agents/skills/`: https://github.com/onnx/onnx (accessed 2026-08-12)
2. ONNX Versioning doc: https://github.com/onnx/onnx/blob/main/docs/Versioning.md (accessed 2026-08-12)
3. ONNX Changelog (generated): https://github.com/onnx/onnx/blob/main/docs/Changelog.md (accessed 2026-08-12)
4. ONNX Release Management: https://github.com/onnx/onnx/blob/main/RELEASE-MANAGEMENT.md (accessed 2026-08-12)
5. StableHLO — repo root, `docs/`, `stablehlo/`, `rfcs/`, `examples/`: https://github.com/openxla/stablehlo (accessed 2026-08-12)
6. StableHLO Compatibility doc: https://github.com/openxla/stablehlo/blob/main/docs/compatibility.md (accessed 2026-08-12)
7. StableHLO Governance doc: https://github.com/openxla/stablehlo/blob/main/docs/governance.md (accessed 2026-08-12)
8. StableHLO VHLO doc: https://github.com/openxla/stablehlo/blob/main/docs/vhlo.md (accessed 2026-08-12)
9. StableHLO Repo SoT Migration RFC (Approved 2026-07-21): https://github.com/openxla/stablehlo/blob/main/rfcs/20260720-repo-sot-migration.md (accessed 2026-08-12)
10. OCI image-spec — repo root, `schema/`: https://github.com/opencontainers/image-spec (accessed 2026-08-12)
11. OCI image-spec Releases doc: https://github.com/opencontainers/image-spec/blob/main/RELEASES.md (accessed 2026-08-12)
12. OCI distribution-spec — repo root, `conformance/`, `extensions/`: https://github.com/opencontainers/distribution-spec (accessed 2026-08-12)
13. OCI distribution-spec conformance README: https://github.com/opencontainers/distribution-spec/blob/main/conformance/README.md (accessed 2026-08-12)
14. OCI distribution-spec Releases doc: https://github.com/opencontainers/distribution-spec/blob/main/RELEASES.md (accessed 2026-08-12)
15. OCI Conformance certification repo: https://github.com/opencontainers/oci-conformance (accessed 2026-08-12, via fetch summary)
16. opencontainers org repo listing: https://api.github.com/orgs/opencontainers/repos (accessed 2026-08-12)
17. W3C json-ld-syntax — repo root: https://github.com/w3c/json-ld-syntax (accessed 2026-08-12)
18. W3C json-ld-api — repo root, `tests/`: https://github.com/w3c/json-ld-api (accessed 2026-08-12)
19. WebAssembly/spec — repo root, `document/`, `interpreter/`, `test/`: https://github.com/WebAssembly/spec (accessed 2026-08-12)
20. WebAssembly/testsuite README: https://github.com/WebAssembly/testsuite/blob/main/README.md (accessed 2026-08-12)
21. WebAssembly org repo listing: https://api.github.com/orgs/WebAssembly/repos (accessed 2026-08-12)

---

**Epistemological Note:** This research is a snapshot of five (seven, counting the OCI pair and the JSON-LD pair separately) live, actively-maintained repositories as observed on 2026-08-12. All tree sketches and doc excerpts above were fetched directly via the GitHub REST API or raw content endpoints in this session — no claim in the "Per-Project Findings" section is from training-data memory. Claims marked `ASSUMPTION:` were not independently verified against primary evidence in this pass and should be treated as lower-confidence inferences, not established fact. Repository structures evolve; re-verify before treating any specific file/directory claim as durable beyond a few months, especially for StableHLO given its SoT migration is actively in progress.
