# U6 — Self-hosting OSIL as an ecosystem: a functional kernel

Status: research proposal, non-normative

## Question

What is the smallest callable surface that lets OSIL count as one of the ecosystems it describes, rather than only as the language that describes other ecosystems?

## Answer

**Five semantic code signatures are sufficient for a minimal self-hosting kernel.**

They are not five implementation functions that must live in one module. They are five *observable roles*. Implementations may fuse or split them internally, but a conforming self-hosted OSIL ecosystem should expose equivalent behavior.

```text
1. parse      : Bytes -> Either[ParseError, Document]
2. resolve    : (Document, Registry) -> Either[ResolutionError, ResolvedDocument]
3. realize    : (SemanticIdentity, Constraints) -> Set[Computation]
4. project    : (Computation, Ecosystem) -> Either[ProjectionError, Artifact]
5. preserve   : (Source, Artifact, Contract) -> PreservationReport
```

These five signatures correspond to a complete semantic path:

```text
syntax -> meaning -> valid realizations -> ecosystem artifact -> evidence
```

The design is deliberately functional: each boundary is modeled as a value transformation, hidden effects are pushed behind interpreters, and failure/loss is explicit in the return type.

## Why five, not more

### 1. `parse`

```text
parse : Bytes -> Either[ParseError, Document]
```

OSIL must be able to ingest its own surface language as data. Parsing is kept separate from semantic resolution so syntactic validity is not confused with referential validity.

### 2. `resolve`

```text
resolve : (Document, Registry) -> Either[ResolutionError, ResolvedDocument]
```

A parsed name is not yet meaning. Resolution connects local references to declared identities and versioned ecosystem vocabulary.

This is the point where OSIL moves from syntax to a semantic object.

### 3. `realize`

```text
realize : (SemanticIdentity, Constraints) -> Set[Computation]
```

This is the core OSIL move. A semantic identity denotes a *set of legal realizations*, not one implementation.

The return type is intentionally plural. Optimization can then be defined as selection over the returned realization set rather than as mutation of an opaque implementation.

### 4. `project`

```text
project : (Computation, Ecosystem) -> Either[ProjectionError, Artifact]
```

Projection is the interpreter boundary. It turns an OSIL computation into a concrete artifact in an ecosystem such as ONNX, MLIR, Wasm — or OSIL itself.

For self-hosting, the critical case is:

```text
project(cir, OSIL) -> osil_artifact
```

This gives OSIL a native realization target instead of exempting itself from its own model.

### 5. `preserve`

```text
preserve : (Source, Artifact, Contract) -> PreservationReport
```

A bridge is not complete merely because it emitted an artifact. OSIL's distinctive claim is that the crossing carries explicit evidence about what survived and what may have been lost.

`PreservationReport` should therefore be a first-class value, not logging side-effect.

## The functional-programming correspondence

```text
Functional programming                 OSIL kernel
----------------------                 -----------
expression                             Document / SemanticIdentity
referential transparency               semantic substitutability
algebraic data                         SIR / CIR
interpreter                            project
explicit effects                       Either / PreservationReport
lawful composition                     preservation contracts
multiple equivalent expressions        realization set
```

The important shared move is:

> Separate a description from the mechanism that realizes it.

## Self-hosting criterion

OSIL should count as an ecosystem only when it can pass through the same machinery as a foreign ecosystem.

A minimal self-hosting test is therefore:

```text
source.osil
   |
   v
parse
   |
   v
resolve
   |
   v
realize
   |
   v
project(..., ecosystem.osil)
   |
   v
artifact.osil
   |
   v
preserve(source, artifact, OSIL_contract)
   |
   v
PreservationReport(pass)
```

The stronger property is a round-trip law:

```text
normalize(decode(encode(x))) ~= normalize(x)
```

where `~=` is parameterized by an explicit OSIL preservation contract rather than assumed byte equality.

## What does *not* need to become a sixth primitive

The following are derivable or policy layers, not minimal semantic signatures:

- `optimize`: selection over `realize(...)` under a cost function.
- `compose`: ordinary composition of transformations plus contract composition.
- `render`: a projection into a visual ecosystem/profile.
- `validate`: syntactic validation belongs with `parse`; semantic validation belongs with `resolve`/`preserve`.
- `execute`: belongs to the chosen runtime ecosystem; OSIL can describe it without making execution a semantic primitive.
- `search`: implementation strategy over the realization set (egglog is one candidate), not part of the kernel's meaning.

## Repository implication

The repository already has most of the structural pieces required for this self-hosting move:

- OSIL-SIR / OSIL-CIR separation;
- ecosystem registry;
- per-ecosystem `PROFILE.md`, `VERSIONS`, and `CONTRACT.osil` convention;
- scored interop suites;
- resolver and validator;
- realization/search machinery;
- policy self-application.

The missing closure is to register **OSIL itself** under the same ecosystem contract used for foreign systems and require an OSIL -> OSIL round-trip gate.

A future normative change could therefore add:

```text
registry/entries/osil.yaml
profiles/ecosystem/osil/PROFILE.md
profiles/ecosystem/osil/VERSIONS
profiles/ecosystem/osil/CONTRACT.osil
conformance/interop/osil/
```

That change should be proposed separately because ecosystem contracts and conformance behavior are normative surfaces.

## Proposed invariant

> **SELF-APPLICATION:** no interoperability property is claimed for foreign ecosystems that OSIL exempts itself from demonstrating on its own native representation.

If adopted, this makes OSIL not merely a metalanguage over ecosystems, but the first ecosystem governed by its own interoperability semantics.
