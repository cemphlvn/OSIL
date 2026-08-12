# Idea-Coverage Ledger — REPO vs IDEA, calibrated

> Source: maintainer's repo-vs-idea bar chart (2026-08-12), folded into the
> production-quality assessment as its missing axis. Quality × coverage gives
> the 2-D map; this file is the coverage side, calibrated against evidence
> and kept as a living ledger. Strategic metric #8: this vector.

| Dimension | Chart | Calibrated | Evidence & correction | Home today | Gate-shaped next step |
|---|---|---|---|---|---|
| Language | ~85% | **~65%** | grammar v0.5 covers the transcript's snippets, but the idea's language includes cross-layer RELATIONS (`implementedBy`, `requires`, `availableOn`, `IS-A` — transcript §5), information flow, approximation tolerance: none expressible. Chart over-credits | `grammar/` | file GAP-6 (relation constructs) + pin |
| Conformance | ≈100% | **>100% — SURPLUS** | the idea contained almost no conformance machinery; rituals, rejections, matrix, boundary obligation, promote exits are repo inventions. The chart's frame (idea ⊇ repo) hides that the delta runs both directions | `conformance/`, `spec/conformance.md` | — (export the surplus: it is the LF story) |
| Visual semantics | ~85% | **~70%** | layout normative, golden loop, `just draw` — but the founding phrase "visual DSL where I can CODE architectures" implies authoring, and we render, never author | `spec/visual.md`, `tools/render_check.py` | auto-layout proposer (deferred by design) |
| ONNX interop | ~60% | **~40%** | registered, preservation 4/4 — over 3 of ~200 ops; sentinels dormant | triad via `registry/entries/onnx.yaml` | suite growth + light the drift schedule |
| Ontology federation | ~10% | **~10%** | correct: BFO applied as *method* (definitions), zero federation *machinery*; profiles are empty stubs | `profiles/ontology/*` | research unknown (federation semantics) + GAP-6 relations are prerequisite |
| E-graph optimization | ~10% | **~15%** | slightly under-credited: the INPUT side exists (equivalences, guards, regimes — ADR-0007 built the rule-set-by-regime grouping egg needs); the projection itself absent | corpus 003/009/013–015/020, `spec/interop/egraph.md` | U5 (egg vs egglog) + adapter behind resolver |
| Semantic compression | ~25% | **~25%** | correct and pointed: the measurement lens exists (ladder, covering set, baselines, scout), the ENGINE (wizard, expansion) does not — and this is the idea's LARGEST bar | `tools/compression_scan.py` | wizard behind resolver |
| Config resolution | 0 | **~60% (G12)** | rungs 1–2 done: rate 18/18=1.00, namespace binding normative, registry oracle live, pin-consistency loop; rung 3 (types/shapes) + vocabulary cross-refs open | `tools/oaas_resolve.py`, `spec/execution.md` §1, `conformance/resolution/` | rung 3; then e-graph/wizard/compiler unblock |
| Compiler | 0 | **0** | semantic optimization space, invariant-guarded rewrite engine: unrealized | none | behind resolver + e-graph |
| ABI/binary contract | 0 | **0 — and UNHOMED** | the chart names a dimension the tree never carved: no subtree, no gap pin, no research unknown. Yet the security heritage (ConstantTime, "show every lowering where constant-time may be lost") only cashes out at the binary level | **none — structural hole** | carve the home (spec/interop chapter + profile) + queue the research unknown |

## Dependency order of the zeros

```
config resolution (gateway)
   ├─> e-graph projection        ├─> compression engine (wizard)
   └─> compiler ──> ABI/binary contract
ontology federation — parallel track, blocked on GAP-6 relations, not on resolution
```

## The two discoveries this chart forced

1. **ABI/binary contract is unhomed** — first structural hole found since the
   intake passes: a dimension of the idea with no folder, no gap, no unknown.
   The transcript's lowering story (metadata surviving StableHLO→MLIR→LLVM,
   constant-time guarantees at the binary boundary) implies a preservation
   contract whose `preserves{}` includes timing behavior — the security
   origin of this whole project becomes real exactly here.
2. **Cross-layer relations are inexpressible** (GAP-6 candidate, unfiled):
   `Attention implementedBy FlashAttention requires SharedMemory availableOn
   GPU_X` — the transcript's vertical-optimization chains cannot be written
   in v0.5. Three idea-dimensions (federation, e-graph enrichment, compiler)
   quietly depend on it.
