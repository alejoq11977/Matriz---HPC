#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char *argv[]) {

    // Verificar que recibimos los parámetros necesarios
    if (argc != 3) {
        printf("Uso: %s <N> <valor_maximo>\n", argv[0]);
        return 1;
    }

    // Convertir los argumentos de texto a enteros
    int N = atoi(argv[1]);
    int valor_maximo = atoi(argv[2]);

    // Validar los parámetros
    if (N <= 0 || valor_maximo <= 0) {
        printf("Error: N y valor_maximo deben ser mayores que 0.\n");
        return 1;
    }

    // Calcular cantidad total de elementos
    size_t total_elementos = (size_t)N * N;

    // Reservar memoria para las tres matrices
    int *A = malloc(total_elementos * sizeof(int));
    int *B = malloc(total_elementos * sizeof(int));
    int *C = malloc(total_elementos * sizeof(int));

    // Verificar que la memoria fue reservada correctamente
    if (A == NULL || B == NULL || C == NULL) {
        printf("Error: no se pudo reservar memoria.\n");

        free(A);
        free(B);
        free(C);

        return 1;
    }

    // Inicializar el generador de números aleatorios
    srand((unsigned int)time(NULL));

    // Llenar A y B con valores aleatorios
    for (size_t i = 0; i < total_elementos; i++) {
        A[i] = (rand() % valor_maximo) + 1;
        B[i] = (rand() % valor_maximo) + 1;
        C[i] = 0;
    }

    // Multiplicación de matrices
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[(size_t)i * N + j] +=
                    A[(size_t)i * N + k] *
                    B[(size_t)k * N + j];
            }
        }
    }

    // No imprimimos las matrices porque pueden ser enormes
    printf("Multiplicacion completada.\n");
    printf("Tamano de las matrices: %d x %d\n", N, N);
    printf("Valor maximo utilizado: %d\n", valor_maximo);

    // Liberar la memoria
    free(A);
    free(B);
    free(C);

    return 0;
}