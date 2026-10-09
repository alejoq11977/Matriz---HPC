#!/bin/bash
# Lab 2: Optimizacion de memoria (cache line)
# Compara la version secuencial original (que accede a B por columna)
# con una version modificada que asume B ya transpuesta y accede por
# fila. La transpuesta aprovecha mejor la cache line de 64 bytes,
# porque cada acceso consecutivo cae en la misma linea.

set -e

N_EVAL=10
SEMILLA=42
VALOR_MAX=9
N_VALORES="500 1000 2000 4000"
BIN_DIR=bin
EXP_DIR=experiments
SALIDA=$EXP_DIR/resultados
mkdir -p $SALIDA

if [ ! -f $BIN_DIR/matriz_monotonic ] || [ ! -f $BIN_DIR/matriz_monotonic_t ]; then
    echo "Error: binarios no encontrados. Ejecuta 'make all' primero."
    exit 1
fi

echo "[Generando referencias con verify_ref (N=$N_EVAL, semilla=$SEMILLA)]"
$EXP_DIR/verify_ref $N_EVAL $SEMILLA normal > $SALIDA/ref_normal.txt
$EXP_DIR/verify_ref $N_EVAL $SEMILLA trans > $SALIDA/ref_trans.txt
echo "  Referencias guardadas."
echo ""

echo "================================================================"
echo "LAB 2: Optimizacion de memoria (cache line)"
echo "================================================================"
echo ""

# Funcion para extraer la matriz C de la salida del binario
extract_matrix() {
    grep -E '^[0-9]' "$1" | sed 's/[[:space:]]*$//' || true
}

validar() {
    local bin=$1
    local ref=$2
    local tmp=$SALIDA/bin_val_out.txt
    $bin $N_EVAL $VALOR_MAX $SEMILLA > $tmp 2>/dev/null
    local bin_matrix=$(extract_matrix $tmp)
    local ref_matrix=$(extract_matrix $ref)
    if [ -n "$bin_matrix" ] && [ "$bin_matrix" = "$ref_matrix" ]; then
        echo "OK"
    else
        echo "FALLO"
    fi
    rm -f $tmp
}

echo "[Validando efectividad...]"
echo "  matriz_monotonic: $(validar $BIN_DIR/matriz_monotonic $SALIDA/ref_normal.txt)"
echo "  matriz_monotonic_t: $(validar $BIN_DIR/matriz_monotonic_t $SALIDA/ref_trans.txt)"
echo ""

echo "[Midiendo tiempos...]"
declare -A T_NORMAL
declare -A T_TRANS

for N in $N_VALORES; do
    t1=$(timeout 600 $BIN_DIR/matriz_monotonic $N $VALOR_MAX 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+' || echo "TIMEOUT")
    t2=$(timeout 600 $BIN_DIR/matriz_monotonic_t $N $VALOR_MAX 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+' || echo "TIMEOUT")
    T_NORMAL[$N]=$t1
    T_TRANS[$N]=$t2
    printf "  N=%-4d  normal: %9ss   transpuesto: %9ss\n" "$N" "$t1" "$t2"
done
echo ""

TABLA=$SALIDA/lab2_tabla.txt
{
    echo "================================================================"
    echo "TABLA FINAL - LAB 2: Optimizacion de memoria"
    echo "================================================================"
    echo "matriz_monotonic: kernel original (B por columna, acceso no contiguo)"
    echo "matriz_monotonic_t: kernel transpuesto (asume B transpuesta, acceso por fila)"
    echo ""
    printf "%-12s %15s %15s\n" "N" "normal (s)" "transpuesto (s)"
    echo "----------------------------------------------------------------"
    for N in $N_VALORES; do
        printf "%-12s %15s %15s\n" "$N" "${T_NORMAL[$N]}" "${T_TRANS[$N]}"
    done
    echo "================================================================"
} | tee $TABLA

echo ""
echo "Tabla guardada en: $TABLA"
