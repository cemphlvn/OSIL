# Self-Description Bootstrap — writing the system in `.oaas` + `.flow`

> PLAN (not yet executed). How the repo's own machinery gets written in OAAS's two
> document kinds, so the existing toolchain becomes the language's first living use
> cases — and G4's first golden diagram is a diagram of OAAS itself. (2026-08-12)

## The move

OAAS was born describing ML compute graphs (use case #1: Attention, MatMul — the
transcript). The repo meanwhile grew real machinery: a validator, a round-trip
harness, a policy layer, skills. Plan: describe that machinery *in OAAS* —
vocabulary in `.oaas`, pipelines in `.flow` — which:

1. **dogfoods the grammar** against a domain it wasn't born for (toolchain/agentic
   pipelines) — every place it can't express reality files a GAP, never a hack;
2. **rejuvenates a new use case**: `profiles/domain/agent/` stops being
   policy-only and becomes a real domain — OAAS as a language for describing
   *engineering loops*, not just compute graphs. Use case #2, built entirely from
   assets we already have;
3. **feeds every existing loop at once**: corpus (closes all 6 remaining
   alternative gaps), curriculum (a "self-hosting" path), and G4 (the first
   layout goldens are the repo's own pipeline diagrams).

The through-line: G2 proved OAAS can express the repo's *policy* (actors). This
phase proves it can express the repo's *behavior* (flows). Together: full
self-description.

## Phase 0 — vocabulary in `.oaas` (grammar v0.2, UNCHANGED)

New file `profiles/domain/agent/toolchain.oaas` + corpus fixtures. Written with
today's grammar only — the falsifiable point of this phase is *current
expressiveness*.

```
profile domain.toolchain {
    version = 0
}

invariant Deterministic
invariant ZeroDiff
invariant PixelDiffNeverGates          // U4's verdict, as a named invariant

concept Validate {
    equivalent_under { grammar_version = 2 }
    to { oaas_check }
}

operator render {
    goal: deterministic_svg
    renderer_version == 1              // closes rel_op:==
    render_budget > 5ms                // closes rel_op:>  (quantity)
    fonts = "PinnedMono"               // closes literal:string
}

projection Identity {
    from OAAS-NATIVE
    preserve everything
}

preserves {
    semantics
    visual_layout                      // total contract: no may_lose block
}
```

Three tiny algebra fixtures ride along to finish the expression alternatives:
`(a + b) - b <=> a` (add_op:-), `x / 1 <=> x` (mul_op:/), `x >> 0 <=> x`
(mul_op:>>), each guarded `numeric_semantics = integer`.

**Gate P0: everything above parses under grammar v0.2 as-is; alternative
coverage reaches 34/34.** (io_decl:output already closed by 011.)

## Phase 1 — pipelines in `.flow` (grammar v0.2, gaps filed not forced)

The three real pipelines become flow documents (also corpus fixtures):

**The check pipeline (G1 loop):**
```
use domain.toolchain

input corpus : Files<oaas>[N]
input grammar : Grammar<ebnf>[1]
output report : Report<coverage>[1]

corpus, grammar -> toolchain::Parse@2 -> ast
ast -> toolchain::Coverage@2 -> report
```
Note the quiet dogfood win: the type production (`identifier < identifier > [dims]`)
was born for `Tensor<f32>[N,D]` and expresses `Files<oaas>[N]` unchanged —
generality we get for free, worth stating in the report.

**The round-trip pipeline (G3 loop):**
```
use domain.toolchain

input case : Generator<py>[1]
const contract : Contract<oaas>[1]     // the preservation contract is a CONSTANT
output score : Score<preservation>[1]

case -> toolchain::MakeModel@1 -> model
model -> toolchain::ExportFlow@1 -> image
image -> toolchain::ImportModel@1 -> rebuilt
model, rebuilt, contract -> toolchain::Verify@1 -> score
```
v0 honesty: `ExportFlow` actually produces TWO things (text + passthrough); v0
bundles them as one `image` artifact since they travel together. But the real
gap stands and is not toolchain-specific — **ONNX itself has multi-output ops
(Split, Dropout), so the suite will hit this wall as cases grow.**
→ **File GAP-4 (multi-output edges) and pin it with an expected-fail fixture**
(`// EXPECTED-FAIL: GAP-4` on a `-> Y, Z` edge). Same mechanism that guarded G2.

**The render pipeline (G4 loop, the target):**
```
use domain.toolchain

input flowdoc : Document<flow>[1]
const golden : Layout<data>[1]         // goldens are constants of the flow
output verdict : Verdict<bool_>[1]

flowdoc -> toolchain::ParseLayout@1 -> layout
layout, golden -> toolchain::DataDiff@1 -> verdict
layout -> toolchain::RenderSVG@1 -> svg
```

**Gate P1: both expressible pipelines parse unchanged; GAP-4 filed + pinned;
fixtures 012–01x land with provenance headers.**

## Phase 2 — the layout block (grammar v0.2 → v0.3, RATIFICATION REQUIRED)

Layout lives **in the same document** (BPMNDI lesson: embed, don't sidecar) and
in **the same artifact class** (U4 rec 8: our artifact class is the OAAS text
grammar itself, validated by the same `just check` toolchain — not a JSON
sidecar). Sketch:

```
layout {
    node corpus  [0, 0, 160, 48]
    node grammar [0, 96, 160, 48]
    node ast     [240, 48, 120, 48]
    node report  [440, 48, 140, 48] z = 2
    edge corpus -> ast waypoints [(160,24) (200,24) (200,72) (240,72)]
    label corpus [8, -20, 90, 16]
    viewport [0, 0, 1.0]               // stored, NON-NORMATIVE, excluded from gate
}
```

Field set per U4 (all six converged requirements): node bounds keyed by stable
id · edge waypoints stored, never recomputed · labels as independently-bounded
objects · `collapsed` for composites (when composites exist) · explicit sparse
integer `z` · viewport optional/non-normative.

**Decisions this phase needs (D1–D3, recommendations attached):**
- **D1 — coordinate convention** (U4 flagged: every format studied is silent;
  we must decide explicitly). *Recommend:* top-left origin, +y down, abstract
  px-like units. Recorded in spec/visual.md + ADR.
- **D2 — edge identity.** Nodes have names; edges don't, and layout must anchor
  to them (BPMNDI anchors everything by id). *Recommend v0:* reference by
  `src -> dst` pair (unique in v0 flows); optional edge names become a later
  gap if flows ever need parallel edges.
- **D3 — GAP-4 syntax** (multi-output), designed but possibly deferred:
  *recommend* `-> (Y, Z)` when ratified; pinning fixture holds until then.

**Gate P2: grammar v0.3 parses fixture 015 (render pipeline WITH layout block);
XPASS guard fires and is resolved through the marker-flip ritual; ADR-0006
records D1–D3.**

## Phase 3 — renderer + the G4 loop proper

- `tools/oaas_render.py`: deterministic SVG. Determinism by construction, not
  mitigation: fixed-metrics monospace text (char-count × constant), no system
  font measurement — deletes U4's #1 flakiness source instead of pinning it.
- `tools/render_check.py` (or extend oaas_check): the three-tier verdict —
  layout-data structural diff = zero-tolerance gate; SVG DOM diff = advisory;
  pixel = never.
- Goldens: `conformance/golden-render/015.layout.golden` (+ `.svg` advisory).
- `improvable/render-verify` activates (body already carries the U4-updated
  procedure); justfile gains `render`; `just test` = check + roundtrip + render.

**Gate P3 (= G4): serialize → parse → re-render on fixture 015 yields
layout-data diff = 0; the SVG advisory is byte-stable across two runs.
First golden = OAAS rendering its own render pipeline — conformance test #0
extended to the visual dimension ("test #0v").**

## Why this ordering is the bootstrap

Each phase consumes only what already exists and produces what the next needs:
P0/P1 need nothing new and produce the fixtures; P2 needs those fixtures to have
something worth laying out; P3 needs P2's layout data to have something to
render and diff. And every phase feeds loops that already run: corpus coverage
(alt 34/34 at P0), the XPASS ritual (P2), the matrix discipline (P3's goldens).

## Standing observations

- The curriculum gains a second path (`self-hosting`: 010 → 012 → 013 → 015)
  ordered by "how the repo describes itself" — pure view, zero new content.
- Horizon (not this plan): a described pipeline is one step from an executable
  one — a flow runner that *executes* toolchain flows is the wizard
  ("configuration compression") pointed at the repo itself. Deliberately out of
  scope until G4 lands.
- ASSUMPTION: single-output bundling in 013 is acceptable v0 semantics; GAP-4
  ratification revisits.
