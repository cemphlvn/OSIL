# ADR-0001: Monorepo cut along version-cadence boundaries (fission-ready)
Date: 2026-08-12 · Status: accepted (revisit at G5, informed by research U3)
Context: subtrees have heterogeneous cadences (spec: consensus-slow; ecosystem
profiles: upstream-driven; registry: fast; improvable/: feedback-speed) and four
ground-truth classes (self/shared/foreign/academic) + one empirical (improvable/).
Decision: single repo at v0; every top-level dir is REPO-SHAPED (own README card,
version stream, loops, policy) so extraction later is mechanical.
Consequence: real conformance is a 3-D matrix (spec x adapter x upstream) kept as
a first-class artifact; per-subtree policy is expressible; fission is cheap.

Addendum 2026-08-12 (U3 landed): WebAssembly runs fission the OPPOSITE
direction (~25 per-proposal repos merged inward once stable). Monorepo stance
RETAINED as an explicit decision, not an inherited assumption. U3 also finds
one-entry-per-file well-validated for corpora, only weakly for registries
(ONNX registry is category-batched code) — registry layout marked revisitable.
