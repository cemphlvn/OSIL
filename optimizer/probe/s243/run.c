#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#define N 32000
void s243_v0(float*,float*,const float*,const float*,const float*,int);
void s243_v1(float*,float*,const float*,const float*,const float*,int,float*);
static float A[N],B[N],C[N],D[N],E[N],TMP[N],A0[N],B0[N],RA[N],RB[N];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3+t.tv_nsec/1e6;}
static void init(void){srand(1);
    for(int i=0;i<N;i++){A0[i]=(float)rand()/RAND_MAX;B0[i]=(float)rand()/RAND_MAX;
        C[i]=(float)rand()/RAND_MAX;D[i]=(float)rand()/RAND_MAX;E[i]=(float)rand()/RAND_MAX;}}
int main(void){
    init();
    memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);s243_v0(A,B,C,D,E,N);
    memcpy(RA,A,sizeof A);memcpy(RB,B,sizeof B);
    memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);s243_v1(A,B,C,D,E,N,TMP);
    int exact=1; double worst=0;
    for(int i=0;i<N;i++){ if(A[i]!=RA[i]||B[i]!=RB[i])exact=0;
        double e1=fabs(A[i]-RA[i]),e2=fabs(B[i]-RB[i]); if(e1>worst)worst=e1; if(e2>worst)worst=e2;}
    printf("  equivalence: %s (max abs diff %.3e)\n", exact?"BIT-IDENTICAL":"DIFFERS", worst);
    if(!exact){printf("  not equivalent - no timing\n"); return 1;}
    double t0=1e18,t1=1e18;
    for(int t=0;t<15;t++){
        memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);
        double s=ms(); for(int r=0;r<300;r++) s243_v0(A,B,C,D,E,N); double dt=ms()-s;
        if(dt<t0)t0=dt;}
    for(int t=0;t<15;t++){
        memcpy(A,A0,sizeof A);memcpy(B,B0,sizeof B);
        double s=ms(); for(int r=0;r<300;r++) s243_v1(A,B,C,D,E,N,TMP); double dt=ms()-s;
        if(dt<t1)t1=dt;}
    printf("\n  %-46s %8.3f ms   %5.2fx\n","v0 as published (clang REFUSES)",t0,1.0);
    printf("  %-46s %8.3f ms   %5.2fx\n","v1 declared node split",t1,t0/t1);
    return 0;}
