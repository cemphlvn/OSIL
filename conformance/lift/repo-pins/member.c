// Member pin: two DISTINCT array members of one struct are distinct storage.
//
// Reduced from opus silk/NSQ_del_dec.c:428, where every access is of the form
// `psDD->sAR2_Q14[j]`. Naming the array by the first identifier in the base
// collapses every member of `psDD` onto one name -- so disjoint arrays look
// like one location, and the analyser INVENTS dependences between them.
//
// The loop is CORRECT AS WRITTEN and dependence-free. The pin is that the
// lifter says so, and that the chooser refuses rather than emitting a
// transformation it has no parameter form for.
struct S { float x[64]; float y[64]; };

void member_v0(struct S *p, float *b, int n)
{
    for (int i = 0; i < n; i++) {
        p->y[i + 0] = b[i];             // writes y
        p->x[i + 1] = b[i] * 2.0f;      // writes x -- NOT dead
    }
}
