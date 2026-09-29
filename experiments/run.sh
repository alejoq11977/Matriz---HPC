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
    if [ "$t" = "1" ]; then
        t_value=$(./bin/matriz_monotonic "$n" "$VALOR_MAXIMO" | grep -oP 'Tiempo.*: \K[0-9.]+')
    else
        t_value=$(./bin/matriz_pthreads "$n" "$VALOR_MAXIMO" "$t" | grep -oP 'Tiempo.*: \K[0-9.]+')
    fi
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

    for run_id in $(seq 1 $RUNS); do
        # Outer loop = repeticiones, inner loop = tamanos
        for n in "${TAMANOS[@]}"; do
            # Verificar si esta corrida especifica (n, t, run_id) ya existe y tiene tiempo valido
            if grep -qE "^${n},${t},${run_id},[0-9]" "$RAW" 2>/dev/null; then
                continue  # ya esta completa, saltar
            fi
            # Si existe la corrida pero sin tiempo valido (interrumpida), la borramos
            if grep -q "^${n},${t},${run_id}," "$RAW" 2>/dev/null; then
                sed -i "/^${n},${t},${run_id},/d" "$RAW"
                echo "  Corrida incompleta detectada para N=$n hilos=$t run=$run_id, reintentando..." | tee -a "$LOG"
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
