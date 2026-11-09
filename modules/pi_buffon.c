#include <math.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "pi.h"
#include "rng.h"

// ---------------------------------------------------------------------------
// Problema de la aguja de Buffon (agujas sobre franjas paralelas).
//
// Se tira una aguja de longitud l sobre un suelo con franjas paralelas de
// ancho t, y se cuenta cuantas agujas cruzan alguna linea. Con l <= t la
// probabilidad de cruzar es
//
//     P = 2l / (pi * t)
//
// y el estimador de pi resulta
//
//     pi_hat = 2 * l * N / (t * h)
//
// donde h es el numero de cruces. En toda la implementacion se usa el
// caso l = t = 1, con lo que pi_hat = 2N/h.
//
// Simulacion de una tirada (caso l = t = 1):
//   - x   : distancia del centro de la aguja a la linea mas cercana.
//            Es uniforme en [0, t/2] = [0, 0.5].
//   - th  : angulo agudo entre la aguja y las lineas, uniforme en [0, pi/2].
//   - la aguja cruza una linea si x <= (l/2) * sin(th).
//
// Nota de paralelismo: el generador de numeros aleatorios es el recurso
// compartido critico. rand() no es thread-safe, y rand_r()/drand48() con
// semillas consecutivas producen flujos correlacionados que sesgan la
// estimacion. Por eso cada hilo tiene su propio xoshiro256** inicializado
// con SplitMix64 a partir de (semilla_base, indice_del_hilo).
// ---------------------------------------------------------------------------

#define BUFFON_L 1.0
#define BUFFON_T 1.0

static inline int buffon_cruza(rng_t *rng) {
    double x = rng_double(rng) * (BUFFON_T / 2.0);
    double th = rng_double(rng) * (M_PI / 2.0);
    return x <= (BUFFON_L / 2.0) * sin(th);
}

long pi_buffon_serial(long N, uint64_t semilla) {
    rng_t rng;
    rng_inicializar(&rng, semilla, 0);

    long cruces = 0;
    for (long i = 0; i < N; i++) {
        cruces += buffon_cruza(&rng);
    }
    return cruces;
}

#ifdef _OPENMP

long pi_buffon_omp_reduccion(long N, uint64_t semilla, int T) {
    long cruces = 0;

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();

        // Copia local del estado del generador: ver la nota de aliasing en
        // modules/pi_dartboard.c.
        rng_t rng;
        rng_inicializar(&rng, semilla, (uint64_t)tid);

        #pragma omp for schedule(static) reduction(+:cruces)
        for (long i = 0; i < N; i++) {
            cruces += buffon_cruza(&rng);
        }
    }

    return cruces;
}

// Contador privado por hilo, con relleno hasta un linea de cache completa.
// Sin el relleno, todos los hilos escribirian en el mismo linea de 64 bytes
// y se produciria false sharing: cada escritura invalidaria la linea en
// la cache de los demas.
typedef struct {
    long valor;
    char relleno[64 - sizeof(long)];
} contador_cache;

long pi_buffon_omp_privado(long N, uint64_t semilla, int T) {
    contador_cache *contadores = calloc((size_t)T, sizeof(contador_cache));

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();
        rng_t rng;
        rng_inicializar(&rng, semilla, (uint64_t)tid);

        long local = 0;
        #pragma omp for schedule(static)
        for (long i = 0; i < N; i++) {
            local += buffon_cruza(&rng);
        }
        contadores[tid].valor = local;
    }

    long cruces = 0;
    for (int t = 0; t < T; t++) {
        cruces += contadores[t].valor;
    }

    free(contadores);
    return cruces;
}

// Variante "naive" que se mantiene como contraejemplo medible: el estado del
// generador se accede a traves del arreglo compartido. El compilador no puede
// demostrar que esas escrituras no solapan con el acumulador, de modo que lo
// vuelca a memoria en cada iteracion y el paralelismo se pierde.
long pi_buffon_omp_alias(long N, uint64_t semilla, int T) {
    long cruces = 0;
    rng_t *rngs = malloc((size_t)T * sizeof(rng_t));

    #pragma omp parallel num_threads(T)
    {
        int tid = omp_get_thread_num();
        rng_inicializar(&rngs[tid], semilla, (uint64_t)tid);

        #pragma omp for schedule(static) reduction(+:cruces)
        for (long i = 0; i < N; i++) {
            cruces += buffon_cruza(&rngs[tid]);
        }
    }

    free(rngs);
    return cruces;
}

#endif
