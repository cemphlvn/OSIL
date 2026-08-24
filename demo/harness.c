/* Correctness first: no timing is printed unless the two versions agree
 * BIT FOR BIT. A wrong transformation is infinitely fast. */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdlib.h>
#ifndef N
#define N 32000
#endif
#define TRIALS 15
#define REPS   2000
void ref_s1113(float * restrict a, const float * restrict b);
void split_s1113(float * restrict a, const float * restrict b);
static float A0[N], B[N], R[N], S[N], W[N];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3 + t.tv_nsec/1e6;}
static double bench(void(*f)(float*restrict,const float*restrict)){
    double best = 1e18;
    for (int t = 0; t < TRIALS; t++) {
        memcpy(W, A0, sizeof A0);
        double t0 = ms();
        for (int r = 0; r < REPS; r++) { W[r % N] += 1e-9f; f(W, B); }
        double d = ms() - t0;
        if (d < best) best = d;          /* min: least interference */
    }
    return best;
}
int main(void){
    srand(1);
    for (int i = 0; i < N; i++) { A0[i]=(float)rand()/RAND_MAX; B[i]=(float)rand()/RAND_MAX; }
    memcpy(R, A0, sizeof A0); ref_s1113(R, B);
    memcpy(S, A0, sizeof A0); split_s1113(S, B);
    double worst = 0;
    for (int i = 0; i < N; i++) { double e = fabs(R[i]-S[i]); if (e > worst) worst = e; }
    printf("  correctness : max |ref - split| = %.3e   %s\n",
           worst, worst == 0.0 ? "BIT-IDENTICAL" : "*** DIFFERS ***");
    if (worst != 0.0) { printf("  not equivalent - no timing reported\n"); return 1; }
    double t0 = bench(ref_s1113), t1 = bench(split_s1113);
    printf("\n  %-38s %8.2f ms   %5.2fx\n", "as written (compiler refuses)", t0, 1.0);
    printf("  %-38s %8.2f ms   %5.2fx\n", "split at the crossing point",   t1, t0/t1);
    printf("\n  (min of %d trials x %d reps. Timing is sensitive to machine\n"
           "   load — close other work before believing the ratio.)\n", TRIALS, REPS);
    return 0;
}
