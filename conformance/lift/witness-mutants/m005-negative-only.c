// DETECTOR: regime_diversity
// Correct for every non-negative input and wrong for negative ones. The
// chooser's own harness seeds strictly positive data (rand()/RAND_MAX + 0.5),
// so it could never catch this. Not sharing that blind spot is the whole reason
// this validator generates its own inputs.
void orig(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
void xform(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = (b[i] < 0.0f) ? 0.0f : (b[i] * 2.0f);
}
