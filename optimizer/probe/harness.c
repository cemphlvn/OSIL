#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <stdlib.h>
#include <unistd.h>
#include <libproc.h>
#define N 32000
void ref_s1113(float * restrict a, const float * restrict b);
void split_s1113(float * restrict a, const float * restrict b);
static float A[N], B[N], R[N], S[N];
static double ms(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);
    return t.tv_sec*1e3+t.tv_nsec/1e6;}
static void fill(void){srand(1);
    for(int i=0;i<N;i++){A[i]=(float)rand()/RAND_MAX;B[i]=(float)rand()/RAND_MAX;}}
static double bench(void(*f)(float*restrict,const float*restrict),float*buf){
    double best=1e18;
    for(int t=0;t<15;t++){memcpy(buf,A,sizeof A);double t0=ms();
        for(int r=0;r<2000;r++){buf[r%N]+=1e-9f;f(buf,B);}
        double dt=ms()-t0; if(dt<best)best=dt;}
    return best;}
int main(void){
    fill(); memcpy(R,A,sizeof A); ref_s1113(R,B);
    fill(); memcpy(S,A,sizeof A); split_s1113(S,B);
    double worst=0; for(int i=0;i<N;i++){double e=fabs(R[i]-S[i]); if(e>worst)worst=e;}
    printf("  differential (ref vs split): max abs diff = %.3e  %s\n",
           worst, worst==0.0?"BIT-IDENTICAL":"DIFFERS");
    if(worst!=0.0){printf("  split is not equivalent - no timing reported\n");return 1;}
    double t_ref=bench(ref_s1113,R), t_split=bench(split_s1113,S);
    printf("\n  %-34s %8.2f ms   %5.2fx\n","clang -O3 (REFUSES to vectorize)",t_ref,1.0);
    printf("  %-34s %8.2f ms   %5.2fx\n","declared split (two clean maps)",t_split,t_ref/t_split);
    return 0;}
