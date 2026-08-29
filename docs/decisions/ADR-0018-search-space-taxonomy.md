# ADR-0018: position OSIL's existing vocabulary against NAS's search-space taxonomy, and prove it with a second domain

Date: 2026-08-29 · Status: proposed (branch `research/search-space-taxonomy`, not yet merged)

## Context

A downstream user of OSIL (threadlab — a continuity layer that declares a
fork as an OSIL `concept` with realizations and a preservation contract,
`profiles/domain/thread/thread.osil`) ran a live, multi-round experiment
against a third-party agent harness (Prime Intellect's `prime-agent`) on
2026-08-29. Two independently-spawned subagents, given the same declared
fork, wrote substantive, independent design documents and — talking only
to each other over peer messaging, no shared training, no central
orchestrator — converged on identical resource-arbitration boundaries. The
question that followed: could this kind of "multiple realizations held
live and searched" become the basis of a real search algorithm, and if so,
what does OSIL already have toward that, versus what would be new?

Grounding the question against the literature (not recall) surfaced
Elsken, Metzen & Hutter's canonical decomposition of every Neural
Architecture Search method into three independent dimensions
(arXiv:1808.05377): **search space** (which candidates are considered),
**search strategy** (how candidates get explored), and **performance
estimation strategy** (how a candidate gets scored without the full cost
of building and running it). Li & Talwalkar (arXiv:1902.07638) showed a
well-designed search space with plain random search is a competitive NAS
baseline — the space matters at least as much as the strategy searching
it, which is directly relevant to how much credit `concept`/`equivalence`
declarations already deserve on their own.

Checked against this repo's own history rather than against NAS's
literature in the abstract: **G21 already built the performance-estimation
dimension**, for one domain. `capability_decl` (`admits`/`refuses` named
features) lets `just ceiling`/`just price` derive what a loop-transformation
chooser could achieve, and price a capability *before* building it — a
zero-cost structural proxy, not a measured result. This is, in NAS's own
vocabulary, a training-free/zero-cost performance estimator (the
TE-NAS/PC-DARTS family: architecture quality estimated from declared
structure in GPU-minutes, not GPU-days — the field's own cost curve has
already flattened this way). It has so far only ever been used inside
`ecosystem/c`'s optimizer track. Nothing in `grammar/osil.ebnf` ties
`capability_decl` to C, loops, or any ecosystem at all — the grammar
production is `identifier { admits {id_list} refuses {id_list} }`, pure
names. The tooling that *derives a ceiling from* declared capabilities
(`tools/capability_ceiling.py`) is what's actually C-loop-specific (a
hardcoded corpus path, TSVC-style kernel name matching) — the vocabulary
generalizes; one particular consumer of it does not, and this ADR does not
claim otherwise or attempt to generalize that tool.

`model_decl` (intake corpus 006 — purpose + constraints + an optional
named ecosystem, "configuration compression") turns out to be the missing
third dimension: a search strategy is, honestly, an external algorithm
OSIL should reference by name and never redefine — exactly the discipline
already governing `ecosystem/` bindings ("OSIL never redefines what
another system's operations mean"). `model` already has the right shape
for "declare the objective a search strategy must satisfy, and which
ecosystem realizes it" — it has simply never been used for anything
resembling a search strategy before now.

## Decision

### 1. Name the mapping, do not build new grammar

No grammar or resolver change accompanies this ADR. All three NAS
dimensions land on constructs this repository already ships and gates:

| NAS dimension | OSIL construct | Proven since |
|---|---|---|
| search space | `concept { equivalent_under {...} to {...} } ` | G1 (corpus 008) |
| performance estimation | `capability { admits {...} refuses {...} }` | G21 |
| search strategy | `model { purpose: ... constraints {...} [ecosystem X] }` | intake (corpus 006), unused since |

### 2. Prove the generalization with a second, unrelated domain

`profiles/domain/thread/thread.osil` (threadlab's own domain, developing
separately as its own consumer of OSIL) is extended, in this same change,
with a `capability` block per continuity mechanism and a `model` block
naming the resumption objective — grounded in the real Prime Agent trial
data (session-scoped memory admits same-turn recall only; a global
project-scoped memory additionally survives a full daemon restart; a
git-based ledger additionally survives moving to a different machine
days later, at the cost of needing an explicit "go look" step). This is
the actual test of the claim: if `capability_decl`/`model_decl` only ever
worked for C loops, this file would not parse or resolve. It does —
`just check` and `just resolve` both pass, unchanged resolution rate
(18/18 = 1.00), zero new grammar productions, against the unmodified
grammar. The one pre-existing, already-disclosed limitation carries over
unchanged: `just views` refuses `ContextSwitch` for want of an
`ECOSYSTEM_OF` entry (`tools/view_render.py`) — a closed lookup table, not
a grammar or resolver fact, and not something this ADR attempts to paper
over by inventing a false ecosystem mapping.

### 3. What this does not claim

This does not make OSIL, or `profiles/domain/thread/`, "an ML algorithm."
By the taxonomy's own accounting, threadlab has a search space and can now
declare estimators and strategies — it has no search *procedure* that
iterates using that estimator, and no realization has ever been scored
against an actual outcome. Building that (e.g., mining an append-only
decision log as training data for a real search strategy) is future work,
explicitly out of scope here, and would be its own ADR with its own
falsifiable gate.

### 4. Open question this ADR does not resolve

Whether `domain/thread` belongs upstream in this repository at all, or
should remain a downstream consumer's own profile that merely depends on
`osil` as an installed package, is not settled by this change. This ADR
only establishes that IF it lands here, it does not need new grammar to
do so. Given this repository's proximity to its terminal submission gate
(GX), that placement question is left to whoever merges this branch, not
decided by writing the file.
