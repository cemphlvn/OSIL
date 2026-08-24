// TSVC_2 s1113:  for i: a[i] = a[LEN_1D/2] + b[i]
// clang 17 -O3 refuses: "unsafe dependent memory operations in loop".
//
// The dependence is real but has EXACTLY ONE crossing point, at i = mid:
//   i <  mid : a[mid] still holds its original value  s
//   i == mid : a[mid] is overwritten with s + b[mid] = s2
//   i >  mid : a[mid] holds s2
// So the loop is two independent parallel maps. That fact is what clang
// cannot prove and what a declaration would supply.
#define N 32000
#define MID (N/2)

// verbatim TSVC shape — the baseline clang refuses to vectorize
void ref_s1113(float * restrict a, const float * restrict b) {
    for (int i = 0; i < N; i++) a[i] = a[MID] + b[i];
}

// the split the declaration would license: two dependence-free maps
void split_s1113(float * restrict a, const float * restrict b) {
    float s  = a[MID];
    float s2 = s + b[MID];
    for (int i = 0; i <= MID; i++) a[i] = s  + b[i];
    for (int i = MID + 1; i < N; i++) a[i] = s2 + b[i];
}
