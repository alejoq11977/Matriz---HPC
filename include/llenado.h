#ifndef LLENADO_H
#define LLENADO_H

#include <stddef.h>

void llenar_matrices(int *A, int *B, int *C, size_t total_elementos, int valor_maximo);

void llenar_matrices_con_semilla(int *A, int *B, int *C, size_t total_elementos, int valor_maximo, unsigned int semilla);

#endif
