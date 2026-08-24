// Same loop, but WITH the outer repeat loop and the opaque dummy() call that
// the real TSVC kernel has. My first extraction dropped both.
extern void dummy_op(float*,float*,const float*,const float*,const float*);
void s243_ctx(float * restrict a, float * restrict b, const float * restrict c,
              const float * restrict d, const float * restrict e, int n, int reps) {
    for (int nl = 0; nl < reps; nl++) {
        for (int i = 0; i < n-1; i++) {
            a[i] = b[i] + c[i] * d[i];
            b[i] = a[i] + d[i] * e[i];
            a[i] = b[i] + a[i+1] * d[i];
        }
        dummy_op(a,b,c,d,e);
    }
}
