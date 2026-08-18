# spec/TERMS.md — term inventory (maintained by univocity-lint)

| term | defined at | definition form | synonyms / notes |
|---|---|---|---|
| regime (guard key) | profiles/domain/numeric/numeric.osil · ADR-0007 | Aristotelian (in ADR: a validity domain (genus) whose carriers realize it (differentia)) | CANONICAL guard form `regime = <Concept>`. Declared expansion (synonym, kept valid): `numeric_semantics = <value>` — fixtures 003/009/013/014/015 retain it transcript-faithfully. First entry recorded at ADR-0007 ratification, 2026-08-12. |
| `:` (role binding) | grammar v0.5 (model_field, operator_field) · ADR-0008 | Aristotelian (spec/core.md §2) | binds CLOSED roles only (purpose, goal, preserves); never open keys — refusal pinned by R006. GAP-2 resolution, G11. |
| `=` (asserted equality) | grammar v0.5 (profile_field, guards, arg, constraint, node_layout) · ADR-0008 | Aristotelian (spec/core.md §2) | one meaning spec-wide; block kind supplies force (stipulated vs required). Not a synonym pair with `:` — disjoint domains by rule. |
| realizability (of an equivalence direction) | spec/core.md · G14 (docs/reports/g14-2026-08-12.md) | Aristotelian | engine-forced (egglog rejects ungrounded directions); `<=>` is bidirectional as assertion, directed as computation when only one side anchors a match. A semantic PROPERTY, not a construct — no grammar change, no new boundary. Recorded per case by `just egraph`. Ratified 2026-08-12. |
| stage | spec/core.md · grammar v0.6 (stage_decl) · ADR-0010 | Aristotelian | the toolchain as vocabulary; write-sets are FILE-granular resource ids, self-class truth. Corpus 023. G15. |
| `then` (composition) | spec/core.md · grammar v0.6 (compose_expr) · ADR-0010 | Aristotelian | CONTEXTUAL keyword — no new operator token; `.` stays univocal as namespace path (ADR-0008 discipline). Operands identifiers only; sort boundary pinned by R008. Corpus 024. |
| writes_disjoint (guard key) | spec/core.md · ADR-0010 | Aristotelian | first COMPUTED guard: harness asserts the binary relation from declared write-sets (both orders); Bernstein read-write refinement recorded as future tightening in ADR-0010. |
