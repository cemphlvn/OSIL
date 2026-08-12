# Compression Grounding — inventory, missing homes, tour-1 nuance

> Grounding for the compression-ecosystem-interop question (2026-08-12).
> Protocol: 2-tour paste; this file records the structural inventory and the
> tour-1 nuance. Tour 2 pending; the size computation follows it.

## Inventory (honest, post-pycache-cleanup)

| Subtree | Bytes | Files | Note |
|---|---|---|---|
| docs/ | 206,417 | 23 | analysis outweighs system ~5:1 |
| tools/ | 50,487 | 4 | 3 harnesses + card |
| improvable/ | 17,342 | 20 | 6 skills |
| spec/ | 15,247 | 11 | |
| conformance/ | 15,375 | 27 | 19 corpus fixtures = 6,879 bytes |
| grammar/ | 8,832 | 3 | 59 productions |
| profiles/ | 7,330 | 21 | |
| registry/ | 2,506 | 3 | |
| curriculum/ | 2,232 | 3 | 2 paths |
| **core** (spec+grammar+corpus+profiles+registry+curriculum) | **43,026** | | the system's semantic identity is ~43KB |

Hygiene fixed during grounding: `__pycache__` had been committed (inflated
tools/ by 43KB); now ignored and untracked.

## Missing relative to our own plans + the transcript's pillars

1. **Compression has NO home — the transcript's third pillar is homeless.**
   Preservation got spec §, contract files, harness, matrix. Compression
   (representational / configuration / search-space) has: nothing. Proposed
   fit, mirroring the preservation pattern exactly:
   - `spec/conformance.md` gains the metric definition (compression ratio as
     the sibling of preservation score);
   - `conformance/compression/baselines.yaml` — tracked ratios per case,
     agent-maintained like matrix cells (regression loop: vocabulary changes
     must not silently make representations less compact);
   - `tools/compression_scan.py` — the measurement + detection mechanism;
   - `improvable/compression-scout/` — the skill (propose-only; grammar stays
     constitutional).
2. `profiles/ecosystem/{egg,mlir,wasm}`: no CONTRACT.oaas, no interop suite —
   ONNX is the only registered (tested) ecosystem. egg blocked on U5.
3. `profiles/ontology/*`: content-less; citation-fidelity loop dormant.
4. `spec/TERMS.md` absent — univocity-lint has never run as an agent (GAP-2
   sits in its queue).
5. `tools/`: no wizard (`oaas add`) — configuration compression has no engine.
6. No CI runner config — every loop is manual via `just`. (Deliberate so far;
   listed for honesty.)

## TOUR-1 NUANCE (on the record)

**The founding "this" of OAAS was already a compression artifact.** In this
transcript variant, what got converted to a visual DSL was not a degree
program but a *compressed curriculum*: an undergraduate CS education
quotiented into 4 semantic layers (formal / computational / systems /
adversarial), one canonical realization picked per layer (a book), ordered
into a spine — explicitly called "the entire undergraduate compression."
That is search-space compression (thousands of books → 4 layers → 1 pick
each) plus configuration compression (curriculum → reading order), performed
on education instead of computation.

Consequences:

1. **`curriculum/` is not adjacent to the compression substrate — it IS the
   original compression use case.** A learning path is a minimal covering
   selection over a pool, ordered by pedagogy. The book spine and
   `paths/*.yaml` are the same artifact type.
2. **We already own the quotient map.** Production-coverage-per-fixture
   (which the validator computes) is exactly the layer structure: productions
   = semantic layers, fixtures = books, path = spine. So "find the corpus's
   4 books" is computable today: minimal set cover over the
   fixture → productions matrix.
3. **The detection mechanism gets its two directions from this duality:**
   - **Cover direction** (curriculum compression): set-cover → minimal
     covering path; redundancy profile (fixtures per production) shows where
     the corpus is fat and where it is thin.
   - **Name direction** (representational compression): mine recurring
     patterns across fixtures that are NOT reducible to one production or
     declared concept → each recurrence is an unnamed compression
     opportunity → propose a concept (domain vocabulary) or grammar sugar.
     Propose-only; grammar changes remain constitutional.
   - Third, already-measurable axis (interop): native bytes vs projection
     bytes per ONNX case, passthrough split out honestly.

## Pending

Tour 2 of the paste; then build the detector + measure "current size" through
the compression lens. ASSUMPTION to check in tour 2: whether the second tour
changes the origin story again or deepens the compression framing.
