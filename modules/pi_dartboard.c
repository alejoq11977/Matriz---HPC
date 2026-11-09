#include <math.h>
#include <stdlib.h>
#include <stdint.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "pi.h"
#include "rng.h"

// ---------------------------------------------------------------------------
// Metodo del dartboard (Monte Carlo con dardos).
//
// Se lanzan N dardos al azar sobre el cuadrado unidad [0,1] x [0,1] y se
// cuenta cuantos caen dentro del cuarto de circunferencia inscrito
// (x^2 + y^2 <= 1). La probabilidad de acertar es el area del cuarto de
// circunferencia sobre el area del cuadrado, es decir p = pi/4, y el
// estimador es
//
//     pi_hat = 4 * h / N
//
// A diferencia del metodo de Buffon, aqui no hay ninguna funcion
// trigonometrica: el predicado es un producto y una suma. Esa diferencia es
// la que explica que el dartboard sea mas rapido por muestra.
//
// Simulacion de un dardo:
//   - x, y : coordenadas uniformes en [0,1).
//   - acierta si x^2 + y^2 <= 1.
// ---------------------------------------------------------------------------

static inline int dartboard_acierta(rng_t *rng) {
    double x = rng_double(rng);
    double y = rng_double(rng);
    return x * x + y * y <= 1.0;
}

long pi_dartboard_serial(long N, uint64_t semilla) {
    rng_t rng;
    rng_inicializar(&rng, semilla, 0);

    long aciertos = 0;
    for (long i = 0; i < N; i++) {
        aciertos += dartboard_acierta(&rng);
    }
    return aciertos;
}

#ifdef _OPENMP

long pi_dartboard_omp_reduccion(long N, uint64_t semilla, int T) {
    long aciertos = 0;

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();

        // El estado del generador se copia a una variable local del hilo.
        // Esto no es cosmetico: si el estado se leyera a traves de un puntero
        // compartido (rngs[tid]), el compilador no podria demostrar que las
        // escrituras al estado no solapan con el acumulador, y tendria que
        // volcarlo a memoria en cada iteracion. Medido: la copia local da
        // 3.8x de speedup frente a 0.8x de la version con puntero
        // compartido. Es una optimizacion de CPU habilitada por el aliasing.
        rng_t rng;
        rng_inicializar(&rng, semilla, (uint64_t)tid);

        #pragma omp for schedule(static) reduction(+:aciertos)
        for (long i = 0; i < N; i++) {
            aciertos += dartboard_acierta(&rng);
        }
    }

    return aciertos;
}

// Contador privado por hilo, con relleno hasta completar una linea de cache.
// Sin el relleno, todos los hilos escribirian en la misma linea de 64 bytes
// y se produciria false sharing.
typedef struct {
    long valor;
    char relleno[64 - sizeof(long)];
} contador_cache;

long pi_dartboard_omp_privado(long N, uint64_t semilla, int T) {
    contador_cache *contadores = calloc((size_t)T, sizeof(contador_cache));

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();
        rng_t rng;
        rng_inicializar(&rng, semilla, (uint64_t)tid);

        long local = 0;
        #pragma omp for schedule(static)
        for (long i = 0; i < N; i++) {
            local += dartboard_acierta(&rng);
        }
        contadores[tid].valor = local;
    }

    long aciertos = 0;
    for (int t = 0; t < T; t++) {
        aciertos += contadores[t].valor;
    }

    free(contadores);
    return aciertos;
}

// Variante "naive" que se mantiene como contraejemplo medible: el estado del
// generador se lee y escribe a traves del arreglo compartido, igual que
// haria alguien que reparte un rng por hilo sin pensar en el aliasing.
long pi_dartboard_omp_alias(long N, uint64_t semilla, int T) {
    long aciertos = 0;
    rng_t *rngs = malloc((size_t)T * sizeof(rng_t));

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();
        rng_inicializar(&rngs[tid], semilla, (uint64_t)tid);

        #pragma omp for schedule(static) reduction(+:aciertos)
        for (long i = 0; i < N; i++) {
            aciertos += dartboard_acierta(&rngs[tid]);
        }
    }

    free(rngs);
    return aciertos;
}

#endif
