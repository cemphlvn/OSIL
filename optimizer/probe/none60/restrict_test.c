// Does `restrict` ALONE (no restructuring) recover these loops?
// Same bodies as v0, only the pointers are declared non-aliasing.
extern void opaque(float*,float*,float*,float*,float*);
void r212(float * restrict a,float * restrict b,float * restrict c,
          float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++){ a[i]*=c[i]; b[i]+=a[i+1]*d[i]; }
        opaque(a,b,c,d,e);} }
void r241(float * restrict a,float * restrict b,float * restrict c,
          float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;i++){ a[i]=b[i]*c[i]*d[i]; b[i]=a[i]*a[i+1]*d[i]; }
        opaque(a,b,c,d,e);} }
void r244(float * restrict a,float * restrict b,float * restrict c,
          float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-1;++i){ a[i]=b[i]+c[i]*d[i]; b[i]=c[i]+b[i];
                                a[i+1]=b[i]+a[i+1]*d[i]; }
        opaque(a,b,c,d,e);} }
void r291(float * restrict a,float * restrict b,float * restrict c,
          float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){ int im1=n-1;
        for(int i=0;i<n;i++){ a[i]=(b[i]+b[im1])*0.5f; im1=i; }
        opaque(a,b,c,d,e);} }
void r116(float * restrict a,float * restrict b,float * restrict c,
          float * restrict d,float * restrict e,int n,int reps){
    for(int nl=0;nl<reps;nl++){
        for(int i=0;i<n-5;i+=5){
            a[i]=a[i+1]*a[i]; a[i+1]=a[i+2]*a[i+1]; a[i+2]=a[i+3]*a[i+2];
            a[i+3]=a[i+4]*a[i+3]; a[i+4]=a[i+5]*a[i+4]; }
        opaque(a,b,c,d,e);} }
