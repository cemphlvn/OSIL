// Differential + timing harness for the OSIL N=1 slice.
//
// RULE: correctness gates performance. No timing is printed for a realization
// that has not first passed the differential test against the declaration-order
// scalar product.
//
// SECOND PURPOSE: check the cost model against ground truth. osil-opt picks a
// realization from its own model of the machine; this harness measures every
// realization in the licensed space and reports whether the model's PICK was
// the empirical best. A cost model that never meets a measured outcome is
// unfalsified taste.

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

float ref_s312(const float * restrict a, int n);
float fm_s312(const float * restrict a, int n);
float osil_s312_i1(const float * restrict a, int n);
float osil_s312_i2(const float * restrict a, int n);
float osil_s312_i4(const float * restrict a, int n);
float osil_s312_i8(const float * restrict a, int n);

#define N 32000
#define REPS 2000
#define TRIALS 20

static float A[N];
static volatile float sink;

typedef float (*kern)(const float * restrict, int);

typedef struct { const char *name; kern f; double modeled; } entry;

static void fill(unsigned seed) {
    srand(seed);
    // Values in a tight band around 1.0: a 32000-term product of values far
    // from 1.0 would overflow or flush to zero, and the comparison would then
    // measure saturation rather than reassociation error.
    for (int i = 0; i < N; i++)
        A[i] = 1.0f + ((float)rand() / (float)RAND_MAX - 0.5f) * 0.002f;
}

static double now_ms(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}

static double bench(kern f) {
    double best = 1e18;
    for (int t = 0; t < TRIALS; t++) {
        double t0 = now_ms();
        for (int r = 0; r < REPS; r++) {
            A[r % N] += 1e-9f;      // defeat hoisting: input changes each rep
            sink = f(A, N);
        }
        double dt = now_ms() - t0;
        if (dt < best) best = dt;   // min over trials: least thermal noise
    }
    return best;
}

int main(void) {
    // modeled costs are those osil-opt printed for each realization
    entry osil[] = {
        {"osil lanes w4 i1", osil_s312_i1, 32012},
        {"osil lanes w4 i2", osil_s312_i2, 16028},
        {"osil lanes w4 i4", osil_s312_i4,  8060},
        {"osil lanes w4 i8", osil_s312_i8,  4124},
    };
    const int NK = sizeof(osil) / sizeof(osil[0]);

    printf("== differential test (correctness gate) ==\n");
    int fail = 0;
    for (int k = 0; k < NK; k++) {
        double worst = 0;
        for (unsigned s = 1; s <= 5; s++) {
            fill(s);
            double r = ref_s312(A, N), o = osil[k].f(A, N);
            double rel = fabs(o - r) / fabs(r);
            if (rel > worst) worst = rel;
        }
        int ok = worst < 1e-4;
        if (!ok) fail = 1;
        printf("  %-18s  worst rel.err over 5 seeds: %.3e  %s\n",
               osil[k].name, worst, ok ? "ok" : "FAIL");
    }
    if (fail) { printf("\n  FAILED — no timing reported.\n"); return 1; }
    printf("\n  PASSED (bound rel.err < 1e-4). Not bit-identical by\n"
           "  construction: reassociation changes rounding. That is the\n"
           "  declared, accepted cost of the `reassociable` regime.\n");

    fill(1);
    double t_ref = bench(ref_s312), t_fm = bench(fm_s312);

    printf("\n== timing (min of %d trials x %d reps, n=%d) ==\n", TRIALS, REPS, N);
    printf("  %-22s %8s %9s %12s\n", "realization", "ms", "speedup", "modeled");
    printf("  %-22s %8.2f %8.2fx %12s\n", "clang -O3 (REFUSES)", t_ref, 1.0, "-");
    printf("  %-22s %8.2f %8.2fx %12s\n", "clang -O3 -ffast-math", t_fm, t_ref/t_fm, "-");

    int best_k = 0; double best_t = 1e18;
    for (int k = 0; k < NK; k++) {
        double t = bench(osil[k].f);
        if (t < best_t) { best_t = t; best_k = k; }
        printf("  %-22s %8.2f %8.2fx %12.0f\n",
               osil[k].name, t, t_ref/t, osil[k].modeled);
    }

    // The model picks the lowest modeled cost.
    int pick = 0;
    for (int k = 1; k < NK; k++) if (osil[k].modeled < osil[pick].modeled) pick = k;

    printf("\n== cost model vs ground truth ==\n");
    printf("  model picked   : %s\n", osil[pick].name);
    printf("  measured best  : %s\n", osil[best_k].name);
    printf("  verdict        : %s\n",
        pick == best_k ? "AGREES"
                       : "MODEL WRONG — the picked realization is not the fastest");
    if (pick != best_k)
        printf("  cost of error  : %.2fx slower than the best licensed realization\n",
               bench(osil[pick].f) / best_t);
    return 0;
}
