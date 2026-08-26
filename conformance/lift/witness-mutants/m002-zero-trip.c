// DETECTOR: trip_count
// Correct for every n > 0. Wrong ONLY at n == 0 — which is exactly the shape of
// the real bug this validator found on its first run: dead-store elimination
// replaying its removed store at `int i = n - 1`, i.e. index -1.
// A validator that measures only at n = 32000 confirms this happily.
void orig(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
void xform(float * restrict a, float * restrict b, int n){
    if (n == 0) a[0] = 99.0f;
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
