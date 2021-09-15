#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
#include <string.h>
#include <sys/stat.h>
#include <fcntl.h>



int main (int argc, char *argv[])
{
    int opt, timeout = 120, pages = 40960, i;
    char *dirty_rate = "100";
    char pid[10];
    void wakeup();
    char *buf;
    
    while ((opt = getopt(argc, argv, "r:s:t:")) != -1) {
        switch(opt) {
        case 'r':
            dirty_rate = optarg;
            printf("Dirty rate=%s\n", optarg);
            break;
        case 's':
            pages = atoi(optarg)/4;
            printf("Number of pages=%s\n", optarg);
            break;
        case 't':
            timeout = atoi(optarg);
            printf("Timeout=%s\n", optarg);
            break;
        }
    }

    signal(SIGALRM,wakeup);
    alarm(timeout);
    sprintf(pid,"%d\0",getpid());
    if(!fork()){
        execlp("cpulimit", "cpulimit", "-l", dirty_rate, "-p", pid, NULL);
        exit(1);
    }

    buf = (char *) calloc(pages, 4096);
    while (1) {
        for (i = 0; i < pages; i++) {
            buf[i * 4096]++;
        }
    }
}
void wakeup()
{
    exit(0);
}