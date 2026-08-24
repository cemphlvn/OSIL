#!/usr/bin/env python3
"""C projection harness (G17): the lowering-ecosystem analog of G3 and G14.

Metric — PRESERVATION SCORE (spec/conformance.md): the fraction of the C
projection's CONTRACT.osil `preserves` fields mechanically verified over every
case in conformance/interop/c/cases/. Gate G17 requires score = 4/4.

Fields (profiles/ecosystem/c/CONTRACT.osil):
  realization_identity  — every realization the declared guards license emits C
                          that COMPILES. None silently dropped, none emitted
                          that the guards did not license.
  value_equivalence     — the emitted C, run, computes the value the
                          declaration says it computes, checked against a
                          reference computed independently in Python. Fixture
                          data is chosen so the exact result is invariant under
                          reassociation, so this field measures the PROJECTION
                          and not floating-point regime drift (which is what
                          the guards are for).
  guard_selectivity     — the negative lane: with the licensing guard WITHHELD,
                          the realization it licensed must be ABSENT. Pattern
                          inherited from G14.
  emission_determinism  — the same declaration emits BYTE-IDENTICAL C across
                          runs. Required because a projection whose output
                          drifts cannot be audited.

NOT verified here, and declared `may_lose` for a measured reason: the emitted C
does not CARRY its licence. C has no syntax for the guards — `restrict` is
inter-array only and recovered 0 of 151 TSVC loops (optimizer/repro/). The
licence survives as a comment: provenance, not semantics.

Run: `just cproj`  (needs a C compiler; uses $CC or clang)
Writes: conformance/matrix/matrix.yaml cell (own cell only, idempotent) +
docs/reports/roundtrip-c-<date>.md
"""
from __future__ import annotations

import datetime
import os
import shutil
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from osil_check import tokenize  # reference lexer — dogfood, do not fork

PRESERVES = ["realization_identity", "value_equivalence",
             "guard_selectivity", "emission_determinism"]
CASES = ROOT / "conformance" / "interop" / "c" / "cases"
REFUSALS = ROOT / "conformance" / "interop" / "c" / "refusals"
CC = os.environ.get("CC", "clang")
LANE_WIDTH = 4
INTERLEAVES = [1, 2, 4, 8]


class Unsupported(ValueError):
    """A DELIBERATE refusal: a construct the projection knowingly does not
    support. Distinguished from incidental errors (a bad int, a missing key)
    so a refusal fixture cannot pass by crashing for the wrong reason —
    that would be a fabricated pass, which conformance/README.md forbids."""


# ----------------------------------------------------------------- case reader
def parse_case(path: Path) -> dict:
    """Read a case declaration using the REFERENCE lexer."""
    toks = [t for t in tokenize(path.read_text()) if t.kind != "eof"]
    words = [t.text for t in toks]

    def block(head: str) -> list[str]:
        """Tokens between the brace following `head` and its match."""
        if head not in words:
            return []
        i = words.index(head)
        while i < len(words) and words[i] != "{":
            i += 1
        depth, out = 0, []
        for w in words[i:]:
            if w == "{":
                depth += 1
                if depth == 1:
                    continue
            elif w == "}":
                depth -= 1
                if depth == 0:
                    break
            out.append(w)
        return out

    def kvs(ws: list[str]) -> dict:
        d = {}
        for j, w in enumerate(ws):
            if w == "=" and j and j + 1 < len(ws):
                d[ws[j - 1]] = ws[j + 1]
        return d

    name = words[words.index("model") + 1]
    return {
        "name": name,
        "path": path,
        "constraints": kvs(block("constraints")),
        "guards": kvs(block("guards")),
        "sir": block("sir"),
    }


def read_sir(sir: list[str]) -> dict:
    """(reduce <op> (range <arr> <n>)) -> a flat description."""
    w = [t for t in sir if t not in "()"]
    if not w or w[0] != "reduce":
        raise Unsupported(f"unsupported SIR head: {w[:1]}")
    op, src = w[1], w[2]
    if src != "range":
        raise Unsupported(f"unsupported source form: {src}")
    if op not in IDENT:
        raise Unsupported(f"unsupported reduction operator: {op} "
                          f"(no declared identity element)")
    return {"op": op, "src": "range", "arr": w[3], "n": int(w[4])}


# ------------------------------------------------------------------ projection
def realizations(sir: dict, guards: dict) -> list[dict]:
    """The licensed space. `chain` always; `lanes` only under the regime that
    licenses reordering. Guards are DATA (ADR-0009), never code paths."""
    out = [{"kind": "chain"}]
    if guards.get("numeric_semantics") == "reassociable":
        out += [{"kind": "lanes", "w": LANE_WIDTH, "i": i} for i in INTERLEAVES]
    return out


IDENT = {"mul": "1.0f", "add": "0.0f"}
COP = {"mul": "*", "add": "+"}


def emit_c(case: dict, sir: dict, r: dict) -> str:
    """Deterministic by construction: no dict iteration, no hashing, no time."""
    op, arr, n = sir["op"], sir["arr"], sir["n"]
    o, idv = COP[op], IDENT[op]
    lic = "\n".join(f"//   {k} = {case['guards'][k]}" for k in sorted(case["guards"]))
    if r["kind"] == "chain":
        body = (f"    float acc = {idv};\n"
                f"    for (int i = 0; i < {n}; ++i) acc = acc {o} {arr}[i];\n"
                f"    return acc;")
        what = "chain (sequential fold — requires no guard)"
    else:
        w, il = r["w"], r["i"]
        decls = "\n".join(f"    vec_t acc{k} = {{ {', '.join([idv]*w)} }};"
                          for k in range(il))
        upd = "\n".join(
            "        {{ vec_t v = {{ {} }}; acc{k} = acc{k} {o} v; }}".format(
                ", ".join(f"{arr}[i + {k*w+l}]" for l in range(w)), k=k, o=o)
            for k in range(il))
        fold = "\n".join(f"    acc0 = acc0 {o} acc{k};" for k in range(1, il))
        comb = f" {o} ".join(f"acc0[{l}]" for l in range(w))
        step = w * il
        body = (f"    typedef float vec_t __attribute__((vector_size({4*w})));\n"
                f"{decls}\n    int i = 0;\n"
                f"    for (; i + {step} <= {n}; i += {step}) {{\n{upd}\n    }}\n"
                f"{fold}\n    float acc = {comb};\n"
                f"    for (; i < {n}; ++i) acc = acc {o} {arr}[i];\n"
                f"    return acc;")
        what = f"lanes width={w} interleave={il} ({w*il} independent chains)"
    return (f"// GENERATED by tools/c_roundtrip.py — do not edit.\n"
            f"// case        : {case['name']}\n"
            f"// realization : {what}\n"
            f"// licensed by :\n{lic}\n"
            f"// NOTE: the licence above is a COMMENT. C cannot carry it as\n"
            f"// semantics — see profiles/ecosystem/c/PROFILE.md.\n\n"
            f"float kernel(const float * restrict {arr}) {{\n{body}\n}}\n")


# ------------------------------------------------------------------- reference
def fill(op: str, i: int) -> float:
    """Fixture data chosen so the exact result is INVARIANT under reassociation:
    products stay small and order-free, sums stay integral and below 2^24."""
    return (2.0 if i < 4 else 1.0) if op == "mul" else float(i % 4)


def reference(op: str, n: int) -> float:
    acc = 1.0 if op == "mul" else 0.0
    for i in range(n):
        acc = acc * fill(op, i) if op == "mul" else acc + fill(op, i)
    return acc


HARNESS = """
#include <stdio.h>
float kernel(const float * restrict a);
static float A[%(n)d];
int main(void){
    for (int i = 0; i < %(n)d; ++i) A[i] = %(fill)s;
    printf("%%.9g\\n", (double)kernel(A));
    return 0; }
"""


def build_and_run(src: str, sir: dict, tmp: Path) -> tuple[bool, float | None, str]:
    f = "(i < 4 ? 2.0f : 1.0f)" if sir["op"] == "mul" else "(float)(i % 4)"
    cfile = tmp / "k.c"
    cfile.write_text(src + HARNESS % {"n": sir["n"], "fill": f})
    exe = tmp / "k"
    p = subprocess.run([CC, "-O2", "-std=c11", "-w", str(cfile), "-o", str(exe)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return False, None, p.stderr.strip()[:200]
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    if r.returncode != 0:
        return False, None, "runtime failure"
    return True, float(r.stdout.strip()), ""


# ------------------------------------------------------------------------ main
def main() -> int:
    if shutil.which(CC) is None:
        print(f"C-PROJ SKIP: no C compiler ({CC}) on PATH")
        return 0
    today = datetime.date.today().isoformat()
    cases = sorted(CASES.glob("*.osil"))
    if not cases:
        print("C-PROJ FAIL: no cases"); return 1

    field = {f: True for f in PRESERVES}
    field["declared_loss_holds"] = True   # may_lose lane, reported separately
    rows, names = [], []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for path in cases:
            case = parse_case(path)
            sir = read_sir(case["sir"])
            names.append(case["name"])
            rs = realizations(sir, case["guards"])
            want = reference(sir["op"], sir["n"])

            # --- realization_identity + value_equivalence
            for r in rs:
                src = emit_c(case, sir, r)
                ok, got, err = build_and_run(src, sir, tmp)
                tag = r["kind"] + (f"-w{r['w']}i{r['i']}" if r["kind"] == "lanes" else "")
                if not ok:
                    field["realization_identity"] = False
                    rows.append((case["name"], tag, "COMPILE-FAIL", err)); continue
                if got != want:
                    field["value_equivalence"] = False
                    rows.append((case["name"], tag, "VALUE-MISMATCH",
                                 f"got {got} want {want}"))
                else:
                    rows.append((case["name"], tag, "ok", f"{got:g}"))

            # --- guard_selectivity: withhold the guard, the lanes must vanish
            withheld = realizations(sir, {})
            kinds = sorted({r["kind"] for r in withheld})
            declared_exact = case["guards"].get("numeric_semantics") == "exact"
            # POSITIVE assertion, not merely "nothing leaked": with no licensing
            # guard the space must be EXACTLY {chain} -- one realization, the
            # order-preserving one. A vacuous pass (nothing to withhold) is not
            # evidence, so a case declaring `exact` is checked the same way.
            if kinds != ["chain"] or len(withheld) != 1:
                field["guard_selectivity"] = False
                rows.append((case["name"], "guard-withheld", "LEAKED",
                             f"expected exactly [chain], got {kinds}"))
            elif declared_exact and len(rs) != 1:
                field["guard_selectivity"] = False
                rows.append((case["name"], "guard-withheld", "LEAKED",
                             f"`exact` licensed {len(rs)} realizations"))
            else:
                rows.append((case["name"], "guard-withheld", "ok",
                             f"space {len(rs)} -> exactly [chain]"))

            # --- emission_determinism
            a = emit_c(case, sir, rs[-1])
            b = emit_c(case, sir, rs[-1])
            if a != b:
                field["emission_determinism"] = False
                rows.append((case["name"], "determinism", "DRIFT", ""))
            else:
                rows.append((case["name"], "determinism", "ok", f"{len(a)} bytes"))

    # --- may_lose lane: the DECLARED LOSS must actually occur (XFAIL).
    # `may_lose { declared_licence }` asserts C cannot carry the guards. That
    # is the ADR's central measured claim, so it gets a fixture rather than
    # prose: strip every comment from the emitted C and the guard must appear
    # NOWHERE in what remains. If it ever does, C (or our emitter) gained a way
    # to carry the licence — the declared loss is no longer a loss, and that
    # must be RATIFIED through the lifecycle, never flip silently.
    with tempfile.TemporaryDirectory() as td2:
        for path in cases:
            case = parse_case(path)
            sir = read_sir(case["sir"])
            src = emit_c(case, sir, realizations(sir, case["guards"])[-1])
            stripped = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
            stripped = re.sub(r"//[^\n]*", " ", stripped)
            leaked = [k for k in case["guards"] if k in stripped]
            if leaked:
                field["declared_loss_holds"] = False
                rows.append((case["name"], "may_lose", "XPASS-ALARM",
                             f"licence survived stripping: {leaked} — RATIFY"))
            else:
                rows.append((case["name"], "may_lose", "XFAIL-HOLDS",
                             "licence is comment-only, as declared"))

    # --- refusal lane: the projector must refuse what it does not support
    for path in sorted(REFUSALS.glob("*.osil")):
        case = parse_case(path)
        try:
            read_sir(case["sir"])
        except Unsupported as e:
            rows.append((case["name"], "REFUSED", "XFAIL-HOLDS", str(e)[:52]))
        except Exception as e:
            # Refused, but by ACCIDENT. A fixture that passes because the
            # projector happened to crash is not evidence of a refusal.
            field["realization_identity"] = False
            rows.append((case["name"], "REFUSED", "WRONG-REASON",
                         f"{type(e).__name__}: {str(e)[:40]}"))
        else:
            field["realization_identity"] = False
            rows.append((case["name"], "REFUSED", "XPASS-ALARM",
                         "projected a construct it does not support"))

    loss_ok = field.pop("declared_loss_holds")
    verified = sum(field.values())
    status = "pass" if verified == len(PRESERVES) and loss_ok else "fail"
    for c, tag, st, note in rows:
        print(f"  {c:<6} {tag:<16} {st:<14} {note}")
    why = "" if status == "pass" else (
        "" if verified == len(PRESERVES) else " [preserves field failed]")
    if status != "pass" and verified == len(PRESERVES):
        why = " [preserves 4/4, but a DECLARED LOSS no longer holds — ratify]"
    print(f"\nC-PROJ {status.upper()}: preservation score {verified}/{len(PRESERVES)}"
          f"{why} over cases {names}")
    for f in PRESERVES:
        print(f"  {'PASS' if field[f] else 'FAIL'}  {f}")
    print(f"  {'XFAIL-HOLDS' if loss_ok else 'XPASS-ALARM'}  "
          f"may_lose declared_licence (the loss is real, and tested)")

    write_matrix_cell(field, verified, status, names, today)
    write_report(field, verified, status, rows, names, today)
    return 0 if status == "pass" else 1


def write_matrix_cell(field, verified, status, names, today):
    """Rewrite ONLY our own cell; other adapters' cells pass through untouched."""
    mpath = ROOT / "conformance" / "matrix" / "matrix.yaml"
    txt = mpath.read_text()
    head, *blocks = txt.split("  - spec:")
    cells = ["  - spec:" + b for b in blocks if "c-projection" not in b]
    cc = subprocess.run([CC, "--version"], capture_output=True, text=True)
    ver = cc.stdout.splitlines()[0] if cc.returncode == 0 else CC
    fields = ", ".join(f"{f}: {str(field[f]).lower()}" for f in PRESERVES)
    cells.append(f"""  - spec: "0.0.0-draft (grammar v0.6)"
    adapter: "c-projection v0 (tools/c_roundtrip.py)"
    upstream: "{ver}"
    status: {status}
    preservation_score: "{verified}/{len(PRESERVES)}"
    fields: {{{fields}}}
    cases: [{', '.join(names)}]
    checked: {today}
""")
    mpath.write_text(head + "".join(cells))


def write_report(field, verified, status, rows, names, today):
    p = ROOT / "docs" / "reports" / f"roundtrip-c-{today}.md"
    lines = [f"# C projection round-trip — {today}", "",
             f"Status: **{status}** — preservation score {verified}/{len(PRESERVES)}",
             f"Cases: {', '.join(names)}", "", "| field | result |", "|---|---|"]
    lines += [f"| `{f}` | {'PASS' if field[f] else 'FAIL'} |" for f in PRESERVES]
    lines += ["", "| case | realization | result | note |", "|---|---|---|---|"]
    lines += [f"| {c} | `{t}` | {s} | {n} |" for c, t, s, n in rows]
    lines += ["", "## Declared losses (not failures)", "",
              "`may_lose { declared_licence }` — C has no syntax for the guards.",
              "The emitted C carries its licence as a comment: provenance, not",
              "semantics. Evidence: `restrict` on every array pointer across all",
              "151 TSVC loops recovered 0 (`optimizer/repro/`)."]
    p.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
