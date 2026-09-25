#include <pthread.h>
#include <stddef.h>
#include <time.h>

#include "pthread_mult.h"

typedef struct {
    int inicio;
    int fin;
    int N;
    int *A;
    int *B;
    int *C;
} ArgsHilo;

static void *worker(void *arg) {
    ArgsHilo *a = (ArgsHilo *)arg;
    for (int i = a->inicio; i < a->fin; i++) {
        for (int j = 0; j < a->N; j++) {
            for (int k = 0; k < a->N; k++) {
                a->C[(size_t)i * a->N + j] +=
                    a->A[(size_t)i * a->N + k] *
                    a->B[(size_t)k * a->N + j];
            }
        }
    }
    return NULL;
}

double multiplicar_pthreads(int *A, int *B, int *C, int N, int num_hilos) {
    pthread_t hilos[num_hilos];
    ArgsHilo args[num_hilos];

    int filas_por_hilo = N / num_hilos;
    int resto = N % num_hilos;
    int actual = 0;
    for (int t = 0; t < num_hilos; t++) {
        int extra = (t < resto) ? 1 : 0;
        args[t].inicio = actual;
        args[t].fin = actual + filas_por_hilo + extra;
        actual = args[t].fin;
        args[t].N = N;
        args[t].A = A;
        args[t].B = B;
        args[t].C = C;
    }

    struct timespec inicio, fin;
    clock_gettime(CLOCK_MONOTONIC, &inicio);

    for (int t = 0; t < num_hilos; t++) {
        pthread_create(&hilos[t], NULL, worker, &args[t]);
    }

    for (int t = 0; t < num_hilos; t++) {
        pthread_join(hilos[t], NULL);
    }

    clock_gettime(CLOCK_MONOTONIC, &fin);

    return (double)(fin.tv_sec - inicio.tv_sec) +
           (double)(fin.tv_nsec - inicio.tv_nsec) / 1e9;
}
