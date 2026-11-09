#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <limits.h>
#include <time.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "pi.h"
#include "rng.h"

static double cronometro(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC_RAW, &t);
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

static void uso(const char *prog) {
    fprintf(stderr,
            "Uso: %s <algoritmo> <N> <T> <variante> [semilla]\n"
            "       %s validar <algoritmo> <N> <T> <variante> <repeticiones> [semilla]\n"
            "\n"
            "Algoritmos : dartboard, buffon\n"
            "Variantes  : serial, omp_reduccion, omp_privado\n",
            prog, prog);
}

// Modo validacion: repite la corrida y analiza la distribucion de pi_hat.
// Como los algoritmos de Monte Carlo son estocasticos, el resultado cambia
// entre ejecuciones. Lo que se valida es que el estimador converja al valor
// real de pi con el error teorico esperado, y que todas las variantes
// (serial y paralelas) sean estadisticamente equivalentes.
static int modo_validar(int argc, char **argv) {
    pi_algoritmo algoritmo;
    pi_variante variante;
    long N;
    int T;
    int repeticiones;

    if (argc < 8) {
        uso(argv[0]);
        return 1;
    }
    if (!pi_parse_algoritmo(argv[2], &algoritmo)) {
        fprintf(stderr, "Algoritmo desconocido: %s\n", argv[2]);
        return 1;
    }
    N = atol(argv[3]);
    T = atoi(argv[4]);
    if (!pi_parse_variante(argv[5], &variante)) {
        fprintf(stderr, "Variante desconocida: %s\n", argv[5]);
        return 1;
    }
    repeticiones = atoi(argv[6]);

    uint64_t semilla_base = (argc > 7) ? (uint64_t)strtoull(argv[7], NULL, 10) : 42ULL;

    double *estimaciones = malloc((size_t)repeticiones * sizeof(double));
    double suma = 0.0, suma2 = 0.0;
    double minimo = 0.0, maximo = 0.0;

    for (int r = 0; r < repeticiones; r++) {
        // Cada repeticion usa una semilla distinta: es lo que se quiere
        // medir, la dispersion del estimador entre corridas independientes.
        uint64_t semilla = semilla_base + (uint64_t)r * 0x9E3779B97F4A7C15ULL;
        long aciertos = pi_aciertos(algoritmo, variante, N, semilla, T);
        double pi_hat = pi_estimar(algoritmo, N, aciertos);
        estimaciones[r] = pi_hat;
        suma += pi_hat;
        suma2 += pi_hat * pi_hat;
        if (r == 0 || pi_hat < minimo) minimo = pi_hat;
        if (r == 0 || pi_hat > maximo) maximo = pi_hat;
    }

    double media = suma / repeticiones;
    double varianza = (suma2 / repeticiones) - media * media;
    if (varianza < 0.0) varianza = 0.0;
    double desviacion = sqrt(varianza);
    double sigma_teorica = pi_sigma_teorica(algoritmo, N);
    const double PI = 3.14159265358979323846;

    // z: cuantas desviaciones tipicas teóricas se aparta la media de pi.
    double z = (sigma_teorica > 0.0) ? fabs(media - PI) / sigma_teorica : 0.0;

    printf("ALGORITMO=%s\n", pi_nombre_algoritmo(algoritmo));
    printf("VARIANTE=%s\n", pi_nombre_variante(variante));
    printf("N=%ld\n", N);
    printf("T=%d\n", T);
    printf("REPETICIONES=%d\n", repeticiones);
    printf("PI_EST_MEDIA=%.9f\n", media);
    printf("PI_EST_DESV=%.9f\n", desviacion);
    printf("PI_EST_MIN=%.9f\n", minimo);
    printf("PI_EST_MAX=%.9f\n", maximo);
    printf("SIGMA_TEORICA=%.9f\n", sigma_teorica);
    printf("ERROR_MEDIA=%.9f\n", media - PI);
    printf("Z_SCORE=%.4f\n", z);
    // Veredicto: el estimador es efectivo si la media esta dentro de 3
    // desviaciones teoricas del valor real (criterio de tres sigma).
    printf("VALIDO=%d\n", (z < 3.0) ? 1 : 0);

    free(estimaciones);
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        uso(argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "validar") == 0) {
        return modo_validar(argc, argv);
    }

    if (argc < 5) {
        uso(argv[0]);
        return 1;
    }

    pi_algoritmo algoritmo;
    pi_variante variante;

    if (!pi_parse_algoritmo(argv[1], &algoritmo)) {
        fprintf(stderr, "Algoritmo desconocido: %s\n", argv[1]);
        return 1;
    }
    long N = atol(argv[2]);
    int T = atoi(argv[3]);
    if (!pi_parse_variante(argv[4], &variante)) {
        fprintf(stderr, "Variante desconocida: %s\n", argv[4]);
        return 1;
    }
    uint64_t semilla = (argc > 5) ? (uint64_t)strtoull(argv[5], NULL, 10) : 42ULL;

    if (N <= 0 || T < 1) {
        fprintf(stderr, "N debe ser positivo y T >= 1\n");
        return 1;
    }
    if (variante != PI_VAR_SERIAL && T <= 1) {
        fprintf(stderr, "Las variantes OpenMP requieren T >= 2\n");
        return 1;
    }

    double t0 = cronometro();
    long aciertos = pi_aciertos(algoritmo, variante, N, semilla, T);
    double t1 = cronometro();

    double pi_hat = pi_estimar(algoritmo, N, aciertos);
    double sigma = pi_sigma_teorica(algoritmo, N);
    const double PI = 3.14159265358979323846;

    printf("ALGORITMO=%s\n", pi_nombre_algoritmo(algoritmo));
    printf("VARIANTE=%s\n", pi_nombre_variante(variante));
    printf("N=%ld\n", N);
    printf("T=%d\n", T);
    printf("SEMILLA=%llu\n", (unsigned long long)semilla);
    printf("ACIERTOS=%ld\n", aciertos);
    printf("PI_EST=%.9f\n", pi_hat);
    printf("ERROR=%.9f\n", pi_hat - PI);
    printf("SIGMA_TEORICA=%.9f\n", sigma);
    printf("Z_SCORE=%.4f\n", sigma > 0.0 ? fabs(pi_hat - PI) / sigma : 0.0);
    printf("TIEMPO=%.9f\n", t1 - t0);

    return 0;
}
