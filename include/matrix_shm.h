#ifndef MATRIX_SHM_H
#define MATRIX_SHM_H

#include <stddef.h>

typedef struct {
    int N;
    size_t total_elementos;
    size_t bytes;
    int *A;
    int *B;
    int *C;
    int fd_A;
    int fd_B;
    int fd_C;
} MatricesShm;

MatricesShm crear_matrices_compartidas(int N);
void liberar_matrices_compartidas(int N);

#endif
