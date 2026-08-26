// DETECTOR: value_comparison
// Wrong at every n, in every input regime. If this survives, the validator is
// not comparing values at all.
void orig(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
void xform(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i + 1] * 2.0f;
}
