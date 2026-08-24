#!/usr/bin/env python3
"""Harness discipline (G22) — the test-case validity problem, made mechanical.

C-Reduce's PLDI 2012 paper named this bug class fourteen years before this
project hit it three times: **a harness that silently changes what is measured
while still reporting success.** Every one of this session's eight harness
failures was an instance. U15 ranked codifying the discipline as the single
highest-value fix, ahead of adopting any tool.

Discipline is not a policy document here; it is checked. Four rules, each
traced to an actual incident:

  H1 THE FILTER MUST NOT BE NARROWER THAN THE DIAGNOSTICS IT WILL MEET —
     a pattern that reads compiler remarks must match every vectorization
     remark the compiler actually emits, or the unmatched ones vanish.
     Incident: an if-conversion experiment grepped for `vectorized loop` and
     `not vectorized:`, but the diagnostic emitted was "the cost-model
     indicates that vectorization is not beneficial" — matching neither. Four
     variants read as "no data" when the data was there and the filter dropped
     it. Note the first version of THIS rule blamed `-w`; that premise was
     tested and is false (8 remarks emitted with and without it). The bug was
     never at the compiler. It was in the filter, which is worse, because a
     compiler flag is visible and a too-narrow regex is not.

  H2 A TIMEOUT IS A VERDICT — every `subprocess.run(..., timeout=)` must be
     guarded by `except TimeoutExpired`. Incident: a generated candidate looped
     forever and killed a 151-kernel run outright, instead of scoring REJECT.

  H3 CONTEXT TRAVELS WITH EXTRACTION — corpus evaluation must use the
     in-context evaluator, never the standalone one. Incident: extracted TSVC
     candidates lost `#define LEN_1D`; 34/34 compile-failed and the run
     reported "0 recovered", which was nearly published as a finding.

  H4 THE ORACLE IS DETERMINISTIC — running the correctness gate twice must give
     the same verdict. A nondeterministic interestingness test produces
     garbage, silently (C-Vise, 2026).
"""
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
# Files whose job is to READ compiler diagnostics.
READS_DIAGNOSTICS = {"tsvc_rate.py", "c_choose.py"}


def h1_filter_extracts_something() -> list[str]:
    """A diagnostic filter that matches ZERO lines of NON-EMPTY compiler output
    is broken, and "zero matches" must never be read as "nothing happened".

    Demanding that a filter match EVERY remark is the wrong property — the
    first version of this rule did that and false-positived on `baseline()`,
    which matches only `vectorized loop` because it counts successes and
    legitimately ignores failures. The checkable property is weaker and
    correct: given output the compiler definitely produced, the tool must
    extract something.
    """
    probe = ROOT / "optimizer" / "probe" / "none60" / "k.c"
    if not probe.exists():
        return ["probe source missing; cannot exercise the filter"]
    r = subprocess.run(["clang", "-O3", "-mcpu=native", "-c", str(probe),
                        "-o", "/dev/null", "-Rpass=loop-vectorize",
                        "-Rpass-missed=loop-vectorize"],
                       capture_output=True, text=True)
    if not [l for l in r.stderr.splitlines() if "remark:" in l]:
        return ["compiler emitted no remarks; H1 cannot be exercised"]
    sys.path.insert(0, str(TOOLS))
    import tsvc_rate
    vec, allk = tsvc_rate.baseline(probe, probe.parent)
    bad = []
    if not allk:
        bad.append("tsvc_rate.baseline: recognised NO kernels from real output")
    if not vec:
        bad.append("tsvc_rate.baseline: matched ZERO vectorized-loop remarks "
                   "from non-empty compiler output — filter is broken, and a "
                   "zero here would read as 'nothing vectorized'")
    return bad


def h2_timeout_is_a_verdict() -> list[str]:
    """Every timed subprocess must catch TimeoutExpired."""
    bad = []
    for f in sorted(TOOLS.glob("*.py")):
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        guarded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                names = " ".join(ast.dump(h) for h in node.handlers)
                if "TimeoutExpired" in names:
                    for n in ast.walk(node):
                        guarded.add(id(n))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and any(k.arg == "timeout" for k in node.keywords)
                    and id(node) not in guarded):
                bad.append(f"{f.name}:{node.lineno}: timed call not guarded "
                           f"by except TimeoutExpired")
    return bad


def h3_context_travels() -> list[str]:
    """Corpus evaluation must use the in-context evaluator."""
    src = (TOOLS / "tsvc_rate.py").read_text()
    bad = []
    if "def eval_ctx" not in src:
        bad.append("tsvc_rate.py: no in-context evaluator")
    if re.search(r"(?<!def )\bc_choose\.evaluate\(", src):
        bad.append("tsvc_rate.py: calls the STANDALONE evaluator on corpus "
                   "candidates — context would not travel with extraction")
    return bad


def h4_oracle_is_deterministic() -> list[str]:
    """Two runs of the correctness gate must agree."""
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, str(TOOLS / "choose_check.py")],
                           capture_output=True, text=True)
        outs.append([l.split()[:3] for l in r.stdout.splitlines()
                     if "EXACT" in l or "INCORRECT" in l])
    return ([] if outs[0] == outs[1] else
            ["choose_check: correctness verdicts differ between runs"])


def main() -> int:
    checks = [("H1 filter extracts from real output", h1_filter_extracts_something),
              ("H2 a timeout is a verdict", h2_timeout_is_a_verdict),
              ("H3 context travels with extraction", h3_context_travels),
              ("H4 the oracle is deterministic", h4_oracle_is_deterministic)]
    bad = 0
    for name, fn in checks:
        errs = fn()
        bad += len(errs)
        print(f"  {'FAIL' if errs else 'ok  '}  {name}")
        for e in errs:
            print(f"          {e}")
    print(f"\nHARNESS {'PASS' if bad == 0 else 'FAIL'}: the test-case validity "
          f"discipline is checked, not remembered"
          + ("" if bad == 0 else f" ({bad} violation(s))"))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
