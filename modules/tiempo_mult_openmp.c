#include <time.h>
#include <omp.h>

#include "tiempo_mult_openmp.h"

double multiplicar_y_medir_openmp(int *A, int *B, int *C, int N) {
    struct timespec inicio;
    clock_gettime(CLOCK_MONOTONIC_RAW, &inicio);

    // Paralelizacion del triple loop con OpenMP.
    //
    // Por que estas directivas y no otras (analisis basado en los ejemplos
    // del PDF "OpenMP Application Programming Interface Examples v6.0.1",
    // https://github.com/OpenMP/Examples/tree/v6.0.1):
    //
    //   - Ejemplo 3.1 (ploop.1.c): #pragma omp parallel for basico.
    //     Solo paraleliza UN loop. Si lo aplicamos al loop i del kernel,
    //     con N=4000 tenemos 4000 chunks y mal balanceo entre 12 cores.
    //
    //   - Ejemplo 3.8 (collapse.1.c): clausula collapse. ES EL PATRON
    //     que nos sirve: une los loops i y j en un unico espacio de
    //     N*N iteraciones (16M para N=4000), repartido entre los hilos.
    //     El loop k queda secuencial dentro de cada (i,j) -- es la
    //     acumulacion del producto punto.
    //
    //   - Ejemplo 5.3.5 (task_dep.5.c): matrix multiplication con tasks
    //     y depend(in/inout) por bloques. Es mas complejo de lo que
    //     necesitamos: asume un kernel bloqueado BSxBS y el calculo de
    //     dependencias por bloques. Lo descartamos para este caso.
    //
    // Clausulas elegidas:
    //   - collapse(2): une i+j en un solo espacio de iteraciones.
    //   - NO se usa private(k) explicito porque C99 ya hace a las
    //     variables de control de un loop implicitamente privadas en
    //     el loop construct. Agregar private(k) haria fallar la
    //     compilacion porque k esta declarada DENTRO del for y no es
    //     visible en el punto donde aparece la directiva.
    //
    // Por que NO se necesitan otras clausulas:
    //   - A, B, C son shared por defecto. Es correcto: A y B solo se
    //     leen, y cada hilo solo escribe en C[i*N+j] para el (i,j) que
    //     le toco en el espacio colapsado. No hay race condition.
    //   - No hace falta reduction(+:): cada C[i][j] lo escribe un solo
    //     hilo. La acumulacion es interna al hilo en su propio (i,j).
    //   - No hace falta critical ni atomic.
    #pragma omp parallel for collapse(2)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            for (int k = 0; k < N; k++) {
                C[(size_t)i * N + j] +=
                    A[(size_t)i * N + k] *
                    B[(size_t)k * N + j];
            }
        }
    }

    struct timespec fin;
    clock_gettime(CLOCK_MONOTONIC_RAW, &fin);

    return (double)(fin.tv_sec - inicio.tv_sec) +
           (double)(fin.tv_nsec - inicio.tv_nsec) / 1000000000.0;
}
