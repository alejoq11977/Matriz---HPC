#include <stddef.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "fork_mult.h"

static void multiplicar_rango(int *A, int *B, int *C, int N, int inicio, int fin) {
    for (int i = inicio; i < fin; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[(size_t)i * N + j] +=
                    A[(size_t)i * N + k] *
                    B[(size_t)k * N + j];
            }
        }
    }
}

double multiplicar_fork(int *A, int *B, int *C, int N, int num_procesos) {
    int filas_por_proceso = N / num_procesos;
    int resto = N % num_procesos;
    int actual = 0;
    int pids[num_procesos];

    struct timespec inicio, fin;
    clock_gettime(CLOCK_MONOTONIC_RAW, &inicio);

    for (int t = 0; t < num_procesos; t++) {
        int extra = (t < resto) ? 1 : 0;
        int inicio_hijo = actual;
        int fin_hijo = actual + filas_por_proceso + extra;
        actual = fin_hijo;

        pid_t pid = fork();
        if (pid < 0) {
            _exit(1);
        }
        if (pid == 0) {
            multiplicar_rango(A, B, C, N, inicio_hijo, fin_hijo);
            _exit(0);
        }
        pids[t] = pid;
    }

    for (int t = 0; t < num_procesos; t++) {
        waitpid(pids[t], NULL, 0);
    }

    clock_gettime(CLOCK_MONOTONIC_RAW, &fin);

    return (double)(fin.tv_sec - inicio.tv_sec) +
           (double)(fin.tv_nsec - inicio.tv_nsec) / 1e9;
}
