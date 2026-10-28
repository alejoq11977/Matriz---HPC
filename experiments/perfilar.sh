#!/bin/bash
# perfilar.sh
# Caracterizacion (perfilado) de la aplicacion: minimo para CPU y para memoria.
#
# Herramientas:
#   CPU     -> GProf  (muestreo + contadores de instrumentacion por funcion)
#   Memoria -> Cachegrind (D1 misses, LL misses, miss rate) + max RSS
#
# Perfiles analizados:
#   secuencial  : modules/tiempo_mult.c      (kernel naive, B por columna)
#   transpuesto : modules/tiempo_mult_trans.c (kernel transpuesto, B por fila)
#   openmp      : modules/tiempo_mult_openmp.c (kernel con #pragma omp parallel for collapse(2))
#
# Salidas en experiments/resultados/perfilado/:
#   gprof_<variante>.txt      reporte de GProf
#   cachegrind_<variante>_<etiqueta>.out   datos crudos de Cachegrind
#   cachegrind_<variante>_<etiqueta>.txt   resumen legible de Cachegrind
#   rss.csv                   footprint de memoria por variante
#   resumen_perfilado.csv     tabla consolidada de todas las metricas
#   hardware.txt              informacion del equipo
#
# Uso:
#   bash experiments/perfilar.sh            # usa N=500 (default)
#   N_PERFILADO=1000 bash experiments/perfilar.sh

set -e

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
cd "$RAIZ"

N_PERFILADO=${N_PERFILADO:-500}
VALOR_MAX=${VALOR_MAX:-9}
SEMILLA=${SEMILLA:-42}
SALIDA="$RAIZ/experiments/resultados/perfilado"
BIN="$RAIZ/bin/perfilado"
TOOLS="$RAIZ/.tools"

mkdir -p "$SALIDA" "$RAIZ/bin/perfilado"

# --- Herramientas ---
bash experiments/bootstrap_tools.sh
VG=""
TIME_V=""
if [ -x "$TOOLS/root/usr/bin/valgrind" ]; then
    VG="$TOOLS/root/usr/bin/valgrind"
    export VALGRIND_LIB="$TOOLS/root/usr/libexec/valgrind"
elif command -v valgrind >/dev/null 2>&1; then
    VG=$(command -v valgrind)
fi
if [ -x "$TOOLS/root/usr/bin/time" ]; then
    TIME_V="$TOOLS/root/usr/bin/time"
elif [ -x /usr/bin/time ]; then
    TIME_V=/usr/bin/time
fi

echo "================================================================"
echo "PERFILADO DE LA APLICACION (CPU con GProf, memoria con Cachegrind)"
echo "================================================================"
echo "N = $N_PERFILADO   valor_max = $VALOR_MAX   semilla = $SEMILLA"
echo "valgrind : ${VG:-NO DISPONIBLE}"
echo "time -v  : ${TIME_V:-NO DISPONIBLE}"
echo ""

# --- Compilacion de las tres variantes ---
echo "[1/5] Compilando variantes (una con -pg para GProf, otra normal)..."
CC=${CC:-gcc}
CFLAGS="-Wall -O2 -Iinclude"

# Con -pg para GProf
$CC $CFLAGS -pg src/matriz_monotonic.c        modules/llenado.c modules/memoria.c modules/tiempo_mult.c        -o $BIN/secuencial_pg
$CC $CFLAGS -pg src/matriz_monotonic_t.c      modules/llenado_trans.c modules/memoria.c modules/tiempo_mult_trans.c -o $BIN/transpuesto_pg
$CC $CFLAGS -pg -fopenmp src/matriz_monotonic_openmp.c modules/llenado.c modules/memoria.c modules/tiempo_mult_openmp.c -o $BIN/openmp_pg

# Normales (sin instrumentacion) para cachegrind y RSS
$CC $CFLAGS src/matriz_monotonic.c        modules/llenado.c modules/memoria.c modules/tiempo_mult.c        -o $BIN/secuencial
$CC $CFLAGS src/matriz_monotonic_t.c      modules/llenado_trans.c modules/memoria.c modules/tiempo_mult_trans.c -o $BIN/transpuesto
$CC $CFLAGS -fopenmp src/matriz_monotonic_openmp.c modules/llenado.c modules/memoria.c modules/tiempo_mult_openmp.c -o $BIN/openmp

# Helper de max RSS
$CC -O2 experiments/maxrss.c -o $BIN/maxrss
echo "      OK"
echo ""

# --- GProf ---
echo "[2/5] Perfilado de CPU con GProf..."
for variante in secuencial transpuesto openmp; do
    case $variante in
        openmp) THREADS=4 ;;
        *)      THREADS=1 ;;
    esac
    (
        cd "$SALIDA"
        rm -f gmon.out
        OMP_NUM_THREADS=$THREADS "$BIN/${variante}_pg" "$N_PERFILADO" "$VALOR_MAX" "$SEMILLA" > /dev/null 2>&1 || true
        if [ -f gmon.out ]; then
            gprof "$BIN/${variante}_pg" gmon.out > "gprof_${variante}.txt" 2>/dev/null || true
            echo "      $variante -> gprof_${variante}.txt"
        else
            echo "      $variante -> NO se genero gmon.out"
        fi
        rm -f gmon.out
    )
done
echo ""

# --- Cachegrind ---
echo "[3/5] Perfilado de memoria con Cachegrind..."
if [ -z "$VG" ]; then
    echo "      valgrind no disponible, se omite cachegrind"
else
    cachegrind_run() {
        local variante="$1"
        local etiqueta="$2"
        local prog="$3"
        local threads="$4"
        local out="$SALIDA/cachegrind_${variante}_${etiqueta}.out"
        OMP_NUM_THREADS="$threads" "$VG" --tool=cachegrind --cache-sim=yes \
            --cachegrind-out-file="$out" "$prog" "$N_PERFILADO" "$VALOR_MAX" "$SEMILLA" \
            > /dev/null 2>"$SALIDA/cachegrind_${variante}_${etiqueta}.txt" || true
        echo "      $variante ($etiqueta) -> cachegrind_${variante}_${etiqueta}.txt"
    }
    cachegrind_run secuencial  T1  "$BIN/secuencial"  1
    cachegrind_run transpuesto T1  "$BIN/transpuesto" 1
    cachegrind_run openmp      T1  "$BIN/openmp"      1
    cachegrind_run openmp      T8  "$BIN/openmp"      8
    cachegrind_run openmp      T16 "$BIN/openmp"      16
fi
echo ""

# --- Max RSS (footprint de memoria) ---
echo "[4/5] Midiendo footprint de memoria (max RSS)..."
echo "variante,threads,max_rss_kb,max_rss_mb" > "$SALIDA/rss.csv"
rss_run() {
    local variante=$1 threads=$2 prog=$3
    local out
    out=$("$BIN/maxrss" "$prog" "$N_PERFILADO" "$VALOR_MAX" "$SEMILLA" 2>&1 >/dev/null | grep -oP 'MAXRSS_KB=\K[0-9]+' || echo 0)
    local mb=$(awk -v kb="$out" 'BEGIN{printf "%.1f", kb/1024}')
    echo "$variante,$threads,$out,$mb" >> "$SALIDA/rss.csv"
    echo "      $variante (T=$threads): $out KB = $mb MB"
}
rss_run secuencial  1  "$BIN/secuencial"
rss_run transpuesto 1  "$BIN/transpuesto"
rss_run openmp      1  "$BIN/openmp"
rss_run openmp      8  "$BIN/openmp"
rss_run openmp      16 "$BIN/openmp"
echo ""

# --- Info del hardware ---
echo "[5/5] Consolidando resultados..."
{
    echo "=============================================="
    echo "INFORMACION DEL EQUIPO"
    echo "=============================================="
    echo "Fecha: $(date)"
    echo "Hostname: $(hostname)"
    echo ""
    echo "--- Kernel / SO ---"
    uname -a
    echo ""
    echo "--- CPU ---"
    lscpu 2>/dev/null | grep -E "^(Architecture|CPU\(s\)|On-line|Model name|Thread|Core|Socket|CPU max|CPU min|L1d|L1i|L2|L3|Vendor)" || true
    echo ""
    echo "--- Memoria ---"
    free -h
    echo ""
    echo "--- Compilador ---"
    ${CC:-gcc} --version | head -1
} > "$SALIDA/hardware.txt"

# --- Tabla consolidada ---
python3 experiments/plot_perfilado.py

echo ""
echo "=============================================="
echo "PERFILADO COMPLETO"
echo "=============================================="
echo "Resultados en: experiments/resultados/perfilado/"
echo "  - resumen_perfilado.csv    tabla consolidada"
echo "  - gprof_*.txt              reportes de CPU (GProf)"
echo "  - cachegrind_*.txt        metricas de cache (memoria)"
echo "  - rss.csv                  footprint de memoria"
echo "  - hardware.txt             info del equipo"
echo "=============================================="
