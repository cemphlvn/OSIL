# OAAS

**A semantic interoperability architecture layer.**

[![gates](https://github.com/cemphlvn/oaas/actions/workflows/gates.yml/badge.svg)](https://github.com/cemphlvn/oaas/actions/workflows/gates.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: draft-0](https://img.shields.io/badge/spec-draft--0-orange.svg)](docs/GATES.md)

OAAS is an open specification — a grammar, a conformance suite, and reference
tooling — for describing computational architectures by their **declared
meaning**, so that toolchains can exchange, verify, and optimize them across
ecosystem boundaries without losing what they were intended to be.

**Contents** · [Why](#why) · [The language](#the-language-in-three-fragments) ·
[What works today](#what-works-today) · [Getting started](#getting-started) ·
[Layout](#repository-layout) · [Conformance](#conformance-and-governance) ·
[Roadmap](#roadmap) · [Contributing](#contributing) · [Naming](#a-note-on-the-name) ·
[License](#license)

## Why

Interchange formats move bytes; what gets lost between ecosystems is *meaning* —
intent, invariants, equivalence conditions, security requirements, even diagram
layout. OAAS takes three positions on that problem:

- **Interoperability is declared preservation, not "works with X."** Every
  connection to an external ecosystem is a *projection* governed by a
  machine-readable *preservation contract* stating exactly which semantic
  properties survive and which may be lost — then a harness scores it.
- **Ecosystems stay sovereign.** OAAS never redefines the semantics of ONNX,
  egglog, MLIR, or WASM. `onnx::MatMul@13` means what ONNX says it means, at
  that version, always. OAAS contributes shared architectural context around
  native identities — coordination, not absorption.
- **Meaning is stratified.** An architecture states *what it is* (OAAS-SIR)
  separately from *how it is computed* (OAAS-CIR), connected by *realization* —
  and the space of valid realizations under declared constraints and invariants
  is the object compilation should search. Security requirements (constant-time
  behavior, information flow, category-level crypto requirements) are
  first-class semantic properties in that search, not annotations.

Visual layout is content here, not decoration: the native serialization is the
*identity projection*, contractually required to preserve everything — diagrams
included.

## The language, in three fragments

Two document kinds: `.oaas` declares vocabulary (the general); `.flow` composes
dataflow (the particular). A flow, pinned to real ONNX semantics:

```
use ecosystem.onnx

input X : Tensor<f32>[N,4]
const W : Tensor<f32>[4,8]
output Y : Tensor<f32>[N,8]

X, W -> onnx::MatMul@13 -> Y
```

An equivalence, valid only in its declared numeric regime (associativity
silently fails under floating point — the guard is the point):

```
equivalence add_associativity {
    (a + b) + c
    <=>
    a + (b + c)

    guards {
        regime = ExactArithmetic
    }
}
```

A preservation contract — what the ONNX projection guarantees, and what it
honestly gives up:

```
projection ONNX {
    from OAAS-CIR
    preserve computation
}

preserves {
    tensor_types
    operator_versions
    graph_topology
    constants
}

may_lose {
    ontology_annotations
    visual_layout
}
```

More: the full corpus in [`conformance/corpus/`](conformance/corpus/), guided
paths in [`curriculum/paths/`](curriculum/paths/), the spec in
[`spec/`](spec/).

## What works today

Grammar **v0.6**, spec **draft-0** (pre-release; nothing is normative yet).
Every capability below is verified by a command, and CI runs the same suite on
every push:

| Capability | Verify with |
|---|---|
| Grammar + corpus validation (dual coverage; negative fixtures) | `just check` |
| Reference resolution — namespaces, strata, dataflow wiring | `just resolve` |
| ONNX round-trip with per-field preservation score | `just roundtrip` |
| Equivalence projection into egglog, scored | `just egraph` |
| Pipeline commutation analysis (the toolchain tests itself) | `just stages` |
| Visual identity projection — golden layout gate, SVG render | `just render` · `just draw FILE` |
| Governed vocabulary views (diagrams derived from declarations) | `just views` |
| Policy agreement — self-hosted policy vs. the agent skill layer | `just policy` |
| Compression-ladder metrics | `just compress` |

`just test` runs the full gatekeeper. Expected tail of a healthy run:

```
resolution rate: 18/18 = 1.00 (north-star metric #1; gate requires 1.00)
Resolution contract satisfied: every reference finds its universal.
```

## Getting started

**Prerequisites**: Python 3 (core tools are dependency-free stdlib),
[`just`](https://github.com/casey/just), and [`uv`](https://docs.astral.sh/uv/)
(supplies `onnx`/`egglog` ephemerally for the interop suites).

```sh
git clone https://github.com/cemphlvn/oaas.git
cd oaas
just            # list all commands
just check      # validate grammar + corpus (no dependencies needed)
just test       # full conformance suite (uses uv for onnx/egglog)
just draw conformance/corpus/019-toolchain-render.flow   # render a flow to SVG
```

## Repository layout

Every top-level directory carries its own README card stating its ground-truth
owner, change cadence, and policy:

```
spec/          normative prose: core, conformance, execution, visual, interop contracts
grammar/       the EBNF (v0.6) + gap ledger — single source for the validator
conformance/   corpus · rejections · resolution refusals · golden renders · matrix · interop suites
profiles/      ecosystem (ONNX, egglog, MLIR, WASM) · ontology (BFO/DOLCE/UFO) · domain
registry/      machine-readable ecosystem manifests (the resolver's oracle)
curriculum/    learning paths — ordered views over the corpus
improvable/    the agent skill layer: procedures, evals, changelogs
tools/         reference validator, resolver, harnesses, renderers (stdlib Python)
docs/          gate ledger · ADRs · dated reports · research memos · design docs
```

## Conformance and governance

Development proceeds through **falsifiable gates** — claims someone could prove
false, closed only by machinery. Sixteen are closed; the ledger with evidence
is [`docs/GATES.md`](docs/GATES.md) (`just gates` for a quick view).

The conformance system is the project's distinguishing surplus:

- a positive corpus where every grammar production must be exemplified;
- **negative fixtures with lifecycles** — temporal pins for open gaps
  (closable only through a documented ritual) and permanent rejections that
  must never parse;
- a **boundary obligation**: grammar enlargements ship their refusals;
- **policy as code**: the repo's own operating policy is written in OAAS,
  parsed, and mechanically checked against the agent skill layer;
- a **witness-diversity requirement**: no semantic-closure claim on the
  strength of a single reader lineage.

Details: [`spec/conformance.md`](spec/conformance.md) ·
[`GOVERNANCE.md`](GOVERNANCE.md). The repo is designed to be operated by
humans and AI agents alike — [`AGENTS.md`](AGENTS.md) is the operating manual.

## Roadmap

Toward the goal — a semantic interoperability layer that *chooses, compresses,
searches, and binds* implementations, not just describes them:

- **MLIR and WASM** projection contracts with scored suites (ONNX and egglog
  are the templates);
- **configuration wizard** (`oaas add <ecosystem>`): expand declared intent +
  machine capabilities into concrete toolchain configuration;
- **compiler search** over realization sets — the semantic optimization space
  made operational;
- **ABI / component boundary** (Wasm Component Model / WIT study first) — a
  separate falsifiable pillar; OAAS claims *interchange* compatibility today,
  never binary compatibility;
- **ontology federation** across BFO / DOLCE / UFO commitments.

Tracked honestly against the vision in
[`docs/design/idea-coverage.md`](docs/design/idea-coverage.md).

## Contributing

Contributions are welcome under **Apache-2.0** with **DCO sign-off**
(`git commit -s`). Start with [`CONTRIBUTING.md`](CONTRIBUTING.md) — it
documents the mechanical rules (triple representation, corpus discipline,
negative-fixture lifecycles) that CI enforces. Community standards:
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · security:
[`SECURITY.md`](SECURITY.md).

## A note on the name

"OAAS" is a working name with a known collision risk (OAAX, an existing
LF AI & Data project). A rename is planned before any foundation submission —
build against the repo, not the acronym.

## License

[Apache-2.0](LICENSE). The full design record — intake analysis, ADRs, dated
gate reports, research memos — lives under [`docs/`](docs/); every normative
decision is traceable to its ratification.
