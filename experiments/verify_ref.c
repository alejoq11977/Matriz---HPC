// Implementacion de referencia: 6 bucles anidados con restrict para que
// el compilador no asuma aliasing. Se usa para verificar que las versiones
// optimizadas (con flags) y la version transpuesta (Lab 2) producen
// el mismo resultado que una implementacion "ingenuamente correcta".

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Kernel normal de referencia: 6 bucles, accede a memoria en el orden
// "natural" del algoritmo i, j, k.
void mult_ref_normal(const int * restrict A,
                    const int * restrict B,
                    int * restrict C,
                    int N) {
    memset(C, 0, (size_t)N * (size_t)N * sizeof(int));
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            for (int k = 0; k < N; k++)
                C[i*N + j] += A[i*N + k] * B[k*N + j];
}

// Kernel transpuesto de referencia: para validar la version transpuesta del Lab 2.
// Asume que B fue llenado en orden transpuesto (B[j*N+k] = M[k*N+j]).
void mult_ref_trans(const int * restrict A,
                   const int * restrict B,
                   int * restrict C,
                   int N) {
    memset(C, 0, (size_t)N * (size_t)N * sizeof(int));
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            for (int k = 0; k < N; k++)
                C[i*N + j] += A[i*N + k] * B[j*N + k];
}

// Llena A y B en orden normal con la semilla dada.
void llenar_normal(int *A, int *B, int N, int vmax, unsigned int s) {
    srand(s);
    for (int i = 0; i < N*N; i++) {
        A[i] = (rand() % vmax) + 1;
        B[i] = (rand() % vmax) + 1;
    }
}

// Llena A en orden normal, y B en orden transpuesto (B[j*N+k] = r).
// Misma secuencia de rand() que llenar_normal, pero asignacion diferente.
void llenar_trans(int *A, int *B, int N, int vmax, unsigned int s) {
    srand(s);
    for (int i = 0; i < N*N; i++) A[i] = (rand() % vmax) + 1;
    for (int j = 0; j < N; j++)
        for (int k = 0; k < N; k++)
            B[j*N + k] = (rand() % vmax) + 1;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Uso: %s N semilla modo (normal|trans)\n", argv[0]);
        return 1;
    }
    int N = atoi(argv[1]);
    unsigned int s = (unsigned int)atol(argv[2]);
    int modo = strcmp(argv[3], "trans") == 0 ? 1 : 0;

    int *A = malloc(N*N*sizeof(int));
    int *B = malloc(N*N*sizeof(int));
    int *C = malloc(N*N*sizeof(int));
    if (!A || !B || !C) return 1;

    if (modo) {
        llenar_trans(A, B, N, 9, s);
        mult_ref_trans(A, B, C, N);
    } else {
        llenar_normal(A, B, N, 9, s);
        mult_ref_normal(A, B, C, N);
    }

    for (int i = 0; i < N*N; i++) printf("%d%c", C[i], (i+1)%N==0?'\n':' ');

    free(A); free(B); free(C);
    return 0;
}
