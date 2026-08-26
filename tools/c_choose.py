#!/usr/bin/env python3
"""Transformation chooser (OQ-2, second half): decide WHAT to do with the
dependence facts the lifter recovers, apply it, and prove it paid.

The lifter answers "is this dependence false?". This answers "so what?".

ALGORITHM — loop distribution by strongly-connected components (Allen &
Kennedy). Build the statement-level dependence graph, find SCCs, emit one loop
per SCC in topological order:
  * statements in the SAME SCC form a recurrence and MUST stay together;
  * distinct SCCs may be split, and splitting is what lets a vectorizable
    statement escape a loop pinned by a neighbouring recurrence.
A single SCC means the loop is indivisible -- reported, not forced.

THREE GATES, in this order. A candidate must clear all three:
  1. LEGAL      — the topological order exists (no cycle spanning the split)
  2. CORRECT    — differential test against the original, on the same inputs
  3. FASTER     — measured, by a margin wider than run-to-run noise
Gate 3 is not optional. `optimizer/probe/none60/` produced an exact
transformation that was 0.33x -- three times SLOWER. Correct-but-slower is a
regression, and a chooser without a stopwatch would ship it.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CC = "clang"


def arch_flag(cc: str = CC) -> str:
    """`-mcpu=native` on ARM, `-march=native` on x86, neither if unsupported.

    Hardcoding `-mcpu=native` made every measurement in this repo ARM-only: on
    x86 clang it is a deprecated alias that tunes nothing, so the numbers would
    silently be untuned-baseline numbers. `demo/run.sh` has probed for this
    since G17; the gated tools had not. Probed once per process, not per call.
    """
    global _ARCH
    try:
        return _ARCH
    except NameError:
        pass
    _ARCH = ""
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "a.c"
        src.write_text("int main(void){return 0;}\n")
        for f in ("-mcpu=native", "-march=native"):
            r = subprocess.run([cc, f, str(src), "-o", str(Path(td) / "a")],
                               capture_output=True, text=True)
            if r.returncode == 0:
                _ARCH = f
                break
    return _ARCH
CANDIDATE_KINDS = ("distribute", "dead-store", "preload", "peel-wraparound",
                   "if-convert")
NOISE_MARGIN = 1.05      # must beat the original by >5%: the measured spread
                         # in optimizer/probe/none60 reached 2.4% run-to-run


def sccs(n: int, edges: set[tuple[int, int]]) -> list[list[int]]:
    """Tarjan. Returns SCCs in reverse topological order."""
    adj = {i: [] for i in range(n)}
    for a, b in edges:
        if a != b:
            adj[a].append(b)
    idx, low, on, stack, out = {}, {}, set(), [], []
    counter = [0]

    def strong(v):
        idx[v] = low[v] = counter[0]; counter[0] += 1
        stack.append(v); on.add(v)
        for w in adj[v]:
            if w not in idx:
                strong(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = stack.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            out.append(sorted(comp))
    for v in range(n):
        if v not in idx:
            strong(v)
    return out


def dead_stores(loop: dict) -> list[int]:
    """Statements whose ONLY effect is a store overwritten at a later iteration.

    Legality, all four required:
      1. the statement writes exactly one array element, arr[i+k];
      2. a carried OUTPUT dependence covers it — some statement writes the same
         location at a later iteration;
      3. nothing READS that location between the two writes — INCLUDING the
         dead statement's own reads at a DIFFERENT offset, which touch that
         address on another iteration;
      4. the statement has no other effect (no second store, no scalar write);
      5. the overwrite is exactly ONE iteration later, and the statement is the
         LAST in the body. Both are properties of the EMITTER, not of the
         analysis: the removed store is replayed once, after the loop, and that
         replay reads the post-loop state. It equals the state the statement
         would have seen only at the final iteration, and only if no statement
         ran after it there.
    Fails any of them -> not eliminated. Refuse, never approximate.

    STEP. Condition 2 is an ADDRESS question, not an offset-ordering one. A
    write at arr[i+q] is overwritten by a write at arr[i'+p] only when the
    iteration i' = i + (q-p) EXISTS, which under step s requires
    (q-p) % s == 0 — the same test the lifter applies (conformance/lift
    /README.md). Omitting it made every 4x-unrolled loop look like three dead
    stores: found on opus silk/float/scale_copy_vector_FLP.c, where the chooser
    proposed deleting three of four live stores and the differential gate
    caught it. See conformance/lift/step-pins/.
    """
    n = len(loop["stmts"])
    step = loop.get("step") or 1
    out = []
    for si in range(n):
        writes = [a for a in loop["accesses"] if a["stmt"] == si and a["is_write"]]
        if len(writes) != 1:
            continue                                   # (1) and (4)
        w = writes[0]
        if w["coeff"] != 1:
            continue
        if any(nm for nm, is_w, st in loop["scalars"] if is_w and st == si):
            continue                                   # (4) also writes a scalar
        if si != n - 1:
            continue                                   # (5) replay position
        # (2) a later-iteration write to the same location. The NEAREST one:
        # the location is overwritten by the first subsequent write, which is
        # the aliasing write with the largest offset below w's. Taking whichever
        # came first in access order made the recogniser's answer depend on
        # traversal order, and with condition (5) measuring the distance, that
        # silently lost legitimate cases.
        cands = [a for a in loop["accesses"]
                 if a["is_write"] and a["array"] == w["array"] and a["coeff"] == 1
                 and a["stmt"] != si and a["offset"] < w["offset"]
                 and (w["offset"] - a["offset"]) % step == 0]
        overwriter = max(cands, key=lambda a: a["offset"]) if cands else None
        if overwriter is None:
            continue
        if (w["offset"] - overwriter["offset"]) // step != 1:
            continue                                   # (5) one iteration only
        # (3) no read of that location between the two writes. Left
        # deliberately WITHOUT a congruence test: over-blocking eliminates
        # fewer stores, which is the safe direction.
        blocked = False
        for a in loop["accesses"]:
            if a["is_write"] or a["array"] != w["array"] or a["coeff"] != 1:
                continue
            if a["stmt"] == si and a["offset"] == w["offset"]:
                continue                # the statement's own read of the SAME
                                        # address is consumed here. A read at a
                                        # DIFFERENT offset is a different
                                        # address on a different iteration and
                                        # must still block: opus src/analysis.c
                                        # :915 reads m[i+16] and writes m[i+24],
                                        # eight iterations apart, and skipping
                                        # it emitted wrong code.
            if overwriter["offset"] <= a["offset"] <= w["offset"]:
                blocked = True
                break
        if blocked:
            continue
        out.append(si)
    return out


ASSIGN = re.compile(r"(?<![=!<>+\-*/])(\+=|-=|\*=|/=|=)(?!=)")


def guards_of(loop: dict) -> list:
    g = loop.get("guards") or []
    return list(g) + [None] * (len(loop["stmts"]) - len(g))


def render(loop: dict, i: int) -> str:
    """A statement as the ORIGINAL wrote it — predicate included.

    Every emitter renders through here. A family that printed `loop["stmts"][i]`
    directly would drop the `if` and emit an unconditional store: correct-looking
    code that runs the guarded work on every iteration."""
    g = guards_of(loop)[i]
    st = loop["stmts"][i]
    return f"if ({g}) {{ {st}; }}" if g else f"{st};"


def predicate(loop: dict, i: int) -> str:
    """The SELECT form: `lhs = P ? rhs : lhs`.

    The false arm is the lvalue itself, so iterations the guard excluded write
    back what was already there. That is what makes the store unconditional
    without changing the value — and it is also why the lifter records a READ of
    the store location for a guarded statement."""
    g = guards_of(loop)[i]
    st = loop["stmts"][i]
    if g is None:
        return f"{st};"
    m = ASSIGN.search(st)
    if m is None:
        return f"{st};"
    lhs, op, rhs = st[:m.start()].strip(), m.group(1), st[m.end():].strip()
    if op == "=":
        return f"{lhs} = ({g}) ? ({rhs}) : ({lhs});"
    return f"{lhs} = ({g}) ? (({lhs}) {op[0]} ({rhs})) : ({lhs});"


def _rhs_sub(stmt: str, old: str, new: str) -> str:
    """Replace `old` with `new` only to the RIGHT of the assignment operator."""
    m = ASSIGN.search(stmt)
    if not m:
        return stmt.replace(old, new)
    head, tail = stmt[:m.end()], stmt[m.end():]
    return head + tail.replace(old, new)


def preloadable(loop: dict) -> list[dict]:
    """Carried ANTI dependences that a preload would break.

    `b[i] = a[i] * a[i+1] * d[i]` reads a[i+1] BEFORE the iteration that writes
    it, so the value read is the pre-loop one. Copying that array once up front
    and redirecting only those reads makes the loop dependence-free.

    Only reads at the offsets actually overwritten are redirected. Redirecting
    every read of the array would be WRONG: in the same statement `a[i]` is the
    value just written this iteration, and must stay live.

    STEP, as in dead_stores(): a read at arr[i+r] sees a write at arr[i'+w]
    only when iteration i' = i + (r-w) exists, i.e. (r-w) % s == 0. Without
    that test an unrolled loop redirects reads that were never overwritten,
    handing them the pre-loop value instead of the current one — wrong in the
    same direction, and silently."""
    step = loop.get("step") or 1
    out = []
    for d in loop["deps"]:
        if d["kind"] != "anti" or not d["carried"] or d["array"].startswith("$"):
            continue
        arr = d["array"]
        reads = sorted({a["offset"] for a in loop["accesses"]
                        if a["array"] == arr and not a["is_write"]
                        and a["coeff"] == 1 and a["offset"] > 0})
        writes = {a["offset"] for a in loop["accesses"]
                  if a["array"] == arr and a["is_write"] and a["coeff"] == 1}
        # only offsets that are BOTH read ahead and written later need saving
        need = [o for o in reads
                if any(o > w and (o - w) % step == 0 for w in writes)]
        if need:
            out.append({"array": arr, "offsets": need})
    # de-duplicate by array
    seen, uniq = set(), []
    for x in out:
        if x["array"] in seen:
            continue
        seen.add(x["array"]); uniq.append(x)
    return uniq


# `j = i`, `j = k`, and also `j = i + 1` / `j = k - 2`. The first version
# matched only bare identifiers, which covered s291/s292 and missed s121, s128
# and s4116 — the price said +3 and the recogniser could only reach +2.
SCALAR_ASSIGN = re.compile(r"^\s*(\w+)\s*=\s*(\w+)\s*(?:([+-])\s*(\d+)\s*)?$")


def wraparound(loop: dict) -> dict | None:
    """Recognise wrap-around subscript scalars and solve their steady state.

    `im1 = n-1; for i { a[i] = b[i] + b[im1]; im1 = i; }` — `im1` equals `i-1`
    on every iteration except the first. Symbolic simulation finds the offsets:
    each scalar holds either an integer offset from `i` or UNKNOWN, the body is
    replayed until offsets stabilise, and the number of replays needed is the
    PEEL DEPTH.

    This is a NORMALISATION, not a new analysis: once the subscripts are affine
    the existing machinery applies unchanged. U13's verdict — wrap-around needs
    no declaration, only induction-variable substitution.
    """
    subs = {u.split("[")[-1].rstrip("]") for u in loop["unhandled"]
            if "(wraparound)" in u}
    if not subs:
        return None
    assigns = []                      # (target, source) in program order
    for st in loop["stmts"]:
        m = SCALAR_ASSIGN.match(st.strip())
        if m:
            k = int(m.group(4)) * (1 if m.group(3) == "+" else -1) if m.group(3) else 0
            assigns.append((m.group(1), m.group(2), k))
    if not assigns:
        return None

    # A WRAP-AROUND scalar is assigned AFTER its use, so the value read is the
    # previous iteration's. A scalar assigned BEFORE its use (`j = i+1; a[j]`)
    # is a same-iteration ALIAS — a different pattern needing plain
    # substitution, no peeling. Modelling the second as the first produced
    # silently wrong code for s121, caught by the differential gate.
    idx = loop["index"]
    use_at = {}
    for n, st in enumerate(loop["stmts"]):
        for sc in subs:
            if f"[ {sc} ]" in st:
                use_at.setdefault(sc, n)
    assign_at = {t: n for n, st in enumerate(loop["stmts"])
                 for t, _, _ in assigns if SCALAR_ASSIGN.match(st.strip())
                 and SCALAR_ASSIGN.match(st.strip()).group(1) == t}
    for sc in subs:
        if sc in use_at and sc in assign_at and assign_at[sc] < use_at[sc]:
            return None            # forward alias, not a wrap-around: refuse

    state: dict[str, int | None] = {t: None for t, _, _ in assigns}
    seen, depth = [], 0
    for step in range(1, 9):
        nxt = dict(state)
        for tgt, src, k in assigns:
            # `im2 = im1` copies the CURRENT value: the offset is unchanged.
            # Subtracting 1 here as well as in the ageing step below double-aged
            # every chained scalar — `im2` solved to -3 instead of -2, and the
            # emitted code was silently wrong. The differential gate caught it.
            base = 0 if src == idx else state.get(src)
            nxt[tgt] = None if base is None else base + k
        # entering the NEXT iteration every offset ages by one
        state = {k: (None if v is None else v - 1) for k, v in nxt.items()}
        key = tuple(sorted(state.items(), key=lambda kv: kv[0]))
        if key in seen:
            break
        seen.append(key)
        depth = step
        if all(v is not None for v in state.values()):
            break
    if any(state.get(sc) is None for sc in subs):
        return None                   # never stabilises: refuse
    return {"kind": "peel-wraparound", "offsets": state, "depth": depth,
            "why": f"wrap-around scalars {dict((k, state[k]) for k in sorted(subs))}"
                   f" stabilise after {depth} iteration(s): peel then substitute"}


def plans(loop: dict) -> list[dict]:
    """Every applicable family, not the first one that matches.

    Choosing by a fixed priority was wrong: preload fired before distribute on
    s212/s211/s1213 and measured WORSE (1.13x where distribute got 2.11x). The
    stopwatch exists precisely so the order does not have to be guessed --
    propose them all, measure, keep the winner."""
    n = len(loop["stmts"])
    # The emitter builds a standalone function whose parameters are the array
    # names. A member-qualified name (`p->x`) is a valid ARRAY but not a valid
    # PARAMETER, so there is no emission form for it and no transformation to
    # propose. Refusing here is the honest answer; before this, such loops were
    # counted as candidates and then died as compile-fail.
    # A guarded loop is offered if-conversion and NOTHING else. The other four
    # emitters render `loop["stmts"]` in ways predication would have to be
    # threaded through (preload rewrites subscripts inside statement text; peel
    # substitutes scalars), and a family that dropped a guard would emit an
    # unconditional store. Composing predication with the rest is a STAGE
    # question (G15), deliberately left to one — refuse, do not approximate.
    if any(g is not None for g in guards_of(loop)):
        if loop["unhandled"]:
            return [{"kind": "refuse", "why": f"unhandled: {loop['unhandled'][0]}"}]
        return [{"kind": "if-convert",
                 "guarded": [i for i, g in enumerate(guards_of(loop))
                             if g is not None],
                 "why": "predicate lifted onto the store; the loop becomes "
                        "straight-line"}]
    unnameable = sorted({a["array"] for a in loop["accesses"]
                         if not a["array"].isidentifier()})
    if unnameable:
        return [{"kind": "refuse",
                 "why": f"no emission form for qualified base: {unnameable[0]}"}]
    if loop["unhandled"]:
        w = wraparound(loop)
        if w and all("(wraparound)" in u for u in loop["unhandled"]):
            return [w]
        return [{"kind": "refuse",
                 "why": f"unhandled: {loop['unhandled'][0]}"}]
    # AFTER the refusal checks, not before. A single-statement loop the lifter
    # REFUSED was reported `none` — "nothing to do here" — rather than `refuse`,
    # which is a different claim and the wrong one. Every one-statement loop with
    # a non-affine subscript in every corpus scan so far was mis-filed this way.
    if n < 2:
        return [{"kind": "none", "why": "single statement"}]
    out = []
    dead = dead_stores(loop)
    if dead and len(dead) < n:
        out.append({"kind": "dead-store", "dead": dead,
                    "live": [i for i in range(n) if i not in dead],
                    "why": f"S{dead} overwritten later with no intervening read"})
    pre = preloadable(loop)
    if pre:
        out.append({"kind": "preload", "preload": pre,
                    "why": "carried anti dependence: preload the pre-loop values"})
    d = _distribute(loop)
    if d:
        out.append(d)
    return out or [{"kind": "none",
                    "why": "one SCC: the statements form a recurrence, indivisible"}]


def _distribute(loop: dict) -> dict | None:
    """The SCC split. Dead-store used to be re-offered from here as well as from
    `plans()`, so every dead-store loop was proposed TWICE — measured twice, and
    counted twice in the witness score. `plans()` owns that family."""
    n = len(loop["stmts"])
    edges = set()
    for d in loop["deps"]:
        a, b = d["src"], d["dst"]
        if not (0 <= a < n and 0 <= b < n):
            continue
        edges.add((a, b))
        if d["array"].startswith("$"):
            # A SCALAR is one memory cell reused every iteration. Splitting the
            # statements that share it would leave the reader seeing the LAST
            # iteration's value instead of its own -- silently wrong. Doing it
            # legally requires scalar EXPANSION (promote to an array), which is
            # not implemented, so the edge is made bidirectional: the two
            # statements are forced into one SCC and never separated.
            edges.add((b, a))
    comps = sccs(n, edges)          # reverse topological
    order = list(reversed(comps))   # topological: producers first
    if len(order) < 2:
        return None
    return {"kind": "distribute", "groups": order,
            "why": f"{len(order)} SCCs -> {len(order)} loops, "
                   f"topological order {[g for g in order]}"}


def _sig(loop: dict, p: dict) -> tuple[list, str, str, str]:
    """Parameters, loop header and index declaration — shared by every emitter
    and by the branch probe, so the probe measures the SAME loop the stopwatch
    times rather than a re-derived approximation of it."""
    arrays = sorted({a["array"] for a in loop["accesses"]})
    params = ", ".join(f"float * restrict {a}" for a in arrays) + ", int n"
    # A wrap-around scalar is initialised BEFORE the loop, outside what the
    # lifter sees. Both functions therefore take it as a parameter, and the
    # harness hands both the SAME value — so the differential test still
    # compares like with like, for that initial state.
    wscalars = sorted(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else []
    if wscalars:
        params = ", ".join(f"int {w}_init" for w in wscalars) + ", " + params
    hdr = loop["header"]
    # `for (i = 0; ...)` with `i` declared OUTSIDE the loop is ordinary C and
    # common in real code; the emitted standalone function has no such
    # declaration. Every repo loop that reached the differential test died here
    # as `use of undeclared identifier`, which reads as "not measurable" when it
    # actually means "the rig cannot build a harness for this shape yet".
    _idx = loop["index"] or "i"
    # The header is copied VERBATIM, which works only when everything it names
    # is a parameter. Real loops count to a file-scope constant or an enclosing
    # local (`i < posts`, `i < EHMER_MAX`), and every such loop died in the
    # differential test as `use of undeclared identifier` — reported as "not
    # measurable" when it means "the rig cannot build a harness for this shape".
    #
    # When the header names something the harness cannot supply, a NORMALISED
    # header is synthesised instead: same index, same step, counting to `n`. The
    # lower bound is pulled up far enough that the most negative subscript stays
    # in range, because the original bound may have existed precisely to keep
    # `a[i-1]` on the array. Both functions get the identical header, so the
    # differential test stays valid — what changes is only WHICH iterations the
    # shape is benchmarked over, and that was already synthetic.
    _kw = {"int", "long", "short", "unsigned", "signed", "size_t", "const",
           "for", "n", _idx}
    _known = _kw | {a["array"] for a in loop["accesses"]}
    _free = [t for t in re.findall(r"[A-Za-z_]\w*", hdr)
             if t not in _known and not t.isdigit()]
    if _free:
        _minoff = min([a["offset"] for a in loop["accesses"]] + [0])
        _lo = max(0, -_minoff)
        _st = loop.get("step") or 1
        _inc = f"++{_idx}" if _st == 1 else f"{_idx} += {_st}"
        hdr = f"for (int {_idx} = {_lo}; {_idx} < n; {_inc})"
    idecl = ("" if re.search(rf"\b(int|long|short|unsigned|size_t)\s+{_idx}\b", hdr)
             else f"    int {_idx};\n")
    return arrays, params, hdr, idecl


def emit_probe(loop: dict, p: dict) -> str:
    """A function that COUNTS how often each guard holds, on the harness's own
    seeded data.

    `branch_probability` is the quantity if-conversion's profitability turns on,
    and it is a property of the DATA, not of the loop. Declaring the dependence
    (PROFILE_DEPENDENCE) is only half the job — the rig has to be able to report
    the value it decided under."""
    arrays, params, hdr, idecl = _sig(loop, p)
    gs = [g for g in guards_of(loop) if g is not None]
    if not gs:
        return ""
    body = "\n".join(f"        if ({g}) k++;" for g in gs)
    return (f"long probe({params}) {{\n{idecl}    long k = 0;\n"
            f"    {hdr} {{\n{body}\n    }}\n    return k;\n}}\n")


def emit(loop: dict, p: dict, suffix: str) -> tuple[str, str]:
    """Emit (original, transformed) as two C functions with identical signatures."""
    arrays, params, hdr, idecl = _sig(loop, p)
    wscalars = sorted(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else []
    wdecl = "".join(f"    int {w} = {w}_init;\n" for w in wscalars)
    body_all = "\n".join(f"        {render(loop, i)}"
                         for i in range(len(loop["stmts"])))
    orig = (f"void orig{suffix}({params}) {{\n{wdecl}{idecl}"
            f"    {hdr} {{\n{body_all}\n    }}\n}}\n")
    if p["kind"] == "if-convert":
        b = "\n".join(f"        {predicate(loop, i)}"
                      for i in range(len(loop["stmts"])))
        xf = (f"void xform{suffix}({params}) {{\n{idecl}"
              f"    {hdr} {{\n{b}\n    }}\n}}\n")
        return orig, xf
    if p["kind"] == "dead-store":
        live = "\n".join(f"        {render(loop, i)}" for i in p["live"])
        # The removed store still has to happen once, for the final iteration —
        # IF there was one. `int i = n - 1` with n == 0 replays the store at
        # index -1, writing outside the array. The chooser's own harness cannot
        # see this: it measures at n = 32000 and nothing else. The independent
        # witness validator found it at n = 0 on its first run (G25).
        #
        # The last executed index is the largest `i < up` congruent to `lo`
        # mod step — not `up - 1`, which is only correct for step 1.
        _lo, _up = loop["lower"], loop["upper"]
        _st = loop.get("step") or 1
        last = f"({_lo}) + (((({_up}) - 1 - ({_lo})) / ({_st})) * ({_st}))"
        tail = "\n".join(
            f"    if (({_up}) > ({_lo})) {{ int {loop['index']} = {last}; "
            f"{render(loop, i)} }}"
            for i in p["dead"])
        xf = (f"void xform{suffix}({params}) {{\n{idecl}"
              f"    {hdr} {{\n{live}\n    }}\n{tail}\n}}\n")
        return orig, xf
    if p["kind"] == "peel-wraparound":
        idx, d = loop["index"], p["depth"]
        lo, up = loop["lower"], loop["upper"]
        # The peeled prologue is the ORIGINAL loop restricted to its first
        # `depth` iterations. Reusing the body verbatim means the pre-loop
        # initialisation of the scalars (which lives OUTSIDE the loop and the
        # lifter never sees) is never needed.
        body = "\n".join(f"        {st};" for st in loop["stmts"])
        steady = list(loop["stmts"])
        for sc, off in p["offsets"].items():
            steady = [st.replace(f"[ {sc} ]", f"[ {idx} {off:+d} ]") for st in steady]
        sbody = "\n".join(f"        {st};" for st in steady)
        xf = (f"void xform{suffix}({params}) {{\n{wdecl}"
              f"    int {idx};\n"
              f"    for ({idx} = ({lo}); {idx} < ({lo}) + {d} && {idx} < ({up}); ++{idx}) {{\n"
              f"{body}\n    }}\n"
              f"    for (; {idx} < ({up}); ++{idx}) {{\n{sbody}\n    }}\n}}\n")
        return orig, xf
    if p["kind"] == "preload":
        idx = loop["index"]
        tmps, saves, body = [], [], list(loop["stmts"])
        for x in p["preload"]:
            arr, t = x["array"], f"__pre_{x['array']}"
            tmps.append(t)
            saves.append(f"    for (int {idx} = ({loop['lower']}); "
                         f"{idx} < ({loop['upper']}) + {max(x['offsets'])}; ++{idx}) "
                         f"{t}[{idx}] = {arr}[{idx}];")
            for off in x["offsets"]:
                # RHS ONLY. `a[i+1] = a[i+2] * a[i+1]` has the same array and
                # offset on BOTH sides; rewriting the left one would redirect
                # the STORE into the scratch buffer and never write the real
                # array. The differential test caught exactly that.
                body = [_rhs_sub(st, f"{arr} [ {idx} + {off} ]",
                                 f"{t} [ {idx} + {off} ]") for st in body]
        decl = "".join(f"float * restrict {t}, " for t in tmps)
        allb = "\n".join(f"        {st};" for st in body)
        xf = (f"void xform{suffix}({decl}{params}) {{\n{idecl}"
              + "\n".join(saves) + f"\n    {hdr} {{\n{allb}\n    }}\n}}\n")
        return orig, xf
    if p["kind"] != "distribute":
        return orig, ""
    loops = []
    for g in p["groups"]:
        b = "\n".join(f"        {render(loop, i)}" for i in g)
        loops.append(f"    {hdr} {{\n{b}\n    }}")
    xf = (f"void xform{suffix}({params}) {{\n{idecl}" + "\n".join(loops) + "\n}\n")
    return orig, xf


# ---------------------------------------------------------------------------
# WHAT EACH FAMILY'S PROFITABILITY DEPENDS ON (G24 / partition B).
#
# The capability model exists because the ANALYSER has blind spots that must be
# declared and priced. The STOPWATCH has blind spots too, and until now there
# was no vocabulary for them: gate 3 returned ACCEPT on questions it had no
# right to an opinion about.
#
# Each family declares the dynamic quantities its profitability turns on. A
# verdict is only ever ACCEPT *under a stated profile*; when the verdict differs
# across the profiles tested, it is UNDECIDED — not averaged, not silently
# resolved to the faster one.
PROFILE_DEPENDENCE = {
    "if-convert":      ("branch_probability", "trip_count"),
    "preload":         ("working_set", "trip_count"),
    "distribute":      ("trip_count", "register_pressure"),
    "dead-store":      ("trip_count",),
    "peel-wraparound": ("trip_count",),
}

HARNESS = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 32000
/* PAD: loops touch arr[i + k] for i < N, so the buffers must extend past N by
   the largest offset in the loop. Without it the last rows ran off the end of
   the object and the differential test compared undefined behaviour -- which
   is how a wrong dead-store elimination on opus src/analysis.c:915 was scored
   EXACT. The pad is also COMPARED: that loop's only wrong elements were the
   trailing ones. */
#define PAD %(pad)d
#define NP (N + PAD)
#define TRIALS 151
%(decls)s
static float REF[%(na)d][NP], WRK[%(na)d][NP], SAV[%(na)d][NP];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
  return t.tv_sec*1e3+t.tv_nsec/1e6;}

/* TWO INPUT REGIMES. Profitability can depend on the DATA -- if-conversion's on
   how often the guard holds -- and a rig that tests one distribution cannot see
   that dependence. Regime 1 scales alternate arrays apart, which skews
   comparison guards hard in one direction. */
static void seed(int regime){srand(7);
  for(int k=0;k<%(na)d;k++) for(int i=0;i<NP;i++){
      float v=(float)rand()/RAND_MAX+0.5f;
      /* Regime 1 randomises the SIGN, keeping |v| >= 0.5 so nothing drifts into
         denormals. Scaling alternate arrays (the first attempt) could not move
         a `c[i] > 0.0f` guard at all on strictly positive data -- the probe
         reported p=1.000 in both regimes, and the regimes were inert. */
      SAV[k][i] = regime ? (((rand()&1) ? v : -v)) : v;}}
static void reset(float dst[%(na)d][NP]){memcpy(dst,SAV,sizeof SAV);}

/* min over TRIALS SINGLE calls, each on FRESH input, with the reset OUTSIDE the
   timed region. The previous formulation reset once per trial and then ran 200
   repetitions over whatever the last repetition left behind -- so it timed
   converged data. On a min/max kernel that converges after one pass, it
   reported the SAME speedup whether the guard held 5%% or 50%% of the time:
   structurally blind to the one quantity that decides the transformation. */
#define TIME(CALL, DST) ({ double b_=1e18; \
  for(int t_=0;t_<TRIALS;t_++){ reset(DST); double s_=ms(); CALL \
    double d_=ms()-s_; if(d_<b_)b_=d_; } b_; })

int main(void){
  double o[2], x[2], pr[2]; int exact=1; double worst=0;
  for(int g=0; g<2; g++){
    seed(g);
    reset(REF); %(call_ref)s
    reset(WRK); %(call_xf)s
    for(int k=0;k<%(na)d;k++) for(int i=0;i<NP;i++){
      if(WRK[k][i]!=REF[k][i]) exact=0;
      double d=fabs((double)WRK[k][i]-REF[k][i])/(fabs((double)REF[k][i])+1e-30);
      if(d>worst) worst=d; }
    reset(REF); pr[g] = %(probe)s;
    o[g] = TIME(%(call_ref)s, REF);
    x[g] = TIME(%(call_xf)s, WRK);
  }
  if(!exact && worst>1e-6){ printf("INCORRECT %%.3e\n",worst); return 1; }
  printf("%%s %%.6f %%.6f %%.4f %%.6f %%.6f %%.4f\n", exact?"EXACT":"CLOSE",
         o[0],x[0],pr[0], o[1],x[1],pr[1]);
  return 0; }
"""


def evaluate(loop: dict, p: dict, tmp: Path) -> dict:
    """Gate 3, under a STATED profile.

    Returns `speedup` = the WORST of the regimes tested, so a single number can
    still be reported, and `profile` carrying what it was decided under. When
    the regimes disagree about accept-vs-reject the verdict is UNDECIDED: the
    decision genuinely depends on a quantity this rig cannot know for the
    caller's workload, and picking the flattering regime would be a lie."""
    arrays = sorted({a["array"] for a in loop["accesses"]})
    orig, xf = emit(loop, p, "")
    if not xf:
        return {"verdict": "no-candidate"}
    na = len(arrays)
    npre = len(p.get("preload", []))
    # the largest positive subscript offset the loop touches, +1 for the
    # peel/dead-store tails that run one index past the loop
    pad = max([a["offset"] for a in loop["accesses"]] + [0]) + 1
    # wrap-around scalars are parameters of BOTH functions; the harness gives
    # both the same initial values (TSVC's own idiom: n-1, n-2, ...)
    winit = "".join(f"N-{k+1}, " for k in
                    range(len(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else 0))
    args_ref = winit + ", ".join(f"REF[{i}]" for i in range(na)) + ", N"
    pre_args = "".join(f"SCRATCH[{i}], " for i in range(npre))
    args_xf = winit + pre_args + ", ".join(f"WRK[{i}]" for i in range(na)) + ", N"
    nw = len(p.get("offsets", {})) if p["kind"] == "peel-wraparound" else 0
    wp = "".join("int, " for _ in range(nw))
    probe_fn = emit_probe(loop, p)
    nguards = sum(1 for g in guards_of(loop) if g is not None)
    probe_expr = (f"((double)probe({args_ref}))/((double)N*{nguards})"
                  if probe_fn else "-1.0")
    decls = (f"void orig({wp}{', '.join(['float * restrict']*na)}, int);\n"
             f"void xform({wp}{', '.join(['float * restrict']*(na+npre))}, int);\n"
             + (f"long probe({wp}{', '.join(['float * restrict']*na)}, int);\n"
                if probe_fn else "")
             + f"static float SCRATCH[{max(npre,1)}][32000+{pad}];")
    src = tmp / "cand.c"
    src.write_text(orig + xf + probe_fn)
    run = tmp / "run.c"
    run.write_text(HARNESS % {"decls": decls, "na": na, "pad": pad,
                              "probe": probe_expr,
                              "call_ref": f"orig({args_ref});",
                              "call_xf": f"xform({args_xf});"})
    exe = tmp / "cand"
    c = subprocess.run([CC, "-O3", *([arch_flag()] if arch_flag() else []),
                        "-w", str(src), str(run), "-o", str(exe), "-lm"],
                       capture_output=True, text=True)
    if c.returncode != 0:
        return {"verdict": "compile-fail", "err": c.stderr[:160]}
    r = subprocess.run([str(exe)], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return {"verdict": "INCORRECT", "err": r.stdout.strip()[:80]}
    parts = r.stdout.split()
    if parts[0] == "INCORRECT":
        return {"verdict": "INCORRECT", "err": parts[1]}
    eq = parts[0]
    o0, x0, p0, o1, x1, p1 = (float(v) for v in parts[1:7])
    sp0, sp1 = (o0 / x0 if x0 else 0.0), (o1 / x1 if x1 else 0.0)
    fast0, fast1 = sp0 >= NOISE_MARGIN, sp1 >= NOISE_MARGIN
    # A disagreement between regimes is only PROFILE dependence if the regimes
    # actually differ in the quantity the family depends on. When the probe says
    # they do not — `p=1.000` in both, because the guard cannot be moved by the
    # seeding — a disagreement is the margin, not the data, and calling it
    # profile dependence would be inventing a cause.
    inert = probe_fn and abs(p0 - p1) < 0.05
    if fast0 and fast1:
        verdict = "ACCEPT"
    elif not fast0 and not fast1:
        verdict = "REJECT-not-faster"
    elif inert or not probe_fn:
        verdict = "UNSTABLE-margin"
    else:
        verdict = "UNDECIDED-profile"
    return {"verdict": verdict, "equivalence": eq,
            "orig_ms": min(o0, o1), "xform_ms": min(x0, x1),
            "speedup": min(sp0, sp1), "speedup_best": max(sp0, sp1),
            "depends_on": PROFILE_DEPENDENCE.get(p["kind"], ()),
            "profile": {"regime0": {"speedup": sp0, "branch_probability": p0},
                        "regime1": {"speedup": sp1, "branch_probability": p1}},
            # A PRESERVATION WITNESS (G25, after SV-COMP). Everything an
            # INDEPENDENT checker needs to re-decide the equivalence claim
            # without trusting — or sharing any code with — this chooser.
            "witness": {
                "witness_version": 1,
                "loop": loop.get("func"), "family": p["kind"],
                "index": loop.get("index"), "step": loop.get("step") or 1,
                "arrays": arrays,
                "n_arrays": na, "n_scratch": npre, "n_int_prefix": nw,
                "pad": pad,
                "claim": {"equivalence": eq, "tolerance": 0.0 if eq == "EXACT" else 1e-6},
                "measured_under": {"regime0_branch_probability": p0,
                                   "regime1_branch_probability": p1},
                "source": {"orig": orig, "xform": xf}}}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__); return 2
    lifted = json.loads(Path(sys.argv[1]).read_text())
    loops = [l for l in lifted if l["func"].endswith("_v0")] or lifted
    print(f"  {'loop':<11}{'decision':<13}{'orig':>8}{'xform':>8}"
          f"{'speedup':>9}  verdict")
    acc = rej = skip = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for lp in loops:
            cands = [c for c in plans(lp) if c["kind"] in CANDIDATE_KINDS]
            if not cands:
                skip += 1
                q = plans(lp)[0]
                print(f"  {lp['func']:<11}{q['kind']:<13}{'—':>8}{'—':>8}"
                      f"{'—':>9}  {q['why'][:44]}")
                continue
            results = [(c, evaluate(lp, c, tmp)) for c in cands]
            good = [(c, e) for c, e in results if e.get("verdict") == "ACCEPT"]
            if good:
                p, e = max(good, key=lambda ce: ce[1]["speedup"])
            else:
                p, e = max(results, key=lambda ce: ce[1].get("speedup", 0))
            v = e["verdict"]
            acc += v == "ACCEPT"; rej += v.startswith(("REJECT", "INCORRECT"))
            if "speedup" in e:
                print(f"  {lp['func']:<11}{p['kind']:<13}{e['orig_ms']:>8.3f}"
                      f"{e['xform_ms']:>8.3f}{e['speedup']:>8.2f}x  {v}"
                      f"  [{e['equivalence']}]")
            else:
                print(f"  {lp['func']:<11}{p['kind']:<13}{'—':>8}{'—':>8}"
                      f"{'—':>9}  {v} {e.get('err','')[:40]}")
    print(f"\n  accepted {acc} · rejected {rej} · no-candidate {skip}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
