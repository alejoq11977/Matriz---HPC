#!/bin/bash
set -e

# ============================================================
# Experimento de speedup para multiplicacion de matrices
# ============================================================
# Bloque 1: pthreads (T = 1, 2, 4, 8, 16)   -> resultados_raw.csv
# Bloque 2: fork    (T = 2, 4, 8, 16)       -> resultados_fork_raw.csv
#
# - 5 tamanos: 500, 1000, 2000, 4000, 8000
# - 10 corridas por configuracion
# - Loop order: outer = repeticiones, inner = tamanos
#   (segun indicacion del profesor para evitar cache poisoning)
# - Resumible: si ya existe la corrida (N, T, run) en el CSV, la salta
# - sleep 1 entre corridas para que time(NULL) cambie la semilla
# ============================================================

VALOR_MAXIMO=10
TAMANOS=(500 1000 2000 4000 8000)
HILOS_PTHREADS=(1 2 4 8 16)
HILOS_FORK=(2 4 8 16)
RUNS=10

LOG=experiments/run.log

mkdir -p experiments

# Verifica que los binarios existan
if [ ! -x bin/matriz_monotonic ] || [ ! -x bin/matriz_pthreads ] || [ ! -x bin/matriz_fork ]; then
    echo "Error: binarios no encontrados. Ejecuta 'make' primero." >&2
    exit 1
fi

# -------------------------------------------------------
# Helpers genericos
# -------------------------------------------------------

# Cuenta cuantas corridas hay registradas para (N, T) en un CSV
count_runs() {
    local raw=$1 n=$2 t=$3
    awk -F, -v n="$n" -v t="$t" '$1==n && $2==t {c++} END {print c+0}' "$raw" 2>/dev/null
}

# Corre una medicion individual y la appendea al CSV
#   $1 = raw, $2 = N, $3 = threads, $4 = run_id, $5 = binario, $6 = label
measure() {
    local raw=$1 n=$2 t=$3 run_id=$4 bin=$5 label=$6
    local t_value
    if [ "$t" = "1" ]; then
        t_value=$("$bin" "$n" "$VALOR_MAXIMO" | grep -oP 'Tiempo.*: \K[0-9.]+')
    else
        t_value=$("$bin" "$n" "$VALOR_MAXIMO" "$t" | grep -oP 'Tiempo.*: \K[0-9.]+')
    fi
    echo "$n,$t,$run_id,$t_value" >> "$raw"
    echo "  [$(date +%H:%M:%S)] $label N=$n T=$t run=$run_id tiempo=$t_value" | tee -a "$LOG"
}

# Procesa un bloque de experimento (pthreads o fork)
#   $1 = raw, $2 = label, $3 = binario, $4-.. = array de T
run_block() {
    local raw=$1 label=$2 bin=$3
    shift 3
    local hilos=("$@")

    [ -f "$raw" ] || echo "N,threads,run,tiempo" > "$raw"

    for t in "${hilos[@]}"; do
        echo "" | tee -a "$LOG"
        echo "=== $label: $t hilo(s)/proceso(s) ===" | tee -a "$LOG"

        for run_id in $(seq 1 $RUNS); do
            for n in "${TAMANOS[@]}"; do
                if grep -qE "^${n},${t},${run_id},[0-9]" "$raw" 2>/dev/null; then
                    continue
                fi
                if grep -q "^${n},${t},${run_id}," "$raw" 2>/dev/null; then
                    sed -i "/^${n},${t},${run_id},/d" "$raw"
                    echo "  Corrida incompleta para N=$n T=$t run=$run_id, reintentando..." | tee -a "$LOG"
                fi

                measure "$raw" "$n" "$t" "$run_id" "$bin" "$label"

                sleep 1
            done
        done

        out="${raw%_raw.csv}.csv"
        python3 experiments/aggregate.py "$raw" "$out" 2>/dev/null || true
    done
}

# -------------------------------------------------------
# Ejecucion
# -------------------------------------------------------
echo "Inicio del experimento: $(date)" | tee -a "$LOG"

# Bloque 1: pthreads
run_block experiments/resultados_raw.csv "pthreads" ./bin/matriz_pthreads "${HILOS_PTHREADS[@]}"

# Bloque 2: fork
run_block experiments/resultados_fork_raw.csv "fork" ./bin/matriz_fork "${HILOS_FORK[@]}"

echo "" | tee -a "$LOG"
echo "Fin del experimento: $(date)" | tee -a "$LOG"

# Agregacion final de ambos bloques
python3 experiments/aggregate.py experiments/resultados_raw.csv experiments/resultados.csv
python3 experiments/aggregate.py experiments/resultados_fork_raw.csv experiments/resultados_fork.csv

# Graficas
python3 experiments/plot.py
