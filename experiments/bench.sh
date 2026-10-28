#!/bin/bash
# bench.sh
# Benchmark portable: se ejecuta en CUALQUIER maquina Linux y produce un
# archivo de resultados con el hardware detectado + el rendimiento medido.
#
# Se usa para la comparacion entre dos maquinas diferentes que exige el
# enunciado del caso de estudio 2. El script es autocontenido: no necesita
# nada instalado que no venga de base, salvo opcionalmente valgrind (que se
# descarga solo, sin sudo, via bootstrap_tools.sh).
#
# Salidas en experiments/resultados/benchmark/:
#   <etiqueta>.csv        metricas del benchmark de esta maquina
#   <etiqueta>_hardware.txt   descripcion completa del hardware
#   <etiqueta>_raw.csv    corridas crudas de la multiplicacion
#
# Uso:
#   bash experiments/bench.sh <etiqueta> [N ...]
#   bash experiments/bench.sh maquinaA 500 1000 2000
#
# La etiqueta identifica la maquina (ej: "A", "B", "portatil-Mateo").

set -e

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
cd "$RAIZ"

ETIQUETA=${1:-maquina}
shift || true
NS=${*:-"500 1000 2000"}

VALOR_MAX=${VALOR_MAX:-9}
SEMILLA=${SEMILLA:-42}
T_VALORES=${T_VALORES:-"1 2 4 8 16"}
ITERACIONES=${ITERACIONES:-10}

SALIDA="$RAIZ/experiments/resultados/benchmark"
BIN="$RAIZ/bin/bench"
mkdir -p "$SALIDA" "$RAIZ/bin"

echo "================================================================"
echo "BENCHMARK - maquina: $ETIQUETA"
echo "================================================================"
echo "N: $NS   T: $T_VALORES   iteraciones: $ITERACIONES"
echo ""

# --- Compilar el binario de multiplicacion con OpenMP (igual que el experimento) ---
CC=${CC:-gcc}
echo "[1/4] Compilando binario OpenMP (-fopenmp -O2)..."
$CC -Wall -O2 -fopenmp -Iinclude src/matriz_monotonic_openmp.c \
    modules/llenado.c modules/memoria.c modules/tiempo_mult_openmp.c -o $BIN
echo "      OK"
echo ""

# --- Informacion del hardware ---
echo "[2/4] Capturando informacion del hardware..."
HARD="$SALIDA/${ETIQUETA}_hardware.txt"
{
    echo "=============================================="
    echo "BENCHMARK - MAQUINA: $ETIQUETA"
    echo "=============================================="
    echo "Fecha de medicion : $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "Hostname          : $(hostname)"
    echo "Usuario           : $(whoami)"
    echo ""
    echo "--- Sistema operativo ---"
    uname -a
    if [ -r /etc/os-release ]; then
        . /etc/os-release
        echo "Distribucion      : $PRETTY_NAME"
    fi
    echo ""
    echo "--- Procesador ---"
    lscpu 2>/dev/null || cat /proc/cpuinfo | head -30
    echo ""
    echo "--- Memoria ---"
    free -h | head -2
    echo ""
    echo "--- Almacenamiento (raiz) ---"
    df -h / | tail -1
    echo ""
    echo "--- Compilador ---"
    echo "Compiler: $($CC --version | head -1)"
    echo ""
    echo "--- Nucleos logicos detectados ---"
    echo "Nucleos logicos detectados: $(nproc)"
    echo ""
    echo "--- Parametros del experimento ---"
    echo "N               : $NS"
    echo "T               : $T_VALORES"
    echo "Iteraciones     : $ITERACIONES"
    echo "Semilla         : $SEMILLA"
    echo "Valor maximo    : $VALOR_MAX"
    echo "Flags de compil.: -Wall -O2 -fopenmp"
} > "$HARD"
echo "      -> $HARD"
echo ""

# --- Corridas ---
echo "[3/4] Ejecutando mediciones..."
RAW="$SALIDA/${ETIQUETA}_raw.csv"
echo "N,T,run,tiempo" > "$RAW"
for T in $T_VALORES; do
    export OMP_NUM_THREADS=$T
    for iter in $(seq 1 $ITERACIONES); do
        for N in $NS; do
            t=$("$BIN" "$N" "$VALOR_MAX" "$SEMILLA" 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+' || echo "")
            if [ -n "$t" ]; then
                echo "$N,$T,$iter,$t" >> "$RAW"
                printf "      T=%-3s iter=%-3s N=%-5s t=%ss\n" "$T" "$iter" "$N" "$t"
            else
                echo "      ERROR en N=$N T=$T iter=$iter"
            fi
        done
    done
done
unset OMP_NUM_THREADS
echo "      $(wc -l < "$RAW") lineas en $RAW"
echo ""

# --- Consolidar ---
echo "[4/4] Consolidando metricas..."
python3 experiments/plot_benchmark.py --maquina "$ETIQUETA"

echo ""
echo "=============================================="
echo "BENCHMARK COMPLETO - $ETIQUETA"
echo "=============================================="
echo "Archivos:"
echo "  $RAW"
echo "  $SALIDA/${ETIQUETA}.csv"
echo "  $HARD"
echo ""
echo "Para la otra maquina: copie la rama y corra el mismo comando"
echo "  bash experiments/bench.sh <otra-etiqueta> $NS"
echo "=============================================="
