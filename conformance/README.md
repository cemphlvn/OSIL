# conformance/ — subtree card
ground-truth: SHARED (corpus: ours; matrix cells: verified against foreign upstreams)
cadence: continuous
version-stream: corpus ids are stable forever; matrix cells timestamped
loops: corpus-gardener (per-PR) · matrix-refresh (scheduled, activates G3) · render-verify (activates G4)
invariants: one-construct-per-file · provenance headers · additions-free/deletions-ratified · never-fabricate-a-pass
policy: agents add/refresh freely within invariants
note: corpus/ is the ONE canonical example pool — curriculum/ holds views over it, never copies
