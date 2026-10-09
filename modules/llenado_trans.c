#include <stdlib.h>
#include <time.h>

#include "llenado_trans.h"

static void llenar_matrices_transpuesto_impl(int *A, int *B, int *C, size_t total_elementos, int valor_maximo) {
    size_t N = 0;
    while (N * N < total_elementos) N++;

    for (size_t i = 0; i < total_elementos; i++) {
        A[i] = (rand() % valor_maximo) + 1;
        C[i] = 0;
    }

    for (size_t j = 0; j < N; j++) {
        for (size_t k = 0; k < N; k++) {
            B[j * N + k] = (rand() % valor_maximo) + 1;
        }
    }
}

void llenar_matrices_transpuesto(int *A, int *B, int *C, size_t total_elementos, int valor_maximo) {
    srand((unsigned int)time(NULL));
    llenar_matrices_transpuesto_impl(A, B, C, total_elementos, valor_maximo);
}

void llenar_matrices_transpuesto_con_semilla(int *A, int *B, int *C, size_t total_elementos, int valor_maximo, unsigned int semilla) {
    srand(semilla);
    llenar_matrices_transpuesto_impl(A, B, C, total_elementos, valor_maximo);
}
