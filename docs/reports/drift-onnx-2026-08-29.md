# drift-watch: onnx — 2026-08-29

Pins read from `profiles/ecosystem/onnx/VERSIONS`: ir_version = 13, opset ai.onnx = 27
(observed against onnx 1.22.0, pinned 2026-08-12 per docs/reports/roundtrip-onnx-2026-08-12.md).

Primary source checked: GitHub releases API, `onnx/onnx`.
```
gh api repos/onnx/onnx/releases/latest --jq '{tag,name,published_at}'
-> v1.22.0, published 2026-06-15T15:04:00Z
```

Cross-checked against today's live re-run: `docs/reports/roundtrip-onnx-2026-08-29.md`
observed IR 13 / lib opset 27 — matches the pin exactly.

## Verdict: no drift

v1.22.0 is still the latest upstream release; it is the same version the pins were
taken from. No cell marked stale, no bump proposed.

Heartbeat only.
