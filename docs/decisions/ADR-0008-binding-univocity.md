# ADR-0008: Binding univocity — `:` binds roles, `=` asserts equality

Date: 2026-08-12 · Status: RATIFIED (closure by maintainer instruction
"close GAP-2 as G11"; direction chosen under the delegated-judgment precedent
of ADR-0006/D1–D3 — see Honesty).

## Context
GAP-2: the transcript used `:` and `=` without a principled distinction
(`purpose: inference` vs `device = apple_silicon`; original `privacy:
local_only` normalized away in 007 and pinned bidirectionally by corpus 021).
The univocity rule violated was not "two operators exist" but "no declared
meaning per operator."

## Decision
Ratify the distinction the grammar v0.5 already implements — NO grammar change:

- **`:` — role binding**: binds a CLOSED grammar role (`purpose`, `goal`,
  `preserves`) to a term or constraint. Roles are grammar keywords; user keys
  never bind with `:`.
- **`=` — asserted equality**: binds an open key to a value; ONE meaning
  spec-wide, with the block kind supplying force — stipulated in profile
  fields / guards / args / layout attributes, required in constraint blocks
  (where `=` is one relational operator among `< <= > >= ==`).

## Consequences
1. `privacy: local_only` is a PERMANENT refusal (privacy is an open key) →
   corpus 021 takes the pin lifecycle's third exit: **PROMOTED** to
   `conformance/rejections/R006-colon-binding.oaas` (first performance of the
   G10-B promote exit; corpus id 021 retired, never reused).
2. No XPASS ritual runs: the gap closes by ratifying existing acceptance, so
   the acceptance frontier does not move. Boundary obligation: **no new
   boundary — justified** (no enlargement); the refusal frontier is
   nonetheless strengthened by R006.
3. `spec/TERMS.md` gains both operators (univocity-lint's ledger);
   `spec/core.md` gains the two definitions; the EBNF gains a NOTE comment
   (annotation only — grammar stays v0.5).

## Alternatives rejected
- **Enlarge to allow `:` on open keys** (021 flips): makes `:` equivocal —
  the opposite of what GAP-2 asked for.
- **`=`-only everywhere**: `preserves = accuracy >= 0.997` is
  double-relational and ambiguous; fixing it needs block restructuring — a
  larger change for a worse story.

## Honesty
The closure instruction is explicit ratification; the *direction* was chosen
by the agent under the delegated-judgment pattern the maintainer established
at D1–D3, with the bidirectional pin (021's own header, written at G7)
pre-scripting both outcomes. If the maintainer wants the other fork, the
promote is reversible by ratified change: R006 would flip back through the
alarm-XPASS it would trigger.
