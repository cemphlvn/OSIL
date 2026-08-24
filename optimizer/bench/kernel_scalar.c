// TSVC_2 s312 inner loop, verbatim shape. Compiled WITHOUT fast-math.
// This is both the correctness ORACLE (declaration-order product) and the
// clang -O3 BASELINE, because clang refuses to vectorize it.
float ref_s312(const float * restrict a, int n) {
    (void)n;  // trip count fixed at 32000, matching the emitted kernel
    float prod = 1.0f;
    for (int i = 0; i < 32000; i++) prod *= a[i];
    return prod;
}
