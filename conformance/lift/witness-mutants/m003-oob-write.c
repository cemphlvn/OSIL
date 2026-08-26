// DETECTOR: canary
// Every in-range element is correct; the transformation simply writes one slot
// BEFORE the array. Only a guard region catches this — a value comparison over
// the data range cannot.
void orig(float * restrict a, float * restrict b, int n){
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
void xform(float * restrict a, float * restrict b, int n){
    a[-1] = 7.0f;
    for (int i = 0; i < n; i++) a[i] = b[i] * 2.0f;
}
