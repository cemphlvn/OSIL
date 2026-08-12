# Versioning & Compatibility
Status: stub (draft-0). Added on research U3's finding that our tree had no
analogue of ONNX's Versioning.md / StableHLO's compatibility.md — the one document
class every mature interop spec ships.
Will define: spec version stream vs per-subtree streams (see ADR-0001); what a
breaking change is per artifact class (grammar production, contract field, corpus
id, registry schema); compatibility guarantees across the 3-D matrix
(spec x adapter x upstream); deprecation policy (corpus: supersede, never delete).
