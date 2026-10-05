#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#include "fork_mult.h"
#include "llenado.h"
#include "matrix_shm.h"

int main(int argc, char *argv[]) {

    if (argc != 4) {
        printf("Uso: %s <N> <valor_maximo> <num_procesos>\n", argv[0]);
        return 1;
    }

    int N = atoi(argv[1]);
    int valor_maximo = atoi(argv[2]);
    int num_procesos = atoi(argv[3]);

    if (N <= 0 || valor_maximo <= 0 || num_procesos < 2) {
        printf("Error: N y valor_maximo > 0; num_procesos >= 2.\n");
        return 1;
    }

    MatricesShm m = crear_matrices_compartidas(N);

    srand((unsigned int)time(NULL));
    for (size_t i = 0; i < m.total_elementos; i++) {
        m.A[i] = (rand() % valor_maximo) + 1;
        m.B[i] = (rand() % valor_maximo) + 1;
    }

    double tiempo = multiplicar_fork(m.A, m.B, m.C, N, num_procesos);

    printf("Multiplicacion completada.\n");
    printf("Tamano de las matrices: %d x %d\n", N, N);
    printf("Valor maximo utilizado: %d\n", valor_maximo);
    printf("Procesos utilizados: %d\n", num_procesos);
    printf("Tiempo medido con CLOCK_MONOTONIC_RAW: %.9f segundos\n", tiempo);

    liberar_matrices_compartidas(N);
    return 0;
}
