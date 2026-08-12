# ADR-0001: Monorepo cut along version-cadence boundaries (fission-ready)
Date: 2026-08-12 · Status: accepted (revisit at G5, informed by research U3)
Context: subtrees have heterogeneous cadences (spec: consensus-slow; ecosystem
profiles: upstream-driven; registry: fast; improvable/: feedback-speed) and four
ground-truth classes (self/shared/foreign/academic) + one empirical (improvable/).
Decision: single repo at v0; every top-level dir is REPO-SHAPED (own README card,
version stream, loops, policy) so extraction later is mechanical.
Consequence: real conformance is a 3-D matrix (spec x adapter x upstream) kept as
a first-class artifact; per-subtree policy is expressible; fission is cheap.
