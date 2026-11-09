#!/bin/bash
# perfilar_montecarlo.sh
# Perfilado de los algoritmos de Monte Carlo para pi: CPU con GProf y
# memoria con Cachegrind y max RSS.
#
# Es la version del Reto 2 del script experiments/perfilar.sh (que sigue
# intacto para el caso de estudio 2).
#
# Salidas en experiments/resultados/perfilado_reto2/:
#   gprof_<algoritmo>.txt        tiempo por funcion (CPU)
#   cachegrind_<algoritmo>.txt   D1 misses, miss rate, LL misses (memoria)
#   rss.csv                      memoria maxima residente
#   resumen_perfilado.csv        tabla consolidada
#   hardware.txt                 info del equipo
#
# Uso:
#   bash experiments/perfilar_montecarlo.sh
#   N_PERFILADO=100000 bash experiments/perfilar_montecarlo.sh

set -e
export LC_ALL=C
export LANG=C

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
cd "$RAIZ"

# GProf muestrea a 100 Hz: necesita runtime suficiente para acumular
# muestras. Con N=10^9 el kernel corre varios segundos y el perfil es
# representativo. Cachegrind es ~100x mas lento, asi que usa un N mucho
# menor (la tasa de fallo es una propiedad del patron de acceso, no de N).
N_GPROF=${N_GPROF:-1000000000}
N_CACHEGRIND=${N_CACHEGRIND:-10000000}
SEMILLA=${SEMILLA:-42}
SALIDA="$RAIZ/experiments/resultados/perfilado_reto2"
BIN="$RAIZ/bin/perfilado_mc"
TOOLS="$RAIZ/.tools"

mkdir -p "$SALIDA" "$RAIZ/bin/perfilado_mc"

# --- Herramientas ---
bash experiments/bootstrap_tools.sh
VG=""
if [ -x "$TOOLS/root/usr/bin/valgrind" ]; then
    VG="$TOOLS/root/usr/bin/valgrind"
    export VALGRIND_LIB="$TOOLS/root/usr/libexec/valgrind"
elif command -v valgrind >/dev/null 2>&1; then
    VG=$(command -v valgrind)
fi

CC=${CC:-gcc}
CFLAGS="-Wall -Wextra -O2 -fopenmp -Iinclude"
FUENTES="src/montecarlo.c modules/pi_common.c modules/pi_dartboard.c modules/pi_buffon.c modules/rng.c"

echo "================================================================"
echo "PERFILADO DE LOS ALGORITMOS DE MONTE CARLO"
echo "================================================================"
echo "N para GProf = $N_GPROF   N para Cachegrind = $N_CACHEGRIND"
echo "valgrind: ${VG:-NO DISPONIBLE}"
echo ""

echo "[1/4] Compilando (version normal y version con -pg para GProf)..."
$CC $CFLAGS $FUENTES -o "$BIN/montecarlo" -lm
$CC $CFLAGS -pg $FUENTES -o "$BIN/montecarlo_pg" -lm
echo "      OK"
echo ""

echo "[2/4] Perfilado de CPU con GProf..."
for algo in dartboard buffon; do
    (
        cd "$SALIDA"
        rm -f gmon.out
        "$BIN/montecarlo_pg" "$algo" "$N_GPROF" 1 serial "$SEMILLA" > /dev/null 2>&1 || true
        if [ -f gmon.out ]; then
            gprof "$BIN/montecarlo_pg" gmon.out > "gprof_${algo}.txt" 2>/dev/null || true
            echo "      $algo -> gprof_${algo}.txt"
        else
            echo "      $algo -> NO se genero gmon.out"
        fi
        rm -f gmon.out
    )
done
echo ""

echo "[3/4] Perfilado de memoria con Cachegrind + max RSS..."
if [ -z "$VG" ]; then
    echo "      valgrind no disponible, se omite cachegrind"
else
    for algo in dartboard buffon; do
        "$VG" --tool=cachegrind --cache-sim=yes \
            --cachegrind-out-file="$SALIDA/cachegrind_${algo}.out" \
            "$BIN/montecarlo" "$algo" "$N_CACHEGRIND" 1 serial "$SEMILLA" \
            > /dev/null 2>"$SALIDA/cachegrind_${algo}.txt" || true
        echo "      $algo -> cachegrind_${algo}.txt"
    done
fi

# Max RSS: footprint de memoria del proceso
$CC -O2 experiments/maxrss.c -o "$BIN/maxrss"
echo "algoritmo,variante,threads,max_rss_kb,max_rss_mb" > "$SALIDA/rss.csv"
for algo in dartboard buffon; do
    for var in serial omp_privado; do
        T=1
        [ "$var" != "serial" ] && T=8
        out=$("$BIN/maxrss" "$BIN/montecarlo" "$algo" "$N_CACHEGRIND" "$T" "$var" "$SEMILLA" \
              2>&1 >/dev/null | grep -oP 'MAXRSS_KB=\K[0-9]+' || echo 0)
        mb=$(awk -v kb="$out" 'BEGIN{printf "%.2f", kb/1024}')
        echo "$algo,$var,$T,$out,$mb" >> "$SALIDA/rss.csv"
        echo "      $algo ($var, T=$T): $out KB = $mb MB"
    done
done
echo ""

echo "[4/4] Consolidando..."
python3 experiments/plot_perfilado_montecarlo.py

{
    echo "=============================================="
    echo "INFORMACION DEL EQUIPO - perfilado Monte Carlo"
    echo "=============================================="
    echo "Fecha: $(date)"
    echo "Hostname: $(hostname)"
    echo ""
    echo "--- CPU ---"
    lscpu 2>/dev/null | grep -E "^(Architecture|CPU\(s\)|On-line|Model name|Thread|Core|Socket|CPU max|CPU min|L1d|L1i|L2|L3|Vendor)" || true
    echo ""
    echo "--- Memoria ---"
    free -h | head -2
    echo ""
    echo "--- Compilador ---"
    ${CC:-gcc} --version | head -1
    echo ""
    echo "N para GProf: $N_GPROF"
    echo "N para Cachegrind: $N_CACHEGRIND"
} > "$SALIDA/hardware.txt"

echo ""
echo "=============================================="
echo "PERFILADO COMPLETO"
echo "=============================================="
echo "  $SALIDA"
echo "=============================================="
