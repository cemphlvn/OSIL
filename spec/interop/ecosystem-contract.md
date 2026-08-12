# Ecosystem Contract (general form)

Status: draft-0. This document defines what EVERY ecosystem profile
(`profiles/ecosystem/<x>/`) must provide. Instances: `onnx.md`, `egraph.md`.

## 1. Sovereignty

An ecosystem profile references native identities (`onnx::MatMul@13`,
`egg::RewriteSet@name`, `mlir::linalg.matmul`) and MUST NOT redefine their
semantics. OAAS supplies architectural context around them; the upstream
specification remains the sole normative source.

## 2. Required artifacts per ecosystem profile

| Artifact | Purpose | Checked by |
|---|---|---|
| `PROFILE.md` | prose: what the ecosystem contributes (IR? search? execution?) | univocity-lint |
| `VERSIONS` | pinned upstream versions (e.g. `ir_version=11`, `opset ai.onnx=24`) | drift-watch |
| `CONTRACT.oaas` | machine-readable preservation contract for the projection | matrix-refresh / round-trip evals |

## 3. Preservation contracts

Every projection declares:

```
preserves { <property> ... }    // guaranteed to survive the round trip
may_lose  { <property> ... }    // explicitly sacrificial
```

Rules:
- Interoperability status is per-property, not binary. The compatibility matrix
  (`conformance/matrix/`) records verification per (spec, adapter, upstream) cell.
- **Opaque passthrough**: fields the adapter does not understand MUST survive
  round-trip as opaque namespaced annotations — never deleted.
- The **identity projection** (OAAS native serialization) is the unique projection
  with an empty `may_lose` set. `visual_layout` is preservable there and only
  optional elsewhere.

## 4. Projection dimension declarations

Each projection states which semantic dimension it preserves, because ecosystems
differ in kind, not just in format:

| Ecosystem | Contributes | Projection preserves |
|---|---|---|
| ONNX | executable graph interchange | computation |
| egg / e-graphs | equivalence-space search | equivalence (guards included) |
| MLIR | lowering toward hardware | execution |
| (identity) | OAAS native | everything, incl. visual layout |

## 5. Drift obligations

Foreign ground truth moves on its own schedule. Each ecosystem profile must be
watchable: `VERSIONS` pins + a drift-watch loop that (a) detects upstream releases,
(b) marks affected matrix cells stale, (c) proposes pin bumps — never silently
rewrites contracts.
