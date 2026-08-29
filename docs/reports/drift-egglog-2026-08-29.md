# drift-watch: egglog — 2026-08-29

Pins read from `profiles/ecosystem/egglog/VERSIONS`: egglog pypi = 13.2.0,
core git rev 2e5657b (opaque/transitive inside the wheel), pinned 2026-08-12
per research U5 (docs/research/U5-egg-vs-egglog.md).

Primary source checked: PyPI JSON API for the `egglog` project (the executed
harness dependency — NOT crates.io `egg`, which U5 established is decoupled
numbering and never cross-checked).
```
curl -s https://pypi.org/pypi/egglog/json | jq '.info.version, .releases["13.2.0"][0].upload_time'
-> "13.2.0", "2026-06-03T00:23:01"
```

Cross-checked against today's live re-run: `docs/reports/roundtrip-egraph-2026-08-29.md`
— `uv run --with 'egglog==13.2.0'` resolved and ran clean, preservation score 4/4.

## Verdict: no drift

13.2.0 is still the latest PyPI release; the vendored core rev cannot be checked
independently of the wheel (opaque/transitive per the pin note) and nothing
in the PyPI metadata indicates a newer wheel superseding it.

Heartbeat only.
