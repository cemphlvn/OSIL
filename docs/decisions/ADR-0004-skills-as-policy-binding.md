# ADR-0004: Skills bind policy to procedures; frontmatter is constitutional
Date: 2026-08-12 · Status: accepted
Context: per-subtree policy needs an enforcement point; the spec's own principle
says a rewrite is legal iff it preserves required invariants (transcript §9).
Decision: a deployed loop = skill x subtree x cadence. Skill frontmatter declares
scope/verbs/invariants; the merge gate checks diff ⊆ scope(skill) + subtree
invariants. Bodies improve freely under evals+CHANGELOG (legislation); frontmatter
changes require ratification (constitution). skill-improver never edits its own
frontmatter. Skill scopes must agree with profiles/domain/agent/repo-policy.oaas.
Consequence: agent policy is versioned, reviewable, and eventually expressible in
OAAS itself (gate G2 / conformance test #0).
