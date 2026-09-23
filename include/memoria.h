#ifndef MEMORIA_H
#define MEMORIA_H

#include <stddef.h>

typedef struct {
    int *A;
    int *B;
    int *C;
    size_t total_elementos;
} Matrices;

Matrices reservar_matrices(int N);

#endif
