// darknet (YOLO) src/blas.c:110 variance_cpu — batch-norm variance.
// Real, widely-deployed ML code. Verbatim, then a ladder of declarations.
#include <math.h>

// ---- v0: VERBATIM darknet. clang refuses:
//      "value that could not be identified as reduction is used outside the loop"
void variance_v0(float *x, float *mean, int batch, int filters, int spatial, float *variance)
{
    float scale = 1./(batch * spatial - 1);
    int i,j,k;
    for(i = 0; i < filters; ++i){
        variance[i] = 0;
        for(j = 0; j < batch; ++j){
            for(k = 0; k < spatial; ++k){
                int index = j*filters*spatial + i*spatial + k;
                variance[i] += pow((x[index] - mean[i]), 2);
            }
        }
        variance[i] *= scale;
    }
}

// ---- v1: pow(v,2) -> v*v.  EXACT: a correctly-rounded pow returns the single
//      correct rounding of the exact square, which is what v*v computes.
//      No numeric licence required; this is a semantic identity.
void variance_v1(float *x, float *mean, int batch, int filters, int spatial, float *variance)
{
    float scale = 1./(batch * spatial - 1);
    int i,j,k;
    for(i = 0; i < filters; ++i){
        variance[i] = 0;
        for(j = 0; j < batch; ++j){
            for(k = 0; k < spatial; ++k){
                int index = j*filters*spatial + i*spatial + k;
                float d = x[index] - mean[i];
                variance[i] += d*d;
            }
        }
        variance[i] *= scale;
    }
}

// ---- v2: + accumulator hoisted out of memory into a register.
//      EXACT: same order, same values; only the storage location changes.
//      This is the declaration clang cannot make for itself, because it
//      cannot prove variance[] does not alias x[] or mean[].
void variance_v2(float *x, float *mean, int batch, int filters, int spatial, float *variance)
{
    float scale = 1./(batch * spatial - 1);
    int i,j,k;
    for(i = 0; i < filters; ++i){
        float acc = 0;
        float m = mean[i];
        for(j = 0; j < batch; ++j){
            for(k = 0; k < spatial; ++k){
                int index = j*filters*spatial + i*spatial + k;
                float d = x[index] - m;
                acc += d*d;
            }
        }
        variance[i] = acc * scale;
    }
}

// ---- v3: + lanes w4 i4 over the innermost extent.
//      NOT exact: reassociation. Requires numeric_semantics = reassociable.
typedef float vec_t __attribute__((vector_size(16)));
void variance_v3(float *x, float *mean, int batch, int filters, int spatial, float *variance)
{
    float scale = 1./(batch * spatial - 1);
    for(int i = 0; i < filters; ++i){
        float m = mean[i];
        vec_t a0={0,0,0,0}, a1={0,0,0,0}, a2={0,0,0,0}, a3={0,0,0,0};
        vec_t mv = {m,m,m,m};
        float tail = 0;
        for(int j = 0; j < batch; ++j){
            const float *p = x + j*filters*spatial + i*spatial;
            int k = 0;
            {
            #pragma clang fp contract(fast)
            for(; k + 16 <= spatial; k += 16){
                vec_t d0 = *(const vec_t*)(p+k+0)  - mv;
                vec_t d1 = *(const vec_t*)(p+k+4)  - mv;
                vec_t d2 = *(const vec_t*)(p+k+8)  - mv;
                vec_t d3 = *(const vec_t*)(p+k+12) - mv;
                a0 += d0*d0; a1 += d1*d1; a2 += d2*d2; a3 += d3*d3;
            }
            }
            for(; k < spatial; ++k){ float d = p[k]-m; tail += d*d; }
        }
        vec_t s = (a0+a1)+(a2+a3);
        variance[i] = ((s[0]+s[1]+s[2]+s[3]) + tail) * scale;
    }
}
