#!/bin/bash
set -e

OUT=experiments/resultados.csv
echo "N,threads,tiempo" > $OUT

for N in 500 1000 2000 4000; do
    echo "=== N=$N secuencial ==="
    T=$(./bin/matriz_monotonic $N 10 | grep -oP 'Tiempo.*: \K[0-9.]+')
    echo "$N,1,$T" >> $OUT

    for THREADS in 2 4 8 16; do
        echo "=== N=$N, $THREADS hilos ==="
        T=$(./bin/matriz_pthreads $N 10 $THREADS | grep -oP 'Tiempo.*: \K[0-9.]+')
        echo "$N,$THREADS,$T" >> $OUT
    done
done

echo ""
echo "Resultados en $OUT"
cat $OUT
