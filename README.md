# OSIL

**Open Semantic Interoperability Layer.** An open specification for
describing computation by its declared meaning.

[![gates](https://github.com/cemphlvn/osil/actions/workflows/gates.yml/badge.svg)](https://github.com/cemphlvn/osil/actions/workflows/gates.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Status: draft-0](https://img.shields.io/badge/spec-draft--0-orange.svg)](docs/GATES.md)

**Contents** · [The two layers](#the-two-layers) ·
[What this enables](#what-this-enables-for-interoperability-research) ·
[Why](#why) · [The language](#the-language-two-more-fragments) ·
[What works today](#what-works-today) · [Getting started](#getting-started) ·
[Layout](#repository-layout) · [Conformance](#conformance-and-governance) ·
[Roadmap](#roadmap) · [Contributing](#contributing) · [Naming](#a-note-on-the-name) ·
[License](#license)

## The two layers

OSIL is built on one separation. Every architecture is described at two
levels, kept strictly apart:

**OSIL-SIR, the semantic layer: what it is.**

```
concept Attention {
    equivalent_under { fp16, causal = true }
    to {
        decomposition_A
        decomposition_B
        fused_kernel_C
    }
}
```

Read it as: Attention is one identity with three interchangeable ways of
being computed, together with the exact conditions under which they count as
the same. Nothing here says how anything runs.

**OSIL-CIR, the computational layer: how it is computed.**

```
use ecosystem.onnx

input X : Tensor<f32>[N,4]
const W : Tensor<f32>[4,8]
output Y : Tensor<f32>[N,8]

X, W -> onnx::MatMul@13 -> Y
```

Read it as: take an input X and a constant W, multiply them using ONNX's
exact definition of matrix multiplication (version 13), and call the result
Y. This is one concrete computation, step by step.

**Realization is the bridge.** A realization is a commitment from one
semantic identity to one concrete computation that honors every declared
constraint and invariant. One identity usually has many valid realizations,
and that set is the whole point:

> **semantic optimization space = valid realizations(SIR, constraints, invariants)**

Choosing the best realization for a given machine, under stated requirements
(including security requirements such as constant-time behavior), is what
optimization means in this project. A dish is not its recipe: one dish has
many recipes, and the best recipe depends on your kitchen.

## What this enables for interoperability research

- **Measured interoperability.** Preservation contracts turn "format A works
  with format B" into a scored, reproducible claim; formats and bridges can
  be compared by what they provably keep.
- **Optimization as search.** With identity separated from computation,
  implementation choice becomes search over a declared realization set;
  equality-saturation engines (egglog here) slot in directly instead of
  pattern-matching opaque code.
- **Loss accounting across toolchains.** Every hop declares what it may lose,
  so end-to-end meaning loss across a chain of tools becomes auditable,
  security properties included.
- **Category-level substitution.** Requirements stated as categories (say,
  authenticated encryption rather than one cipher's name) let each target
  swap implementations legally.
- **Machine-governable specifications.** The spec's own policy language
  governs the repository that develops it, a live testbed for standards work
  operated jointly by humans and AI agents.

## Why

When a book is translated, some meaning always slips away, and a careful
translator tells you what was kept and what was sacrificed. Software has the
same problem. Programs and machine learning models are constantly "translated"
between tools, and each hop can quietly drop something the original author
cared about: an intention, a safety requirement, even the layout of a diagram
someone drew. Today those losses are invisible, because nobody writes them
down.

Beyond the two-layer separation above, OSIL takes two further positions:

- **Promises are written down and checked.** Every bridge from OSIL to another
  tool comes with a *preservation contract*: a short, machine-readable list of
  what survives the crossing and what may be lost. A test suite then scores
  whether the promise actually holds.
- **Other tools keep their own dictionaries.** OSIL never redefines what
  another system's operations mean. `onnx::MatMul@13` means exactly what ONNX
  says it means, at exactly that version. OSIL adds shared context around
  native names; it never replaces them.

And one more stance, unusual enough to state up front: **diagrams are
content**. OSIL's native file format is contractually required to preserve
everything, including the visual layout people draw. Nothing is "just
cosmetic."

## The language, two more fragments

OSIL files come in two kinds: `.osil` files declare vocabulary (the general),
and `.flow` files compose actual dataflow (the particular). You have already
seen one of each above. Two more constructs carry the honesty:

An equivalence, valid only inside its declared numeric regime:

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

Read it as: these two ways of adding three numbers are interchangeable, but
*only* under exact arithmetic. On floating-point hardware the swap can change
results, and the guard writes that boundary down instead of hoping.

A preservation contract, in full:

```
projection ONNX {
    from OSIL-CIR
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

Read it as: crossing into ONNX starts from the computational layer, keeps the
types, the operation versions, the structure, and the constants; annotations
and diagram layout may be lost, and the format says so up front rather than
losing them silently.

More examples: the full corpus in [`conformance/corpus/`](conformance/corpus/),
guided reading paths in [`curriculum/paths/`](curriculum/paths/), the
specification in [`spec/`](spec/).

## What works today

Grammar **v0.6**, spec **draft-0** (pre-release; nothing is normative yet).
Everything in this table runs today, each row has a command that proves it,
and CI runs the same suite on every push:

| Capability | Verify with |
|---|---|
| Grammar and corpus validation (every rule exemplified; illegal inputs pinned) | `just check` |
| Reference resolution: every name must point at a real declaration | `just resolve` |
| ONNX round-trip with a scored preservation contract | `just roundtrip` |
| Equivalence search via egglog, scored | `just egraph` |
| Pipeline commutation analysis (the toolchain tests itself) | `just stages` |
| Visual rendering with an exact layout-preservation gate | `just render` · `just draw FILE` |
| Diagrams derived from the same declarations the tests read | `just views` |
| Policy check: the repo's own rules, written in OSIL, verified mechanically | `just policy` |
| Size and compression metrics | `just compress` |

`just test` runs the full suite. Expected tail of a healthy run:

```
resolution rate: 18/18 = 1.00 (north-star metric #1; gate requires 1.00)
Resolution contract satisfied: every reference finds its universal.
```

## Getting started

**Prerequisites**: Python 3 (the core tools have zero dependencies),
[`just`](https://github.com/casey/just) (a command runner), and
[`uv`](https://docs.astral.sh/uv/) (fetches `onnx` and `egglog` on demand for
the interop suites).

```sh
git clone https://github.com/cemphlvn/osil.git
cd oaas
just            # list all commands
just check      # validate grammar + corpus (no dependencies needed)
just test       # full conformance suite (uses uv for onnx/egglog)
just draw conformance/corpus/019-toolchain-render.flow   # render a flow to SVG
```

## Repository layout

Every top-level directory carries its own README card stating who owns its
ground truth, how fast it changes, and what agents may do there:

```
spec/          the specification text: core concepts, conformance, visual layout, interop contracts
grammar/       the language definition (EBNF, v0.6), single source for the validator
conformance/   examples that must parse, inputs that must be rejected, golden renders, interop suites
profiles/      ecosystem bindings (ONNX, egglog, MLIR, WASM) · ontologies · domain vocabularies
registry/      machine-readable descriptions of each ecosystem (the resolver's oracle)
curriculum/    ordered reading paths through the examples, for learning
improvable/    the agent skill layer: procedures, evals, changelogs
tools/         reference validator, resolver, test harnesses, renderers (plain Python)
docs/          gate ledger · decision records · dated reports · research memos
```

## Conformance and governance

Progress here happens through **falsifiable gates**: every milestone is a
claim someone could prove wrong, and it counts as done only when machinery
demonstrates it. Sixteen gates are closed; the full ledger with evidence is
[`docs/GATES.md`](docs/GATES.md) (`just gates` for a quick view).

The habits that keep it honest:

- every grammar rule must have a working example, checked mechanically;
- illegal inputs are collected too: things that must *never* parse are kept as
  permanent test fixtures, so the language's boundaries are as tested as its
  features;
- any change that grows the grammar must also ship the new boundary it creates;
- the repository's own operating rules are written in OSIL itself, parsed, and
  verified, so the project is its own first user;
- no claim of completeness is accepted on the word of a single reader,
  human or machine (witness diversity, in [`GOVERNANCE.md`](GOVERNANCE.md)).

The repo is designed to be operated by humans and AI agents alike;
[`AGENTS.md`](AGENTS.md) is the operating manual.

## Roadmap

The goal is a semantic interoperability layer that not only describes
implementations but helps choose, compress, search, and bind them:

- **MLIR and WASM** bridges with scored contracts (ONNX and egglog are the
  templates);
- a **configuration wizard** (`oaas add <ecosystem>`): state your intent and
  your machine, get a concrete working setup expanded for you;
- **compiler search** across the many valid recipes for one declared dish;
- an **ABI and component boundary** (studying the Wasm Component Model first),
  kept as its own separately tested pillar. OSIL claims *interchange*
  compatibility today, never binary compatibility;
- **ontology federation** across BFO, DOLCE, and UFO commitments.

Progress is tracked honestly against the vision in
[`docs/design/idea-coverage.md`](docs/design/idea-coverage.md).

## Contributing

Contributions are welcome under **Apache-2.0** with **DCO sign-off**
(`git commit -s`). Start with [`CONTRIBUTING.md`](CONTRIBUTING.md), which
explains the house rules that CI enforces. Community standards:
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) · security:
[`SECURITY.md`](SECURITY.md).

## A note on the name

OSIL (Open Semantic Interoperability Layer) is this project's name as of
2026-08-18. It was developed under the working name OAAS; the rename resolved
a collision risk with OAAX, an existing LF AI & Data project (ADR-0012).
Historical documents under `docs/` retain the old name, faithfully. The old
GitHub URL redirects.

## License

[Apache-2.0](LICENSE). The full design record (intake analysis, decision
records, dated gate reports, research memos) lives under [`docs/`](docs/);
every normative decision is traceable to its ratification.
