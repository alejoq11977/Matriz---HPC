#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "llenado_trans.h"
#include "memoria.h"
#include "tiempo_mult_trans.h"

int main(int argc, char *argv[]) {

    if (argc < 3 || argc > 4) {
        printf("Uso: %s <N> <valor_maximo> [semilla]\n", argv[0]);
        return 1;
    }

    int N = atoi(argv[1]);
    int valor_maximo = atoi(argv[2]);

    if (N <= 0 || valor_maximo <= 0) {
        printf("Error: N y valor_maximo deben ser mayores que 0.\n");
        return 1;
    }

    Matrices m = reservar_matrices(N);
    if (m.A == NULL || m.B == NULL || m.C == NULL) {
        return 1;
    }

    if (argc == 4) {
        unsigned int semilla = (unsigned int)atol(argv[3]);
        llenar_matrices_transpuesto_con_semilla(m.A, m.B, m.C, m.total_elementos, valor_maximo, semilla);
    } else {
        llenar_matrices_transpuesto(m.A, m.B, m.C, m.total_elementos, valor_maximo);
    }

    double tiempo = multiplicar_y_medir_trans(m.A, m.B, m.C, N);

    printf("Multiplicacion completada.\n");
    printf("Tamano de las matrices: %d x %d\n", N, N);
    printf("Valor maximo utilizado: %d\n", valor_maximo);
    printf("Tiempo medido con CLOCK_MONOTONIC_RAW: %.9f segundos\n", tiempo);

    if (N <= 50) {
        printf("Matriz C:\n");
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                printf("%d ", m.C[i * N + j]);
            }
            printf("\n");
        }
    }

    free(m.A);
    free(m.B);
    free(m.C);

    return 0;
}
