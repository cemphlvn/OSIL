# Conformance & Testing

Status: draft-0. Defines the system's own testing metric and suite organization.
The metric is not borrowed from generic testing practice — it is derived from the
spec's own vocabulary: preservation contracts (spec/interop/ecosystem-contract.md).

## 1. Definitions

**round-trip test** — a test (genus) that carries a native ecosystem artifact
through a projection into OAAS and back, then compares original and
reconstruction field-by-field against the projection's preservation contract
(differentia).

**preservation score** — a ratio (genus): the number of a contract's `preserves`
fields mechanically verified on a round trip, divided by the number declared
(differentia). `may_lose` fields are excluded by definition — sacrificing them
costs nothing, which is what declaring them means. A field may count as verified
ONLY on mechanical evidence; inference or inspection-by-eye never counts.

**opaque passthrough** — the transport (genus) by which native data the OAAS
text does not model survives a round trip as annotations attached to the
projection image (differentia). Passthrough survival is contract-honest: the
contract requires fields to *survive*, not to be re-expressed in OAAS syntax.

**matrix cell** — a record (genus) binding one (spec version, adapter, upstream
version) triple to a status, a preservation score, per-field results, the case
list exercised, and a check timestamp (differentia). Lifecycle:
`unverified → (stale ↔) pass | fail`. Only a round-trip run may move a cell to
`pass`; only drift-watch or a failing run may move it to `stale`/`fail`.

## 2. Gate semantics

- **G3-class gates** (per ecosystem): preservation score = 1.0 over the
  ecosystem's suite, with the suite's scope stated in the gate record. A perfect
  score over a narrow suite is a narrow claim — suites grow monotonically, and
  the score is always reported together with the case count.
- **Negative-fixture taxonomy** (two classes, two homes, two lifecycles):
  - **Temporal pins** — deliberately-open gaps, pinned in `conformance/corpus/`
    by a `// EXPECTED-FAIL: <gap-id>` header (syntactic marker at line start;
    prose mentions do not trigger). Parsing success fails the build (XPASS)
    until the marker is removed by ratified change — the XPASS ritual. Pins
    make the *future* falsifiable. A pin's lifecycle has THREE ratified exits:
    **flip** (the XPASS ritual — the construct becomes accepted), **delete**
    (the pinned idea is abandoned), or **promote** — the pin migrates to
    `conformance/rejections/` as a MUST-FAIL when the decision makes the
    construct a permanent refusal. Promotion preserves the boundary that
    deletion would erase (anticipated case: 021/GAP-2 under an `=`-only
    ratification — the colon form would become a univocity refusal, not a
    forgotten experiment).
  - **Permanent rejections** — normative refusals, pinned in
    `conformance/rejections/` by a `// MUST-FAIL: <rule>` header. These NEVER
    flip: an XPASS is always a parser/spec regression. Rejections make the
    *boundaries* falsifiable — without them a parser that accepts everything
    would pass the positive suite. Selection principle: one fixture per
    normative refusal, anchored to its rule/ADR; arbitrary syntax errors are
    noise, not rejections.
  - **Boundary obligation** (G10): an XPASS ritual that ENLARGES the grammar
    must ship, in the same ratified change, at least one MUST-FAIL rejection
    pinning the new construct's boundary — or an explicit "no new boundary"
    declaration with justification. That declaration is legitimate only for
    restriction-removals whose edges are already pinned, or for
    implementation-defect flips where the language itself did not change.
    Rationale: a ritual moves the ACCEPTANCE frontier; rejections re-survey
    the REFUSAL frontier; a language change is complete only when both
    frontiers are re-mapped.
  - **Ritual-XPASS vs alarm-XPASS**: an XPASS inside a ratified closure is a
    ritual step. An XPASS anywhere else — a rejection fixture parsing, a pin
    parsing outside a ratified change — is a regression alarm and is never
    legitimate.

## 3. Suite organization

One case per file, as **generator code**, not stored binaries — adopting the
pattern research U3 verified in ONNX itself (`onnx/backend/test/case/node/`,
one generator per operator):

```
conformance/interop/<ecosystem>/
  README.md          suite card (scope, how to run, LF registration pointer)
  cases/<case>.py    def make_model() -> native artifact (deterministic)
```

Rationale: generators are diffable, reviewable, and deterministic; binaries are
none of those. The harness (`tools/onnx_roundtrip.py` for ONNX) builds each
case, round-trips it, verifies per-contract-field, writes the matrix cell and a
report under `docs/reports/`.

## 4. Compression metrics (sibling of the preservation score)

**compression ladder** — a measurement scale (genus) that orders size metrics
by semantic rung: bytes → tokens → productions → concepts (differentia). A
compression claim MUST name its rung. Byte ratios are the crudest rung and are
never the headline claim — the founding text's own caveat ("not mainly fewer
bytes") is normative here.

**covering set** — a fixture subset (genus) that fires every grammar
production (differentia). The corpus's "books": the same minimal-covering
pattern as a curriculum spine, computed by `tools/compression_scan.py`.

**naming opportunity** — a recurring corpus pattern (genus) not reducible to
one production or declared concept (differentia). The name-direction output of
representational compression; always PROPOSE-ONLY (vocabulary and grammar
changes stay constitutional).

Baselines live in `conformance/compression/baselines.yaml`, agent-maintained
like matrix cells; the regression a baseline guards against is representations
silently getting less compact.

## 5. Registration

An ecosystem is a REGISTERED interop when its `registry/entries/<eco>.yaml`
carries an `interop` binding naming its suite and its machine-readable contract.
Registration is what turns a described ecosystem into a tested one — the
registry stops being descriptive data and becomes the index of enforceable
claims.
