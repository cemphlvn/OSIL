# C projection suite (G17)

Cases for `tools/c_roundtrip.py`, which verifies the four `preserves` fields of
`profiles/ecosystem/c/CONTRACT.osil`.

One case per file, `cNNN-slug.osil`, ids stable (corpus discipline, ADR-0005).
Each case is a declaration; the harness projects it to C, compiles it, runs it,
and checks the emitted C against an independent reference computed in Python.

`c003` is the same computation as `c001` under a stricter regime — the pair
exists so the collapse of the licensed space is a fixture, not an assertion.

## Refusal lane (`refusals/`)

Negative fixtures, `RCNNN-slug.osil`. The projector MUST refuse these loudly.
A projection that silently mis-lowers an unknown construct is worse than one
with no support for it: it emits code that looks right and is not.

| id | refused because |
|---|---|
| `RC001` | `gather` is not a source form the projection knows |
| `RC002` | `maxof` has no declared identity element, so folding it would require the projector to INVENT one |

**Refusals must be DELIBERATE.** The harness accepts only the `Unsupported`
exception as evidence. An incidental crash (a bad `int()`, a missing key)
reports `WRONG-REASON` and FAILS the gate — a fixture that passes because the
projector happened to crash is a fabricated pass.

## The `may_lose` lane is an XFAIL, not prose

`CONTRACT.osil` declares `may_lose { declared_licence }` — C cannot carry the
guards. That is the ADR's central measured claim, so it gets a **fixture**:
every comment is stripped from the emitted C and the guard must appear nowhere
in what remains.

- **XFAIL-HOLDS** — the licence is comment-only, as declared. The loss is real.
- **XPASS-ALARM** — the licence survived into code. The declared loss is no
  longer a loss: C (or our emitter) gained a way to carry it. That is a
  ratification event, not a silent improvement. Same discipline as `ES004`.

This is the repo's first `may_lose` field with a test rather than an assertion.

## Witnesses (the tests are themselves tested)

Every check here was verified to FAIL when violated, not merely to pass:

| perturbation | result |
|---|---|
| projector wrongly accepts `gather` | `rc001 WRONG-REASON` -> FAIL |
| guard gate removed (lanes licensed unconditionally) | `guard-withheld LEAKED` on all 3 cases -> FAIL |
| emitter encodes the guard in CODE instead of a comment | `may_lose XPASS-ALARM ... RATIFY` on all 3 cases -> FAIL |

A check that has never been observed to fail is not evidence.
