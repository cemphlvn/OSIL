// DETECTOR: exactness
// Off by roughly 2.5e-7 relative — comfortably inside a 1e-6 tolerance. The
// witness claims EXACT, so accepting this would mean the validator honours the
// tolerance but not the CLAIM.
void orig(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
void xform(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0000005f;
}
