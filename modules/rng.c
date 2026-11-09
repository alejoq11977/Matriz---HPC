#include "rng.h"

// ---------------------------------------------------------------------------
// Mezclador de semillas SplitMix64.
//
// Su unico proposito es dispersar las semillas: a partir de un par
// (semilla, indice) produce un estado de 64 bits del que no se deduce nada
// sobre el original. Se usa para derivar las semillas de cada hilo a partir
// de una unica semilla base, de modo que los flujos de dos hilos con
// indices consecutivos no queden correlacionados.
// ---------------------------------------------------------------------------
static uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

// ---------------------------------------------------------------------------
// xoshiro256** (Blackman y Vigna).
//
// Generador de 256 bits con periodo 2^256, pasado en las pruebas de
// velocidad y calidad de referencia. La variante "**" es la de mejor
// calidad estadistica y usa una multiplicacion de 128 bits, que el
// compilador resuelve con un par de instrucciones.
// ---------------------------------------------------------------------------
static inline uint64_t rotl64(uint64_t x, int k) {
    return (x << k) | (x >> (64 - k));
}

static inline uint64_t xoshiro256starstar(rng_t *r) {
    uint64_t resultado = rotl64(r->s[1] * 5, 7) * 9;
    uint64_t t = r->s[1] << 17;

    r->s[2] ^= r->s[0];
    r->s[3] ^= r->s[1];
    r->s[1] ^= r->s[2];
    r->s[0] ^= r->s[3];
    r->s[2] ^= t;
    r->s[3] = rotl64(r->s[3], 45);

    return resultado;
}

void rng_inicializar(rng_t *r, uint64_t semilla_base, uint64_t indice) {
    // Se mezcla el indice con una constante prima golden ratio para que
    // indices consecutivos den entradas muy distintas al mezclador, y luego
    // se usa SplitMix64 para llenar el estado de 256 bits.
    uint64_t x = semilla_base ^ (indice * 0x9E3779B97F4A7C15ULL);

    r->s[0] = splitmix64(&x);
    r->s[1] = splitmix64(&x);
    r->s[2] = splitmix64(&x);
    r->s[3] = splitmix64(&x);

    // xoshiro exige que el estado no sea todo cero.
    if ((r->s[0] | r->s[1] | r->s[2] | r->s[3]) == 0) {
        r->s[0] = 0x9E3779B97F4A7C15ULL;
    }
}

uint64_t rng_next(rng_t *r) {
    return xoshiro256starstar(r);
}

double rng_double(rng_t *r) {
    // Se toman los 53 bits mas significativos, que es la precision exacta
    // de un double. Descartar los bits bajos evita la conocida debilidad de
    // los LCG, donde los bits bajos tienen periodos muy cortos.
    return (double)(rng_next(r) >> 11) * (1.0 / 9007199254740992.0);
}
