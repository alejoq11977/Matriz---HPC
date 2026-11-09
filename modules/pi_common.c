#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "pi.h"

// Kernels implementados en los modulos de cada algoritmo.
long pi_dartboard_serial(long N, uint64_t semilla);
long pi_buffon_serial(long N, uint64_t semilla);
#ifdef _OPENMP
long pi_dartboard_omp_reduccion(long N, uint64_t semilla, int T);
long pi_buffon_omp_reduccion(long N, uint64_t semilla, int T);
long pi_dartboard_omp_privado(long N, uint64_t semilla, int T);
long pi_buffon_omp_privado(long N, uint64_t semilla, int T);
long pi_dartboard_omp_alias(long N, uint64_t semilla, int T);
long pi_buffon_omp_alias(long N, uint64_t semilla, int T);
#endif

long pi_aciertos(pi_algoritmo algoritmo, pi_variante variante,
                 long N, uint64_t semilla, int T) {
    switch (algoritmo) {
    case PI_ALGO_DARTBOARD:
        switch (variante) {
        case PI_VAR_SERIAL:
            return pi_dartboard_serial(N, semilla);
#ifdef _OPENMP
        case PI_VAR_OMP_REDUCCION:
            return pi_dartboard_omp_reduccion(N, semilla, T);
        case PI_VAR_OMP_PRIVADO:
            return pi_dartboard_omp_privado(N, semilla, T);
        case PI_VAR_OMP_ALIAS:
            return pi_dartboard_omp_alias(N, semilla, T);
#endif
        default:
            break;
        }
        break;

    case PI_ALGO_BUFFON:
        switch (variante) {
        case PI_VAR_SERIAL:
            return pi_buffon_serial(N, semilla);
#ifdef _OPENMP
        case PI_VAR_OMP_REDUCCION:
            return pi_buffon_omp_reduccion(N, semilla, T);
        case PI_VAR_OMP_PRIVADO:
            return pi_buffon_omp_privado(N, semilla, T);
        case PI_VAR_OMP_ALIAS:
            return pi_buffon_omp_alias(N, semilla, T);
#endif
        default:
            break;
        }
        break;
    }

    fprintf(stderr, "Variante no soportada para este algoritmo\n");
    exit(1);
}

double pi_estimar(pi_algoritmo algoritmo, long N, long aciertos) {
    if (aciertos <= 0) {
        return 0.0;
    }
    if (algoritmo == PI_ALGO_DARTBOARD) {
        // pi_hat = 4h/N
        return 4.0 * (double)aciertos / (double)N;
    }
    // pi_hat = 2N/h  (caso l = t = 1)
    return 2.0 * (double)N / (double)aciertos;
}

double pi_sigma_teorica(pi_algoritmo algoritmo, long N) {
    const double pi = 3.14159265358979323846;
    double k;
    if (algoritmo == PI_ALGO_DARTBOARD) {
        // Var(pi_hat) = pi(4-pi)/N
        k = sqrt(pi * (4.0 - pi));
    } else {
        // Var(pi_hat) = pi^2(pi-2)/(2N)
        k = sqrt(pi * pi * (pi - 2.0) / 2.0);
    }
    return k / sqrt((double)N);
}

const char *pi_nombre_algoritmo(pi_algoritmo algoritmo) {
    return algoritmo == PI_ALGO_DARTBOARD ? "dartboard" : "buffon";
}

const char *pi_nombre_variante(pi_variante variante) {
    switch (variante) {
    case PI_VAR_SERIAL:          return "serial";
    case PI_VAR_OMP_REDUCCION:   return "omp_reduccion";
    case PI_VAR_OMP_PRIVADO:     return "omp_privado";
    case PI_VAR_OMP_ALIAS:       return "omp_alias";
    default:                     return "desconocida";
    }
}

int pi_parse_algoritmo(const char *texto, pi_algoritmo *salida) {
    if (strcmp(texto, "dartboard") == 0 || strcmp(texto, "dardos") == 0) {
        *salida = PI_ALGO_DARTBOARD;
        return 1;
    }
    if (strcmp(texto, "buffon") == 0 || strcmp(texto, "agujas") == 0) {
        *salida = PI_ALGO_BUFFON;
        return 1;
    }
    return 0;
}

int pi_parse_variante(const char *texto, pi_variante *salida) {
    if (strcmp(texto, "serial") == 0) {
        *salida = PI_VAR_SERIAL;
        return 1;
    }
    if (strcmp(texto, "omp_reduccion") == 0) {
        *salida = PI_VAR_OMP_REDUCCION;
        return 1;
    }
    if (strcmp(texto, "omp_privado") == 0) {
        *salida = PI_VAR_OMP_PRIVADO;
        return 1;
    }
    if (strcmp(texto, "omp_alias") == 0) {
        *salida = PI_VAR_OMP_ALIAS;
        return 1;
    }
    return 0;
}
