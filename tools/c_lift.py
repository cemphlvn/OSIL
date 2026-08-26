#!/usr/bin/env python3
"""C lifter (OQ-2): recover OSIL-SIR dependence facts from C source, mechanically.

Falsifiable claim (docs/decisions/ADR-0014, OQ-2):
    "a mechanical lifter can recover the SIR of the 10 loops in
     optimizer/probe/none60/ from their C source alone."

WHY THIS MATTERS: every .osil file in this repo is hand-written. Until a lifter
exists, OSIL cannot be pointed at a codebase it did not author. This is the
load-bearing question for everything downstream.

APPROACH: parse with libclang -- the actual compiler frontend -- not a bespoke
parser. For a real repository the flags come from compile_commands.json, which
build systems emit already, so nothing here is hand-fed.

SCOPE, stated up front: affine single-index array accesses of the form
`arr[i + c]` inside a countable `for` loop. That covers every loop in the
none60 probe. It does NOT cover indirect (`a[idx[i]]`), multi-dimensional, or
non-affine subscripts -- those are REPORTED as unhandled rather than guessed at.

Usage:
  python3 tools/c_lift.py <file.c> [--flags "-I..."] [--json out.json]
  python3 tools/c_lift.py --compile-db path/to/compile_commands.json
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

import clang.cindex as ci

for _p in ("/Library/Developer/CommandLineTools/usr/lib/libclang.dylib",
           "/Applications/Xcode.app/Contents/Developer/Toolchains/"
           "XcodeDefault.xctoolchain/usr/lib/libclang.dylib"):
    if os.path.exists(_p):
        try:
            ci.Config.set_library_file(_p)
        except Exception:
            pass
        break

K = ci.CursorKind


@dataclass
class Access:
    array: str
    coeff: int          # multiplier on the loop index (1 for a[i], a[i+3])
    offset: int         # constant offset      (0 for a[i], 3 for a[i+3])
    is_write: bool
    stmt: int           # position in the loop body: program order matters


@dataclass
class Dep:
    array: str
    kind: str           # flow (RAW) | anti (WAR) | output (WAW)
    distance: int       # in iterations; 0 == loop-independent
    carried: bool
    breakable: bool     # a FALSE dependence: reordering/expansion removes it
    why: str
    src: int = -1       # statement that must run FIRST (program order)
    dst: int = -1       # statement that must run SECOND


@dataclass
class Loop:
    func: str
    line: int
    header: str = ""            # `for (...)` text, verbatim
    stmts: list = field(default_factory=list)   # body statements, verbatim
    index: str | None = None
    lower: str | None = None
    upper: str | None = None
    step: int | None = None
    accesses: list = field(default_factory=list)
    scalars: list = field(default_factory=list)   # (name, is_write, stmt)
    guards: list = field(default_factory=list)    # per stmt: predicate text | None
    deps: list = field(default_factory=list)
    unhandled: list = field(default_factory=list)


def _txt(node) -> str:
    toks = [t.spelling for t in node.get_tokens()]
    return " ".join(toks)


def affine(node, index: str) -> tuple[int, int] | None:
    """Reduce a subscript expression to (coeff, offset) on `index`, or None.

    Deliberately narrow: `i`, `i + c`, `i - c`, `c + i`. Anything else returns
    None and is reported as unhandled -- never approximated."""
    toks = [t.spelling for t in node.get_tokens()]
    toks = [t for t in toks if t not in ("(", ")")]
    if toks == [index]:
        return (1, 0)
    if len(toks) == 3 and toks[1] in "+-":
        a, op, b = toks
        if a == index and b.lstrip("-").isdigit():
            return (1, int(b) if op == "+" else -int(b))
        if b == index and op == "+" and a.lstrip("-").isdigit():
            return (1, int(a))
    return None


def loop_header(node) -> tuple[str | None, str | None, str | None, int | None]:
    """Recover (index, lower, upper, step) from a ForStmt."""
    kids = list(node.get_children())
    if len(kids) < 4:
        return (None, None, None, None)
    init, cond, inc = kids[0], kids[1], kids[2]
    idx = low = up = None
    for d in init.walk_preorder():
        if d.kind == K.VAR_DECL:
            idx = d.spelling
            ch = list(d.get_children())
            if ch:
                low = _txt(ch[-1])
    if idx is None:
        t = _txt(init).split()
        if len(t) >= 3 and t[1] == "=":
            idx, low = t[0], t[2]
    ct = _txt(cond).split()
    if len(ct) >= 3 and ct[1] in ("<", "<=", "!="):
        up = " ".join(ct[2:])
    it = _txt(inc)
    step = 1 if ("++" in it) else None
    if step is None and "+=" in it:
        tail = it.split("+=")[1].strip()
        step = int(tail) if tail.lstrip("-").isdigit() else None
    return (idx, low, up, step)


# Statement kinds whose presence means the body is not a straight-line
# sequence. The dependence model here is program-order over straight-line
# statements; it has no notion of predication or branching, so REORDERING
# across any of these is unsound. Three TSVC loops (s277, s278, s279) were
# distributed across `goto`/label pairs and produced WRONG results before this
# check existed — the differential test caught them, but a differential test on
# one input distribution is not something to rely on for control flow.
CONTROL_FLOW = {
    K.GOTO_STMT, K.INDIRECT_GOTO_STMT, K.LABEL_STMT, K.BREAK_STMT,
    K.CONTINUE_STMT, K.RETURN_STMT, K.IF_STMT, K.SWITCH_STMT,
    K.WHILE_STMT, K.DO_STMT, K.FOR_STMT, K.CONDITIONAL_OPERATOR,
}


# Control flow, resolved into SPECIES. `body.control_flow` was a genus: once the
# analyser admits ANY control flow it stops being univocal, so it is replaced by
# the species below (ADR-0015). Each is a distinct risk with a distinct price.
EARLY_EXIT = {K.GOTO_STMT, K.INDIRECT_GOTO_STMT, K.LABEL_STMT, K.BREAK_STMT,
              K.CONTINUE_STMT, K.RETURN_STMT, K.SWITCH_STMT}
NESTED_LOOP = {K.WHILE_STMT, K.DO_STMT, K.FOR_STMT}
TRAPPING = {"/", "%", "/=", "%="}


def _species(c) -> str:
    if c.kind in EARLY_EXIT:
        return f"body.early_exit ({c.kind.name})"
    if c.kind in NESTED_LOOP:
        return f"body.nested_loop ({c.kind.name})"
    if c.kind in (K.IF_STMT, K.CONDITIONAL_OPERATOR):
        return f"body.nested_guard ({c.kind.name})"
    return f"body.early_exit ({c.kind.name})"


def _effectful(node) -> bool:
    """A predicate that calls, assigns or increments cannot be evaluated for
    iterations the original skipped."""
    for c in node.walk_preorder():
        if c.kind in (K.CALL_EXPR, K.COMPOUND_ASSIGNMENT_OPERATOR):
            return True
        toks = [t.spelling for t in c.get_tokens()]
        if c.kind == K.UNARY_OPERATOR and ("++" in toks or "--" in toks):
            return True
        if c.kind == K.BINARY_OPERATOR and "=" in toks:
            return True
    return False


def maskable_if(st, index: str, loop: Loop):
    """Recognise `if (P) lhs = rhs;` — the only control flow this lifter admits.

    Returns (guard_text, inner_cursor) or None, appending the refusal SPECIES to
    loop.unhandled. See ADR-0015 for why each condition is required; the short
    form is that if-conversion executes the guarded work on iterations the
    original skipped, so that work must be safe to execute unconditionally.
    """
    ch = list(st.get_children())
    if len(ch) < 2:
        loop.unhandled.append("body.guarded_nonassignment (malformed if)")
        return None
    if len(ch) > 2:
        # `if/else` masks to `lhs = P ? a : b` when both arms assign the same
        # lvalue. Genuinely convertible, deliberately NOT built here: declared,
        # priced, and left for a later capability rather than assumed.
        loop.unhandled.append("body.guarded_alternative (if/else)")
        return None
    cond, then = ch[0], ch[1]
    if _effectful(cond):
        loop.unhandled.append("body.unsafe_speculation (effectful predicate)")
        return None
    # A predicate over the loop INDEX bounds the iteration space; converting it
    # speculates loads outside the range the guard was protecting. That is
    # index-set splitting's job, not predication's.
    #
    # The index INSIDE a subscript does not count: `c[i] > 0` is data-dependent,
    # and reading it as index-dependence refused every admissible case on the
    # first run of this recogniser. Only a BARE reference — `i < m` — bounds the
    # iteration space.
    subscripted = set()
    for c in cond.walk_preorder():
        if c.kind == K.ARRAY_SUBSCRIPT_EXPR:
            subscripted.update(d.hash for d in c.walk_preorder())
    if any(c.kind == K.DECL_REF_EXPR and c.spelling == index
           and c.hash not in subscripted for c in cond.walk_preorder()):
        loop.unhandled.append("body.unsafe_speculation (index-dependent guard)")
        return None
    # Species BEFORE shape: `if (P) break;` is an early exit, not a malformed
    # assignment, and naming it the latter prices the wrong capability.
    for c in then.walk_preorder():
        if c.kind in EARLY_EXIT | NESTED_LOOP:
            loop.unhandled.append(_species(c))
            return None
    # A POINTER-VALIDITY guard protects the dereference itself. `if (da) da[i]
    # += x;` converts to `da[i] = (da) ? ... : (da[i])`, and BOTH arms subscript
    # `da` — a null dereference on exactly the iterations the guard existed to
    # prevent. Found on darknet src/blas.c:61.
    #
    # The correctness gate CANNOT catch this class: the differential harness
    # only ever passes valid, non-null arrays, so the input that would expose it
    # is not in the test distribution. That makes it an ANALYSIS obligation, not
    # something the stopwatch can be trusted to find. (G22's test-case validity
    # problem, one level up.)
    for c in cond.walk_preorder():
        if c.kind != K.DECL_REF_EXPR:
            continue
        if c.hash in subscripted:
            continue                      # `c[i] > 0` — a value, not a pointer
        if c.type.kind in (ci.TypeKind.POINTER, ci.TypeKind.CONSTANTARRAY,
                           ci.TypeKind.INCOMPLETEARRAY):
            loop.unhandled.append(
                "body.unsafe_speculation (pointer-validity guard)")
            return None
    inner = then
    if inner.kind == K.COMPOUND_STMT:
        kids = list(inner.get_children())
        if len(kids) != 1:
            loop.unhandled.append(
                f"body.guarded_nonassignment ({len(kids)} statements)")
            return None
        inner = kids[0]
    if inner.kind not in (K.BINARY_OPERATOR, K.COMPOUND_ASSIGNMENT_OPERATOR):
        loop.unhandled.append("body.guarded_nonassignment (not an assignment)")
        return None
    ikids = list(inner.get_children())
    if inner.kind == K.BINARY_OPERATOR:
        toks = [t.spelling for t in inner.get_tokens()]
        if "=" not in toks:
            loop.unhandled.append("body.guarded_nonassignment (not an assignment)")
            return None
    if not ikids or ikids[0].kind != K.ARRAY_SUBSCRIPT_EXPR:
        loop.unhandled.append(
            "body.guarded_nonassignment (target is not an array element)")
        return None
    # The guarded work runs on every iteration after conversion, so it must not
    # TRAP. Division is the case that matters: `if (a[i]) b[i] = c[i]/a[i];`
    # converts to a division by zero on exactly the iterations the guard existed
    # to prevent.
    for c in inner.walk_preorder():
        if c.kind in (K.BINARY_OPERATOR, K.COMPOUND_ASSIGNMENT_OPERATOR):
            if any(t.spelling in TRAPPING for t in c.get_tokens()):
                loop.unhandled.append(
                    "body.unsafe_speculation (trapping guarded expression)")
                return None
        if c.kind == K.CALL_EXPR:
            loop.unhandled.append(
                "body.unsafe_speculation (call in guarded expression)")
            return None
    for c in inner.walk_preorder():
        if c.kind in EARLY_EXIT | NESTED_LOOP | {K.IF_STMT, K.CONDITIONAL_OPERATOR}:
            loop.unhandled.append(_species(c))
            return None
    return (_txt(cond).strip(), inner)


def qualified_base(base) -> str | None:
    """Name the array by its FULL base expression, not by the first identifier.

    `psDD->sAR2_Q14[j]` was named `psDD`, which merges every array member of one
    struct into a single name. Two disjoint members then look like one location:
    on a reduction of opus silk/NSQ_del_dec.c the lifter INVENTED a loop-carried
    output dependence between `p->x` and `p->y`, and the chooser proposed
    deleting the stores to one of them. Distinct members are distinct storage,
    so the qualified name is both sound and strictly more precise.

    Accepts identifier chains joined by `.` / `->`. Anything else -- a call, an
    indexed base like `p[k]->m`, arithmetic -- is REFUSED rather than named
    after whichever identifier happened to come first.
    """
    toks = [t.spelling for t in base.get_tokens()]
    while len(toks) >= 2 and toks[0] == "(" and toks[-1] == ")":
        toks = toks[1:-1]
    if not toks or len(toks) % 2 == 0:
        return None
    for i, t in enumerate(toks):
        if i % 2 == 0:
            if not t.isidentifier():
                return None
        elif t not in (".", "->"):
            return None
    return "".join(toks)


def collect(body, index: str, loop: Loop) -> None:
    """Walk the loop body in program order, recording array accesses.

    A top-level `if (P) lhs = rhs;` is NORMALISED, not refused: the predicate is
    lifted onto the statement and the body becomes straight-line again, so every
    downstream analysis applies unchanged. Everything else about control flow is
    still refused, now by SPECIES rather than as one genus (ADR-0015).

    The whole `if` cursor is what gets scanned for accesses, so the PREDICATE's
    own reads are recorded. Dropping them would hide a real dependence.
    """
    raw = list(body.get_children()) if body.kind == K.COMPOUND_STMT else [body]
    stmts, guards, texts = [], [], []
    for st in raw:
        if st.kind == K.IF_STMT:
            m = maskable_if(st, index, loop)
            if m is None:
                return
            guards.append(m[0]); stmts.append(st); texts.append(_txt(m[1]))
            continue
        bad = next((c for c in st.walk_preorder() if c.kind in CONTROL_FLOW),
                   None)
        if bad is not None:
            loop.unhandled.append(_species(bad))
            return
        guards.append(None); stmts.append(st); texts.append(_txt(st))
    loop.stmts, loop.guards = texts, guards

    def subscripts(node, writes: set):
        for sub in node.walk_preorder():
            if sub.kind != K.ARRAY_SUBSCRIPT_EXPR:
                continue
            ch = list(sub.get_children())
            if len(ch) != 2:
                continue
            base, idxe = ch
            name = qualified_base(base)
            if name is None:
                # Label the SHAPE, not just the failure. G21 prices capabilities
                # from these strings, and a multi-dimensional access filed under
                # `subscript.indirect` prices the wrong capability. `A[i][j]` has
                # an INDEXED base; that is the structural test, and it replaces
                # the hard-coded list of TSVC array names the classifier used.
                btxt = _txt(base).strip()
                shape = "multi_dimensional" if "[" in btxt else "opaque_base"
                loop.unhandled.append(
                    f"non-affine base ({shape}) {btxt[:40]}[...]")
                continue
            a = affine(idxe, index)
            if a is None:
                expr = _txt(idxe).strip()
                # A WRAP-AROUND subscript is a bare scalar assigned inside the
                # loop (`im1 = i` at the end of the body), not an arbitrary
                # non-affine expression. It is a distinct, recognisable pattern
                # with a distinct risk profile, so it gets a distinct label —
                # collapsing it into "indirect" made it unpriceable.
                written = {nm for nm, is_w, _ in loop.scalars if is_w}
                kind = ("wraparound" if expr.isidentifier() and expr in written
                        else "indirect")
                loop.unhandled.append(
                    f"non-affine subscript ({kind}) {name}[{expr}]")
                continue
            yield name, a[0], a[1], sub

    arrays_seen = {a.array for a in loop.accesses}

    def scalars_in(st, n):
        """Scalar (non-array) variables a statement reads or writes.

        These carry dependences EXACTLY like arrays do. Omitting them is
        unsound: a distribution that separates `t = ...` from `... = t` is
        silently wrong. The first version of this lifter tracked only arrays,
        and only an undeclared-variable compile error stopped a wrong
        transformation from being accepted."""
        sub_bases, written = set(), set()
        for c in st.walk_preorder():
            if c.kind == K.ARRAY_SUBSCRIPT_EXPR:
                for b in c.walk_preorder():
                    if b.kind == K.DECL_REF_EXPR:
                        sub_bases.add(b.spelling); break
            if c.kind in (K.BINARY_OPERATOR, K.COMPOUND_ASSIGNMENT_OPERATOR):
                toks = [t.spelling for t in c.get_tokens()]
                if "=" in toks or c.kind == K.COMPOUND_ASSIGNMENT_OPERATOR:
                    kids = list(c.get_children())
                    if kids and kids[0].kind == K.DECL_REF_EXPR:
                        written.add(kids[0].spelling)
        for c in st.walk_preorder():
            if c.kind != K.DECL_REF_EXPR:
                continue
            nm = c.spelling
            if nm == index or nm in sub_bases or nm in arrays_seen:
                continue
            if c.type.kind in (ci.TypeKind.FUNCTIONPROTO,
                               ci.TypeKind.FUNCTIONNOPROTO):
                continue
            if c.type.kind in (ci.TypeKind.POINTER, ci.TypeKind.CONSTANTARRAY,
                               ci.TypeKind.INCOMPLETEARRAY):
                continue          # an array touched without a subscript here
            loop.scalars.append((nm, nm in written, n))

    # PASS 1 — all scalars first. `im1 = i` sits in a LATER statement than the
    # `b[im1]` that reads it, so a single forward pass has not yet seen the
    # scalar written when it classifies the subscript, and every wrap-around
    # was mislabelled `indirect` — which then priced at +0 by construction.
    for n, st in enumerate(stmts):
        scalars_in(st, n)

    # PASS 2 — subscripts, now able to see every scalar the loop writes.
    for n, st in enumerate(stmts):
        # writes: LHS of `=` and the target of compound assignment
        write_nodes = set()
        for c in st.walk_preorder():
            if c.kind == K.BINARY_OPERATOR:
                toks = [t.spelling for t in c.get_tokens()]
                if "=" in toks:
                    kids = list(c.get_children())
                    if kids:
                        write_nodes.add(kids[0].hash)
            elif c.kind == K.COMPOUND_ASSIGNMENT_OPERATOR:
                kids = list(c.get_children())
                if kids:
                    write_nodes.add(kids[0].hash)
        for name, coeff, off, sub in subscripts(st, write_nodes):
            is_w = sub.hash in write_nodes
            loop.accesses.append(Access(name, coeff, off, is_w, n))
            # A GUARDED store becomes `lhs = P ? rhs : lhs`, which READS the
            # location it writes on the iterations the guard excludes. That read
            # is real and must appear in the dependence graph.
            if is_w and loop.guards[n] is not None:
                loop.accesses.append(Access(name, coeff, off, False, n))
            # a compound assignment (`a[i] += ...`) both reads AND writes
            if is_w:
                par = sub.semantic_parent
                for c in st.walk_preorder():
                    if (c.kind == K.COMPOUND_ASSIGNMENT_OPERATOR
                            and list(c.get_children())
                            and list(c.get_children())[0].hash == sub.hash):
                        loop.accesses.append(
                            Access(name, coeff, off, False, n))
                        break


def analyse(loop: Loop) -> None:
    """Classify dependences between accesses to the same array.

    THE DEPENDENCE TEST (single-index affine, loop step s):
      W writes arr[i + q] at iteration i;  A touches arr[i' + p] at iteration i'.
      Same address  <=>  i + q = i' + p  <=>  i' - i = q - p.
      Iterations advance by s, so a dependence exists only when (q - p) % s == 0,
      and the iteration distance is delta = (q - p) / s.

        delta > 0 : A happens LATER  -> W first -> flow (RAW) if A reads
        delta < 0 : A happens EARLIER-> A first -> anti (WAR) if A reads
        delta = 0 : same iteration   -> program order decides

    Classifying by statement order alone is WRONG and was the first version's
    bug: in `a[i] *= c[i]; b[i] += a[i+1]*d[i]` the read of a[i+1] textually
    follows the write of a[i], but the write that would supply it happens a
    LATER iteration, so the value read is the pre-loop one -- an anti
    dependence, and a FALSE one."""
    acc = loop.accesses
    step = loop.step or 1
    seen = set()
    for w in acc:
        if not w.is_write or w.coeff != 1:
            continue
        for a in acc:
            if a is w or a.array != w.array or a.coeff != 1:
                continue
            gap = w.offset - a.offset
            if step == 0 or gap % step != 0:
                continue                    # never the same address
            delta = gap // step
            if delta > 0:
                kind = "output" if a.is_write else "flow"
                first, later = w, a
            elif delta < 0:
                kind = "output" if a.is_write else "anti"
                first, later = a, w
            else:
                if a.is_write:
                    kind = "output"
                elif a.stmt < w.stmt:
                    kind = "anti"
                elif a.stmt > w.stmt:
                    kind = "flow"
                else:
                    kind = "anti"           # read side of `x[i] op= ...`
            key = (w.array, kind, delta, w.offset, a.offset, w.stmt, a.stmt)
            if key in seen:
                continue
            seen.add(key)
            carried = delta != 0
            breakable, why = False, ""
            if kind == "anti":
                breakable = True
                why = (f"reads {a.array}[i{a.offset:+d}] whose write happens "
                       f"{abs(delta)} iteration(s) later, so the value read is "
                       f"the PRE-LOOP one: FALSE dependence, removable by "
                       f"expansion/preloading/reordering"
                       if carried else
                       f"read of {a.array}[i{a.offset:+d}] precedes its write "
                       f"within one iteration: loop-independent, not a barrier")
            elif kind == "output" and carried:
                breakable = True
                why = (f"{w.array}[i{w.offset:+d}] is overwritten "
                       f"{abs(delta)} iteration(s) later: the earlier store is "
                       f"DEAD except on the final iteration")
            elif kind == "flow":
                why = ("true carried dependence: value produced then consumed "
                       "across iterations -- NOT removable by reordering"
                       if carried else
                       "loop-independent flow: produced and consumed in the "
                       "same iteration, not a vectorization barrier")
            # Direction: which statement must precede which for the ORIGINAL
            # semantics to hold. For a carried dep the earlier ITERATION runs
            # first; for a loop-independent one, program order within the body.
            if delta > 0:
                src, dst = w.stmt, a.stmt      # W's iteration precedes A's
            elif delta < 0:
                src, dst = a.stmt, w.stmt
            else:
                src, dst = (min(w.stmt, a.stmt), max(w.stmt, a.stmt))
            loop.deps.append(Dep(w.array, kind, abs(delta), carried,
                                 breakable, why, src, dst))

    # Scalar-carried dependences. A scalar written in one statement and read in
    # another pins their order exactly as an array element would.
    for nm, is_w, sw in loop.scalars:
        if not is_w:
            continue
        for nm2, is_w2, sr in loop.scalars:
            if nm2 != nm or sw == sr:
                continue
            if is_w2:
                kind, a_first = "output", sr < sw
            else:
                kind, a_first = ("flow", False) if sr > sw else ("anti", True)
            src, dst = (sr, sw) if a_first else (sw, sr)
            loop.deps.append(Dep(f"${nm}", kind, 0, False,
                                 kind == "anti",
                                 f"scalar `{nm}` links S{src} -> S{dst}",
                                 src, dst))


def lift_file(path: Path, flags: list[str]) -> list[Loop]:
    idx = ci.Index.create()
    tu = idx.parse(str(path), args=flags + ["-w"])
    out: list[Loop] = []

    def walk(node, func):
        if node.kind == K.FUNCTION_DECL:
            func = node.spelling
        if node.kind == K.FOR_STMT:
            i, lo, up, st = loop_header(node)
            kids = list(node.get_children())
            if i and kids:
                body = kids[-1]
                # The header is every token BEFORE the body starts. Cutting
                # at the first `{` works only for a braced body: on
                # `for (...) if (P) a[i] = b[i];` there is no brace, so the
                # whole loop became its own header and the emitted function
                # failed to compile. Ask the cursor extents instead of the text.
                _b0 = body.extent.start.offset
                hdr = " ".join(t.spelling for t in node.get_tokens()
                               if t.extent.start.offset < _b0).strip()
                bs = (list(body.get_children())
                      if body.kind == K.COMPOUND_STMT else [body])
                lp = Loop(func or "?", node.location.line, hdr,
                          [_txt(x) for x in bs], i, lo, up, st)
                collect(kids[-1], i, lp)
                # A REFUSED loop is still a loop. `collect` returns before
                # recording accesses when it refuses, so gating on accesses
                # alone would drop refusals from every corpus count — shrinking
                # the denominator and inflating the affine rate.
                if lp.accesses or lp.unhandled:
                    # An UNPARSED header is not a step-1 ascending loop. On
                    # `for (k = lt-1; k >= 1; k--)` the header yields no upper
                    # bound and no step, and analysing the body anyway assumes
                    # both -- reversing every dependence direction, since under
                    # a descending step a LOWER offset is reached EARLIER. The
                    # chooser then proposed deleting a live store (NPB MG
                    # mg.c:343). Refuse, never approximate.
                    if lp.upper is None or lp.step is None:
                        lp.unhandled.append(
                            "unparsed loop header (iteration.unparsed_header) "
                            + hdr[:50])
                    else:
                        analyse(lp)
                    out.append(lp)
        for c in node.get_children():
            walk(c, func)

    walk(tu.cursor, None)
    return out


def to_sir(lp: Loop) -> str:
    """Propose an OSIL declaration carrying the recovered facts.

    NOTE: `iteration` and `dependences` are NOT in grammar v0.6. This is a
    PROPOSAL emitted for review, not a corpus-legal document -- recorded as a
    grammar gap rather than silently invented into the language."""
    ds = "\n".join(
        f"        {d.kind} {d.array} distance {d.distance}"
        f"{'  // BREAKABLE: ' + d.why if d.breakable else ''}"
        for d in lp.deps) or "        // none recovered"
    return (f"// LIFTED from {lp.func}() by tools/c_lift.py — proposal, not corpus-legal\n"
            f"model {lp.func} {{\n"
            f"    purpose: map\n"
            f"    iteration {{ index = {lp.index}  lower = {lp.lower}  "
            f"upper = {lp.upper}  step = {lp.step} }}\n"
            f"    dependences {{\n{ds}\n    }}\n}}\n")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__); return 2
    flags: list[str] = []
    if "--flags" in args:
        flags = args[args.index("--flags") + 1].split()
    files = [Path(a) for a in args if a.endswith(".c")]
    if "--compile-db" in args:
        db = json.loads(Path(args[args.index("--compile-db") + 1]).read_text())
        files, flags = [Path(e["file"]) for e in db], []
    loops: list[Loop] = []
    for f in files:
        loops += lift_file(f, flags)
    print(f"  lifted {len(loops)} loop(s) from {len(files)} file(s)")
    for lp in loops:
        br = [d for d in lp.deps if d.breakable]
        tr = [d for d in lp.deps if d.carried and not d.breakable]
        print(f"  {lp.func:<12} line {lp.line:<5} i={lp.index} "
              f"[{lp.lower}..{lp.upper}) step {lp.step}  "
              f"deps={len(lp.deps)} breakable={len(br)} true-carried={len(tr)}"
              + (f"  UNHANDLED={len(lp.unhandled)}" if lp.unhandled else ""))
    if "--json" in args:
        out = args[args.index("--json") + 1]
        Path(out).write_text(json.dumps([asdict(l) for l in loops], indent=1))
        print(f"  -> {out}")
    if "--sir" in args:
        for lp in loops:
            print(to_sir(lp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
