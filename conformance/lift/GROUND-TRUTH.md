# Lifter ground truth — the 10 loops of `optimizer/probe/none60/`

These classifications were derived **by hand** (see `optimizer/probe/none60/README.md`)
BEFORE `tools/c_lift.py` existed, and each was then confirmed empirically: the
transformation implied by the classification was written, checked bit-identical,
and measured. The lifter must reproduce them from C source alone.

| loop | hand analysis | expect breakable | expect true-carried | expect unhandled |
|---|---|---|---|---|
| s212 | `a[i+1]` read is of the PRE-LOOP value -> false dep | >0 | 0 | 0 |
| s211 | `b[i-1]` is a TRUE recurrence; `b[i+1]` read is false | >0 | >0 | 0 |
| s1213 | `b[i-1]` true; `a[i+1]` read false | >0 | >0 | 0 |
| s261 | `c[i-1]` read is the NEW value -> true carried | >0 | >0 | 0 |
| s244 | `a[i+1]` store is OVERWRITTEN next iteration -> dead | >0 | 0 | 0 |
| s241 | `a[i+1]` read is old -> false, needs preload | >0 | 0 | 0 |
| s116 | every read is of the old value (stride 5) -> all false | >0 | 0 | 0 |
| s221 | `b[i]=b[i-1]+...` is a TRUE recurrence, irreducible | >0 | >0 | 0 |
| s291 | `b[im1]` — wrap-around scalar, NOT affine in i | - | - | >0 |
| s292 | `b[im1]`,`b[im2]` — NOT affine in i | - | - | >0 |

The last two are the important rows: the lifter must **refuse** them rather than
guess. A lifter that silently approximates a non-affine subscript would produce
a declaration that licenses an unsound transformation.

Cross-check against measurement: the two loops the lifter marks with a true
carried dependence AND that gained least (`s221` 1.08x, `s261` 1.63x) are the
two where an irreducible recurrence caps the win. The lifter's classification
and the stopwatch agree about which loops are hard.
