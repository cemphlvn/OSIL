// Which realization is actually CLOSER to the true product?
//
// The `exact` regime preserves DECLARATION ORDER. That is not the same as
// preserving ACCURACY, and the two are routinely conflated. A long sequential
// float chain accumulates rounding error at every step; independent chains
// each accumulate less and are combined once at the end.
//
// Ground truth here is the same product computed in double precision.
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

float ref_s312(const float * restrict a, int n);
float osil_s312_i1(const float * restrict a, int n);
float osil_s312_i8(const float * restrict a, int n);

#define N 32000
static float A[N];

static double truth(void) {           // double-precision reference
    double p = 1.0;
    for (int i = 0; i < N; i++) p *= (double)A[i];
    return p;
}

int main(void) {
    printf("  %-22s %-14s %-14s\n", "realization", "rel.err vs f64", "verdict");
    double sum_seq = 0, sum_i8 = 0;
    int seq_worse = 0;
    for (unsigned s = 1; s <= 20; s++) {
        srand(s);
        for (int i = 0; i < N; i++)
            A[i] = 1.0f + ((float)rand() / (float)RAND_MAX - 0.5f) * 0.002f;
        double t = truth();
        double e_seq = fabs((double)ref_s312(A, N)      - t) / fabs(t);
        double e_i8  = fabs((double)osil_s312_i8(A, N)  - t) / fabs(t);
        sum_seq += e_seq; sum_i8 += e_i8;
        if (e_seq > e_i8) seq_worse++;
        if (s <= 5)
            printf("  seed %-2u  sequential %.3e   lanes-i8 %.3e   %s\n",
                   s, e_seq, e_i8, e_seq > e_i8 ? "vectorized is CLOSER" : "sequential closer");
    }
    printf("\n  over 20 seeds: mean rel.err vs f64 truth\n");
    printf("    sequential (`exact` regime) : %.3e\n", sum_seq / 20);
    printf("    lanes w4 i8 (`reassociable`): %.3e\n", sum_i8 / 20);
    printf("    vectorized was closer in %d/20 cases\n", seq_worse);
    return 0;
}
