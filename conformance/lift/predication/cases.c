// Predication cases (G23). Each loop contains control flow that the analyser
// must either NORMALISE into a guarded assignment or REFUSE by species.
// One shape per function; the name says the expected verdict.

#define N 32000

// ---- ADMIT: the canonical maskable form -----------------------------------
void p001_mask_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] > 0.0f) a[i] = b[i];
}

// ---- ADMIT: guarded compound assignment ------------------------------------
void p002_accum_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] > 0.0f) a[i] += b[i];
}

// ---- ADMIT: guard reads an array the body does not ------------------------
void p003_twoarray_v0(float *a, float *b, float *c, float *d, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] > d[i]) a[i] = b[i] * 2.0f;
}

// ---- ADMIT: a guarded statement beside an unguarded one -------------------
void p004_mixed_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        b[i] = b[i] * 1.5f;
        if (c[i] > 0.0f) a[i] = b[i];
    }
}

// ---- REFUSE: the guarded expression can TRAP -------------------------------
// Converting this divides by zero on exactly the iterations the guard existed
// to prevent.
void r001_trap_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] != 0.0f) a[i] = b[i] / c[i];
}

// ---- REFUSE: the predicate bounds the iteration space ----------------------
// `b[i]` is only known valid where the guard admits it; speculating the load
// reads outside that range. Index-set splitting's job, not predication's.
void r002_indexguard_v0(float *a, float *b, int n, int m) {
    for (int i = 0; i < n; i++)
        if (i < m) a[i] = b[i];
}

// ---- REFUSE: early exit ----------------------------------------------------
void r003_break_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        if (c[i] < 0.0f) break;
        a[i] = b[i];
    }
}

// ---- REFUSE: if/else — convertible, deliberately not built yet -------------
void r004_else_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        if (c[i] > 0.0f) a[i] = b[i];
        else             a[i] = c[i];
    }
}

// ---- REFUSE: a call in the guarded expression ------------------------------
extern float f(float);
void r005_call_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] > 0.0f) a[i] = f(b[i]);
}

// ---- REFUSE: the guarded branch is not a single assignment -----------------
void r006_block_v0(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++)
        if (c[i] > 0.0f) { a[i] = b[i]; b[i] = 0.0f; }
}

// ---- REFUSE: the guard is a POINTER-VALIDITY check -------------------------
// Reduced from darknet src/blas.c:61. `da` may be null; the select form
// subscripts it on BOTH arms, so conversion dereferences null on exactly the
// iterations the guard existed to prevent.
//
// The correctness gate cannot catch this: the differential harness only ever
// passes valid arrays, so the input that exposes it is not in the test
// distribution. Refusing is an ANALYSIS obligation, not a stopwatch one.
void r007_nullguard_v0(float *da, float *dc, float *s, int n) {
    for (int i = 0; i < n; i++)
        if (da) da[i] += dc[i] * s[i];
}
