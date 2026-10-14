#!/bin/bash
# medir_optimizaciones.sh
# Mide 10 corridas por binario, variando N en cada iteracion.
# Argumentos: N1 N2 N3 N4 iters binario1 binario2 ...
#   Ejemplo: ./medir_optimizaciones.sh 500 1000 2000 4000 10 mm_full matriz_monotonic_t

set -e

if [ $# -lt 6 ]; then
    echo "Uso: $0 N1 N2 N3 N4 iters bin1 bin2 ..."
    exit 1
fi

TAMS=("$1" "$2" "$3" "$4")
ITERS=$5
shift 5
BINS=("$@")

mkdir -p experiments/resultados

# Un solo bin a la vez, en orden inverso al pasado (mm_full primero, matriz_monotonic_t despues)
# Para cada bin: 10 iteraciones. En cada iter, recorrer los 4 N en orden directo.
for BIN in "${BINS[@]}"; do
    NOMBRE=$(basename "$BIN")
    # Quitar extension si la tiene
    NOMBRE="${NOMBRE%.c}"
    SALIDA="experiments/resultados/med_${NOMBRE}_raw.csv"
    echo "N,run,tiempo" > "$SALIDA"
    echo "[midiendo $BIN -> $SALIDA]"

    for iter in $(seq 1 "$ITERS"); do
        for N in "${TAMS[@]}"; do
            t=$(./bin/"$BIN" "$N" 9 42 2>/dev/null | grep -oP 'Tiempo medido con CLOCK_MONOTONIC_RAW: \K[0-9.]+')
            echo "$N,$iter,$t" >> "$SALIDA"
        done
    done
    echo "  OK: $(wc -l < "$SALIDA") lineas en $SALIDA"
done
