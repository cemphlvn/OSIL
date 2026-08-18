# Security Policy

OSIL is a specification + conformance toolchain; it ships no network service
and executes no untrusted input beyond parsing text fixtures. The most
security-relevant surfaces are: the parser/resolver (malformed-input
handling), the CI workflow, and — at the design level — the spec's security
invariants (ConstantTime-class guarantees, namespace binding as a
dependency-confusion control; see spec/core.md and spec/execution.md).

**Reporting**: use GitHub private vulnerability reporting on this repository,
or email phlvncm@gmail.com. Please do not open public issues for suspected
vulnerabilities. Supported branch: `main`.
