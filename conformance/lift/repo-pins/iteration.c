// Iteration pin: a DESCENDING loop is not an ascending one with a sign flipped.
//
// Reduced from NPB3.0-omp-C MG/mg.c:343 (`for (k = lt-1; k >= 1; k--)`). The
// header parser yields no upper bound and no step for that form -- and the
// lifter used to analyse the body ANYWAY, under the default step-1 ascending
// assumption.
//
// That inverts every dependence direction: under a descending step a LOWER
// offset is reached EARLIER. The two loops below have the SAME BODY and
// opposite answers, which is the whole point.

// a[i+1] is written at iteration i and overwritten at i+1: dead but for the
// last iteration. `dead-store` is legal here.
void asc_v0(float *a, float *b, int n)
{
    for (int i = 0; i < n; i++) {
        a[i + 0] = b[i];
        a[i + 1] = b[i] * 2.0f;
    }
}

// Same body, descending. a[i+1] is written BEFORE a[i+0] is reached and is
// never overwritten: every store is live. The lifter must REFUSE, not invert.
void desc_v0(float *a, float *b, int n)
{
    for (int i = n - 1; i >= 0; i--) {
        a[i + 0] = b[i];
        a[i + 1] = b[i] * 2.0f;
    }
}
