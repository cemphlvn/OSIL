# U9 — Competitive benchmarks: is there an external scoreboard for a CPU-side, ARM-targeting semantic vectorizer?

**Date:** 2026-08-22
**Researcher:** research-agent (four parallel sub-agents dispatched by wave decomposition; synthesis by the dispatching agent)
**Question:** `optimizer/` (see `optimizer/README.md`) measured ~33x over clang -O3 and ~2.1x over clang -O3 -ffast-math on TSVC_2's `s312` product reduction, on an Apple M4 (NEON, 128-bit, no classic SVE). Is there a public benchmark, leaderboard, or competition where this system — a deterministic, CPU-side, source/SIR-to-realization semantic optimizer built on equality saturation (`egg`) — could post an externally-checkable number, as opposed to a self-reported one?

**Relationship to prior research:** U7 (`docs/research/U7-vectorization-benchmark-corpora.md`) already surveyed *benchmark corpora* (TSVC_2, PolyBench, LLVM test-suite) — the kernels to run. This document is strictly about *external venues* — a live scoreboard, competition, or independent-comparison mechanism a third party maintains and others submit numbers to. That distinction matters: several candidates below have a benchmark corpus (kernels) but no external venue (nowhere to post a number and have it ranked against others).

---

## TL;DR

**The honest answer is: there is no good external leaderboard for this niche, and that is a confirmed, not just under-searched, gap.** Every candidate investigated fails on one of three axes: (a) wrong object of evaluation — LLM code generation or RL policy quality, not a deterministic rewrite-selection optimizer; (b) wrong problem shape — GPU kernels, DNN tensor programs, or Python algorithmic efficiency, not general CPU loop vectorization; or (c) dead/archived infrastructure. The one venue that ever structurally matched OSIL's shape — **CompilerGym**'s LLVM leaderboard — is **archived** (2026-05-27) and its own leaderboard had already gone four years without a submission before that. No ARM/NEON-specific leaderboard exists anywhere, from any of Arm Ltd, the Arm HPC User Group, Apple, or the Graviton/Ampere/Neoverse server community.

**What the field actually does instead**, confirmed convergently by the e-graph/superoptimization sub-agent and the SPEC/AI-benchmarks sub-agent: every comparable system (Souper, STOKE, Minotaur, Diospyros, Ansor, the TSVC_2-based ARM-vs-x86 comparison paper) **self-reports on a self-chosen, published, reproducible corpus against named baseline compilers**. That is not a weaker position than the field's norm — **it is the field's norm.** OSIL's current TSVC_2 `s312` measurement already follows this convention.

**Recommended substitute (ranked, detail in "Ranked shortlist" below):**
1. Artifact Evaluation at CGO/PLDI/ASPLOS/OOPSLA — genuine external, independent-committee validation, but gated on an accepted paper (not an open leaderboard).
2. Reproduce a published paper's numbers on overlapping kernels/corpora and cite as a direct comparison — concretely, the TSVC_2-on-ARM paper (arXiv:2502.11906, already known from U7) is the single best candidate for an apples-to-apples number, since it already used the same corpus on ARM hardware.
3. Watch (not act on) GSO (`gso-bench/gso`) — actively maintained, MIT, includes real SIMD/systems codebases (llama.cpp, NumPy) — closest subject-matter overlap of anything found, but currently an LLM-agent-only leaderboard with no non-agent submission path.

**Confidence:** HIGH on maintenance status and licensing (all verified against GitHub API metadata, live repo pages, or primary documents — a fetched commit date or archive banner, not a README claim). MEDIUM-HIGH on the SPEC CPU run-rules interpretation (verified against the actual rule text, but rule application to a hypothetical submission is inherently a judgment call). MEDIUM on "no leaderboard exists" claims for the e-graph and ARM-specific communities — these are negative claims (absence of evidence), mitigated by direct fetches of the EGRAPHS workshop's own program pages across three years and Arm Ltd's own developer documentation, but a negative claim can never be proven exhaustively by search.

---

## Method (wave decomposition)

Default line I would have run: search each of the nine named candidates sequentially myself. Simulated finding: general status blurbs, plausible but not evidentially strong enough for a claim this document needs to support ("no good venue exists" is a strong negative claim that requires primary-source verification, not a search-summary paraphrase). Gaps relative to the task, this project's evidence hierarchy, and the maintainer's actual goal (a number they can point to and defend under scrutiny):

- Gap A — GPU/RL-shaped venues (KernelBench, CompilerGym) needed **live repo-state verification** (archived banner, actual last-commit date), not README self-description, since "is it alive" is exactly the kind of claim that goes stale between a doc's writing and today.
- Gap B — ML-guided/tensor-compiler venues (MLGO, TenSet/Ansor/Halide) needed a **framework-vs-benchmark-vs-infrastructure ontological distinction** made explicit, since conflating "has a repo" with "has a leaderboard" was the single most likely failure mode across all nine candidates.
- Gap C — commercial/LLM-benchmark venues (SPEC CPU2017, EffiBench/Mercury/SWE-Perf-class) needed **primary legal/rules text** (SPEC's actual run-rules HTML, not a summary) and a precise **language-level check** (is the benchmark scored on Python solutions to algorithmic problems, or on compiled/vectorized code) since these are easy to conflate from titles alone.
- Gap D — the e-graph/superoptimization community and ARM-specific venues needed **direct fetches of the community's own program pages** (EGRAPHS workshop 2024–2026) to distinguish "a workshop exists" from "a bake-off exists within it" — these are different claims routinely elided in search-engine summaries.

Each gap became one parallel sub-agent dispatch (four `research-agent` instances, single message, per this agent's own Wave Protocol). Item 9 (PL conference artifact evaluation) and the final synthesis were handled directly by the dispatching agent, since it required judgment calls the sub-agents' narrower briefs did not cover.

**Synthesis: convergent.** All four sub-agents, working independently on non-overlapping candidate sets, arrived at the same structural verdict without being told to: *the leaderboard model does not exist in this niche; self-report-on-a-known-corpus is the field's actual practice.* This convergence across independently-dispatched agents is itself evidence — not proof, but a meaningfully stronger signal than one agent's opinion — that the gap is real rather than an artifact of any one search strategy.

---

## Quick-reference table

| # | Candidate | Alive? (evidence date) | External submission? | Hardware assumed | Metric | License | Fit verdict |
|---|---|---|---|---|---|---|---|
| 1 | KernelBench (Stanford) | Alive, `pushed_at` 2026-03-24 | No central leaderboard (BYO-hardware by design) | GPU only (CUDA/HIP/Triton/CUTE/TileLang/ThunderKittens) | `fast_p` (correct + speedup>p vs. PyTorch eager) | MIT | **Out of scope** — hard GPU wall + LLM-codegen object |
| 1b | GPU MODE / KernelBot (successor leaderboard) | Alive, `pushed_at` 2026-07-29 | Yes — Discord bot + `popcorn-cli` | Sponsor GPU nodes (H100, MI250) | Wall-clock speedup, correctness gate | Custom "Researcher Reciprocity License v1.0" | **Out of scope** — GPU-only |
| 2 | CompilerGym (Meta) | **Archived 2026-05-27**; last real feature commit 2023-03-10 | Was PR-based (`leaderboard/llvm_instcount`); 6 submissions total, last 2022-07-06 | LLVM 10.0.0 pinned, arch-agnostic IR decisions | Mean LLVM instruction-count reduction | MIT | **Out of scope, and dead** — wrong problem class (pass-ordering) even when alive |
| 3 | MLGO (Google) | Alive, last commit 2026-08-23 | None — no benchmark/leaderboard exists at all | Arch-agnostic (IR-level decisions) | Code size (inlining) / regalloc quality | Apache-2.0 | **Out of scope** — no venue exists; wrong decision surface (inlining/regalloc, not vectorization) |
| 4a | TenSet (dataset) | **Dead since 2021-08-31**, zero releases | Never had one — static frozen dataset | Intel CPU, AMD EPYC, ARM Graviton2, NVIDIA GPU | N/A | Apache-2.0 (code) / CC BY 4.0 (data) | **Out of scope** — dead, never a venue |
| 4b | Ansor / TVM | Alive, commits today | No public leaderboard; paper-embedded, commit-pinned reproducible suite | Intel Xeon 8124M, ARM Cortex-A53 (RPi), NVIDIA V100 | Runtime vs. baselines (PyTorch/AutoTVM/FlexTensor/Halide-AS) | Apache-2.0 | **Reproduce-and-cite only** — DNN tensor-scheduling shaped, not general C-loop vectorization |
| 4c | Halide autoscheduler | Alive, commit today (2026-08-24) | No leaderboard; paper-embedded app suite | Intel Core i9-7960X | Runtime vs. hand-tuned/prior autoscheduler | MIT | **Reproduce-and-cite only** — image-pipeline shaped |
| 5 | SPEC CPU2017 / CPU2026 | Alive; CPU2026 launched 2026-05-05; CPU2017 sunsetting ~2026-11-03 | Yes, $500/result publication + $50–1000 license | Vendor-declared, published in each result | SPECrate/SPECspeed | Commercial (paid) | **Out of scope by rule, not cost** — run rules (1.2.1, 2.2.1, 1.4) structurally exclude an unsupported research source-rewrite tool |
| 6 | EffiBench / EffiBench-X / Mercury / SWE-Perf | Alive (varying staleness, 5.5–21 months) | Static datasets / paper-embedded LLM-agent eval, no non-agent path | N/A (Python/algorithmic execution) | Runtime/memory vs. human baseline (LLM-generated code) | Mixed (none/Apache-2.0) | **Out of scope** — LLM-code-gen quality at Python level, not compiler optimization |
| 6b | GSO (`gso-bench`) | Alive, last push 2026-07-12 (most active of cluster) | LLM-agent leaderboard only (`livecodebench.github.io/gso.html`) | Real systems codebases (NumPy, Pandas, Pillow, llama.cpp — C/C++/SIMD/Rust) | Opt@K vs. expert patch | MIT | **Watch, not act** — closest subject matter, but no non-agent submission path today |
| 7a | EGRAPHS workshop | Alive, 2022–2026 confirmed via direct fetch | **No comparison track exists** (talks-only venue, confirmed by reading 2025/2026 programs) | N/A | N/A | N/A | **No venue** |
| 7b | Souper | **Archived 2025-10-30** | Self-reported corpora only (SPEC CINT2006 subset, llvm-test-suite) | x86/general LLVM IR | Correctness + count of found optimizations | Apache-2.0 | **Out of scope, dead** |
| 7c | STOKE | Dormant (last commit 2023-08-14) | Self-reported | x86-64 only | Correctness (SMT) + cycle count | Apache-2.0 | **Out of scope** — wrong ISA regardless |
| 7d | Ruler / Enumo (`chompy`) | Alive, last push 2026-08-16 / 2026-05-10 | Intra-lab comparison only, no external venue | N/A (arithmetic/bitvector/bool domains) | Ruleset quality vs. prior in-house system | MIT | **Out of scope** — not vectorization-relevant, no external venue |
| 7e | extraction-gym | Alive, last push 2026-02-02 | Yes, open-contribution ("add data as JSON"), but **no ranking/leaderboard page** | N/A | Extraction-algorithm cost | MIT | **Wrong sub-problem** — extraction only, not end-to-end rewrite+realize |
| 7f | Minotaur (adjacent, not user-named) | Alive, last push 2026-03-25 | Self-reported (GMP, SPEC CPU2017 subset) | x86-64/AVX (Cascade Lake) | Speedup vs. plain LLVM | MIT | **Related-work citation only** — wrong ISA, closest conceptual sibling |
| 8 | ARM/NEON-specific leaderboard (Arm Ltd, Arm HPC UG, Apple, Graviton/Neoverse community) | N/A — **confirmed does not exist** | N/A | N/A | N/A | N/A | **Genuine ecosystem gap** |
| 8b | Swan benchmark (closest artifact) | Single-paper release, 2023 (arXiv:2309.02680) | No — static Zenodo artifact | Simulated NEON, up to 1024-bit exploration | Workload throughput (design-space exploration) | Academic release | **Not competitive-shaped** — workload DSE, not an optimizer comparison |
| 9 | PL conference Artifact Evaluation (PLDI/CGO/ASPLOS) | Alive, ongoing (PLDI 2026 deadlines confirmed: submission 2026-03-17) | Yes, but **gated on an already-accepted paper** | Whatever the paper specifies | Reproduction of the paper's own claims; comparison vs. related systems required if claimed | N/A (process, not a licensed corpus) | **Best available real venue** — external, independent, but not an open leaderboard |

---

## 1. KernelBench (Stanford)

**Repo:** [`ScalingIntelligence/KernelBench`](https://github.com/ScalingIntelligence/KernelBench) — created 2024-10-25, `pushed_at` 2026-03-24, not archived, **MIT**. Paper: Ouyang, Guo, Arora, Zhang, Hu, Ré, Mirhoseini, "KernelBench: Can LLMs Write Efficient GPU Kernels?" arXiv:2502.10517 (Stanford + Princeton).

Design, verbatim from the paper (§3.3): *"KernelBench is an evaluation-only benchmark. We do not provide ground truth kernels for the tasks since we imagine users benchmarking on a variety of hardware platforms..."* — a **bring-your-own-hardware harness**, not a hosted leaderboard. Task format: a PyTorch `nn.Module` reference, and the system under test (an LLM) emits a `ModelNew` class with inline generated kernel code in one of CUDA, Triton, HIP, CUTE, TileLang, or ThunderKittens. **All GPU. No CPU track exists.** Metric `fast_p` = fraction of tasks both correct (5 random-input checks) and faster than a threshold vs. PyTorch eager baseline.

The de facto **live external leaderboard** descended from this idea is a separate community project: **GPU MODE / KernelBot** (`gpu-mode/kernelbot`, `pushed_at` 2026-07-29; `gpu-mode/reference-kernels`, `pushed_at` 2026-07-26; both active). Submission is via Discord bot + `popcorn-cli`, graded on sponsor-donated GPU nodes (AMD MI250, NVIDIA H100 via Modal/Nebius/Northflank), under a custom "June 9 Researcher Reciprocity License v1.0" (a RAIL-derived license with an AI-training-reciprocity clause). NVIDIA's own engineering blog has covered "topping the GPU MODE leaderboard," corroborating it is genuinely active, not a ghost project.

**Verdict: out of scope, bluntly.** Two independent, hard blockers: (1) every backend is a GPU kernel DSL — there is no slot in the harness's schema for "a CPU realization," so a NEON vectorizer has nowhere to plug in even hypothetically; (2) the object being evaluated is an LLM's ability to *write* kernel source from a prompt, not a deterministic optimizer's ability to *select* a realization from a declared equivalence class — the two systems answer different questions even when the domain overlaps.

---

## 2. CompilerGym (Meta) — confirmed dead

**Repo:** [`facebookresearch/CompilerGym`](https://github.com/facebookresearch/CompilerGym). GitHub API: `"archived": true`. The live repo page carries the banner, fetched verbatim: *"This repository was archived by the owner on May 27, 2026. It is now read-only."*

Commit history tells a more precise story than the archive date alone: the last commit of any kind was 2024-10-09 (a dependency/CVE bump), the **last substantive feature commit was 2023-03-10** — meaning the project was functionally dormant for roughly 20 months before it was formally archived. Measured from the last real feature work, the project has now been dead for **~3.4 years**. Last release was v0.2.5 (2022-era Python 3.10 support note); the bundled LLVM environment is still pinned to **LLVM 10.0.0**.

The leaderboard mechanism was real, not aspirational — `leaderboard/llvm_instcount` had an actual `SUBMISSION_TEMPLATE.md` and PR-based process, ranked by mean LLVM instruction-count reduction on a held-out set. But it only ever received **six submissions in the project's entire history** (2021-04-27 through 2022-07-06), and had already gone **four years without a new submission** before the repo was archived. License: MIT.

**No official successor exists.** The same lead author (Chris Cummins, Meta) later released **Meta Large Language Model Compiler** (arXiv:2407.02524, July 2024) — an LLM-based approach under a bespoke commercial license, evaluated in a paper, not a live leaderboard — a thematic/authorship successor, not an infrastructure replacement. Multiple 2024–2026 academic RL-for-compilers papers found in search (CompilerDream, Compiler-R1, GRACE, a "Synergy-Guided" pass-pipeline paper) **still use the archived CompilerGym LLVM environment as their harness** rather than any live replacement — the field kept using the corpse rather than replacing it.

Even setting deadness aside: CompilerGym's flagship LLVM environment is **pass-ordering / phase selection** (a sequence of `opt` passes minimizing instruction count), plus a `loop_tool` environment (tensor-program loop-nest scheduling) and a GCC flag-selection environment. None of these expose "select a realization from a guard-licensed equivalence class of semantically-equivalent vectorized rewrites" — sequential discrete pass-choice and saturating equivalence-class rewrite search are different search problems over different spaces. Posing OSIL's decision as a CompilerGym action would require building an entirely new environment from scratch.

**Verdict: out of scope, and dead besides.** Archived, wrong problem class even when alive, and the one leaderboard it ever had stopped taking submissions four years before the archival.

---

## 3. MLGO (Google, ML-guided optimization in LLVM)

**Repo:** [`google/ml-compiler-opt`](https://github.com/google/ml-compiler-opt) — alive, actively developed; latest commit 2026-08-23 (a GPG-signed perf optimization with CI-checked reproducibility numbers in the commit message — this is not a dormant repo). Tagged releases across five years (`inlining-Oz-v1.0` 2021-07-02 through `inlining-Oz-v1.2` 2025-04-08) confirm a slow but real cadence. License: **Apache-2.0**.

**Ontologically, MLGO is a FRAMEWORK / production-adjacent infrastructure, not a benchmark.** Per `llvm.org/docs/MLGO.html`: exactly two heuristics have upstream LLVM integration — inlining-for-size and register-allocation-eviction-for-performance. The trained-model *inference* side ships in `llvm/lib`; only the *training* orchestration lives in the separate, dependency-heavy `ml-compiler-opt` repo (explicitly "not part of LLVM" per the docs). There is **no vectorization, loop transformation, or any other pass** with MLGO integration.

**No external comparison mechanism exists.** No leaderboard, no published comparison set with a standard metric other groups submit numbers against. MLGO's own reported numbers (e.g., "up to 7% code-size reduction vs. -Oz") are self-measured by Google on internal/Chrome/Fuchsia-style corpora. A targeted search for independent third-party reproductions or head-to-head comparisons on a shared standard suite returned nothing beyond MLGO's own docs and blog post, plus one tangential paper (RL4ReAl, a different RL-regalloc approach that does not report head-to-head MLGO numbers).

**Verdict: out of scope — apples to oranges, and there is no shared table to even attempt it on.** MLGO targets a completely different decision surface (inline/don't-inline, spill/evict) than "which vectorized realization to select for a declared reduction." The only honest connection for a paper to draw is philosophical/structural (both replace a hand-written LLVM heuristic with something else), never numeric.

---

## 4. TenSet / TVM Ansor / Halide autoscheduler

**TenSet (`uwsampl/tenset`) — dead.** `pushed_at` 2021-08-31; last commit 2021-08-29; zero releases; effectively frozen for five years as of 2026. Apache-2.0 (code) / CC BY 4.0 (dataset). It was always a static, frozen performance-measurement dataset (52M records, 120 networks, 13,848 tasks, six hardware platforms including ARM Graviton2) for training cost models used *inside* Ansor's search — never a venue with a submission mechanism, alive or dead.

**Ansor (the actual TVM auto-scheduler system) — the substantive artifact.** Read directly from the OSDI 2020 paper (Zheng et al., [usenix.org/system/files/osdi20-zheng.pdf](https://www.usenix.org/system/files/osdi20-zheng.pdf)), §7: hardware = Intel Xeon Platinum 8124M, NVIDIA V100, ARM Cortex-A53 (Raspberry Pi 3B+) — **no Apple Silicon, no M-series NEON data point anywhere**. Single-Operator Benchmark (§7.1): 10 operators × 4 shapes × 2 batch sizes = 80 cases on the Intel CPU only, against commit-pinned baselines (PyTorch v1.5/MKL-DNN, Halide auto-scheduler, FlexTensor, AutoTVM). This is a genuinely reproducible, commit-pinned suite — later papers (e.g. a 2024 coordinate-descent fine-tuning paper, arXiv:2406.20037) do cite and re-run Ansor's numbers as a baseline, giving it real citation lineage, unlike MLGO. One operator, "NRM" (matrix 2-norm), is structurally a reduction — the single narrow point of contact with OSIL's `s312` kernel. But it's a reduction *inside TVM's tensor-expression scheduling framework*, evaluated via stochastic sketch-and-anneal search with a learned cost model requiring up to 1,000 on-device measurement trials — not a source-level C loop, not ARM NEON, not equality saturation, not a single deterministic decision from a guard-licensed space.

**Halide autoscheduler** (Adams et al. 2019, [halide-lang.org/papers/halide_autoscheduler_2019.pdf](https://halide-lang.org/papers/halide_autoscheduler_2019.pdf)): Intel Core i9-7960X only. Benchmark = 15 named image-processing apps + 100 synthetic pipelines, released as reproducible supplemental material. `halide/Halide` repo is very actively maintained (commit today, 2026-08-24), MIT license. Same category mismatch as Ansor: Halide-DSL pipeline scheduling, image-processing shaped, not general C-source loop vectorization — SGEMM and a conv+ReLU layer are the only entries with any vectorization-kernel flavor.

**TVM itself** (`apache/tvm`): alive, very active (commit today), Apache-2.0. No official standing leaderboard page — only Discuss-forum threads and ad hoc `apps/benchmark` scripts.

**Verdict: reproduce-and-cite only, not a real comparison venue.** All three systems are DNN-tensor-program or image-pipeline auto-scheduling (search + learned cost model over a different IR), evaluated on hardware that excludes Apple M-series NEON. Posting a "comparable" number here would require reimplementing the OSIL kernel as a TVM tensor-expression or Halide pipeline and running it through their search loop on their hardware — at which point the number measures whether OSIL's rewrite is reachable inside someone else's DSL, not OSIL's own system. Not a fair or standard comparison.

---

## 5. SPEC CPU 2017 / CPU2026

Verified directly against SPEC's own pages, not summaries.

**Cost** ([spec.org/cpu2017/press/academicpricing.html](https://www.spec.org/cpu2017/press/academicpricing.html)): commercial $1,000, non-profit $250, accredited-academic-institution $50 — **institutional, not individual**; the CPU2026 page states a student "must place the order on behalf of the institution" through a professor or staff member, so an unaffiliated solo maintainer has no clean path to the academic tier. **SPEC CPU2026 launched 2026-05-05** at $3,000 commercial / $750 non-profit, with a $2,000 upgrade path for CPU2017 licensees through **2026-11-03**, after which CPU2017 submissions appear to be sunsetting (per [spec.org/spec/submitting_results/](https://www.spec.org/spec/submitting_results/), which lists both benchmarks' active publication windows). Publication fee (getting a result into SPEC's own published-results database) is **$500/result** for non-members; SPEC members submit free but membership dues run to the low thousands of dollars/year (weakest-sourced figure in this document — no single canonical number found, flagged accordingly). Net floor for one externally-checkable, database-published result as a non-member: roughly **$550–$750**. Cost is not the real barrier.

**The real barrier is the run rules**, read directly from [spec.org/cpu2017/Docs/runrules.html](https://www.spec.org/cpu2017/Docs/runrules.html) (rule numbers verified against the raw HTML anchors):
- **Rule 1.2.1**: benchmark source code "testers are **not allowed to modify** except under certain very restricted circumstances."
- **Rule 2.2.1**: forbids naming benchmark source files/variables/subroutines in optimization flags or using preprocessor directives to select alternative source — with two narrow, subcommittee-pre-approved exceptions (library substitution for `alloca()`/BLAS/FFT in FP peak runs; portability flags for builds that literally cannot succeed otherwise). Neither fits an arbitrary source-rewriting optimizer.
- **Rule 2.1.1**: compilation must go through SPEC's own `runcpu` tool; no vendor-supplied third-party preprocessor pass is permitted in the pipeline at all.
- **Rule 1.4** is the sharpest: a published result is a claim that the optimization method is *"generally available, documented, supported"* and explicitly **not** *"just 'prototype' or 'experimental' or 'research'"* — a bar a single-maintainer open-source research project cannot credibly self-certify for a compliant *peak* result.

**Verdict: out of scope by rule, not by cost.** SPEC CPU's rule system is purpose-built to exclude exactly this class of tool. A path exists only if OSIL's rewrite passes were eventually upstreamed into a mainline, vendor-supported compiler (LLVM/GCC) — at which point *that compiler's* SPEC submission, not OSIL's, would carry the number. Running SPEC's source privately and reporting a clearly-labeled "estimate" (a common practice in papers) is legal but forfeits exactly the externally-checkable-scoreboard property being sought here.

---

## 6. Code-efficiency benchmarks for AI-generated code

All repo metadata below is from the GitHub API directly (`pushed_at`, `license.key`, `archived`), not a rendered README.

| Benchmark | Venue | Last push | License | What it measures |
|---|---|---|---|---|
| EffiBench | NeurIPS 2024 | 2024-11-30 (~21 mo stale) | none detected | Python-only, 1,000 LeetCode-style problems, LLM-generated solution runtime/memory vs. human baseline |
| EffiBench-X | NeurIPS 2025 (arXiv:2505.13004) | 2025-10-24 | Apache-2.0 | Multi-language (Py/JS/C++/Java/Go/Ruby), still competitive-programming problems, still LLM-solution quality, default compile flags |
| Mercury | NeurIPS 2024 (arXiv:2402.07844) | 2026-03-06 | none detected | Python-only, 1,889 tasks, novel "Beyond@K" metric vs. historical percentile |
| SWE-Perf | ICML 2026 poster (arXiv:2507.12415) | 2025-10-28 | none detected | 140 instances from real perf-improving PRs across 9 **pure-Python** repos (astropy, matplotlib, scikit-learn, etc.); patches dominated by redundancy elimination/caching, not compiler-level work; no leaderboard infra |
| GSO (`gso-bench/gso`) | NeurIPS 2025 (arXiv:2505.23671) | **2026-07-12** (most active) | MIT | 102 tasks, 10 codebases incl. **NumPy, Pandas, Pillow, llama.cpp** (Python/C/C++/SIMD/Rust/Cython) — closest subject matter to systems performance work found in this entire survey |

GSO deserves the closest look since it's the only one with real systems/SIMD content. Its public leaderboard ([livecodebench.github.io/gso.html](https://livecodebench.github.io/gso.html)) ranks language models/agents by **Opt@1/Opt@K** — whether an LLM SWE-agent's single-shot patch reaches ≥95% of an expert's speedup (leading agents currently score under 5%). The framing throughout ("evaluates language models' capabilities," "SWE-Agents") gives no indication a deterministic, non-agent tool is in scope, and no submission path for one was found.

Adjacent SIMD-specific finds, all still LLM-benchmark-shaped rather than compiler-shaped: **SimdBench** (arXiv:2507.15224, LLM-generated SSE/AVX intrinsics from a scalar spec), **LLaMeSIMD** (`VectorCamp/LLaMeSIMD`, LLM-based SIMD intrinsic translation across ISAs), **VecIntrinBench** (arXiv:2511.18867, LLM cross-architecture intrinsic migration for RISC-V Vector). None model an optimizer selecting a realization from a rewrite space; all model an LLM's ability to hand-write or translate intrinsic code.

The closest historical analog to a genuine, non-LLM compiler-optimization leaderboard — CompilerGym's `llvm-ic-v0` leaderboard — is confirmed archived (§2). Nothing found at CGO/PLDI/MLSys 2025–2026 replaces it as a compiler-optimizer-specific (as opposed to LLM-code-generation) leaderboard.

**Verdict: out of scope for all six.** Every one measures LLM-generated or LLM-patched code at the Python (or Python-plus-competitive-programming-language) algorithmic level, scored against human baselines — a categorically different question from whether a deterministic SIR-to-realization optimizer picks a correct, faster vectorization. GSO is worth *watching* — actively maintained, real systems codebases, MIT license — in case it ever opens a non-agent track; it does not offer one today.

---

## 7. Superoptimization / equality-saturation community

**EGRAPHS workshop** ([egraphs.org](https://egraphs.org), PLDI co-located) — alive and active; site last updated 2026-08-20; ran every year 2022–2026 (EGRAPHS 2026 CFP confirms 16 accepted talks). Directly fetched the main page plus the 2025 (`pldi25.sigplan.org/home/egraphs-2025`, 12 talks) and 2026 (`pldi26.sigplan.org/home/egraphs-2026`, 16 talks) program pages: **zero mention of a benchmark suite, competition track, or bake-off in any year checked.** It is a talks/community venue (Zulip, monthly Zoom calls, annual workshop) with no comparison mechanism. The community's own curated list (`philzook58/awesome-egraphs`) surfaces exactly one benchmark-shaped pointer — `philzook58/egg-bench`, a single maintainer's personal collection, never adopted as a cross-tool standard, no ranking.

**Souper** (`google/souper`) — **archived 2025-10-30** (verbatim GitHub banner), last push 2024-08-28, Apache-2.0. Self-reported corpora only: the original paper (arXiv:1711.04422) used ~30k expressions from SPEC CINT2006; later work used llvm-test-suite SingleSource (1,788 functions). No shared registry others submit numbers to.

**STOKE** (`StanfordPL/stoke`) — not formally archived, but last commit **2023-08-14**, over three years dormant. x86-64 only, irrelevant to ARM regardless of status. Still cited as historical prior art in 2024–2025 papers, but purely as a citation, not an active shared baseline.

**Ruler / Enumo** (`uwplse/ruler`, MIT, last push 2026-08-16; successor `ninehusky/chompy`, MIT, last push 2026-05-10) — both genuinely alive. Enumo (OOPSLA'23) is reported to outperform Ruler (OOPSLA'21) on arithmetic/bitvector/boolean domains, but this is an intra-lab comparison between the same group's two successive systems, not an external leaderboard, and the domain (rule synthesis for arithmetic/bitvector reasoning) is not vectorization-relevant.

**extraction-gym** (`egraphs-good/extraction-gym`) — alive, MIT, last push 2026-02-02, 53 stars, genuinely open-contribution ("add data — it's just a JSON"). This is the **closest thing to real shared infrastructure** found anywhere in the e-graph community. But it benchmarks *extraction algorithms* (given a fixed e-graph, which algorithm picks the best term) — not full rewrite-then-realize pipelines, not vectorization, no ARM angle, and **no ranking/leaderboard page** — you clone it and run `make` locally. Wrong sub-problem for what OSIL would report.

**Minotaur** (`minotaur-toolkit/minotaur`, OOPSLA'24, Regehr/Utah — flagged as an adjacent find, not user-named) — alive, MIT, last push 2026-03-25. A SMT-verified (Alive2-based) synthesizing superoptimizer for SIMD, direct successor to Souper — but **x86-64/AVX only** (Cascade Lake). Self-reports on the GMP benchmark suite (avg 7.3%, max 13% speedup) and SPEC CPU2017 (avg 1.5%, max 4.5% on `638.imagick`) vs. plain LLVM — again a self-chosen corpus in its own paper, no scoreboard. This is the single closest conceptual sibling to OSIL found in this whole survey (SIMD-focused, formally-verified superoptimizer) and is worth a related-work citation, but wrong ISA and a different technique family (SMT synthesis vs. equality saturation).

**Verdict: no external leaderboard exists anywhere in this community, confirmed by direct fetch, not inference.** Everyone self-reports on self-chosen kernels in their own paper — Souper on SPEC CINT2006/llvm-test-suite, STOKE on hand-picked x86 routines, Minotaur on GMP/SPEC CPU2017. An OSIL number has nowhere external to be posted here; the realistic move is citing these as related work, not submitting to a scoreboard.

---

## 8. ARM/NEON-specific benchmark or leaderboard

**Arm Ltd** (arm.com, developer.arm.com): no benchmark leaderboard found anywhere on the official site. "Compiling for Neon with auto-vectorization" and "SVE and Neon coding compared" are how-to documentation, zero comparative numbers, no submission mechanism. Neoverse whitepapers cover microarchitecture analysis methodology, not compiler-vectorization comparison.

**Arm HPC User Group** (`github.com/arm-hpc-user-group`) — alive (ISC24/HiPEAC24/HPCAsia24 tutorials), but its repos are hands-on how-to-compile-and-profile material, not a benchmark leaderboard.

**Apple-specific** — nothing found beyond a decade-old developer-forum thread and independent third-party blog posts (Eclectic Light Company's M1/M3 Pro NEON write-ups). Apple exposes no codegen-quality leaderboard; NEON access for most developers is via Accelerate or hand intrinsics, not a benchmarked compiler path.

**ARM server (Graviton/Ampere/Neoverse)** — no standard public leaderboard. What exists is a scatter of one-off comparisons with no shared registry: Phoronix's Graviton3 compiler-tuning benchmarks (tech journalism, own methodology, not submittable); NVIDIA's `grace-cpu-benchmarking-guide` (vendor documentation with example numbers, not a comparison target); several single-paper academic benchmarks (arXiv:2602.09604, arXiv:2505.09462, arXiv:2504.06813 "Arm-membench") each with its own kernels and no shared registry; and — already known from U7 — arXiv:2502.11906, the TSVC_2-based ARM-vs-x86 vectorization comparison paper, which is a single self-run study with no public repo/submission flow, but is the closest thing to a directly reproducible number (see "Ranked shortlist" below).

**Closest genuine ARM-NEON-specific benchmark artifact:** **Swan** (arXiv:2309.02680, "Vector-Processing for Mobile Devices: Benchmark and Analysis," [Zenodo 8267667](https://zenodo.org/records/8267667)) — a real NEON-targeted suite built from actual mobile workloads (OS kernel routines, browser, audio/video, PDF rendering), with a public "fake ARM Neon library" and cycle-accurate simulator allowing exploration up to 1024-bit vector widths. Application/workload-level design-space exploration (for hypothetical future wider-vector hardware), not a compiler/optimizer comparison target — a single-paper artifact with no ranking mechanism.

**Verdict: genuine ecosystem gap, confirmed rather than merely under-searched.** No ARM/NEON-specific external leaderboard exists — not from Arm Ltd, not from the Arm HPC User Group, not from Apple, not in the Graviton/Ampere/Neoverse server world. There is nowhere for an ARM-NEON vectorization tool to post a number and have it externally checked against others' numbers on the same harness.

---

## 9. PL conference artifact evaluation (PLDI, CGO, ASPLOS, OOPSLA)

Verified directly against PLDI 2026's live track page ([pldi26.sigplan.org/track/pldi-2026-pldi-research-artifacts](https://pldi26.sigplan.org/track/pldi-2026-pldi-research-artifacts)) and CGO's badging pages.

**Process (PLDI 2026, confirmed dates):** artifact submission deadline **2026-03-17**, registration **2026-03-12**; two-phase review — Phase 1 (2026-04-01) tests the Getting Started Guide, Phase 2 (2026-04-14) completes full step-by-step evaluation with an author-response period in between. Artifacts are archived to Zenodo (GitHub alone does not qualify for the badge).

**Badges (ACM standard, used by PLDI/CGO/ASPLOS/OOPSLA alike):** **Functional** (artifact supports all claims made in the paper, sufficiently documented/complete/exercisable); **Reusable** (Functional-plus, well-packaged enough for others to build on); **Results Replicated** (CGO-specific third badge — an independent party reproduced the paper's main results, not necessarily exactly).

**Comparison requirement, confirmed from PLDI's own guidelines:** *"If the artifact claims to outperform a related system... artifacts should include a version of that related system, and instructions for reproducing the numbers used for comparison."* — so AE does force a reproducible, checkable comparison against named baselines when the paper makes a comparative claim, which is exactly the kind of external check the maintainer wants.

**Critical limitation, also confirmed:** submission is **restricted to authors of already-accepted papers** — AE happens after paper acceptance, not as a standalone open-submission venue. It is not a ranking/leaderboard across competing systems; it is an independent-committee reproducibility check on one paper's own claims. There is no path to "post a number to AE" without first writing and getting a paper through the regular PC review process.

**Verdict: the best available real external-validation mechanism found in this entire survey, with the caveat that it is a gate, not a scoreboard.** It provides what nothing else in this document does — an independent third party actually re-running the code and checking the claimed numbers, with a durable, citable badge — but only as the second half of "write a paper, get it accepted, then get it verified," not as an immediately submittable venue.

---

## Ranked shortlist

**Where this system could actually compete or gain external validation, ranked by realism:**

1. **Artifact Evaluation at CGO / PLDI / ASPLOS / OOPSLA (§9).** The one mechanism in this entire survey involving an independent party actually re-running the code. Requires: write a paper (the TSVC_2 `s312` result plus whatever generalization work follows is plausible material — CGO in particular is the most natural venue given its compiler/code-generation focus), get it through PC review, then submit for AE. This is a process on the order of months to a year+, not something to point to today, but it is real and durable once obtained.

2. **Reproduce a published paper's numbers on overlapping kernels and cite directly.** The single best candidate found: **arXiv:2502.11906** (the TSVC_2-based ARM-vs-x86 vectorization comparison paper, already known from U7) used the *exact same corpus* (TSVC_2) on ARM hardware, comparing GCC/Clang/ACfL vectorization rates and speedups. Since OSIL already targets TSVC_2 on ARM, this is the most directly apples-to-apples comparison available anywhere in this survey — running the same paper's methodology against OSIL's optimizer on overlapping kernels and citing both numbers side-by-side in a write-up would be honest, checkable (the paper is public, the corpus is public and already vendored per U7), and requires no new infrastructure. Secondary candidates for the same move: Minotaur's GMP/SPEC-CPU2017-subset numbers and Souper's SPEC-CINT2006/llvm-test-suite numbers (both x86-only, so weaker fit, but same-corpus reproduction is still possible and gives a related-work anchor).

3. **Watch, do not act on: GSO (`gso-bench/gso`).** The only actively-growing (commit 6 weeks old at time of research), real-systems-codebase (llama.cpp, NumPy, Pandas — includes actual SIMD/C/C++/Rust) benchmark found anywhere in this survey. It is currently an LLM-agent-only leaderboard with no submission path for a deterministic tool. If it, or something structurally similar, ever opens a non-agent track, that would be the first genuine fit found in this entire investigation. Worth checking again in 6–12 months, not worth building toward today.

4. **Everything else investigated is out of reach or out of scope**, for the specific, sourced reasons given in sections 1–8 above: GPU-only hard walls (KernelBench/GPU MODE), dead infrastructure (CompilerGym, TenSet, Souper), wrong decision surface (MLGO), wrong problem shape requiring reimplementation in someone else's DSL (Ansor/TVM/Halide), rules-based exclusion of research-grade tools (SPEC CPU2017/2026), wrong language level (EffiBench/Mercury/SWE-Perf/SimdBench-class), and a confirmed, not merely under-searched, absence of any ARM/NEON-specific venue at all.

---

## What would make a claim on this topic dishonest (per this project's evaluation philosophy)

- **Treating "GSO includes llama.cpp" as if GSO could score OSIL today.** It cannot — no non-agent submission path exists. Reporting GSO as a live venue rather than a watch-item would overstate what was actually found.
- **Citing CompilerGym's leaderboard as if it were active.** It is archived; its own leaderboard died in 2022, years before the repo itself was archived in 2026. Any reference to CompilerGym must carry both dates.
- **Presenting Ansor/TVM/Halide numbers as a head-to-head comparison without disclosing the reimplementation requirement.** A number obtained by porting the OSIL kernel into TVM's tensor-expression IR measures something different from what OSIL's own pipeline does; conflating the two would misrepresent what was actually compared.
- **Implying SPEC CPU2017 is unaffordable rather than rules-excluded.** The cost floor (~$550–750 non-member) is not the real barrier — the run rules are. Leading with "too expensive" instead of "structurally excludes research-grade/prototype tools by rule 1.4" would be a less accurate, easier-to-dismiss framing than the sourced one.
- **Calling Artifact Evaluation a "leaderboard."** It is a reproducibility gate on one paper's own claims, not a cross-system ranking. Presenting it as equivalent to a scoreboard would overclaim what AE actually provides.
- **Reporting "no leaderboard found" without disclosing this is a negative claim from a search-limited investigation.** Absence of evidence for a niche external leaderboard is not proof of absence; the confidence section above states this explicitly rather than presenting the gap as logically certain.

---

## Sources

1. KernelBench — [github.com/ScalingIntelligence/KernelBench](https://github.com/ScalingIntelligence/KernelBench); Ouyang et al., arXiv:2502.10517
2. GPU MODE / KernelBot — [github.com/gpu-mode/kernelbot](https://github.com/gpu-mode/kernelbot), [github.com/gpu-mode/reference-kernels](https://github.com/gpu-mode/reference-kernels)
3. CompilerGym — [github.com/facebookresearch/CompilerGym](https://github.com/facebookresearch/CompilerGym); leaderboard — [.../tree/development/leaderboard](https://github.com/facebookresearch/CompilerGym/tree/development/leaderboard); Cummins et al., arXiv:2109.08267 (CGO'22); Meta LLM Compiler — arXiv:2407.02524
4. MLGO — [github.com/google/ml-compiler-opt](https://github.com/google/ml-compiler-opt); [llvm.org/docs/MLGO.html](https://llvm.org/docs/MLGO.html)
5. TenSet — [github.com/uwsampl/tenset](https://github.com/uwsampl/tenset)
6. Ansor — Zheng et al., OSDI 2020, [usenix.org/system/files/osdi20-zheng.pdf](https://www.usenix.org/system/files/osdi20-zheng.pdf); citing paper arXiv:2406.20037
7. Halide autoscheduler — Adams et al. 2019, [halide-lang.org/papers/halide_autoscheduler_2019.pdf](https://halide-lang.org/papers/halide_autoscheduler_2019.pdf); [github.com/halide/Halide](https://github.com/halide/Halide)
8. TVM — [github.com/apache/tvm](https://github.com/apache/tvm); [discuss.tvm.apache.org/t/efforts-on-benchmarking-for-tvm/4998](https://discuss.tvm.apache.org/t/efforts-on-benchmarking-for-tvm/4998)
9. SPEC CPU pricing — [spec.org/cpu2017/press/academicpricing.html](https://www.spec.org/cpu2017/press/academicpricing.html); submission process/fees — [spec.org/spec/submitting_results/](https://www.spec.org/spec/submitting_results/); run rules — [spec.org/cpu2017/Docs/runrules.html](https://www.spec.org/cpu2017/Docs/runrules.html); CPU2026 — [spec.org/cpu2026/](https://www.spec.org/cpu2026/)
10. EffiBench — [github.com/huangd1999/EffiBench](https://github.com/huangd1999/EffiBench); EffiBench-X — [github.com/EffiBench/EffiBench-X](https://github.com/EffiBench/EffiBench-X), arXiv:2505.13004; Mercury — [github.com/Elfsong/Mercury](https://github.com/Elfsong/Mercury), arXiv:2402.07844; SWE-Perf — [github.com/SWE-Perf/SWE-Perf](https://github.com/SWE-Perf/SWE-Perf), arXiv:2507.12415
11. GSO — [github.com/gso-bench/gso](https://github.com/gso-bench/gso), arXiv:2505.23671, leaderboard [livecodebench.github.io/gso.html](https://livecodebench.github.io/gso.html)
12. SimdBench — arXiv:2507.15224; LLaMeSIMD — [github.com/VectorCamp/LLaMeSIMD](https://github.com/VectorCamp/LLaMeSIMD); VecIntrinBench — arXiv:2511.18867
13. EGRAPHS workshop — [egraphs.org](https://egraphs.org); [pldi25.sigplan.org/home/egraphs-2025](https://pldi25.sigplan.org/home/egraphs-2025); [pldi26.sigplan.org/home/egraphs-2026](https://pldi26.sigplan.org/home/egraphs-2026); community list — [github.com/philzook58/awesome-egraphs](https://github.com/philzook58/awesome-egraphs)
14. Souper — [github.com/google/souper](https://github.com/google/souper), arXiv:1711.04422
15. STOKE — [github.com/StanfordPL/stoke](https://github.com/StanfordPL/stoke)
16. Ruler — [github.com/uwplse/ruler](https://github.com/uwplse/ruler); chompy/Enumo successor — [github.com/ninehusky/chompy](https://github.com/ninehusky/chompy)
17. extraction-gym — [github.com/egraphs-good/extraction-gym](https://github.com/egraphs-good/extraction-gym)
18. Minotaur — [github.com/minotaur-toolkit/minotaur](https://github.com/minotaur-toolkit/minotaur), arXiv:2306.00229 (OOPSLA'24)
19. Arm developer docs — [developer.arm.com/documentation/102525/latest/](https://developer.arm.com/documentation/102525/latest/); Arm HPC User Group — [github.com/arm-hpc-user-group](https://github.com/arm-hpc-user-group)
20. Swan benchmark — arXiv:2309.02680, [zenodo.org/records/8267667](https://zenodo.org/records/8267667)
21. TSVC_2-based ARM-vs-x86 vectorization comparison — arXiv:2502.11906 (already sourced in U7; reused here as the ranked-shortlist #2 recommendation)
22. PLDI 2026 Artifact Evaluation — [pldi26.sigplan.org/track/pldi-2026-pldi-research-artifacts](https://pldi26.sigplan.org/track/pldi-2026-pldi-research-artifacts); CGO artifact badging — [2025.cgo.org/track/cgo-2025-artifact-evaluation](https://2025.cgo.org/track/cgo-2025-artifact-evaluation)
23. Papers with Code shutdown (ruled out as a candidate) — shut down 2025-07-24, redirects to Hugging Face `pwc-archive`
24. LLVM compile-time tracker (ruled out — wrong metric, measures compiler build speed not generated-code performance) — [llvm-compile-time-tracker.com](https://llvm-compile-time-tracker.com/about.php), [github.com/nikic/llvm-compile-time-tracker](https://github.com/nikic/llvm-compile-time-tracker)
25. "Are We Fast Yet" (ruled out — dynamic-language runtime benchmark, wrong domain) — [github.com/smarr/are-we-fast-yet](https://github.com/smarr/are-we-fast-yet)

---

**Epistemological note.** This document's central claim — "there is no good external leaderboard for this niche" — is a negative claim, and negative claims from search-based investigation can never be proven exhaustive. The confidence assigned (HIGH on individual candidates' maintenance/license status; MEDIUM on the community-wide "no venue exists" claims) reflects that distinction: each individual candidate's status (archived, dead, alive, wrong-shaped) is verified against a primary source (a fetched commit date, an archive banner, a rules document) and is about as solid as evidence gets in this domain; the aggregate conclusion that *nothing else exists* rests on four independent, convergent search efforts rather than a proof, and should be revisited if the ecosystem changes. Valid as of 2026-08-22. Re-run the archive/commit-date checks in §§2, 3, 4, 7 before citing them in a paper, since "is it still archived / still dead" is exactly the kind of fact that can silently go stale, and this document's own evidence hierarchy (§ Method) treats a live-fetched date as stronger evidence than any claim in this document itself once enough time has passed.
