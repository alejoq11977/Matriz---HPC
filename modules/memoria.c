#include <stdio.h>
#include <stdlib.h>

#include "memoria.h"

Matrices reservar_matrices(int N) {
    Matrices m = {NULL, NULL, NULL, 0};

    m.total_elementos = (size_t)N * (size_t)N;

    m.A = malloc(m.total_elementos * sizeof(int));
    m.B = malloc(m.total_elementos * sizeof(int));
    m.C = malloc(m.total_elementos * sizeof(int));

    if (m.A == NULL || m.B == NULL || m.C == NULL) {
        printf("Error: no se pudo reservar memoria.\n");
        free(m.A);
        free(m.B);
        free(m.C);
        m.A = NULL;
        m.B = NULL;
        m.C = NULL;
        m.total_elementos = 0;
    }

    return m;
}
