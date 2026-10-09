#!/bin/bash
# Lab 1: Optimizacion por compilacion con GCC
# Compila el mismo codigo fuente con diferentes flags de optimizacion
# y mide cuanto tarda cada uno. Para validar que todos producen el mismo
# resultado, se compara contra una implementacion de referencia (verify_ref)
# que usa la misma semilla.

set -e

CC=gcc
N_EVAL=10
SEMILLA=42
VALOR_MAX=9
N_VALORES="500 1000 2000 4000"
BIN_DIR=bin
EXP_DIR=experiments
SALIDA=$EXP_DIR/resultados
mkdir -p $SALIDA

# Lista de binarios a probar con flags.
declare -A BINARIOS=(
    ["O0"]="-O0"
    ["O1"]="-O1"
    ["O2"]="-O2"
    ["O3"]="-O3"
    ["full"]="-O3 -march=native -floop-interchange -funroll-loops -floop-nest-optimize"
    ["sin_interchange"]="-O3 -march=native -funroll-loops -floop-nest-optimize"
    ["sin_nest"]="-O3 -march=native -floop-interchange -funroll-loops"
)

# Tiempo maximo por medicion (segundos)
TIMEOUT=600

echo "================================================================"
echo "LAB 1: Optimizacion por compilacion con GCC"
echo "================================================================"
echo ""

# Compilar todos los binarios
echo "[Compilando binarios...]"
mkdir -p $BIN_DIR
for nombre in "${!BINARIOS[@]}"; do
    flags=${BINARIOS[$nombre]}
    bin=$BIN_DIR/mm_${nombre}
    if [ ! -f $bin ]; then
        echo "  Compilando mm_${nombre} con flags: $flags"
        $CC -Wall -Iinclude $flags src/matriz_monotonic.c modules/llenado.c modules/memoria.c modules/tiempo_mult.c -o $bin
    fi
done
echo ""

# Generar referencia con verify_ref (N=10, semilla=42)
echo "[Generando resultado de referencia con verify_ref (N=$N_EVAL, semilla=$SEMILLA)]"
$EXP_DIR/verify_ref $N_EVAL $SEMILLA normal > $SALIDA/ref_normal.txt
echo "  Referencia guardada."
echo ""

# Tabla de resultados
echo "[Validando efectividad y midiendo tiempos...]"
echo ""

declare -A TIEMPOS
declare -A EFECTIVOS

# Funcion para correr binario con timeout
run_with_timeout() {
    local bin=$1
    local N=$2
    timeout $TIMEOUT $bin $N $VALOR_MAX 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+' || echo "TIMEOUT"
}

# Extrae solo las lineas que son SOLO numeros (la matriz C) de una salida
extract_matrix() {
    grep -E '^[0-9]' "$1" | sed 's/[[:space:]]*$//' || true
}

for nombre in O0 O1 O2 O3 full sin_interchange sin_nest; do
    bin=$BIN_DIR/mm_${nombre}
    echo "--- mm_${nombre} (flags: ${BINARIOS[$nombre]}) ---"

    # Test de efectividad: comparar SOLO la matriz C de la salida
    bin_output_file=$SALIDA/bin_${nombre}_out.txt
    $bin $N_EVAL $VALOR_MAX $SEMILLA > $bin_output_file 2>/dev/null
    bin_matrix=$(extract_matrix $bin_output_file)
    ref_matrix=$(extract_matrix $SALIDA/ref_normal.txt)

    if [ -n "$bin_matrix" ] && [ "$bin_matrix" = "$ref_matrix" ]; then
        echo "  Efectividad: OK (matriz C identica a la referencia)"
        EFECTIVOS[$nombre]="OK"
    else
        echo "  Efectividad: FALLO (matriz C distinta a la referencia)"
        EFECTIVOS[$nombre]="FALLO"
    fi
    rm -f $bin_output_file

    # Medir tiempos
    TIEMPOS[$nombre,500]=""
    TIEMPOS[$nombre,1000]=""
    TIEMPOS[$nombre,2000]=""
    TIEMPOS[$nombre,4000]=""
    for N in $N_VALORES; do
        t=$(run_with_timeout $bin $N)
        TIEMPOS[$nombre,$N]=$t
    done
    printf "  N=500: %9ss | N=1000: %9ss | N=2000: %9ss | N=4000: %9ss\n" \
        "${TIEMPOS[$nombre,500]}" \
        "${TIEMPOS[$nombre,1000]}" \
        "${TIEMPOS[$nombre,2000]}" \
        "${TIEMPOS[$nombre,4000]}"
    echo ""
done

# Generar tabla final
TABLA=$SALIDA/lab1_tabla.txt
{
    echo "================================================================"
    echo "TABLA FINAL - LAB 1: Optimizacion por compilacion con GCC"
    echo "================================================================"
    echo "Cada version fue compilada con -Wall (warnings) y los flags indicados."
    echo "La efectividad compara la matriz C resultante (N=$N_EVAL, semilla=$SEMILLA)"
    echo "contra una implementacion de referencia con 6 bucles anidados (verify_ref)."
    echo ""
    printf "%-20s %-15s %12s %12s %12s %12s\n" "Version" "Efectividad" "t(500)" "t(1000)" "t(2000)" "t(4000)"
    echo "----------------------------------------------------------------"
    for nombre in O0 O1 O2 O3 full sin_interchange sin_nest; do
        printf "%-20s %-15s %12s %12s %12s %12s\n" \
            "mm_${nombre}" \
            "${EFECTIVOS[$nombre]}" \
            "${TIEMPOS[$nombre,500]}" \
            "${TIEMPOS[$nombre,1000]}" \
            "${TIEMPOS[$nombre,2000]}" \
            "${TIEMPOS[$nombre,4000]}"
    done
    echo "----------------------------------------------------------------"
    echo ""
    echo "Flags de cada version:"
    for nombre in O0 O1 O2 O3 full sin_interchange sin_nest; do
        echo "  mm_${nombre}: ${BINARIOS[$nombre]}"
    done
    echo "================================================================"
} | tee $TABLA

echo ""
echo "Tabla guardada en: $TABLA"
