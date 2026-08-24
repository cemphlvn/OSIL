# c ecosystem profile

Status: **contracted and verified at G17** (`just cproj`).
Contributes: portable lowering, and the substrate where OSIL's claims become
measurable — every performance number this project has produced passed through
a C compiler.
Projection preserves: **execution**. Source stratum: **OSIL-CIR**.
Upstream canonical source: ISO/IEC 9899 (the C standard) + the compiler's own
documentation for the extensions used (verify via drift-watch).

## Sovereignty note

Per `spec/interop/ecosystem-contract.md` §1, this profile REFERENCES C and its
compiler extensions and does not redefine them. In particular the emitted
vector type uses `__attribute__((vector_size(N)))`, which is a **GNU/Clang
extension, not ISO C** — accepted silently even under `-std=c11 -pedantic`.
That dependency is pinned in `VERSIONS` and is a portability liability recorded
here rather than hidden: a conforming ISO C compiler need not accept it.

## What this projection LOSES, and why it matters

`CONTRACT.osil` declares `may_lose { declared_licence }`. This is measured, not
assumed. C has no syntax for the semantic licences OSIL declares:

- `restrict` is the only alias declaration C offers, and it is **inter-array**.
  Applied to every array pointer across all 151 TSVC loops it recovered
  **0 loops** (`optimizer/repro/`).
- Clang's own diagnostic names the gap: *"Backward loop carried data
  dependence. Memory location is the same as accessed at ..."* — an
  **intra-array** fact, which no C annotation expresses
  (`optimizer/probe/none60/`).

So the emitted C carries its licence as a **comment**: provenance a human can
audit, not semantics a compiler can check. Anything downstream that re-derives
guarantees from the emitted C alone is re-entering the space of things the
compiler must prove for itself.
