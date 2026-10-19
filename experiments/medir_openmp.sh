#!/bin/bash
# medir_openmp.sh
# Compila matriz_monotonic.c con -fopenmp -O0 y mide 10 corridas,
# variando N en cada iteracion para evitar problemas de cache.

set -e

CC_OPTS="-fopenmp -O0 -Iinclude"
SRC=src/matriz_monotonic.c
MOD_LLENADO=modules/llenado.c
MOD_LLENADO_HDR=include/llenado.h
MOD_MEM=modules/memoria.c
MOD_MEM_HDR=include/memoria.h
MOD_TIEMPO=modules/tiempo_mult.c
MOD_TIEMPO_HDR=include/tiempo_mult.h
BIN=bin/matriz_openmp_O0
SALIDA=experiments/resultados/med_openmp_raw.csv

mkdir -p bin
mkdir -p experiments/resultados

echo "[1/3] Compilando $BIN con '$CC_OPTS'..."
gcc -Wall $CC_OPTS $SRC $MOD_LLENADO $MOD_MEM $MOD_TIEMPO -o $BIN

echo "[2/3] Miediendo 10 corridas con variacion de N..."
echo "N,run,tiempo" > $SALIDA
for iter in $(seq 1 10); do
    for N in 500 1000 2000 4000; do
        t=$($BIN $N 9 42 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+')
        echo "$N,$iter,$t" >> $SALIDA
    done
done

echo "[3/3] Listo. $(wc -l < $SALIDA) lineas en $SALIDA"
