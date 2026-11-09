#ifndef PI_H
#define PI_H

#include <stdint.h>

// Algoritmo de Monte Carlo usado para estimar pi.
typedef enum {
    PI_ALGO_DARTBOARD = 0,  // dardos en el cuadrado unidad
    PI_ALGO_BUFFON = 1       // agujas sobre franjas paralelas
} pi_algoritmo;

// Variante de ejecucion. Las cuatro hacen exactamente el mismo trabajo
// (N muestras); lo que cambia es como se paraleliza, como se cuenta y como
// se accede al estado del generador de numeros aleatorios.
typedef enum {
    PI_VAR_SERIAL = 0,       // una sola hebra
    PI_VAR_OMP_REDUCCION = 1, // omp for con reduction(+:hits), RNG en copia local
    PI_VAR_OMP_PRIVADO = 2,  // contadores privados por hilo, RNG en copia local
    PI_VAR_OMP_ALIAS = 3       // RNG via puntero compartido (contraejemplo)
} pi_variante;

// Numero de aciertos (muestras que cumplen la condicion) de N simulaciones.
// El estimador de pi se obtiene a partir de los aciertos:
//   dartboard: pi_hat = 4 * aciertos / N
//   buffon   : pi_hat = 2 * N / aciertos
long pi_aciertos(pi_algoritmo algoritmo, pi_variante variante,
                 long N, uint64_t semilla, int T);

// Estimador de pi a partir del numero de aciertos.
double pi_estimar(pi_algoritmo algoritmo, long N, long aciertos);

// Desviacion tipica teorica del estimador, usada para la validacion de
// efectividad: sigma = k / sqrt(N).
//   dartboard: k = sqrt(pi*(4-pi))          = 1.6420
//   buffon   : k = sqrt(pi^2*(pi-2)/2)      = 2.3735
double pi_sigma_teorica(pi_algoritmo algoritmo, long N);

const char *pi_nombre_algoritmo(pi_algoritmo algoritmo);
const char *pi_nombre_variante(pi_variante variante);
int pi_parse_algoritmo(const char *texto, pi_algoritmo *salida);
int pi_parse_variante(const char *texto, pi_variante *salida);

#endif
