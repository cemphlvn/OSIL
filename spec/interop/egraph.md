# E-graph Interop Contract
Status: draft-1. egg/e-graphs contribute EQUIVALENCE-SPACE SEARCH — a search
ecosystem, not a backend. The EGraph projection preserves equivalence (guards
included): OAAS-SIR -> e-graph -> equality saturation -> extraction -> OAAS-SIR.
OAAS declares equivalences (corpus: 003); the adapter translates them to native
rewrite rules as DATA: each `guards { k = v }` pair becomes a nullary relation
fact, attached to the generated bidirectional rewrite as a condition. Engine:
egglog, decided by research U5 (ADR-0009); egg remains the algorithm citation
(POPL 2021), never executed. Contract: profiles/ecosystem/egg/CONTRACT.oaas;
harness: tools/egraph_roundtrip.py (`just egraph`).
