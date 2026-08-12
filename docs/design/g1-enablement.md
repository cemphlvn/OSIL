# What the G1 Layer Enables

> Written at the moment G1 went green (2026-08-12): `just check` = 9/9 corpus files
> parse, 42/42 productions exemplified, conformance test #0 XFAILs as designed.
> This doc reasons about what the parser layer *is* in the architecture — not just
> what it does — including the `.flow`-in-`.oaas` split (ADR-0005).

## 1. The repo's semantics became load-bearing

Before G1, every policy statement was prose: loops could only be executed by an
LLM reading instructions and promising to comply. Now the smallest contract is
mechanical, and everything above it inherits that:

- **Triple representation is enforceable, both directions.** A spec change adding
  a construct without a corpus example → uncovered production → build fails. A
  corpus file using an undeclared construct → parse fail. The rule stopped being
  a convention and became physics.
- **Conformance test #0 is *watched*, not just declared.** `repo-policy.oaas`
  must fail to parse (XFAIL). When G2 extends the grammar, it will parse — and the
  validator flags XPASS until the EXPECTED-FAIL marker is removed by a ratified
  change. A gap can no longer close silently. This mechanism generalizes: any
  deliberately-open gap in GAPS.md can be pinned by an EXPECTED-FAIL fixture.
- **The first G1 run already earned its keep**: it discovered GAP-3 (quantity
  lexing underspecified — `0.997\nmemory` lexed as a quantity like `20ms`).
  A gap no amount of prose review had surfaced. This is what "loops bite on
  artifacts" looks like in practice.

## 2. Document kinds put policy inside the language (ADR-0005)

The policy address space now has three nested levels:

1. **organization** (future: repos, per pass-3 fission lines)
2. **tree** (paths: subtree cards, skill scopes)
3. **language** (document kinds: `.oaas` vocabulary vs `.flow` composition)

Level 3 is new and is what `.flow` bought us: an agent can now be scoped not just
by *where* it may write but by *what kind of statement* it may author. A
flow-authoring agent (user-space: cheap, parallel, generative) structurally cannot
introduce vocabulary — the parser rejects vocabulary declarations in a flow
document. Spec-space (`.oaas` vocabulary) stays slow and ratified. The
general/particular distinction (BFO rule) became an enforcement boundary, not a
style note.

## 3. Agents move from text to structure

Each existing skill gets sharper teeth:

| Skill | Before G1 | After G1 |
|---|---|---|
| corpus-gardener | "by-hand derivation against the EBNF" | `just check`, mechanical |
| univocity-lint | grep-based term maps | token/AST-grounded term inventory; keyword-vs-identifier occurrences distinguishable |
| matrix-refresh | nothing checkable | first checkable dimension: does an adapter's CONTRACT.oaas parse under spec grammar vX? |
| render-verify | no input format | `.flow` parse trees are the renderer's input; U4's "layout keyed by stable IDs" gets its ID universe from the AST |
| curriculum loops | resolution/reachability only | **production coverage per fixture = pedagogical metadata**: a learning path's grammar coverage is now measurable ("does getting-started exercise every production?") |

The curriculum consequence deserves emphasis: coverage tracking per corpus item
means pool-and-views (ADR-0003) gains a *quantitative* view axis — paths can be
scored for completeness mechanically. The corpus/curriculum unification stops
being an organizational nicety and becomes a measurable invariant.

## 4. The resolver horizon — what G1 deliberately does not do

`use ecosystem.onnx` parses but resolves to nothing. The parser sees names; no
check confirms the profile exists, that `onnx::MatMul@13` is inside the pinned
opset, or that `Tensor<f32>[N,D]` and `[D,H]` compose. That ordered ladder of
absences is the roadmap between G1 and G3, each rung a new loop attachment:

1. **name resolution** (linker): every `use` resolves to a profile; every
   namespaced op resolves through a `use` — dangling-reference loop;
2. **registry validation**: resolved ops checked against
   `registry/entries/<eco>.yaml` capability/operator claims — the registry stops
   being descriptive data and becomes an oracle;
3. **type/shape checking** on flow edges;
4. **projection** (G3): the round-trip harness that scores CONTRACT.oaas fields —
   and populates the compatibility matrix with mechanical `pass` cells.

Rung 2 is where the transcript's wizard ("semantic compiler for infrastructure
decisions") starts being real: a resolved flow + registry manifests = the exact
demand set (`oaas add onnx` knows *what* the flow needs because resolution told it).

## 5. Falsifiability propagates upward

G1's deepest effect: gates above it inherit mechanical meaning. G2 = "this file
stops XFAILing under a ratified grammar change." G3 = "these contract fields score
green in the harness." G4 = "structural layout diff = 0." Each was prose last
week; each is now expressible as an exit code. The project's claim to be
agent-operable rests exactly here — an agent can be *wrong* now, detectably,
which is the precondition for delegating anything that matters.
