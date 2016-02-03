#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "PPMd.h"
#if defined(_WIN32_ENVIRONMENT_)
#include <process.h>
#define FUNC_RET_TYPE void
#define RETURN return
#else
#include <pthread.h>
#define FUNC_RET_TYPE void*
#define RETURN return NULL
#endif /* defined(_WIN32_ENVIRONMENT_) */

#define N_THREADS 3
#define TEST_FILE_NAME "TestFile.bin"
#define TEST_FILE_SIZE UINT(256*256*256)
/*************  indicator of compression, exported function  ****************/
void _STDCALL PrintInfo(_PPMD_FILE* DecodedFile,_PPMD_FILE*)
{
    char WrkStr[81];                        WrkStr[80]=0;
    memset(WrkStr,'\b',80);                 memset(WrkStr,' ',40);
    memset(WrkStr,'-',(40U*ftell(DecodedFile))/TEST_FILE_SIZE);
    printf(WrkStr);                         fflush(stdout);
}
/*************************  thread function  ********************************/
FUNC_RET_TYPE EncodeFile(void* arg)
{
    char WrkStr[16];
    sprintf(WrkStr,"%.4s%04X.enc",TEST_FILE_NAME,(int)long(arg));
    FILE* fpIn=fopen(TEST_FILE_NAME,"rb"), * fpOut=fopen(WrkStr,"wb");
    if (!fpIn || !fpOut || !StartSubAllocator(32)) {
        printf("\nError #1 in thread!\n");  RETURN;
    }
    EncodeFile(fpOut,fpIn,9,TRUE);          StopSubAllocator();
    if (ferror(fpIn) || ferror(fpOut)) {
        printf("\nError #2 in thread!\n");  RETURN;
    }
    fclose(fpIn);                           fclose(fpOut);
	RETURN;
}
int main()
{
    UINT i, t1, t2;
    time_t t0;
    printf("Example of running PPMd library in threads.\n");
/*          generating test file out of simple order-2 model with           *
 *    theoretical entropy = 2.0bpb, but PPMd don`t know about it, hee-hee   */
    FILE* fp=fopen(TEST_FILE_NAME,"wb");
    for (BYTE NextSym, PrevSym=0, PrevPrevSym=i=0;i < TEST_FILE_SIZE;i++) {
        NextSym=PrevSym+11*PrevPrevSym+(4L*rand())/(RAND_MAX+1L);
        putc(NextSym,fp);
        PrevPrevSym=PrevSym;                PrevSym=NextSym;
    }
    fclose(fp);
    printf("  Compressing files sequentially: ");
    t0=time(NULL);
    for (i=0;i < N_THREADS;i++)             EncodeFile((void*)long(i));
    printf("done in %d sec.  \n",t1=difftime(time(NULL),t0));
    printf("Compressing files simultaneously: ");
    t0=time(NULL);
#if defined(_WIN32_ENVIRONMENT_)
    HANDLE hs[N_THREADS];
    for (i=0;i < N_THREADS;i++) {
        hs[i]=(HANDLE)_beginthread(EncodeFile,8192,(void*)long(i+0x1000));
        if (hs[i] == HANDLE(-1)) {
            puts("Error at creation!");     exit(0);
        }
    }
    WaitForMultipleObjects(N_THREADS,hs,TRUE,INFINITE);
#else
    pthread_t hs[N_THREADS];
    for (i=0;i < N_THREADS;i++)
        if (pthread_create(&hs[i],NULL,EncodeFile,(void*)long(i+0x1000)) != 0) {
                puts("Error at creation!"); exit(0);
        }
    for (i=0;i < N_THREADS;i++)             pthread_join(hs[i],NULL);
#endif /* defined(_WIN32_ENVIRONMENT_) */
    printf("done in %d sec.  \n",t2=difftime(time(NULL),t0));
    printf("Perhaps You have a ");
    if (t2 < 0.7*t1)                        printf("multiprocessor PC");
    else if (t2 < t1)                       printf("hyper-threading PC");
    else                                    printf("standard PC");
    printf("\nEnd of program.\n");          return 0;
}
