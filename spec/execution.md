# Execution Semantics

Status: draft-0. Execution proper (evaluation model, state, determinism
classes) remains stubbed — but execution's PRECONDITION is now specified and
mechanical: resolution (G12).

## 1. Resolution (normative-draft)

**resolution** — the process (genus) that binds every reference in a flow to
a declared universal in the resolution universe (differentia). ADR-0005 kept
the general and the particular apart at parse time; resolution is where the
particular must FIND its universal — a dangling reference is a particular
without one.

**resolution universe** — the artifact set (genus) references resolve
against: profile/operator/concept declarations in `profiles/**/*.osil` plus
registry oracles in `registry/entries/` (differentia).

**namespace binding** — the rule (genus) whereby a use declaration binds the
TERMINAL SEGMENT of a profile's qualified id as the flow's namespace prefix
(`use ecosystem.onnx` binds `onnx::`) (differentia). Terminal segments must
be unique across the universe: a collision is an index-time error — the
language-level analog of dependency confusion, and therefore a security
control inherited from the project's origin, not a convenience.

**dangling reference** — a reference (genus) with no declaration in the
universe (differentia). Classes: DANGLING-USE, UNBOUND-NAMESPACE,
UNDECLARED-OP, BROKEN-WIRING (an edge source neither declared nor produced;
a declared output never produced).

Oracles by profile kind: ecosystem namespaces resolve ops against the
registry entry operators list (name@version); domain namespaces resolve ops
against operator/concept declarations in the profile's own directory. Pin
consistency: `profile.osil` is CANONICAL; `VERSIONS` mirrors it and the
resolver enforces agreement.

Out of scope at G12 (deliberate, ONNX checker/shape-inference precedent):
type and shape checking (rung 3), vocabulary cross-references between .osil
files (e.g. `regime =` guard values). Harness: tools/osil_resolve.py
(`just resolve`); refusals in conformance/resolution/.

## 2. Evaluation model (stub)
Blocked behind rung 3 and projection maturity.
