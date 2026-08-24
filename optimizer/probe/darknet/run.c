#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <string.h>
#define BATCH 8
#define FILTERS 64
#define SPATIAL 1024
#define NEL (BATCH*FILTERS*SPATIAL)
typedef void (*vk)(float*,float*,int,int,int,float*);
void variance_v0(float*,float*,int,int,int,float*);
void variance_v1(float*,float*,int,int,int,float*);
void variance_v2(float*,float*,int,int,int,float*);
void variance_v3(float*,float*,int,int,int,float*);
static float *X, MEAN[FILTERS], OUT[FILTERS], REF[FILTERS];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3+t.tv_nsec/1e6;}
static double bench(vk f,int reps){double best=1e18;
    for(int t=0;t<9;t++){double t0=ms();
        for(int r=0;r<reps;r++){X[r%NEL]+=1e-12f;f(X,MEAN,BATCH,FILTERS,SPATIAL,OUT);}
        double dt=ms()-t0; if(dt<best)best=dt;} return best/reps;}
int main(void){
    X=malloc(sizeof(float)*NEL); srand(1);
    for(long i=0;i<NEL;i++) X[i]=(float)rand()/RAND_MAX;
    for(int i=0;i<FILTERS;i++) MEAN[i]=(float)rand()/RAND_MAX;
    vk fs[]={variance_v0,variance_v1,variance_v2,variance_v3};
    const char*nm[]={"v0 verbatim darknet (pow)","v1 + pow(v,2) -> v*v  [exact]",
                     "v2 + accumulator hoisted [exact]","v3 + lanes w4 i4 [reassociable]"};
    variance_v0(X,MEAN,BATCH,FILTERS,SPATIAL,REF);
    printf("  %-34s %10s %9s  %s\n","version","ms/call","speedup","vs verbatim");
    double t0=0;
    for(int v=0;v<4;v++){
        memset(OUT,0,sizeof OUT); fs[v](X,MEAN,BATCH,FILTERS,SPATIAL,OUT);
        double worst=0; int exact=1;
        for(int i=0;i<FILTERS;i++){
            if(OUT[i]!=REF[i]) exact=0;
            double e=fabs((double)OUT[i]-REF[i])/fabs((double)REF[i]);
            if(e>worst)worst=e; }
        double t=bench(fs[v],60);
        if(v==0)t0=t;
        printf("  %-34s %10.4f %8.2fx  %-14s %s\n",nm[v],t,t0/t,
            v==0?"(reference)":(exact?"BIT-IDENTICAL":"reassociated"),
            v==0?"":(exact?"":""));
        if(v) printf("  %-34s %10s %8s   max rel.err vs verbatim: %.2e\n","","","",worst);
    }
    return 0;}
