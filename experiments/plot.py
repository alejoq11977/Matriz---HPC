import csv
import math
from collections import defaultdict
import matplotlib.pyplot as plt

INFILE = 'experiments/resultados.csv'

filas = []
with open(INFILE) as f:
    for row in csv.DictReader(f):
        filas.append({
            'N': int(row['N']),
            'threads': int(row['threads']),
            'media': float(row['media']),
            'mediana': float(row['mediana']),
            'stddev': float(row['stddev']),
            'n': int(row['n']),
        })

# Indexar por (N, threads)
by = {(r['N'], r['threads']): r for r in filas}

# Speedup calculado sobre la MEDIANA (robusto a outliers).
# Propagacion de incertidumbre usa la stddev de los datos crudos.
# Formula: S = T_seq / T_par, sigma_S = S * sqrt((sigma_seq/T_seq)^2 + (sigma_par/T_par)^2)
speedup = defaultdict(dict)
for r in filas:
    n, t = r['N'], r['threads']
    if t == 1:
        continue
    seq = by.get((n, 1))
    par = by.get((n, t))
    if seq is None or par is None:
        continue
    s = seq['mediana'] / par['mediana']
    sigma_s = s * math.sqrt((seq['stddev'] / seq['media']) ** 2 +
                            (par['stddev'] / par['media']) ** 2)
    speedup[n][t] = (s, sigma_s)

# ---------------------------------------------------------------
# Grafica 1: Speedup vs N, una curva por T
# ---------------------------------------------------------------
plt.figure(figsize=(10, 6))
for t in [2, 4, 8, 16]:
    pares = sorted((n, speedup[n][t]) for n in speedup if t in speedup[n])
    xs = [n for n, _ in pares]
    ys = [v[0] for _, v in pares]
    es = [v[1] for _, v in pares]
    plt.errorbar(xs, ys, yerr=es, marker='o', capsize=4, label=f'{t} hilos')
plt.xlabel('Tamano N')
plt.ylabel('Speedup (mediana T_sec / mediana T_par)')
plt.title('Speedup vs N para distintas cantidades de hilos (calculado sobre la mediana)')
plt.legend()
plt.grid(True)
plt.savefig('experiments/speedup_vs_N.png', dpi=150)
plt.close()
print('Grafica guardada en experiments/speedup_vs_N.png')

# ---------------------------------------------------------------
# Grafica 2: Speedup vs T, una curva por N
# ---------------------------------------------------------------
plt.figure(figsize=(10, 6))
for n in sorted(speedup):
    pares = sorted(speedup[n].items())
    xs = [t for t, _ in pares]
    ys = [v[0] for _, v in pares]
    es = [v[1] for _, v in pares]
    plt.errorbar(xs, ys, yerr=es, marker='o', capsize=4, label=f'N = {n}')
plt.xlabel('Cantidad de hilos')
plt.ylabel('Speedup (mediana T_sec / mediana T_par)')
plt.title('Speedup vs cantidad de hilos para distintos tamanos de matriz (sobre la mediana)')
plt.legend()
plt.grid(True)
plt.savefig('experiments/speedup_vs_T.png', dpi=150)
plt.close()
print('Grafica guardada en experiments/speedup_vs_T.png')

# Mantener compat: speedup.png apunta a la primera variante
import shutil
shutil.copyfile('experiments/speedup_vs_N.png', 'experiments/speedup.png')
