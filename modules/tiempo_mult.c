#include <time.h>

#include "tiempo_mult.h"

double multiplicar_y_medir(int *A, int *B, int *C, int N) {
    struct timespec inicio;
    clock_gettime(CLOCK_MONOTONIC, &inicio);

    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[(size_t)i * N + j] +=
                    A[(size_t)i * N + k] *
                    B[(size_t)k * N + j];
            }
        }
    }

    struct timespec fin;
    clock_gettime(CLOCK_MONOTONIC, &fin);

    return (double)(fin.tv_sec - inicio.tv_sec) +
           (double)(fin.tv_nsec - inicio.tv_nsec) / 1000000000.0;
}
