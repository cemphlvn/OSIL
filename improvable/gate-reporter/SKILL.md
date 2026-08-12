---
name: gate-reporter
description: Author gate and loop reports in docs/reports/ from the canonical template
scope: [docs/reports/]
verbs: [report]
cadence: per-gate + per-loop-run
invariants: [template-followed, result-stated-first, honesty-notes-required, claims-cite-artifacts]
evals: evals/
---

# gate-reporter

Every gate closure and loop run lands a report in `docs/reports/`. This skill
owns the format — extracted from reports g1–g9, now explicit and improvable.

## The template (gate reports: `g<N>-<date>.md`; loop reports: `<loop>-<date>.md`)

```
# G<N> report — <YYYY-MM-DD>
Gate: <one-line falsifiable claim>. RESULT: PASS | FAIL | PARTIAL (<scope>).
Ratification: <who/what authorized, when constitutional changes are involved>

## Sequence
<numbered steps AS EXECUTED, each naming its artifact or evidence; guard
events (XPASS firing, XFAIL holding) quoted where they occurred — the
sequence is the proof the ritual ran, not a narrative>

## Final state
<only the counters that MOVED: fixtures, productions, alternatives, scores,
actors/skills — each reproducible by a `just` recipe>

## Honesty notes    <- REQUIRED; "none" must be argued, never defaulted
<direction-of-fit admissions, scope caveats ("4/4 over a 2-case suite"),
residue left open, anything a skeptical reader would find before you do>
```

## Rules

1. RESULT appears in the first two lines — a reader who stops there leaves
   correctly informed.
2. Every claim cites an artifact (file, fixture id, commit) or a reproducible
   command; numbers without a `just` recipe behind them don't go in.
3. Honesty notes are load-bearing, not decoration: the section exists because
   perfect scores and first-run greens are usually direction-of-fit effects,
   and saying so is what keeps the reports trustworthy.
4. Loop reports (drift/matrix/corpus/render/compression) use the same shape
   with `Loop:` replacing `Gate:`.

## Harness notes

Claude Code: author via Write or bash heredoc — the template is the contract,
the mechanism is free.
