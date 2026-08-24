// TSVC loops from the "None" set — vectorized by NEITHER clang 17 NOR gcc 16
// on M4/NEON. Each transformation is the one TSVC's own comment names.
// Context (outer repeat loop + opaque call) is PRESERVED: extracting the inner
// loop alone changes the blocker, which invalidated an earlier probe.
#define N 32000
extern void opaque(float*,float*,float*,float*,float*);

// ---------------- s212  "statement reordering / dependency needing temporary"
// a[i] *= c[i];  b[i] += a[i+1]*d[i];
// a[i+1] is read BEFORE it is written (write happens at iteration i+1), so b
// depends only on the PRE-LOOP a[]. Distributing with the b-loop first is EXACT.
void s212_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++){ a[i] *= c[i]; b[i] += a[i+1]*d[i]; }
        opaque(a,b,c,d,e);
    }
}
void s212_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++) b[i] += a[i+1]*d[i];   // uses pre-loop a[]
        for(int i=0;i<n-1;i++) a[i] *= c[i];
        opaque(a,b,c,d,e);
    }
}

// ---------------- s211  "statement reordering allows vectorization"
// a[i] = b[i-1] + c[i]*d[i];   b[i] = b[i+1] - e[i]*d[i];
// stmt1 reads b[i-1], written by stmt2 at i-1: a true RAW carried dependence.
// Distributing puts the b-update (a pure anti-dependence, safe forward) in its
// own loop, after the a-loop has consumed the old b[].
void s211_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=1;i<n-1;i++){
            a[i] = b[i-1] + c[i]*d[i];
            b[i] = b[i+1] - e[i]*d[i];
        }
        opaque(a,b,c,d,e);
    }
}
void s211_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        // b[i] must be updated in increasing i using old b[i+1]; a[i] needs the
        // NEW b[i-1]. Run the b recurrence first, keeping the old b[i-1] we need.
        float prev = b[0];
        for(int i=1;i<n-1;i++){
            float nb = b[i+1] - e[i]*d[i];
            a[i] = prev + c[i]*d[i];
            prev = nb;
            b[i] = nb;
        }
        opaque(a,b,c,d,e);
    }
}

// ---------------- s1213 "statement reordering / dependency needing temporary"
// a[i]=b[i-1]+c[i] needs the NEW b[i-1]; b[i]=a[i+1]*d[i] needs the OLD a[i+1].
// Running the b-loop entirely first (all old a), then the a-loop (all new b),
// reproduces exactly that. EXACT.
void s1213_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=1;i<n-1;i++){ a[i]=b[i-1]+c[i]; b[i]=a[i+1]*d[i]; }
        opaque(a,b,c,d,e);
    }
}
void s1213_v1(float * restrict a,float * restrict b,float * restrict c,
              float * restrict d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        float b0 = b[0];                        // a[1] needs b[0] before it changes
        for(int i=1;i<n-1;i++) b[i]=a[i+1]*d[i];
        for(int i=2;i<n-1;i++) a[i]=b[i-1]+c[i];
        a[1]=b0+c[1];
        opaque(a,b,c,d,e);
    }
}

// ---------------- s261 "scalar and array expansion / wrap-around scalar"
// a[i] uses c_new[i-1], and c_new[i-1] == c_old[i-1]*d[i-1]. So a depends only
// on the PRE-LOOP c[]. Both loops become independent. EXACT.
void s261_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        float t;
        for(int i=1;i<n;++i){ t=a[i]+b[i]; a[i]=t+c[i-1]; t=c[i]*d[i]; c[i]=t; }
        opaque(a,b,c,d,e);
    }
}
void s261_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        float c0 = c[0];                        // a[1] uses the untouched c[0]
        for(int i=2;i<n;++i) a[i]=(a[i]+b[i])+c[i-1]*d[i-1];
        a[1]=(a[1]+b[1])+c0;
        for(int i=1;i<n;++i) c[i]=c[i]*d[i];
        opaque(a,b,c,d,e);
    }
}

// ---------------- s244 "node splitting / false dependence cycle breaking"
// a[i+1] written by stmt3 at iteration i is OVERWRITTEN by stmt1 at iteration
// i+1. Every one of those stores is DEAD except the final one. Declaring that
// removes an entire store stream. EXACT.
void s244_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;++i){
            a[i]   = b[i] + c[i]*d[i];
            b[i]   = c[i] + b[i];
            a[i+1] = b[i] + a[i+1]*d[i];
        }
        opaque(a,b,c,d,e);
    }
}
void s244_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        float alast = a[n-1];                   // only the final stmt3 survives
        for(int i=0;i<n-1;++i){
            a[i] = b[i] + c[i]*d[i];
            b[i] = c[i] + b[i];
        }
        a[n-1] = b[n-2] + alast*d[n-2];
        opaque(a,b,c,d,e);
    }
}

// ---------------- s291 "loop peeling / wrap-around variable, 1 level"
// im1 == i-1 for EVERY iteration except i==0, where it is n-1. Peeling the
// first iteration leaves a clean 2-point stencil. EXACT.
void s291_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        int im1=n-1;
        for(int i=0;i<n;i++){ a[i]=(b[i]+b[im1])*0.5f; im1=i; }
        opaque(a,b,c,d,e);
    }
}
void s291_v1(float * restrict a,float * restrict b,float *c,float *d,float *e,
             int n,int reps){
    for(int nl=0;nl<reps;nl++){
        a[0]=(b[0]+b[n-1])*0.5f;                       // the peeled iteration
        for(int i=1;i<n;i++) a[i]=(b[i]+b[i-1])*0.5f;
        opaque(a,b,c,d,e);
    }
}

// ---------------- s292 "loop peeling / wrap-around variable, 2 levels"
// Same, two levels deep: peel i==0 and i==1. EXACT.
void s292_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        int im1=n-1, im2=n-2;
        for(int i=0;i<n;i++){ a[i]=(b[i]+b[im1]+b[im2])*0.333f; im2=im1; im1=i; }
        opaque(a,b,c,d,e);
    }
}
void s292_v1(float * restrict a,float * restrict b,float *c,float *d,float *e,
             int n,int reps){
    for(int nl=0;nl<reps;nl++){
        a[0]=(b[0]+b[n-1]+b[n-2])*0.333f;
        a[1]=(b[1]+b[0]  +b[n-1])*0.333f;
        for(int i=2;i<n;i++) a[i]=(b[i]+b[i-1]+b[i-2])*0.333f;
        opaque(a,b,c,d,e);
    }
}

// ---------------- s221 "loop distribution / partially recursive"
// a[i] is independent; b[i] is a genuine first-order recurrence. Distributing
// lets the a-loop vectorize while the b-loop stays scalar. A PARTIAL win by
// construction -- half the loop is not vectorizable at all. EXACT.
void s221_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=1;i<n;i++){ a[i]+=c[i]*d[i]; b[i]=b[i-1]+a[i]+d[i]; }
        opaque(a,b,c,d,e);
    }
}
void s221_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=1;i<n;i++) a[i]+=c[i]*d[i];          // vectorizable
        for(int i=1;i<n;i++) b[i]=b[i-1]+a[i]+d[i];    // irreducibly scalar
        opaque(a,b,c,d,e);
    }
}

// ---------------- s241 "node splitting / preloading necessary"
// b[i] needs a_NEW[i] and a_OLD[i+1]. Preloading the old a[] separates them.
// EXACT.
void s241_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++){
            a[i]=b[i]*c[i]*d[i];
            b[i]=a[i]*a[i+1]*d[i];
        }
        opaque(a,b,c,d,e);
    }
}
void s241_v1(float * restrict a,float * restrict b,float * restrict c,
             float * restrict d,float *e,int n,int reps,float * restrict tmp){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++) tmp[i]=a[i+1];          // preload old a[i+1]
        for(int i=0;i<n-1;i++) a[i]=b[i]*c[i]*d[i];    // b still old here
        for(int i=0;i<n-1;i++) b[i]=a[i]*tmp[i]*d[i];
        opaque(a,b,c,d,e);
    }
}

// ---------------- s116 "linear dependence testing"
// Looks like a tight 5-deep chain. It is not: within each group of five, every
// read of a[k+1] happens BEFORE the statement that writes a[k+1]. So every read
// is of the PRE-LOOP value, and the whole thing is
//     a_new[j] = a_old[j+1] * a_old[j]   for all j
// i.e. fully parallel after one preload. EXACT.
void s116_v0(float *a,float *b,float *c,float *d,float *e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-5;i+=5){
            a[i  ] = a[i+1]*a[i  ];
            a[i+1] = a[i+2]*a[i+1];
            a[i+2] = a[i+3]*a[i+2];
            a[i+3] = a[i+4]*a[i+3];
            a[i+4] = a[i+5]*a[i+4];
        }
        opaque(a,b,c,d,e);
    }
}
void s116_v1(float * restrict a,float *b,float *c,float *d,float *e,
             int n,int reps,float * restrict tmp){
    (void)tmp;
    for(int nl=0;nl<reps;nl++){
        int last = ((n-6)/5)*5 + 4;                 // highest j the original writes
        // NO preload needed: going forward, a[j+1] is always still the old
        // value when a[j] is computed. This is a pure ANTI-dependence
        // (write-after-read, distance 1), which is safe to vectorize because
        // a vector op issues all its loads before any of its stores.
        for(int j=0;j<=last;j++) a[j]=a[j+1]*a[j];
        opaque(a,b,c,d,e);
    }
}
