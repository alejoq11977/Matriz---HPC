#!/bin/bash
set -e

# ============================================================
# Experimento de speedup para multiplicacion de matrices con pthreads
# ============================================================
# - 5 tamanos: 500, 1000, 2000, 4000, 8000
# - 5 configuraciones: 1 (secuencial), 2, 4, 8, 16 hilos
# - 10 corridas por configuracion
# - Loop order: outer = repeticiones, inner = tamanos
#   (segun indicacion del profesor para evitar cache poisoning)
# - Resumible: si ya existe la corrida (N, T, run) en el CSV, la salta
# - sleep 1 entre corridas para que time(NULL) cambie la semilla
# ============================================================

VALOR_MAXIMO=10
TAMANOS=(500 1000 2000 4000 8000)
HILOS=(1 2 4 8 16)
RUNS=10

RAW=experiments/resultados_raw.csv
LOG=experiments/run.log

mkdir -p experiments
[ -f "$RAW" ] || echo "N,threads,run,tiempo" > "$RAW"

# Verifica que los binarios existan
if [ ! -x bin/matriz_monotonic ] || [ ! -x bin/matriz_pthreads ]; then
    echo "Error: binarios no encontrados. Ejecuta 'make' primero." >&2
    exit 1
fi

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

# Cuenta cuantas corridas hay registradas para (N, T)
count_runs() {
    local n=$1 t=$2
    awk -F, -v n="$n" -v t="$t" '$1==n && $2==t {c++} END {print c+0}' "$RAW" 2>/dev/null
}

# Borra corridas parciales de (N, T) (para rehacer si quedaron incompletas)
truncar_parcial() {
    local n=$1 t=$2
    local tmp
    tmp=$(mktemp)
    awk -F, -v n="$n" -v t="$t" '!(($1==n) && ($2==t))' "$RAW" > "$tmp"
    mv "$tmp" "$RAW"
}

# Corre una medicion individual y la appendea al CSV
#   $1 = N, $2 = threads, $3 = run_id
measure() {
    local n=$1 t=$2 run_id=$3
    local t_value
    local bin
    if [ "$t" = "1" ]; then
        bin="./bin/matriz_monotonic"
    else
        bin="./bin/matriz_pthreads"
    fi
    t_value=$("$bin" "$n" "$VALOR_MAXIMO" "$t" | grep -oP 'Tiempo.*: \K[0-9.]+')
    echo "$n,$t,$run_id,$t_value" >> "$RAW"
    echo "  [$(date +%H:%M:%S)] N=$n hilos=$t run=$run_id tiempo=$t_value" | tee -a "$LOG"
}

# -------------------------------------------------------
# Ejecucion
# -------------------------------------------------------
echo "Inicio del experimento: $(date)" | tee -a "$LOG"

for t in "${HILOS[@]}"; do
    echo "" | tee -a "$LOG"
    echo "=== Configuracion: $t hilo(s) ===" | tee -a "$LOG"

    # Si hay corridas parciales (interrupcion previa), las borramos y rehacemos
    actuales=$(count_runs "$t" "$t" 2>/dev/null || echo 0)
    actuales=$(count_runs 500 "$t")
    if [ "$actuales" -gt 0 ] && [ "$actuales" -lt "$RUNS" ]; then
        echo "  Detectadas $actuales corridas parciales para hilos=$t, truncando..." | tee -a "$LOG"
        truncar_parcial 500 "$t"
    fi

    for run_id in $(seq 1 $RUNS); do
        # Outer loop = repeticiones, inner loop = tamanos
        for n in "${TAMANOS[@]}"; do
            actuales=$(count_runs "$n" "$t")
            if [ "$actuales" -ge "$RUNS" ]; then
                continue  # ya estan las 10 corridas de este (N, T)
            fi
            if [ "$actuales" -gt 0 ]; then
                # corridas parciales -> rehacer desde 1
                echo "  Detectadas $actuales corridas parciales para N=$n hilos=$t, truncando..." | tee -a "$LOG"
                truncar_parcial "$n" "$t"
            fi

            measure "$n" "$t" "$run_id"

            # Garantizar semilla distinta entre corridas
            sleep 1
        done
    done

    # Agregacion parcial al final de cada T (no espera a terminar todo)
    python3 experiments/aggregate.py 2>/dev/null || true
done

echo "" | tee -a "$LOG"
echo "Fin del experimento: $(date)" | tee -a "$LOG"

# Agregacion final
python3 experiments/aggregate.py
