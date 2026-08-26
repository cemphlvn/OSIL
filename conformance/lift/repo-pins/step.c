// Step-pin fixture: loops whose step is NOT 1.
//
// Every loop in optimizer/probe/none60/ steps by 1, so `(q-p) % s == 0`
// reduces to `q > p` and the chooser's recognisers agreed with the lifter by
// accident. Manually unrolled loops -- the dominant idiom in production DSP
// code -- break that accident. Found by pointing the shipped lifter at
// xiph/opus; see step-pins/README.md.
//
// Both loops are CORRECT AS WRITTEN. The pin is that the chooser leaves them
// alone, not that it improves them.

// ---- dead-store must NOT fire ---------------------------------------------
// The SILK 4x-unrolled copy idiom, opus silk/float/scale_copy_vector_FLP.c:46.
// a[i+0] and a[i+3] are DIFFERENT addresses under step 4: no store here is
// ever overwritten, and all four are live.
void unrolled_v0(float *a, float *b, int n)
{
    for (int i = 0; i < n; i += 4) {
        a[i + 0] = b[i + 0];
        a[i + 1] = b[i + 1];
        a[i + 2] = b[i + 2];
        a[i + 3] = b[i + 3];
    }
}

// ---- preload must redirect ONLY the aliasing offset ------------------------
// Under step 2, S1's read of a[i+2] IS overwritten later (by S1 itself, two
// iterations on) and genuinely needs the pre-loop value. Its read of a[i+1] is
// written by S0 in the SAME iteration and must stay live. Redirecting both --
// which is what offset ordering alone licenses -- hands S1 the pre-loop value
// of a[i+1] and is silently wrong.
void unroll_pre_v0(float *a, float *b, int n)
{
    for (int i = 0; i < n; i += 2) {
        a[i + 1] = b[i + 1] * 2.0f;
        a[i + 0] = a[i + 2] + a[i + 1];
    }
}
