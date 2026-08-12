# Intake Pass 2 — Loop Attachment Points

> Same transcript, second reading. Pass 1 established the conformance-tree /
> ground-truth-ownership nuance. Pass 2 asks: where do agentic engineering loops
> actually *bite*, and what does that demand of the folder structure? (2026-08-12)

## PASS-2 NUANCE (on the record)

**The spec is self-hosting with respect to its agent infrastructure: §9 of the
transcript ("invariants as optimization guards") is formally the same object as an
agent operating policy — a rewrite is legal iff it preserves declared invariants —
which means the repo's own agent policy should be written in OAAS's own formalism,
and an agent's PR should be treated as a proposed rewrite on the repo tree whose
merge-legality is checked exactly the way OAAS checks rewrite-legality on programs.**

The transcript already reserves the spot without knowing it: `/profiles/domain/agent/`
sits in its proposed tree. Pass 1 read that as a domain profile for agentic-AI
architectures (which it also is). Pass 2 realizes it is *dual-use*: the natural home
for the repo's **own** operating policy, dogfooded as an OAAS domain profile.

The transposition, term by term:

| OAAS compiler concept (transcript) | Repo engineering-loop equivalent |
|---|---|
| rewrite A → B on a program graph | agent diff on the repo tree |
| `invariant ConstantTime / Deterministic` | per-subtree invariants ("external semantics never redefined", "corpus stays parseable", "univocity holds") |
| "rewrite legal only if it preserves required invariants" | merge gate: diff legal only if subtree invariants hold |
| `preserves{} / may_lose{}` preservation contract | ownership-class policy verbs from pass 1, now *evaluable* instead of documentary |
| maximize perf s.t. semantic preservation + constraints | maximize repo progress s.t. policy + conformance |
| cost model selects realization | review/CI selects which agent proposal merges |

Consequences for folder structure:

1. **Every subtree carries an invariant declaration artifact** (front-matter or an
   `INVARIANTS` file in OAAS syntax). `/spec/interop/` declares dual-review;
   `/profiles/ecosystem/onnx/` declares never-redefine; `/spec/` declares univocity +
   definition rules. CI evaluates *diff × invariants*, which is precisely §9's guard
   mechanism pointed at the repo instead of at a kernel.
2. **The repo becomes conformance test #0.** "The first architecture OAAS must be able
   to describe is the OAAS repo itself." If the formalism cannot express its own
   operating policy (actors, allowed operations, invariants, subtree scopes), that is a
   falsifiable expressiveness failure of the spec — a gate someone can fail, in the
   one-shot-bootstrapping sense.
3. This upgrades pass 1's ownership table from *documentation about policy* to
   *policy as a first-class, versioned, machine-evaluable artifact in the project's
   own language* — governance (LF-grade) and agent policy collapse into one document
   class, per the semantic-infrastructure axis.

## Supporting corollary — loops attach to artifacts, not prose

Second realization feeding the same nuance: every DSL block in the transcript
(`profile ecosystem.onnx {}`, `projection ONNX {}`, `equivalence distributivity {}`,
`model MyModel {}`, `invariant ConstantTime`) is a **latent test fixture** currently
trapped inside markdown code fences. A loop cannot bite on prose; it bites on
parseable artifacts. Therefore:

- Normative concepts need **triple representation**: (a) prose definition, (b)
  grammar/schema, (c) example corpus — each in its own addressable location
  (`/spec/…`, `/schema/…` or grammar dir, `/conformance/corpus/…`).
- The attachable loop is the **three-way consistency check**: every prose-defined
  construct has a grammar production; every grammar production has ≥1 corpus example;
  every corpus example parses. Spec drift in any leg fails CI.
- Sequencing consequence: **grammar-first is the critical path.** Until a minimal
  grammar exists, zero engineering loops can bite anywhere — so "minimal grammar +
  corpus extracted from the transcript's own snippets" is the earliest deployable
  agentic gate in the whole project.
- Ecosystem manifests ("each ecosystem ships a manifest: capabilities, versions, cost
  hints, recipes") make part of the repo a **registry** — flat, schema-governed,
  one-entry-per-file data. That layout is what makes parallel agent generation
  conflict-free (agents writing different entries never touch the same file).

## Delta over pass 1

Pass 1: *who owns the truth of each subtree* → loop type + policy verbs per subtree.
Pass 2: *the policy itself is expressible in the project's own formalism and
enforceable as rewrite-legality*; loops need machine-readable fixtures to exist at
all, making grammar+corpus the critical path and the repo its own conformance target.

**Held for pass 3 (adversarial):** the founding request was a *visual* DSL, yet
`visual_layout` is the one thing the transcript's preservation contracts list under
`may_lose` — the origin requirement is currently the structure's only sacrificial
field. Also: the MSc/education origin (open *learning* resource) has no home in the
proposed tree. Both smell like pass-3 material.
