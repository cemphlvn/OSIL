# U8 — Semantic Projection Networks vs. multiary lenses and networks of models

Status: **research comparison, non-normative**

Date: 2026-08-22

## Purpose

This note asks a deliberately adversarial question:

> **Can the proposed Semantic Projection Network (SPN) idea be reduced to existing work on multiary lenses and networks of models?**

If the answer is yes, OSIL should reuse that theory instead of renaming it. If the answer is no, the residue tells us what the actual research contribution is.

## The strongest overlap

The overlap is substantial.

Perdita Stevens' work on **networks of models** already treats a collection of model sets connected by consistency relations and bidirectional transformations. The paper explicitly distinguishes binary bx from **multidirectional transformations** that maintain multiary consistency relations across an arbitrary number of model sets.

Diskin, König, and Lawford go further with **multiary delta lenses**: synchronization among more than two inter-related models, reflective update/amendment, and multiple forms of composition with proved composition results.

Therefore the following SPN intuitions are not novel by themselves:

```text
many representations
        +
relations between them
        +
updates/transformations
        +
network topology
        +
composition
```

Any OSIL paper that claims novelty at that level would be weak.

## Reduction attempt

Start with an SPN:

```text
G = (R, P)

R_i  = representation regime / ecosystem-local representation
P_ij = projection between regimes
```

A first reduction into the bx/model-synchronization vocabulary is straightforward:

```text
OSIL / SPN                         bx / multiary-lens vocabulary
-----------------------------------------------------------------
representation regime R_i         model set M_i
representation instance x_i       model m_i
cross-regime compatibility        consistency relation R
projection P_ij                    bx / update propagation
many connected regimes            network of models
n-way relation                    multiary consistency relation
projection composition            lens / bx composition
```

At this abstraction level, SPN collapses into existing theory.

That is useful: **OSIL should inherit terminology and laws from bx where they fit.**

## Where the reduction begins to fail

The candidate residue appears when we include the parts OSIL treats as first-class.

### 1. OSIL projections are not primarily consistency restoration

The central bx problem is typically:

```text
models are jointly consistent
        ↓
one model changes
        ↓
consistency breaks
        ↓
propagate/amend updates
        ↓
restore consistency
```

The proposed OSIL problem is different:

```text
computation/meaning exists in regime A
        ↓
realize/project it into regime B
        ↓
explicitly state what survived and what may not have
        ↓
continue through B, C, ...
```

OSIL therefore starts from **semantic transport and realization**, not necessarily from co-existing models that must be synchronized after mutation.

This distinction needs formal testing; it may turn out to be expressible as a special case of generalized bx.

### 2. Preservation is intentionally partial and typed by property

A consistency relation usually answers whether a collection of models is jointly acceptable under some relation.

OSIL wants something more diagnostic:

```text
preserved:
  tensor_types
  operator_versions
  graph_topology

may_lose:
  ontology_annotations
  visual_layout
```

The desired object is not merely `consistent / inconsistent`, but a structured account of **which semantic dimensions survive each hop**.

A projection can therefore be useful even when it intentionally loses properties, provided the loss was declared.

Candidate distinction:

> OSIL treats controlled semantic loss as a first-class interoperability result rather than only a failure of consistency.

This is one of the strongest areas to compare against existing delta-lens notions of amendment, information preservation, and consistency relations before claiming novelty.

### 3. Evidence is part of the projection result

Proposed OSIL signature:

```text
P_ij : (R_i, C_ij) -> (R_j, E_ij)
```

where:

- `C_ij` = declared preservation contract;
- `E_ij` = evidence/report produced by the crossing.

The intended distinction is **proof/evidence-carrying interoperability**:

```text
claim before crossing  = contract
observation after      = evidence
```

The literature comparison should ask whether traceability structures, complements, deltas, amendments, and lens laws already subsume this distinction.

### 4. Ecosystem sovereignty

OSIL's current architectural rule is that foreign ecosystems own their own semantics. OSIL refers to versioned native operators and definitions rather than redefining them globally.

So nodes are not just models in one modeling framework. They can be heterogeneous computational regimes:

```text
ONNX
MLIR
Wasm
OSIL
future runtime/compiler IRs
```

Each may have different:

- typing systems;
- operational semantics;
- abstraction levels;
- versioning rules;
- execution capabilities;
- security invariants.

The open question is whether the existing heterogeneous-model and megamodel literature already provides the right abstraction here. We should assume it might.

### 5. Path-level loss accounting

Suppose:

```text
A --P1--> B --P2--> C
```

OSIL wants to derive not only a composed transformation, but a composed preservation statement:

```text
C_AC = C_AB ⊗ C_BC
E_AC = E_AB ⊙ E_BC
```

This should answer questions like:

```text
property q:
A -> B  preserved
B -> C  may lose
-----------------
A -> C  not guaranteed
```

The research question is whether this is merely an instance of composition of consistency relations/lenses, or whether **graded property-specific preservation and loss** requires a different algebra.

### 6. Alternative paths become optimization candidates

For two routes:

```text
        B
      /   \
A ---       --- D
      \   /
        C
```

OSIL wants to compare them along multiple dimensions:

```text
path α:
  preservation = 0.98
  latency      = 20 ms
  memory       = 200 MB

path β:
  preservation = 1.00
  latency      = 50 ms
  memory       = 120 MB
```

Then path selection is:

```text
argmin cost(path)
subject to preservation(path) >= requirement
```

Multiary-lens work emphasizes correctness and consistency restoration; OSIL's intended system-level contribution may be **semantic guarantees as constraints on realization/path search**.

Again, this needs literature falsification against megamodel/build-system and transformation-planning work.

## A better formal decomposition

Instead of treating `projection` as one undifferentiated primitive, SPN research should separate three objects:

```text
1. transformation
   T_ij : R_i -> R_j

2. preservation contract
   C_ij : Property -> Obligation

3. evidence
   E_ij : Property -> Observation/Proof
```

Then a contracted projection is:

```text
P_ij = <T_ij, C_ij, E_ij>
```

This decomposition matters because different research traditions may already solve each component:

```text
T  <- bx / compilers / model transformations
C  <- contracts / refinement / semantic preservation
E  <- verification / conformance testing / proof artifacts
```

The potential OSIL contribution could be the **composition layer binding all three across heterogeneous ecosystems**, not a new transformation calculus from scratch.

## Path composition as the central object

For a path:

```text
π = P_01 ; P_12 ; ... ; P_(n-1)n
```

we need:

```text
T_π = T_(n-1)n o ... o T_01
C_π = C_01 ⊗ C_12 ⊗ ... ⊗ C_(n-1)n
E_π = E_01 ⊙ E_12 ⊙ ... ⊙ E_(n-1)n
```

The research burden is now precise:

1. define `⊗` for contracts;
2. define `⊙` for evidence;
3. establish soundness between composed contract and composed transformation;
4. determine when evidence is observational, tested, derived, or formally proved;
5. determine which algebraic laws hold.

## Candidate laws

These are hypotheses, not OSIL requirements yet.

### Identity

```text
C_id ⊗ C = C = C ⊗ C_id
```

An identity projection should add no semantic loss.

### Associativity

```text
(C_AB ⊗ C_BC) ⊗ C_CD
=
C_AB ⊗ (C_BC ⊗ C_CD)
```

If this fails, path-level reasoning depends on grouping and becomes much harder.

### Conservative composition

The composed contract must never promise a property that some mandatory hop can lose unless a later hop can **demonstrably reconstruct** it under a specified semantics.

Naive rule:

```text
preserved ⊗ may_lose = may_lose
```

But reconstruction means this may need provenance-sensitive semantics rather than simple meet/intersection.

### Evidence soundness

```text
E_π satisfies C_π
```

must be mechanically checkable under the evidence regime claimed by the path.

### Alternative-path equivalence

For `π1, π2 : A -> D`:

```text
T_π1(x) ≈_K T_π2(x)
```

under explicitly stated `K`.

This is not assumed globally; path dependence is itself a result.

## The cycle question

A cycle:

```text
A -> B -> C -> A'
```

is especially useful because source and destination can again be evaluated in a comparable regime.

Possible outcomes:

```text
A' ≈ A          stable cycle
A' < A          declared semantic degradation
A' > A (?)      reconstruction/enrichment
A_n -> A*       convergence/fixed point
A_n oscillates  periodic behavior
```

The first three can be studied without invoking Hopfield networks.

Only if repeated application shows mathematically meaningful convergence dynamics should OSIL introduce language such as **attractor**, **energy**, or **associative retrieval**.

## What the neuroscience analogy contributes today

The strongest safe analogy is not “OSIL is a cortical system.”

It is:

```text
heterogeneous local representations
             +
restricted cross-system projections
             +
coordination without one universal code
```

Work on cortical communication subspaces makes this intuition scientifically interesting, but it remains inspiration until it changes the formalism or predicts measurable behavior.

## Current novelty verdict

### Mostly absorbed by existing theory

- n:n topology;
- multi-model relations;
- bidirectional/multidirectional update propagation;
- transformation composition;
- network consistency reasoning.

### Still plausible as OSIL-specific research residue

```text
heterogeneous computational ecosystems
              +
property-specific preservation/loss contracts
              +
per-hop evidence
              +
path-level contract/evidence composition
              +
optimization constrained by semantic preservation
              +
self-application
```

The word **SPN** is useful only if this bundle survives deeper comparison. Otherwise we should use established bx/megamodel terminology.

## Next falsification targets

Before drafting a venue paper, answer these in order:

1. **Information-preserving bx:** does existing work already model property-specific partial preservation in a way that subsumes OSIL contracts?
2. **Comprehensive systems / multi-model consistency:** do these frameworks already provide the required n-way contract algebra?
3. **Megamodel build systems:** is path selection under consistency constraints already formalized?
4. **Traceability/complements:** is OSIL `Evidence` merely an existing trace/complement notion under another name?
5. **Transformation planning:** does prior work already optimize transformation chains subject to semantic constraints?

Only after those five checks should OSIL freeze a formal SPN definition.

## Working paper claim after this comparison

A defensible working claim is:

> Existing bidirectional-transformation research provides mature theories for maintaining consistency among multiple related models. OSIL investigates a complementary problem: composing explicit, property-level preservation and loss obligations — together with conformance evidence — across paths through heterogeneous computational ecosystems, and using those composed obligations to constrain realization and path search.

That is the current claim to attack next.

## Primary references

- Perdita Stevens. *Maintaining consistency in networks of models: bidirectional transformations in the large.* Software and Systems Modeling 19, 39–65 (2020). DOI `10.1007/s10270-019-00736-x`.
- Zinovy Diskin, Harald König, Mark Lawford. *Multiple Model Synchronization with Multiary Delta Lenses.* FASE 2018, 21–37. DOI `10.1007/978-3-319-89363-1_2`.
- Zinovy Diskin, Harald König, Mark Lawford. *Multiple Model Synchronization with Multiary Delta Lenses with Amendment and K-Putput.* Formal Aspects of Computing 31(5), 611–640 (2019).
- Zinovy Diskin et al. *Towards Multiple Model Synchronization with Comprehensive Systems.* 2020.
