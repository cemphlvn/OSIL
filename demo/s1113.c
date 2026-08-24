/* TSVC_2 s1113 — github.com/UoB-HPC/TSVC_2 (BSD-3-Clause), src/tsvc.c
 *
 *     for (i = 0; i < N; i++)  a[i] = a[N/2] + b[i];
 *
 * Every compiler tested refuses to vectorize this. The dependence is real but
 * has EXACTLY ONE crossing point, at i == MID:
 *
 *     i <  MID :  a[MID] still holds its original value  s
 *     i == MID :  a[MID] is overwritten with s + b[MID] = s2
 *     i >  MID :  a[MID] holds s2
 *
 * So the loop is two independent, dependence-free maps. Splitting it there is
 * exact — not an approximation, not a fast-math trade. The two versions agree
 * bit for bit.
 */
#ifndef N
#define N 32000
#endif
#define MID (N/2)

/* verbatim TSVC shape */
void ref_s1113(float * restrict a, const float * restrict b) {
    for (int i = 0; i < N; i++) a[i] = a[MID] + b[i];
}

/* the split the single crossing point licenses */
void split_s1113(float * restrict a, const float * restrict b) {
    float s  = a[MID];
    float s2 = s + b[MID];
    for (int i = 0; i <= MID; i++)     a[i] = s  + b[i];
    for (int i = MID + 1; i < N; i++)  a[i] = s2 + b[i];
}
