#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 32000
void s212_v0(float*,float*,float*,float*,float*,int,int);
void s212_v1(float*,float*,float*,float*,float*,int,int);
void s211_v0(float*,float*,float*,float*,float*,int,int);
void s211_v1(float*,float*,float*,float*,float*,int,int);
void s1213_v0(float*,float*,float*,float*,float*,int,int);
void s1213_v1(float*,float*,float*,float*,float*,int,int);
void s261_v0(float*,float*,float*,float*,float*,int,int);
void s261_v1(float*,float*,float*,float*,float*,int,int);
void s244_v0(float*,float*,float*,float*,float*,int,int);
void s244_v1(float*,float*,float*,float*,float*,int,int);
void s291_v0(float*,float*,float*,float*,float*,int,int);
void s291_v1(float*,float*,float*,float*,float*,int,int);
void s292_v0(float*,float*,float*,float*,float*,int,int);
void s292_v1(float*,float*,float*,float*,float*,int,int);
void s221_v0(float*,float*,float*,float*,float*,int,int);
void s221_v1(float*,float*,float*,float*,float*,int,int);
void s241_v0(float*,float*,float*,float*,float*,int,int);
void s241_v1(float*,float*,float*,float*,float*,int,int,float*);
static float TMP[N];
void s116_v0(float*,float*,float*,float*,float*,int,int);
void s116_v1(float*,float*,float*,float*,float*,int,int,float*);
static void s116_v1w(float*a,float*b,float*c,float*d,float*e,int n,int r){
    s116_v1(a,b,c,d,e,n,r,TMP); }
static void s241_v1w(float*a,float*b,float*c,float*d,float*e,int n,int r){
    s241_v1(a,b,c,d,e,n,r,TMP); }
static float A0[N],B0[N],C0[N],D[N],E[N],A[N],B[N],C[N],RA[N],RB[N],RC[N];
void opaque(float*a,float*b,float*c,float*d,float*e){(void)a;(void)b;(void)c;(void)d;(void)e;}
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3+t.tv_nsec/1e6;}
static void init(void){srand(1);
    for(int i=0;i<N;i++){A0[i]=(float)rand()/RAND_MAX+0.5f;B0[i]=(float)rand()/RAND_MAX+0.5f;
        C0[i]=(float)rand()/RAND_MAX+0.5f;D[i]=(float)rand()/RAND_MAX;E[i]=(float)rand()/RAND_MAX;}}
typedef void(*K)(float*,float*,float*,float*,float*,int,int);
static void check_and_time(const char*name,K v0,K v1){
    init();
    memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);memcpy(C,C0,sizeof C); v0(A,B,C,D,E,N,1);
    memcpy(RA,A,sizeof A);memcpy(RB,B,sizeof B);memcpy(RC,C,sizeof C);
    memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);memcpy(C,C0,sizeof C); v1(A,B,C,D,E,N,1);
    int exact=1; double worst=0;
    for(int i=0;i<N;i++){ if(A[i]!=RA[i]||B[i]!=RB[i])exact=0;
        double u=fabs(A[i]-RA[i]),w=fabs(B[i]-RB[i]);
        double r1=u/(fabs(RA[i])+1e-30), r2=w/(fabs(RB[i])+1e-30);
        if(r1>worst)worst=r1; if(r2>worst)worst=r2;
        if(C[i]!=RC[i])exact=0;
        double r3=fabs(C[i]-RC[i])/(fabs(RC[i])+1e-30); if(r3>worst)worst=r3; }
    if(!exact && worst>1e-5){
        printf("  %-6s NOT EQUIVALENT (max rel %.2e) - no timing\n",name,worst); return; }
    double t0=1e18,t1=1e18;
    for(int t=0;t<11;t++){memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);memcpy(C,C0,sizeof C);
        double s=ms(); v0(A,B,C,D,E,N,60); double dt=ms()-s; if(dt<t0)t0=dt;}
    for(int t=0;t<11;t++){memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);memcpy(C,C0,sizeof C);
        double s=ms(); v1(A,B,C,D,E,N,60); double dt=ms()-s; if(dt<t1)t1=dt;}
    printf("  %-6s %-14s v0 %7.2f ms   v1 %7.2f ms   %5.2fx\n",
        name, exact?"BIT-IDENTICAL":"rel<1e-5", t0,t1,t0/t1);
}
int main(void){
    printf("  loop   equivalence     verbatim (no compiler vectorizes)   declared\n");
    check_and_time("s212", s212_v0, s212_v1);
    check_and_time("s211", s211_v0, s211_v1);
    check_and_time("s1213", s1213_v0, s1213_v1);
    check_and_time("s261", s261_v0, s261_v1);
    check_and_time("s244", s244_v0, s244_v1);
    check_and_time("s291", s291_v0, s291_v1);
    check_and_time("s292", s292_v0, s292_v1);
    check_and_time("s221", s221_v0, s221_v1);
    check_and_time("s241", s241_v0, s241_v1w);
    check_and_time("s116", s116_v0, s116_v1w);
    return 0;}
