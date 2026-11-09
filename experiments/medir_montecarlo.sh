#!/bin/bash
# medir_montecarlo.sh
# Barrido de desempenho de los dos algoritmos de Monte Carlo para estimar pi
# (dartboard y agujas de Buffon) en sus cuatro variantes de ejecucion.
#
# Antes de medir valida que los algoritmos sigan siendo correctos: la
# estimacion de pi debe converger al valor real dentro de la tolerancia
# teorica (sigma = k/sqrt(N)). Si la validacion falla, no se mide nada.
#
# Modos de ejecucion:
#   bash experiments/medir_montecarlo.sh
#       Barrido completo. Tarda entre 10 y 30 minutos segun el equipo.
#
#   MODO_TEST=1 bash experiments/medir_montecarlo.sh
#       Version rapida: 1 repeticion y N pequenos. Sirve para comprobar que
#       el pipeline funciona. Al final borra los artefactos generados.
#
# Salidas en experiments/resultados/:
#   montecarlo_raw.csv         barrido de desempeno (una fila por corrida)
#   montecarlo_convergencia.csv  curva de convergencia de pi hacia el valor real
#   montecarlo_validacion.csv  resultados del test de efectividad
#   hardware.txt               informacion del equipo
#
# Variables de ambiente que se pueden ajustar:
#   N_VALORES    tamanos de muestra del barrido de desempeno
#   N_CONV       tamanos de muestra del estudio de convergencia
#   T_VALORES    cantidades de hilos
#   REPS         repeticiones por configuracion
#   SEMILLA      semilla base

set -e

# El locale es numerico: con es_ES el printf usa coma decimal y rompe el
# parseo de los resultados. Se fuerza el locale C para que los numeros
# se impriman siempre con punto.
export LC_ALL=C
export LANG=C

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
cd "$RAIZ"

CC=${CC:-gcc}
CFLAGS="-Wall -Wextra -O2 -fopenmp -Iinclude"
SRC="src/montecarlo.c modules/pi_common.c modules/pi_dartboard.c modules/pi_buffon.c modules/rng.c"
BIN="bin/montecarlo"
SALIDA="experiments/resultados"
RAW="$SALIDA/montecarlo_raw.csv"
CONV="$SALIDA/montecarlo_convergencia.csv"
VALID="$SALIDA/montecarlo_validacion.csv"

ALGORITMOS="dartboard buffon"
VARIANTES="serial omp_reduccion omp_privado omp_alias"
T_VALORES=${T_VALORES:-"1 2 4 8 16"}
N_VALORES=${N_VALORES:-"10000000 100000000 1000000000"}
N_CONV=${N_CONV:-"1000 10000 100000 1000000 10000000"}
REPS=${REPS:-10}
SEMILLA=${SEMILLA:-42}

if [ "$MODO_TEST" = "1" ]; then
    N_VALORES="100000 1000000"
    N_CONV="1000 10000"
    REPS=1
fi

mkdir -p "$SALIDA" bin

# --- [1/6] Compilacion ---
echo "[1/6] Compilando $BIN con '$CFLAGS'..."
$CC $CFLAGS $SRC -o $BIN -lm
echo "      OK"
echo ""

# --- [2/6] Validacion de efectividad ---
echo "[2/6] Validando efectividad (convergencia de pi_hat al valor real)..."
REPS_VAL=20
N_VAL=1000000
: > "$VALID"
for algo in $ALGORITMOS; do
    for var in serial omp_privado; do
        T=1
        [ "$var" != "serial" ] && T=8
        salida=$($BIN validar "$algo" "$N_VAL" "$T" "$var" "$REPS_VAL" "$SEMILLA")
        media=$(echo "$salida" | grep PI_EST_MEDIA= | cut -d= -f2)
        desv=$(echo "$salida" | grep PI_EST_DESV= | cut -d= -f2)
        sigma=$(echo "$salida" | grep SIGMA_TEORICA= | cut -d= -f2)
        z=$(echo "$salida" | grep Z_SCORE= | cut -d= -f2)
        valido=$(echo "$salida" | grep VALIDO= | cut -d= -f2)
        echo "$algo,$var,$N_VAL,$T,$REPS_VAL,$media,$desv,$sigma,$z,$valido" >> "$VALID"
        printf "      %-10s %-14s media=%.6f desv=%.6f (teorica %.6f) z=%.2f -> %s\n" \
            "$algo" "$var" "$media" "$desv" "$sigma" "$z" \
            "$([ "$valido" = "1" ] && echo VALIDO || echo FALLO)"
        if [ "$valido" != "1" ]; then
            echo "      ERROR: el algoritmo $algo ($var) no converge a pi. Se aborta."
            exit 1
        fi
    done
done
echo "      Todos los algoritmos convergen dentro de 3 sigma teoricas."
echo ""

# --- [3/6] Estudio de convergencia ---
echo "[3/6] Estudio de convergencia (pi_hat en funcion de N)..."
echo "algoritmo,N,pi_est,error,sigma_teorica" > "$CONV"
for algo in $ALGORITMOS; do
    for N in $N_CONV; do
        salida=$($BIN "$algo" "$N" 1 serial "$SEMILLA")
        pi_est=$(echo "$salida" | grep PI_EST= | cut -d= -f2)
        err=$(echo "$salida" | grep ERROR= | cut -d= -f2)
        sigma=$(echo "$salida" | grep SIGMA_TEORICA= | cut -d= -f2)
        echo "$algo,$N,$pi_est,$err,$sigma" >> "$CONV"
    done
    echo "      $algo: $(wc -l < "$CONV") lineas acumuladas"
done
echo ""

# --- [4/6] Barrido de desempeno ---
echo "[4/6] Barrido de desempeno..."
echo "algoritmo,variante,N,T,run,tiempo,pi_est,aciertos,z_score" > "$RAW"
total=0
for algo in $ALGORITMOS; do
    for var in $VARIANTES; do
        for N in $N_VALORES; do
            for T in $T_VALORES; do
                # La variante serial solo tiene sentido con un hilo.
                if [ "$var" = "serial" ] && [ "$T" != "1" ]; then
                    continue
                fi
                # Las variantes OpenMP necesitan al menos dos hilos.
                if [ "$var" != "serial" ] && [ "$T" = "1" ]; then
                    continue
                fi
                for rep in $(seq 1 $REPS); do
                    salida=$($BIN "$algo" "$N" "$T" "$var" "$SEMILLA")
                    tiempo=$(echo "$salida" | grep TIEMPO= | cut -d= -f2)
                    pi_est=$(echo "$salida" | grep PI_EST= | cut -d= -f2)
                    aciertos=$(echo "$salida" | grep ACIERTOS= | cut -d= -f2)
                    z=$(echo "$salida" | grep Z_SCORE= | cut -d= -f2)
                    echo "$algo,$var,$N,$T,$rep,$tiempo,$pi_est,$aciertos,$z" >> "$RAW"
                    total=$((total + 1))
                done
                printf "      %-10s %-14s N=%-11s T=%-3s\n" "$algo" "$var" "$N" "$T"
            done
        done
    done
done
echo "      $total corridas en $RAW"
echo ""

# --- [5/6] Hardware ---
echo "[5/6] Capturando informacion del hardware..."
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
    free -h | head -2
    echo ""
    echo "--- Compilador ---"
    ${CC:-gcc} --version | head -1
    echo ""
    echo "--- Parametros del experimento ---"
    echo "N (desempeno)   : $N_VALORES"
    echo "N (convergencia): $N_CONV"
    echo "T               : $T_VALORES"
    echo "Repeticiones    : $REPS"
    echo "Semilla         : $SEMILLA"
    echo "Variantes       : $VARIANTES"
    echo "Flags           : $CFLAGS"
} > "$SALIDA/hardware.txt"
echo "      -> $SALIDA/hardware.txt"
echo ""

# --- [6/6] Graficas ---
echo "[6/6] Generando graficas..."
python3 experiments/plot_montecarlo.py
echo ""

if [ "$MODO_TEST" = "1" ]; then
    echo "MODO TEST: limpiando artefactos..."
    rm -f "$RAW" "$CONV" "$VALID" "$SALIDA/hardware.txt"
    rm -f "$SALIDA"/montecarlo_*.png
    echo "      OK"
    echo ""
    echo "Para el experimento real:"
    echo "  bash experiments/medir_montecarlo.sh"
else
    echo "=============================================="
    echo "MEDICION COMPLETA"
    echo "=============================================="
    echo "  $RAW"
    echo "  $CONV"
    echo "  $VALID"
    echo "  $SALIDA/hardware.txt"
    echo "  $SALIDA/montecarlo_*.png"
    echo "=============================================="
fi
