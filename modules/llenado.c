#include <stdlib.h>
#include <time.h>

#include "llenado.h"

void llenar_matrices(int *A, int *B, int *C, size_t total_elementos, int valor_maximo) {
    llenar_matrices_con_semilla(A, B, C, total_elementos, valor_maximo, (unsigned int)time(NULL));
}

void llenar_matrices_con_semilla(int *A, int *B, int *C, size_t total_elementos, int valor_maximo, unsigned int semilla) {
    srand(semilla);

    for (size_t i = 0; i < total_elementos; i++) {
        A[i] = (rand() % valor_maximo) + 1;
        B[i] = (rand() % valor_maximo) + 1;
        C[i] = 0;
    }
}
