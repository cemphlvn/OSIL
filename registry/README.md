# registry/ — subtree card
ground-truth: SHARED (manifests describe foreign capabilities in our schema)
cadence: FAST, data-shaped
version-stream: schema versioned; entries timestamped
loops: schema validation · freshness checks
invariants: one-entry-per-file (parallel agent writes stay conflict-free) · entries-validate-against-schema
policy: agents write entries freely within schema; schema changes propose-only
