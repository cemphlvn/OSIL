# U5 — egg vs egglog: Target Engine for the OAAS Equivalence Projection

**Date:** 2026-08-12
**Researcher:** research-agent
**Question:** Which engine — `egg` (Rust e-graph library) or `egglog` (fixpoint reasoning unifying Datalog + equality saturation) — should the OAAS equivalence projection (`spec/interop/egraph.md`) target for its tested preservation contract (G14, the search-ecosystem analog of G3)?
**Feeds:** `spec/interop/egraph.md` (currently a stub naming this exact open question), `profiles/ecosystem/egg/PROFILE.md` + `VERSIONS` (both explicitly "pending research U5"), gate **G14** (`README.md`: "e-graph contract: U5 decides egg-vs-egglog, then the equivalence projection gets a tested preservation contract").

## Research method (wave decomposition)

Default line: "compare GitHub stars/commit graphs for egg vs egglog." Simulated finding: egg has more stars (older, POPL 2021 precedent), egglog has more recent commits (newer, PLDI 2023). Gaps relative to OAAS's actual decision — a Python-toolchain, zero-manual-setup, guard-carrying, mechanically-verified round-trip contract wired into `just test` — that a stars/commits comparison alone would miss, mapped 1:1 to the five sub-questions the orchestrator supplied:

1. Liveness *of the maintainers' own stated intent*, not just commit counts (do they say egg is superseded, or are these parallel tracks?).
2. Whether a Python binding is **installable today**, on **this machine**, with **zero manual setup** — a packaging/runtime fact, not inferable from repo popularity.
3. How each engine's conditional-rewrite mechanism maps onto OAAS's `guards {}` block as *data* vs *code* — a semantic-fit question, not a liveness question.
4. Round-trip/extraction fidelity — an engineering-shape question (is there a canonical program-text format at all?).
5. Format/version pin stability — a governance question (what does `VERSIONS` actually pin, and does that pin mean what ONNX's `VERSIONS` file means?).

Each gap became one research line below, evidence gathered via direct GitHub/crates.io/PyPI API calls (primary, machine-readable, not summarized-by-a-fetch-tool) plus one **executed** smoke test reproducing `conformance/corpus/003-equivalence-distributivity.oaas` end-to-end on this machine. Synthesis: **convergent** — all five lines point the same direction (egglog as primary target), and one line (round-trip fidelity) is not inference at all but a mechanically verified result produced in this session.

---

## TL;DR

**Recommendation: egglog is the target engine for the tested preservation contract (G14). egg is retained as a foreign-witness/citation reference only, not as an execution target.**

This is not a close call once sub-question 2 (Python installability) and sub-question 3 (guards-as-data) are weighed: there is currently **no maintained Python binding for egg** (`snake-egg`'s last release is 3.5 years stale and ships no wheel for any CPython newer than 3.11), and egg's conditional-rewrite mechanism is **compiled Rust predicate code**, not data — an OAAS→egg adapter would have to generate and compile a `.check()` closure per guard, which is heavier than the "adapter translates declared equivalences to native rewrite rules" framing in `spec/interop/egraph.md` implies. egglog resolves both: `egglog` (PyPI) is installable today via `uv run --with egglog` on this exact macOS arm64 machine (verified, see §4), and its `:when (fact...)` guard mechanism is an ordinary Datalog fact query — a direct, mechanical translation target for `guards { numeric_semantics = exact }`-shaped blocks (verified live, see §4). Sub-questions 1, 4, and 5 corroborate rather than override this: egglog is markedly more active by every commit-cadence metric gathered, its `.egg` program text is a genuine engine-level interchange format (egg has none — it is an embedded-DSL library, not a standalone tool with fixed program syntax), and while egglog's own crate is on a faster-churning SemVer track (already v2.0.0) than egg's (still v0.11.0), the actually-relevant pin for a Python harness is `egglog` (PyPI) `13.2.0`, which — a genuinely surprising finding — is **decoupled from and more precisely reproducible than** the crates.io version number, because it vendors a pinned git commit of the Rust core rather than depending on the published crate (see §5).

**Concrete pin:** `egglog` (PyPI) `== 13.2.0`, binding path `uv run --with egglog python3 tools/egraph_roundtrip.py` (same idiom as the existing `just roundtrip` → `uv run --with onnx ...`).

**Confidence:** HIGH on sub-questions 2, 3, 4 (primary-sourced + one executed round trip). MEDIUM-HIGH on sub-question 1 (quantitative liveness delta is unambiguous; no direct maintainer quote declaring "maintenance mode" was found — see ASSUMPTION flags). MEDIUM on sub-question 5 (format-stability comparison is sound but neither project publishes an IR-version-style stability guarantee comparable to ONNX's).

---

## 1. Maintenance/liveness 2026

**Method:** direct GitHub REST API queries against `egraphs-good/egg` and `egraphs-good/egglog`, plus crates.io API, plus a full listing of the `egraphs-good` org's 18 repositories — all fetched live on 2026-08-12, not summarized from a search engine.

| Metric (as of 2026-08-12) | egg | egglog |
|---|---|---|
| Created | 2019-04-25 | 2022-02-07 |
| Stars / forks | 1808 / 199 | 812 / 112 |
| Open issues | 26 | 128 |
| Last push (`pushed_at`) | 2026-07-19 | 2026-08-11 (1 day before this research) |
| Commits, trailing 90 days | **1** | **≥100** (GitHub API page cap hit — true count higher) |
| Commits, trailing 180 days | **7** | not separately queried (already capped at 90d) |
| Contributors (approx., via paginated Link header) | ~45 | ~52 |
| crates.io latest / published | 0.11.0 / 2025-12-04 | 2.0.0 / 2026-02-12 |
| Foundational paper | Willsey, Nandi, Wang, Flatt, Tatlock, Panchekha, "egg: Fast and Extensible Equality Saturation," POPL 2021, [doi:10.1145/3434304](https://doi.org/10.1145/3434304) | Zhang, Wang, Flatt, Cao, Zucker, Rosenthal, Tatlock, Willsey, "Better Together: Unifying Datalog and Equality Saturation," PLDI 2023, [doi:10.1145/3591239](https://doi.org/10.1145/3591239) |

Higher open-issue count alongside fewer stars is consistent with egglog being the repo people are actively filing issues against (a live-development signal), not a negative signal on its own.

**Direct maintainer statement (primary source, not inference):** egg's own `README.md` (fetched 2026-08-12) states, verbatim:

> "Also check out the [egglog](https://github.com/egraphs-good/egglog) system that provides an alternative approach to equality saturation based on Datalog. It features a language-based design, incremental execution, and composable analyses."

egglog's own `README.md` self-titles as **"egglog: The Next-Generation Equality Saturation Engine."** Both statements are from the same org (`egraphs-good`) and the same core author set (Willsey and Tatlock appear on both papers' author lists), so this is the maintainers speaking about their own two projects, not a third party's characterization.

**Org-wide satellite-repo pattern** (all 18 `egraphs-good` repos, fetched 2026-08-12) corroborates: `egglog-python`, `egglog-experimental`, `egglog-language-server`, `eggcc` ("An experimental optimizing compiler for Bril using egglog"), `extraction-gym`, `egraph-serialize`, `egglog-demo`, `egglog-tutorial` were all pushed within days-to-weeks of this research date. By contrast, egg's own satellite repos are stale: `snake-egg` (Python bindings) last pushed 2023-01-17, `egg-web-demo` last pushed 2020-10-27, `egg-tutorial-pldi-2022` last pushed 2022-06-13. The org is visibly investing new tooling into the egglog ecosystem and not into egg's.

**ASSUMPTION:** No direct quote from Willsey or Tatlock explicitly declaring egg "in maintenance mode" was found in this pass (I searched specifically for this; results returned only the README pointer above, no EGRAPHS-workshop-talk transcript or Zulip quote). The "maintenance mode, not abandoned" characterization in this document's TL;DR is an **inference** from the commit-cadence delta (1 commit/90d vs ≥100/90d) and the README pointer, not a verbatim maintainer statement. This is falsifiable: it would be overturned by evidence of a sustained increase in egg's own commit rate, or a maintainer statement explicitly denying successor status. I did not have Zulip access in this session (`egraphs.zulipchat.com` requires an account) and could not check that channel directly — flag as an evidentiary gap, not a resolved claim.

---

## 2. Python bindings — installable TODAY, zero manual setup

**Method:** PyPI JSON API queries + one **executed** install/import via `uv run --with <pkg>` on this machine (macOS arm64, Darwin 25.5.0, `uv 0.9.10`) — this is mechanical evidence, not a documentation claim.

**egglog (PyPI package `egglog`):**
- Latest version **13.2.0**, uploaded 2026-06-03, `requires-python >= 3.11`.
- Ships prebuilt wheels for cp311/cp312/cp313/cp313t/cp314/cp314t and pp311, including `egglog-13.2.0-cp311-cp311-macosx_10_12_x86_64.macosx_11_0_arm64.macosx_10_12_universal2.whl` — a macOS **arm64** wheel, confirmed by filename directly from the PyPI JSON API.
- **Verified installable and importable, this session, on this exact machine:**
  ```
  $ uv run --with egglog python3 -c "
  import egglog
  from egglog import EGraph, i64, function, rewrite, ruleset, birewrite
  print('core symbols imported OK')
  "
  Installed 34 packages in 154ms
  core symbols imported OK
  ```
- `egglog-python`'s `pyproject.toml` (fetched 2026-08-12) declares hard dependencies `typing-extensions, black, graphviz, anywidget, cloudpickle>=3, opentelemetry-api` — i.e. `black` (used for pretty-printing extracted expressions) and `anywidget` (Jupyter-widget visualization, which transitively pulls `widgetsnbextension`/`jedi`) are **base**, not optional, dependencies. This is real but minor dependency weight for a headless CI harness — noted as a trade-off, not a blocker; the install above completed in 154ms after download and ran headlessly without issue.

**snake-egg (PyPI package `snake-egg`, egg's own Python bindings):**
- Single release, version **0.1.0**, uploaded 2023-01-09 — no subsequent release in ~3.5 years.
- GitHub repo `egraphs-good/snake-egg`: `pushed_at` **2023-01-17**, 50 stars, 2 open issues, description "Python bindings for egg."
- Wheel filenames on PyPI cover cp37/cp38/cp39/cp310/cp311 and pypy37/38/39 — **no wheel targets cp312, cp313, or cp314**, i.e. it was never rebuilt against any Python release from the last ~3 years, and never rebuilt against any `egg` crate release newer than whatever was current in Jan 2023 (egg was at roughly v0.9.x then; egg is now at 0.11.0). This is a directly falsifiable fact from the PyPI file listing, not an inference.
- Not independently smoke-tested for install, because there is no currently-supported CPython target to test it against on this machine, and the staleness evidence alone already disqualifies it from a "zero manual setup, wired into `just test`" bar.

**No other current PyPI package binds egg for Python.** Checked candidate names `pyegg` (exists, but is an unrelated "Python Eggs" packaging tool, confirmed via its PyPI summary), `py-egg`, `egg-python`, `eggpy`, `egraphs`, `egg-rs` — all 404.

**Verdict: on this sub-question alone, egglog is the only viable choice.** There is no engineering path to "egg + Python + zero manual setup" today short of either reviving `snake-egg` upstream (not OAAS's call — foreign ground truth per `GOVERNANCE.md`) or writing and maintaining a new PyO3 binding in-repo (a maintenance burden `spec/interop/ecosystem-contract.md`'s sovereignty principle argues against: OAAS should not be in the business of re-implementing an upstream ecosystem's binding layer).

---

## 3. Conditional rewrites / guards — data vs. code

**Method:** primary source (docs.rs macro documentation, egg's `src/extract.rs`/`src/rewrite.rs` source, egglog's own test corpus, egglog-python's tutorial source files) — all fetched or read directly, 2026-08-12.

**egg:** the `rewrite!` macro's conditional form is

```rust
rewrite!("something_conditional";
         "(/ ?a ?b)" => "(* ?a (/ 1 ?b))"
         if is_not_zero("?b"))
```

which desugars to a `ConditionalApplier<C, A>` that calls `Condition::check(&self, egraph: &mut EGraph<L, N>, eclass: Id, subst: &Subst) -> bool` before applying. `Condition` is implemented by **any Rust closure matching that signature** — i.e. the guard is arbitrary compiled code with access to the live e-graph and analysis data. The only built-in *declarative* condition is `ConditionEqual` (checks that two patterns land in the same e-class) — there is no general "assert a named fact once, reference it from many rewrites" primitive at the language level; each guard is authored per-rewrite, in Rust, and compiled.

**egglog:** the `rewrite` command's conditional form, confirmed directly against egglog's own shipped test suite (`tests/integer_math.egg`, fetched 2026-08-12):

```lisp
(relation is-not-zero (Math))
(rule ((MathU a) (!= a (Const 0))) ((is-not-zero a)))

(rewrite (Div (Const a) (Const b)) (Const (/ a b)) :when ((!= 0 b)))
(rewrite (Div a a) (Const 1) :when ((is-not-zero a)))
(rewrite (Mul (Pow a b) (Pow a c)) (Pow a (Add b c)) :when ((is-not-zero b) (is-not-zero c)))
```

Guards here are ordinary Datalog **facts** over user-declared `relation`s — assertable once, queried by any number of rewrites via `:when (fact...)`. This is data, not code: a mechanical adapter can translate `guards { numeric_semantics = exact }` into `(relation ExactArithmetic ())` + one assertion, and append `:when ((ExactArithmetic))` to every generated rewrite carrying that guard, with no code generation or compilation step.

**Verified live** (this session, egglog-python API, mirroring `conformance/corpus/003-equivalence-distributivity.oaas`):

```python
exact_regime = relation("exact_regime")
egraph.register(exact_regime())  # assert the guard fact once

@egraph.register
def _distributivity(a: Num, b: Num, c: Num):
    yield birewrite((a * c) + (b * c)).to((a + b) * c, exact_regime())
```

Output: `PRE-SATURATION check correctly failed (guard not yet exploited): True` / `POST-SATURATION equivalence VERIFIED: lhs == (a+b)*c -> True` / `Extracted term (repr): (Num.var("a") + Num.var("b")) * Num.var("c")`.

**Verdict:** egglog's guard mechanism maps onto OAAS's `guards { key = value }` block essentially one-to-one, as data. egg's requires generating and compiling a Rust predicate per guard — feasible, but a materially heavier and less declarative adapter, and one that cuts against `spec/interop/egraph.md`'s framing ("the adapter translates them to native rewrite rules," implying a data transformation, not a code-generation-and-compile step).

---

## 4. Round-trip fidelity — text format and extraction

**Method:** primary source (egg's `RecExpr`/`Language` parsing model via docs.rs, egglog's CLI usage from its own README, `extraction-gym`/`egraph-serialize` READMEs) plus one **executed, mechanically verified round trip**.

**egg** has no single, fixed, engine-level program text. `RecExpr<L>` parses/prints via each embedding project's own `Language` definition (`define_language!` macro) — s-expression-*shaped* per node vocabulary (e.g. `"(+ 0 (* 1 10))".parse().unwrap()` in the crate's own doctest), but egg is a **Rust library/embedded DSL**: there is no standalone `.egg`-style file format at the engine level, because "the engine" is whatever Rust type the embedding project defines. An OAAS→egg adapter would therefore need to *own* a bespoke `Language` definition and its concrete syntax inside OAAS's own tooling — this is not a difference OAAS can outsource to upstream, unlike ONNX's `.proto`-defined wire format.

Extraction: `Extractor::new(&egraph, CostFunction)`. `CostFunction` is a Rust trait (`fn cost<C>(&mut self, enode: &L, costs: C) -> Self::Cost`); only `AstSize`/`AstDepth` ship built-in — anything OAAS-specific (e.g., a regime-aware cost) is again Rust code, not data.

**egglog**'s `.egg` program *is* the primary, singular interchange format — confirmed directly from its own README: `cargo run --release [-f fact-directory] ... <files.egg>` is the standard invocation shape, i.e. "load a program file, run it" is the actual contract, matching `spec/interop/egraph.md`'s stated shape ("OAAS-SIR -> e-graph -> equality saturation -> extraction -> OAAS-SIR") as a genuine text-through-an-engine-program pipeline rather than an embed-in-a-host-language one. Extraction is `(extract expr)` / `(extract expr n)` (single or multi-variant), with cost expressed **declaratively**: `:cost N` as a per-constructor annotation (confirmed in `tests/fibonacci-demand.egg`: `(Add Expr Expr :cost 5)`), or, for computed costs, `set_cost` (from `egglog-experimental`) — itself expressed as ordinary rule actions inside the same program, not external compiled code.

**Verified, this session (mechanical evidence, not inference):** the `003-equivalence-distributivity.oaas` fixture — `(a * c) + (b * c) <=> (a + b) * c`, `guards { numeric_semantics = exact }` — was built as a term, saturated under the guard fact, checked for equivalence (`egraph.check(...)`, which raises on failure), and extracted, returning exactly the expected canonical form. This satisfies `spec/conformance.md`'s own evidentiary bar for a "preservation score" field: *"A field may count as verified ONLY on mechanical evidence; inference or inspection-by-eye never counts."* Full script: `/private/tmp/claude-501/-Users-cem-oaas/9f19ae22-cb9b-4e84-8239-423bbdc3a75d/scratchpad/u5_smoketest.py` (scratchpad — not part of the repo; a production version belongs at `tools/egraph_roundtrip.py` if G14 is executed).

**Known extraction gotcha (primary-sourced):** `egraph-serialize`'s own README states plainly: *"One day egg will natively export to this format"* — i.e., as of 2026-08-12, egg does **not** natively export to the shared e-graph JSON interchange format used by `extraction-gym`; third-party conversion exists but is not egg's own contract. **ASSUMPTION:** I did not independently verify egglog's own native (non-Python) export path for feature-parity against `egraph-serialize` in this pass — egglog-python's `Cargo.toml` does depend on `egraph-serialize = "0.3"` directly (stronger integration signal than egg's aspirational note), but I have not confirmed the core `egglog` CLI/crate (outside the Python wrapper) ships this integration natively.

---

## 5. Stability of the textual/serialized format — what should `VERSIONS` actually pin?

**Method:** crates.io + PyPI API, direct read of `egglog-python`'s `Cargo.toml` (fetched 2026-08-12).

- **egg** (crates.io): `0.8.0 → 0.11.0` over the last 10 tags, latest `0.11.0` published 2025-12-04 — a slow, low-churn SemVer cadence, good for pin stability in isolation. But per §4, there is no format to pin beyond the API surface itself: pinning "egg 0.11.0" pins a Rust library version, not an interchange text format, which is a category mismatch against the pattern `spec/interop/ecosystem-contract.md` establishes (`VERSIONS` pins *format* versions — `ir_version`, `opset ai.onnx` — following the ONNX precedent already executed at G3).
- **egglog** (crates.io): `2.0.0`, published 2026-02-12 — already at major version 2 after ~4 years and several 0.x→1.0.0→2.0.0 jumps (tags: `v2.0.0, v1.0.0, v0.5.0 … v0.1.0`, plus a non-SemVer tag `no-tree-decomp` indicating active branch experimentation). This is a genuinely faster-churning, less format-stable track than egg's — the honest cost side of this recommendation.
- **egglog-python** (PyPI, `egglog`): version **13.2.0** — and, critically, its `Cargo.toml` pins the underlying Rust core via `egglog = { git = "https://github.com/egraphs-good/egglog.git", rev = "2e5657b", default-features = false }`, **not** a dependency on the published `egglog` crate (2.0.0). This means `egglog-python`'s own version number is **decoupled from** `egglog`-the-crate's SemVer — it vendors one exact, named git commit. For OAAS's purposes this is actually a *stronger* reproducibility guarantee than a loose crate SemVer range would be (pinning `egglog==13.2.0` on PyPI transitively and exactly fixes the Rust core commit baked into that wheel build), but it means the `VERSIONS` file must pin the **PyPI package version**, and must **not** attempt to cross-reference it against the crates.io `egglog` version number as if the two moved together — they provably do not (13.2.0 vs 2.0.0 are different numbering schemes entirely).
- Neither project ships a JSON-Schema/IDL-style versioned wire format comparable to ONNX's `.proto` files + integer `IR_VERSION`. The closest candidate is `egraph-serialize` (a JSON e-graph interchange crate, currently depended on at `"0.3"` per `egglog-python`'s `Cargo.toml`), which self-describes as being "mostly for use in extraction gym" — i.e., positioned by its own maintainers as benchmarking-tool support, not (yet) a stable public interchange contract. **ASSUMPTION:** I did not fetch `egraph-serialize`'s own crates.io page/changelog to independently confirm its release cadence; the "0.3.x, pre-1.0" characterization comes only from the dependency-line version constraint observed in `egglog-python`'s `Cargo.toml`, which is a lower bound, not necessarily the exact pinned patch version.

**Recommended `VERSIONS` pin (concrete, falsifiable, checkable by `drift-watch` today):**

```
egglog (PyPI, harness dependency)              = 13.2.0   # published 2026-06-03
                                                            # https://pypi.org/project/egglog/13.2.0/
egglog (Rust core, vendored — opaque/transitive) = git rev 2e5657b (egraphs-good/egglog)
                                                            # NOT the crates.io release; do not cross-check
                                                            # against crates.io egglog version — numbering is
                                                            # provably decoupled (13.2.0 vs 2.0.0)
egglog (crates.io, reference only — not a harness dependency) = 2.0.0   # published 2026-02-12
egg (crates.io, foreign-witness reference only — not executed) = 0.11.0 # published 2025-12-04
```

---

## Concrete recommendations for G14

1. **Target engine: egglog.** Bind the Python harness with `uv run --with egglog python3 tools/egraph_roundtrip.py`, following the exact idiom already established by `just roundtrip` (`uv run --with onnx python3 tools/onnx_roundtrip.py`) — no new `justfile` pattern needs inventing.
2. **Guard mapping:** for each `guards { key = value }` block in a corpus fixture (e.g. `numeric_semantics = exact`, `regime = ExactArithmetic`), the adapter emits one nullary `relation` named after the guard (e.g. `ExactArithmetic`), asserts it once per projection scope, and appends it as an extra argument to the generated `birewrite(...).to(rhs, GuardFact())` (Python API) — or, if OAAS ever emits literal `.egg` concrete syntax directly instead of going through the Python embedding, a `:when ((GuardFact))` clause. This was verified end-to-end against `003-equivalence-distributivity.oaas`'s exact shape in this session.
3. **Round-trip sketch** (mirroring the `preserves`/`may_lose` shape `profiles/ecosystem/onnx/CONTRACT.oaas` already uses at G3): `preserves { equivalence_class_membership, guard_conditions }`; `may_lose` is the *unchosen* extraction candidates — by construction, extraction always picks exactly one representative per the contract's cost function, so "which sibling term didn't get chosen" is the analog of ONNX's `may_lose { visual_layout }`: an explicitly sacrificial, named field, not a silent loss.
4. **A `profiles/ecosystem/egg/CONTRACT.oaas`** (referenced by `spec/interop/egraph.md` line 7 but not yet created) should declare `from OAAS-SIR` / `preserve equivalence`, per the source-stratum table already in `spec/interop/ecosystem-contract.md` §4.
5. **Naming flag (not resolved here — human/ADR call):** the existing stub directory is `profiles/ecosystem/egg/`, but the recommended execution target is egglog. Per `spec/interop/ecosystem-contract.md`, the org (`egraphs-good`) is the sovereign upstream and both `egg` and `egglog` are its projects — so keeping the directory named after the org's umbrella identity (or renaming to `profiles/ecosystem/egglog/` with `egg` demoted to a citation inside `PROFILE.md`) is a legitimate, open, ratification-worthy choice. This document does not resolve it — flagged for whoever executes G14.

---

## Assumptions and unresolved items (explicitly flagged, not silently resolved)

- **ASSUMPTION:** "egg is in maintenance mode" is an inference from commit-cadence delta + a README pointer, not a verbatim maintainer quote. I could not reach `egraphs.zulipchat.com` in this session to check for a more explicit statement — flagged as an evidentiary gap. Falsifiable by: a sustained future increase in egg's own commit rate, or a maintainer statement denying successor status.
- **ASSUMPTION:** egglog's own native (non-Python) export path to `egraph-serialize` was not independently feature-verified in this pass; only egg's *lack* of native export was confirmed via a direct quote from `egraph-serialize`'s README.
- **ASSUMPTION:** `egraph-serialize`'s exact current crates.io version was inferred from a dependency-constraint string (`"0.3"`) in `egglog-python`'s `Cargo.toml`, not fetched directly from crates.io — treat as a lower bound, not a confirmed exact version.
- **Not investigated (out of scope for this pass, flag for a future unknown if it becomes decision-relevant):** performance/scaling comparison between the two engines on OAAS-sized SIR graphs — this research answers "which engine can the harness even run," not "which engine saturates faster at scale." If G14's corpus grows large enough that saturation time becomes a gating concern, that is a distinct, falsifiable follow-up question, not answered here.
- **Not investigated:** whether `egg`'s `no_std`/`alloc` support (added in a 2026-04-14 commit, seen in the commit log during this research) signals a WASM/embedded-target roadmap that could someday matter for an OAAS browser-based tool — noted only as a side observation from the commit log, not evaluated.

## Validity

Valid as of 2026-08-12. Re-evaluate if: egglog's crate crosses another major version bump in a way that breaks the `.egg` guard/extraction syntax cited here (re-run the smoke test against the new pin before trusting this doc's guard-mapping sketch); `snake-egg` or any other egg-Python binding receives a new release (re-check sub-question 2); the `egraphs-good` org restructures (e.g., merges `egg` into `egglog` or formally archives `egg`) — any of these would change the liveness picture in §1 materially, not just incrementally.

## Sources (all fetched/executed 2026-08-12)

1. `egraphs-good/egg` — GitHub REST API repo metadata, commits, tags, contributors: https://api.github.com/repos/egraphs-good/egg
2. `egraphs-good/egglog` — same, https://api.github.com/repos/egraphs-good/egglog
3. `egraphs-good` org repo listing (18 repos): https://api.github.com/orgs/egraphs-good/repos
4. egg README (maintainer pointer to egglog): https://raw.githubusercontent.com/egraphs-good/egg/main/README.md
5. egglog README ("Next-Generation Equality Saturation Engine", CLI usage shape): https://raw.githubusercontent.com/egraphs-good/egglog/main/README.md
6. egg CITATION.bib (POPL 2021): https://raw.githubusercontent.com/egraphs-good/egg/main/CITATION.bib
7. egglog CITATION.bib (PLDI 2023): https://raw.githubusercontent.com/egraphs-good/egglog/main/CITATION.bib
8. crates.io `egg`: https://crates.io/api/v1/crates/egg
9. crates.io `egglog`: https://crates.io/api/v1/crates/egglog
10. PyPI `egglog` JSON (version 13.2.0, wheel list incl. macOS arm64): https://pypi.org/pypi/egglog/json
11. PyPI `snake-egg` JSON (version 0.1.0, stale wheel list): https://pypi.org/pypi/snake-egg/json
12. `egraphs-good/snake-egg` repo metadata (pushed_at 2023-01-17): https://api.github.com/repos/egraphs-good/snake-egg
13. PyPI `pyegg` JSON (confirmed unrelated package): https://pypi.org/pypi/pyegg/json
14. egg `rewrite!` macro docs (conditional `if` form, `ConditionalApplier`/`Condition`): https://docs.rs/egg/latest/egg/macro.rewrite.html
15. egg `src/rewrite.rs` (Condition trait, ConditionEqual): https://raw.githubusercontent.com/egraphs-good/egg/main/src/rewrite.rs
16. egg `src/extract.rs` (Extractor, CostFunction trait, AstSize/AstDepth): https://raw.githubusercontent.com/egraphs-good/egg/main/src/extract.rs
17. egglog test corpus, conditional `:when` rewrites (primary syntax evidence): https://raw.githubusercontent.com/egraphs-good/egglog/main/tests/integer_math.egg
18. egglog test corpus, `:cost` annotations and `extract` command: https://raw.githubusercontent.com/egraphs-good/egglog/main/tests/fibonacci-demand.egg
19. egglog-python tutorials (Python API: `relation`, `rewrite/.to()`, `birewrite`, `rule`, `set_cost`, `extract`): https://raw.githubusercontent.com/egraphs-good/egglog-python/main/docs/tutorials/tut_1_basics.py, tut_4_scheduling.py, tut_5_extraction.py
20. egglog-python `Cargo.toml` (git-rev vendoring of egglog core, `egraph-serialize` dependency): https://raw.githubusercontent.com/egraphs-good/egglog-python/main/Cargo.toml
21. egglog-python `pyproject.toml` (base dependency list): https://raw.githubusercontent.com/egraphs-good/egglog-python/main/pyproject.toml
22. `egraph-serialize` README ("One day egg will natively export to this format"): https://raw.githubusercontent.com/egraphs-good/egraph-serialize/main/README.md
23. This session's executed smoke test (round-trip of `conformance/corpus/003-equivalence-distributivity.oaas` via `uv run --with egglog`) — script retained at `/private/tmp/claude-501/-Users-cem-oaas/9f19ae22-cb9b-4e84-8239-423bbdc3a75d/scratchpad/u5_smoketest.py` (scratchpad, not part of the repo).
24. Repo context read before this research: `spec/interop/egraph.md`, `profiles/ecosystem/egg/PROFILE.md`, `profiles/ecosystem/egg/VERSIONS`, `spec/interop/ecosystem-contract.md`, `spec/conformance.md`, `profiles/ecosystem/onnx/CONTRACT.oaas`, `tools/onnx_roundtrip.py`, `GOVERNANCE.md`, `justfile`, `conformance/corpus/003-equivalence-distributivity.oaas` + sibling `*-equivalence-*.oaas` fixtures.

---

**Epistemological note:** This research reflects the best available evidence as of 2026-08-12, gathered via direct GitHub/crates.io/PyPI API calls and primary-source file reads (not search-engine summaries, except where explicitly noted), plus one script actually executed on this machine rather than merely described. Sub-question 4's core claim (round-trip fidelity of the guard-carrying distributivity fixture) is the strongest-evidenced finding in this document precisely because it is not inference — it is a reproducible mechanical result, matching this project's own definition of what counts as verified (`spec/conformance.md` §1). The liveness comparison (§1) is the weakest-evidenced individual claim (no direct maintainer quote on "maintenance mode" was located) and is flagged accordingly; it does not change the recommendation because sub-questions 2 and 3 are independently near-decisive. Both projects evolve fast — egglog crossed a major version bump within the last six months of this research date — so this pin should be treated as a snapshot to re-verify at G14 execution time, not a permanent fact.
