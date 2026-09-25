#include <stdio.h>
#include <stdlib.h>

#include "llenado.h"
#include "memoria.h"
#include "pthread_mult.h"

int main(int argc, char *argv[]) {

    if (argc != 4) {
        printf("Uso: %s <N> <valor_maximo> <num_hilos>\n", argv[0]);
        return 1;
    }

    int N = atoi(argv[1]);
    int valor_maximo = atoi(argv[2]);
    int num_hilos = atoi(argv[3]);

    if (N <= 0 || valor_maximo <= 0 || num_hilos < 1) {
        printf("Error: N, valor_maximo y num_hilos deben ser mayores que 0.\n");
        return 1;
    }

    Matrices m = reservar_matrices(N);
    if (m.A == NULL || m.B == NULL || m.C == NULL) {
        return 1;
    }

    llenar_matrices(m.A, m.B, m.C, m.total_elementos, valor_maximo);

    double tiempo = multiplicar_pthreads(m.A, m.B, m.C, N, num_hilos);

    printf("Multiplicacion completada.\n");
    printf("Tamano de las matrices: %d x %d\n", N, N);
    printf("Valor maximo utilizado: %d\n", valor_maximo);
    printf("Hilos utilizados: %d\n", num_hilos);
    printf("Tiempo medido con CLOCK_MONOTONIC: %.9f segundos\n", tiempo);

    free(m.A);
    free(m.B);
    free(m.C);

    return 0;
}
