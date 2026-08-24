# Calibration history (append-only)

- 2026-08-24 `v1` sha=09b0da9 | train=['s312', 's317-noclosed'] heldout=['s352'] | mul_latency 4.0->3.27, lanes_per_cycle 8.0->18.44 | pick-correctness 2/3->3/3 | held-out gate PASS
- 2026-08-24 `v1` sha=09b0da9 | train=['s312', 's317-noclosed'] heldout=['s352'] | mul_latency 4.0->3.20, lanes_per_cycle 8.0->17.99 | pick-correctness 2/3->3/3 | held-out gate PASS

> **CAVEAT added 2026-08-24, after the fact.** The `v1` fit above was measured
> while research subagents were running concurrently. Machine contention was
> later found to change measured speedups by up to 3.8x and to flip accept/reject
> decisions (`docs/design/measurement-contention.md`). These constants were
> fitted against wall-clock-derived data taken under uncontrolled load and
> should be re-fitted on a quiet machine before being trusted. The
> pick-correctness gate they passed is correspondingly weak evidence.
