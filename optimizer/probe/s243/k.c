// TSVC s243 — "node splitting / false dependence cycle breaking".
// From the arXiv:2502.11906 info-withdrawn variant (NMSU-PEARL/tsvc_withArgs),
// one of the loops that STOPS vectorizing when compile-time information is
// withdrawn. clang: "unsafe dependent memory operations in loop".
//
// The a[i+1] read is of the value BEFORE this pass writes it: a FALSE
// dependence. `restrict` cannot express this -- it declares that distinct
// pointers do not alias, and this dependence is WITHIN a[].
#include <string.h>

// v0: as published in the info-withdrawn variant. clang refuses.
void s243_v0(float * restrict a, float * restrict b, const float * restrict c,
             const float * restrict d, const float * restrict e, int n) {
    for (int i = 0; i < n-1; i++) {
        a[i] = b[i] + c[i] * d[i];
        b[i] = a[i] + d[i] * e[i];
        a[i] = b[i] + a[i+1] * d[i];
    }
}

// v1: the declared node split. Capturing a[i+1] up front makes the false
// dependence explicit and the body dependence-free. EXACT -- same values,
// same order, only the read source is pinned to the pre-loop array.
void s243_v1(float * restrict a, float * restrict b, const float * restrict c,
             const float * restrict d, const float * restrict e, int n,
             float * restrict tmp) {
    for (int i = 0; i < n-1; i++) tmp[i] = a[i+1];
    for (int i = 0; i < n-1; i++) {
        a[i] = b[i] + c[i] * d[i];
        b[i] = a[i] + d[i] * e[i];
        a[i] = b[i] + tmp[i] * d[i];
    }
}
