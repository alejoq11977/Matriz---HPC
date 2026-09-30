#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#include "llenado.h"
#include "matrix_shm.h"

static void multiplicar_rango(int *A, int *B, int *C, int N, int inicio, int fin) {
    for (int i = inicio; i < fin; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[(size_t)i * N + j] +=
                    A[(size_t)i * N + k] *
                    B[(size_t)k * N + j];
            }
        }
    }
}

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

    int filas_por_proceso = N / num_procesos;
    int resto = N % num_procesos;
    int actual = 0;
    int pids[num_procesos];

    struct timespec inicio, fin;
    clock_gettime(CLOCK_MONOTONIC_RAW, &inicio);

    for (int t = 0; t < num_procesos; t++) {
        int extra = (t < resto) ? 1 : 0;
        int inicio_hijo = actual;
        int fin_hijo = actual + filas_por_proceso + extra;
        actual = fin_hijo;

        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            exit(1);
        }
        if (pid == 0) {
            multiplicar_rango(m.A, m.B, m.C, N, inicio_hijo, fin_hijo);
            _exit(0);
        }
        pids[t] = pid;
    }

    for (int t = 0; t < num_procesos; t++) {
        waitpid(pids[t], NULL, 0);
    }

    clock_gettime(CLOCK_MONOTONIC_RAW, &fin);

    double tiempo = (double)(fin.tv_sec - inicio.tv_sec) +
                    (double)(fin.tv_nsec - inicio.tv_nsec) / 1e9;

    printf("Multiplicacion completada.\n");
    printf("Tamano de las matrices: %d x %d\n", N, N);
    printf("Valor maximo utilizado: %d\n", valor_maximo);
    printf("Procesos utilizados: %d\n", num_procesos);
    printf("Tiempo medido con CLOCK_MONOTONIC_RAW: %.9f segundos\n", tiempo);

    liberar_matrices_compartidas(N);
    return 0;
}
