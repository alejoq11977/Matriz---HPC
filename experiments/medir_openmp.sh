#!/bin/bash
# medir_openmp.sh
# Compila src/matriz_monotonic_openmp.c con -fopenmp -O0 (kernel en
# modules/tiempo_mult_openmp.c) y mide el tiempo de la multiplicacion
# barriendo N (500, 1000, 2000, 4000) y cantidad de hilos OpenMP
# (1, 2, 4, 8, 16) -- igual que se hizo para pthreads en la otra rama.
#
# Antes de medir, valida que la matriz C resultante sea IDENTICA a la de
# la implementacion de referencia (experiments/verify_ref), con N=10 y
# semilla 42. Esto se hace SIEMPRE (no se puede saltear).
#
# Modos de ejecucion:
#   MODO_TEST=1 bash experiments/medir_openmp.sh
#       Smoke test RAPIDO: 1 sola iteracion de cada (T, N) pero SOLO con
#       N=500, 1000, 2000 (omite N=4000 que es el mas lento). Total:
#       5 T * 3 Ns * 1 iter = 15 lineas en el CSV, ~30-60 segundos.
#       Sirve para confirmar que el pipeline completo funciona
#       (compilacion, validacion, barrido de T, parseo, plot). Al final
#       BORRA los artefactos (binario, csv raw, csv tabla, png).
#       Pensado para pruebas rapidas en este equipo.
#
#   bash experiments/medir_openmp.sh
#       Barrido completo: 10 iteraciones por cada (T, N) con todos los Ns
#       y todos los T. Total: 5 T * 4 Ns * 10 iter = 200 lineas en el
#       CSV, ~15-20 minutos. Es el modo que se usa para el experimento
#       real. DEJA los artefactos en disco.
#
# Salidas (en modo normal):
#   bin/matriz_openmp_O0
#   experiments/resultados/med_openmp_raw.csv          (header + 200 corridas)
#   experiments/resultados/caso_de_estudio_2_openmp.csv
#   experiments/resultados/caso_de_estudio_2_openmp.png

set -e

CC=${CC:-gcc}
CC_OPTS="-fopenmp -O0 -Iinclude"
SRC=src/matriz_monotonic_openmp.c
MOD_LLENADO=modules/llenado.c
MOD_LLENADO_HDR=include/llenado.h
MOD_MEM=modules/memoria.c
MOD_MEM_HDR=include/memoria.h
MOD_TIEMPO=modules/tiempo_mult_openmp.c
MOD_TIEMPO_HDR=include/tiempo_mult_openmp.h
BIN=bin/matriz_openmp_O0
VERIFY_REF=experiments/verify_ref
SALIDA=experiments/resultados
SALIDA_RAW=$SALIDA/med_openmp_raw.csv
SALIDA_TABLA=$SALIDA/caso_de_estudio_2_openmp.csv
SALIDA_PNG=$SALIDA/caso_de_estudio_2_openmp.png

N_EVAL=10
SEMILLA=42
VALOR_MAX=9
N_VALORES="500 1000 2000 4000"
N_VALORES_TEST="500 1000 2000"
T_VALORES="1 2 4 8 16"
ITERACIONES=10

mkdir -p bin
mkdir -p $SALIDA

# --- [1/5] Compilacion ---
echo "[1/5] Compilando $BIN con '$CC_OPTS'..."
$CC $CC_OPTS $SRC $MOD_LLENADO $MOD_MEM $MOD_TIEMPO -o $BIN
echo "      OK"
echo ""

# --- [2/5] Validacion contra verify_ref ---
# La validacion se hace con T=1 para que sea deterministica.
echo "[2/5] Validando correctitud: matriz C de N=$N_EVAL semilla=$SEMILLA"
echo "      contra experiments/verify_ref (modo normal, T=1)..."

if [ ! -f $VERIFY_REF ]; then
    echo "      Compilando verify_ref..."
    $CC -Wall -O2 -Iinclude $VERIFY_REF.c -o $VERIFY_REF
fi

REF_FILE=$SALIDA/_ref_openmp.txt
OUT_FILE=$SALIDA/_out_openmp.txt
$VERIFY_REF $N_EVAL $SEMILLA normal > $REF_FILE
OMP_NUM_THREADS=1 $BIN $N_EVAL $VALOR_MAX $SEMILLA > $OUT_FILE

ref_matrix=$(grep -E '^[0-9]' $REF_FILE | sed 's/[[:space:]]*$//')
bin_matrix=$(grep -E '^[0-9]' $OUT_FILE | sed 's/[[:space:]]*$//')

if [ -z "$bin_matrix" ]; then
    echo "      FALLO: el binario no imprimio ninguna matriz C (verificar que imprime cuando N<=50)"
    rm -f $REF_FILE $OUT_FILE
    exit 1
fi

if [ "$bin_matrix" = "$ref_matrix" ]; then
    echo "      OK: matriz C identica a la referencia"
else
    echo "      FALLO: matriz C del binario OpenMP NO coincide con la referencia"
    echo "      --- Primeras lineas de la referencia:"
    echo "$ref_matrix" | head -3 | sed 's/^/        /'
    echo "      --- Primeras lineas del binario OpenMP:"
    echo "$bin_matrix" | head -3 | sed 's/^/        /'
    rm -f $REF_FILE $OUT_FILE
    exit 1
fi
rm -f $REF_FILE $OUT_FILE
echo ""

# --- [3/5] Smoke test / medicion real ---
if [ "$MODO_TEST" = "1" ]; then
    ITERACIONES=1
    N_VALORES_RUN=$N_VALORES_TEST
    echo "[3/5] MODO TEST: 1 iteracion de cada (T, N) -- solo N=500,1000,2000"
    echo "      T_VALORES=$T_VALORES  N_VALORES=$N_VALORES_RUN"
else
    N_VALORES_RUN=$N_VALORES
    echo "[3/5] Midiendo $ITERACIONES corridas por cada (T, N)"
    echo "      T_VALORES=$T_VALORES  N_VALORES=$N_VALORES"
    echo "      Total: 5 T * 4 Ns * 10 iter = 200 lineas (~15-20 min)"
fi

echo "N,T,run,tiempo" > $SALIDA_RAW
for T in $T_VALORES; do
    export OMP_NUM_THREADS=$T
    for iter in $(seq 1 $ITERACIONES); do
        for N in $N_VALORES_RUN; do
            t=$($BIN $N $VALOR_MAX $SEMILLA 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+')
            echo "$N,$T,$iter,$t" >> $SALIDA_RAW
            printf "      T=%2d  iter=%2d  N=%4d  t=%ss\n" "$T" "$iter" "$N" "$t"
        done
    done
done
unset OMP_NUM_THREADS
echo "      $(wc -l < $SALIDA_RAW) lineas en $SALIDA_RAW"
echo ""

# --- [4/5] Plot (lee el CSV recien generado y produce tabla + grafica) ---
echo "[4/5] Generando tabla y grafica con python3..."
python3 experiments/plot_caso2_openmp.py
echo ""

# --- [5/5] Cleanup si MODO_TEST ---
if [ "$MODO_TEST" = "1" ]; then
    echo "[5/5] MODO TEST: limpiando artefactos..."
    rm -f $BIN
    rm -f $SALIDA_RAW
    rm -f $SALIDA_TABLA
    rm -f $SALIDA_PNG
    echo "      OK (binario, csv raw, csv tabla y png borrados)"
    echo ""
    echo "Para correr el experimento real:"
    echo "  bash experiments/medir_openmp.sh"
    echo "  python3 experiments/plot_caso2_openmp.py"
else
    echo "[5/5] Listo. Artefactos dejados en disco."
    echo "      - $BIN"
    echo "      - $SALIDA_RAW"
    echo "      - $SALIDA_TABLA"
    echo "      - $SALIDA_PNG"
fi
