#ifndef RNG_H
#define RNG_H

#include <stdint.h>

// Estado de un generador xoshiro256** de 256 bits.
typedef struct {
    uint64_t s[4];
} rng_t;

// Inicializa el generador a partir de una semilla base y un indice.
// El indice permite dar a cada hilo un flujo independiente: la semilla
// de cada hilo se obtiene mezclando (semilla_base, indice) con SplitMix64,
// que es un mezclador de semillas probadamente decorrelaciona dos flujos
// incluso cuando los indices son consecutivos. Esto es indispensable:
// con un LCG clasico, semillas que difieren en 1 producen flujos
// fuertemente correlacionados y la estimacion de pi queda sesgada.
void rng_inicializar(rng_t *r, uint64_t semilla_base, uint64_t indice);

// Siguiente entero de 64 bits.
uint64_t rng_next(rng_t *r);

// Siguiente numero real uniforme en [0, 1), usando los 53 bits mas
// significativos (los bits bajos de un LCG son los de peor calidad).
double rng_double(rng_t *r);

#endif
