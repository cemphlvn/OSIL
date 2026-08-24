// IDENTICAL source to kernel_scalar.c. Only the compiler flags differ
// (-ffast-math). Present to show the transformation is real and that clang
// itself will perform it once the regime is relaxed — the difference OSIL
// claims is not WHETHER but on what LICENCE and at what scope.
float fm_s312(const float * restrict a, int n) {
    (void)n;  // trip count fixed at 32000, matching the emitted kernel
    float prod = 1.0f;
    for (int i = 0; i < 32000; i++) prod *= a[i];
    return prod;
}
