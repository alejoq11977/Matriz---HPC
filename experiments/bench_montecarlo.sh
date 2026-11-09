#!/bin/bash
# bench_montecarlo.sh
# Benchmark portable de los algoritmos de Monte Carlo para pi. Se ejecuta en
# CUALQUIER maquina Linux y produce un archivo de resultados con el hardware
# detectado y el rendimiento medido.
#
# Es la version del Reto 2 del script experiments/bench.sh (que sigue
# intacto para el caso de estudio 2).
#
# Salidas en experiments/resultados/benchmark_reto2/:
#   <etiqueta>_raw.csv        corridas crudas (una fila por configuracion)
#   <etiqueta>_hardware.txt   descripcion completa del hardware
#   <etiqueta>.csv            metricas consolidadas
#
# Uso:
#   bash experiments/bench_montecarlo.sh <etiqueta> [N ...]
#   bash experiments/bench_montecarlo.sh MaquinaB 10000000 100000000
#
# La etiqueta identifica la maquina (ej: "MaquinaA", "MaquinaB").

set -e
export LC_ALL=C
export LANG=C

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
cd "$RAIZ"

ETIQUETA=${1:-maquina}
shift || true
NS=${*:-"10000000 100000000"}

SEMILLA=${SEMILLA:-42}
T_VALORES=${T_VALORES:-"1 2 4 8 16"}
ITERACIONES=${ITERACIONES:-10}
VARIANTE=${VARIANTE:-omp_privado}

SALIDA="$RAIZ/experiments/resultados/benchmark_reto2"
BIN="$RAIZ/bin/montecarlo"
mkdir -p "$SALIDA" "$RAIZ/bin"

echo "================================================================"
echo "BENCHMARK MONTE CARLO - maquina: $ETIQUETA"
echo "================================================================"
echo "N: $NS   T: $T_VALORES   iteraciones: $ITERACIONES   variante: $VARIANTE"
echo ""

CC=${CC:-gcc}
echo "[1/4] Compilando el binario de Monte Carlo (-fopenmp -O2)..."
$CC -Wall -Wextra -O2 -fopenmp -Iinclude \
    src/montecarlo.c modules/pi_common.c modules/pi_dartboard.c \
    modules/pi_buffon.c modules/rng.c -o "$BIN" -lm
echo "      OK"
echo ""

echo "[2/4] Capturando informacion del hardware..."
HARD="$SALIDA/${ETIQUETA}_hardware.txt"
{
    echo "=============================================="
    echo "BENCHMARK MONTE CARLO - MAQUINA: $ETIQUETA"
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
    lscpu 2>/dev/null || head -30 /proc/cpuinfo
    echo "Nucleos logicos detectados: $(nproc)"
    echo ""
    echo "--- Memoria ---"
    free -h | head -2
    echo ""
    echo "--- Compilador ---"
    echo "Compiler: $($CC --version | head -1)"
    echo ""
    echo "--- Parametros del experimento ---"
    echo "N               : $NS"
    echo "T               : $T_VALORES"
    echo "Iteraciones     : $ITERACIONES"
    echo "Variante        : $VARIANTE"
    echo "Semilla         : $SEMILLA"
    echo "Flags de compil.: -Wall -Wextra -O2 -fopenmp"
} > "$HARD"
echo "      -> $HARD"
echo ""

echo "[3/4] Ejecutando mediciones..."
RAW="$SALIDA/${ETIQUETA}_raw.csv"
echo "algoritmo,variante,N,T,run,tiempo,pi_est,aciertos,z_score" > "$RAW"
for algo in dartboard buffon; do
    for N in $NS; do
        for T in $T_VALORES; do
            var=$VARIANTE
            [ "$T" = "1" ] && var=serial
            for rep in $(seq 1 $ITERACIONES); do
                salida=$("$BIN" "$algo" "$N" "$T" "$var" "$SEMILLA")
                tiempo=$(echo "$salida" | grep TIEMPO= | cut -d= -f2)
                pi_est=$(echo "$salida" | grep PI_EST= | cut -d= -f2)
                aciertos=$(echo "$salida" | grep ACIERTOS= | cut -d= -f2)
                z=$(echo "$salida" | grep Z_SCORE= | cut -d= -f2)
                echo "$algo,$var,$N,$T,$rep,$tiempo,$pi_est,$aciertos,$z" >> "$RAW"
            done
            printf "      %-10s N=%-11s T=%-3s  (min de %d corridas)\n" \
                "$algo" "$N" "$T" "$ITERACIONES"
        done
    done
done
echo "      $(wc -l < "$RAW") lineas en $RAW"
echo ""

echo "[4/4] Consolidando metricas..."
python3 experiments/plot_benchmark_montecarlo.py --maquina "$ETIQUETA"

echo ""
echo "=============================================="
echo "BENCHMARK COMPLETO - $ETIQUETA"
echo "=============================================="
echo "  $RAW"
echo "  $HARD"
echo "  $SALIDA/${ETIQUETA}.csv"
echo ""
echo "Para la otra maquina: copie la rama y corra el mismo comando"
echo "  bash experiments/bench_montecarlo.sh <otra-etiqueta> $NS"
echo "=============================================="
