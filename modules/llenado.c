#include <stdlib.h>
#include <time.h>

#include "llenado.h"

void llenar_matrices(int *A, int *B, int *C, size_t total_elementos, int valor_maximo) {
    srand((unsigned int)time(NULL));

    for (size_t i = 0; i < total_elementos; i++) {
        A[i] = (rand() % valor_maximo) + 1;
        B[i] = (rand() % valor_maximo) + 1;
        C[i] = 0;
    }
}
