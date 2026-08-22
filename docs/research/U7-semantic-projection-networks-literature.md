# U7 — Semantic Projection Networks: preliminary literature grounding

Status: **research note, non-normative**

Date: 2026-08-22

## Why this note exists

OSIL is exploring a possible generalization of interoperability from pairwise conversion to **networks of heterogeneous semantic projections**. Before promoting that idea into the specification, this note maps the closest established research traditions and narrows the novelty claim.

The working phrase is **Semantic Projection Networks (SPNs)**:

```text
representation A ──contracted projection──> representation B
       │                                      │
       └────────── alternative paths ─────────┘

nodes  = heterogeneous representational regimes
edges  = transformations with explicit preservation/loss claims
paths  = composed transformations
cycles = opportunities to test semantic stability/drift
```

This is deliberately a research hypothesis, not yet an OSIL language construct.

## Search-status disclosure

A requested Consensus literature search could not be completed on 2026-08-22 because the connected Consensus account had exhausted its monthly search quota. The literature below was therefore collected from primary/publisher sources and bibliographic records through an independent academic-web search. **Do not describe this note as a Consensus systematic review.** Re-run the queries through Consensus after quota renewal and update this note if that search materially changes the map.

## Closest prior art

### 1. Bidirectional transformations and lenses

The lenses literature already gives a rigorous vocabulary for lawful transformations between related representations.

- Bohannon, Foster, Pierce, Pilkiewicz, and Schmitt, **“Boomerang: Resourceful Lenses for String Data,”** POPL 2008. A lens is treated as a bidirectional program, with laws governing forward and backward behavior. DOI: `10.1145/1328438.1328487`.
- Hofmann, Pierce, and Wagner, **“Symmetric Lenses,”** POPL 2011. Removes the privileged “source/view” asymmetry and studies composition of symmetric bidirectional transformations. DOI: `10.1145/1926385.1926428`.

**Implication for OSIL:** pairwise `encode/decode` is not a sufficient novelty claim. Lawful bidirectional and symmetric transformations are established territory.

### 2. Multiary lenses and networks of models — the nearest conceptual neighbor

The most important prior-art cluster for SPNs is not ordinary lenses but work that explicitly moves beyond two models.

- Diskin, König, and Lawford, **“Multiple Model Synchronization with Multiary Delta Lenses,”** FASE 2018. It formalizes synchronization of more than two inter-related models and emphasizes composition. DOI: `10.1007/978-3-319-89363-1_2`.
- Diskin, König, and Lawford, **“Multiple Model Synchronization with Multiary Delta Lenses with Amendment and K-Putput,”** Formal Aspects of Computing 31(5), 2019, 611–640. Extends the framework with reflective updates and composition laws. DOI: `10.1007/s00165-019-00493-0`.
- Stevens, **“Maintaining consistency in networks of models: bidirectional transformations in the large,”** Software and Systems Modeling 19, 2020, 39–65. Models collections of representations as networks and studies consistency restoration, decomposition, and non-interference. DOI: `10.1007/s10270-019-00736-x`.

This literature already contains the graph-level intuition:

```text
model sets  -> nodes
consistency relations / bx -> edges or hyperedges
```

**Implication for OSIL:** “representations form a network and transformations compose” is prior art. SPN should not be presented as discovering network-shaped interoperability.

### 3. Multi-level and heterogeneous intermediate representations

Lattner et al., **“MLIR: Scaling Compiler Infrastructure for Domain Specific Computation,”** CGO 2021, pp. 2–14, develops infrastructure for transformations across multiple abstraction levels, application domains, hardware targets, and execution environments. DOI: `10.1109/CGO51591.2021.9370308`.

**Implication for OSIL:** heterogeneous multi-IR computation and cross-level lowering are also established. OSIL needs a sharper claim than “many IRs connected together.”

### 4. Semantics-preserving compilation

Leroy, **“A Formally Verified Compiler Back-end,”** Journal of Automated Reasoning 43, 2009, develops machine-checked semantic-preservation proofs for compiler transformations.

**Implication for OSIL:** semantic preservation across transformations has a deep formal-verification literature. OSIL's distinctive question is not whether preservation matters, but how **declared, partial, heterogeneous preservation obligations compose across arbitrary interoperability paths**.

### 5. Equality saturation and equivalence classes of realizations

Willsey et al., **“egg: Fast and Extensible Equality Saturation,”** POPL 2021, develops e-graphs as efficient representations of congruence relations over many equivalent expressions and uses equality saturation to search among rewrites.

**Implication for OSIL:** representing many equivalent realizations and searching them is established compiler technology. OSIL can use this machinery, but should not make equivalence-class search itself the novelty claim.

## Adjacent mathematical inspiration, not current prior-art basis

### Recurrent / associative computation

Ramsauer et al., **“Hopfield Networks is All You Need,”** ICLR 2021, characterize modern Hopfield networks through update dynamics, fixed points, metastable states, and associative retrieval (arXiv:2008.02217).

This is useful for thinking about repeated projection, convergence, and attractor-like behavior. It does **not** currently establish a direct theoretical relationship to semantic interoperability.

### Cross-cortical communication subspaces

Semedo et al., **“Cortical Areas Interact through a Communication Subspace,”** Neuron 102(1), 2019, proposes that interactions between cortical populations occur through low-dimensional communication subspaces. DOI: `10.1016/j.neuron.2019.01.026`.

This motivates a useful design intuition: heterogeneous local representational regimes may coordinate through restricted projections without collapsing into one universal representation. For OSIL this remains **analogy/inspiration**, not evidence that software interoperability should literally be modeled neurobiologically.

## Revised novelty boundary

The literature search changes the strongest defensible public claim.

### Claims OSIL should *not* make

Do not claim that OSIL newly introduces:

- bidirectional or symmetric transformations;
- multi-model or network-shaped synchronization;
- composition of transformations;
- heterogeneous/multi-level IR infrastructure;
- semantics-preserving compilation;
- equivalence-class search.

All have substantial prior art.

### Candidate OSIL contribution

The research opportunity is instead the conjunction of the following properties:

1. **Heterogeneous computational ecosystems remain semantically sovereign.** OSIL references native/versioned meanings rather than replacing them with one global operational semantics.
2. **Every projection carries an explicit preservation contract** describing what is preserved, weakened, or permitted to be lost.
3. **Contracts compose at path level**, making a multi-hop interoperability claim inspectable rather than treating each converter independently.
4. **Alternative paths are comparable** with respect to declared semantic preservation, allowing path dependence/path independence to become an empirical or formal property.
5. **Cycles expose semantic drift** by returning to a comparable regime under an explicit equivalence relation rather than byte equality.
6. **Path selection becomes constrained optimization:** search for a realization/path subject to semantic guarantees, cost, target requirements, and possibly security invariants.
7. **OSIL itself participates as an ordinary node**, allowing self-application of the same projection and preservation machinery.

A sharper working thesis is therefore:

> **OSIL investigates evidence-carrying semantic transport across heterogeneous computational representation networks, where preservation obligations compose over paths and can constrain path/realization search.**

That wording is intentionally narrower than “interoperability as a network.”

## Formal research object

Let each ecosystem-local representational regime be a node `R_i`.

A projection is not merely a function `R_i -> R_j`, but a transformation bundled with an explicit contract and resulting evidence:

```text
P_ij : (R_i, C_ij) -> (R_j, E_ij)
```

where:

- `C_ij` is the declared preservation obligation;
- `E_ij` records observed/proved preservation and allowed loss.

For a path

```text
R_A --P_AB--> R_B --P_BC--> R_C
```

we want a composition operator

```text
C_AC = C_AB ⊗ C_BC
```

and evidence composition

```text
E_AC = E_AB ⊙ E_BC
```

whose laws remain an open research question.

Alternative paths create a directly testable condition:

```text
       path α
A ----------------> D
 \                  ↑
  \-> B -> C -> E -/
       path β
```

Ask whether

```text
P_α(x) ≈_K P_β(x)
```

for declared semantic property set/equivalence regime `K`.

Cycles create a second condition:

```text
A -> B -> C -> A'
```

Ask what is preserved in `A'` relative to `A`, and whether repeated cycling converges, oscillates, or accumulates loss.

## Research questions after prior-art correction

**RQ1 — Contract composition.** What algebra correctly composes preservation, weakening, and loss claims over a heterogeneous projection path?

**RQ2 — Path equivalence.** Under what conditions do distinct projection paths between the same ecosystems preserve equivalent declared semantics?

**RQ3 — Drift.** How should semantic loss be measured and attributed across cyclic or recurrent paths?

**RQ4 — Convergence.** Are there useful classes of projection networks for which repeated transformations reach fixed points or stable equivalence classes?

**RQ5 — Search.** Can a projection path be selected by optimizing cost/performance subject to preservation constraints, rather than optimizing execution alone?

**RQ6 — Relationship to bx/multiary lenses.** Can OSIL preservation contracts be embedded into, derived from, or contrasted formally with multiary delta-lens consistency relations and laws?

RQ6 is particularly important: the right outcome may be that part of the proposed SPN formalism should reuse existing lens machinery rather than invent a parallel algebra.

## Immediate falsifiable experiments for OSIL

1. Register OSIL itself as an ecosystem and establish an OSIL -> OSIL preservation baseline.
2. Construct at least two distinct paths between the same endpoints, e.g. `OSIL -> A -> C` and `OSIL -> B -> C`.
3. Compute preservation reports for both and compare the path-level contracts.
4. Add a cycle and measure whether declared semantic properties are monotonically lost, recovered, or stable.
5. Introduce a path cost function and test whether the cheapest path differs from the highest-preservation path.
6. Re-express one experiment using a known lens/multiary-lens formalism to identify exactly what OSIL adds.

## Public posture

Until the formal comparison with multiary lenses and networks-of-models work is complete, public material should use language such as:

> We are exploring evidence-carrying semantic projection networks as an OSIL research direction. Networked and multiary transformations have substantial prior art in bidirectional transformation and model-synchronization research; our current question is whether OSIL's explicit, composable preservation/loss contracts over heterogeneous computational ecosystems enable a distinct and useful layer of path-level reasoning and optimization.

This is stronger scientifically than presenting the graph topology itself as novel.

## Core references

1. A. Bohannon, J. N. Foster, B. C. Pierce, A. Pilkiewicz, A. Schmitt. *Boomerang: Resourceful Lenses for String Data.* POPL 2008. DOI: `10.1145/1328438.1328487`.
2. M. Hofmann, B. C. Pierce, D. Wagner. *Symmetric Lenses.* POPL 2011. DOI: `10.1145/1926385.1926428`.
3. Z. Diskin, H. König, M. Lawford. *Multiple Model Synchronization with Multiary Delta Lenses.* FASE 2018. DOI: `10.1007/978-3-319-89363-1_2`.
4. Z. Diskin, H. König, M. Lawford. *Multiple Model Synchronization with Multiary Delta Lenses with Amendment and K-Putput.* Formal Aspects of Computing 31(5), 2019. DOI: `10.1007/s00165-019-00493-0`.
5. P. Stevens. *Maintaining consistency in networks of models: bidirectional transformations in the large.* Software and Systems Modeling 19, 2020. DOI: `10.1007/s10270-019-00736-x`.
6. C. Lattner et al. *MLIR: Scaling Compiler Infrastructure for Domain Specific Computation.* CGO 2021. DOI: `10.1109/CGO51591.2021.9370308`.
7. X. Leroy. *A Formally Verified Compiler Back-end.* Journal of Automated Reasoning 43, 2009. arXiv:0902.2137.
8. M. Willsey et al. *egg: Fast and Extensible Equality Saturation.* POPL 2021. arXiv:2004.03082.
9. J. D. Semedo et al. *Cortical Areas Interact through a Communication Subspace.* Neuron 102(1), 2019. DOI: `10.1016/j.neuron.2019.01.026`.
10. H. Ramsauer et al. *Hopfield Networks is All You Need.* ICLR 2021. arXiv:2008.02217.

## Next literature pass

When Consensus search becomes available again, query at minimum:

```text
"multiary delta lenses" composition model synchronization
"networks of models" bidirectional transformations consistency
"semantic preservation" heterogeneous intermediate representations compiler
"path independence" bidirectional transformation lens
"contract composition" semantic interoperability software
"information loss" model transformation composition
```

The purpose of that pass is not to accumulate citations but to try to **falsify the narrowed novelty boundary above**.
