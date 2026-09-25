import csv
import matplotlib.pyplot as plt
from collections import defaultdict

filas = []
with open('experiments/resultados.csv') as f:
    for row in csv.DictReader(f):
        filas.append({'N': int(row['N']), 'threads': int(row['threads']), 'tiempo': float(row['tiempo'])})

sec = {r['N']: r['tiempo'] for r in filas if r['threads'] == 1}
for r in filas:
    r['speedup'] = sec[r['N']] / r['tiempo']

por_hilos = defaultdict(list)
for r in filas:
    por_hilos[r['threads']].append((r['N'], r['speedup']))

plt.figure(figsize=(10, 6))
for t in [2, 4, 8, 16]:
    pares = sorted(por_hilos[t])
    xs = [n for n, _ in pares]
    ys = [s for _, s in pares]
    plt.plot(xs, ys, marker='o', label=f'{t} hilos')

plt.xlabel('Tamano N')
plt.ylabel('Speedup (T_sec / T_par)')
plt.title('Speedup vs N para distintas cantidades de hilos')
plt.legend()
plt.grid(True)
plt.savefig('experiments/speedup.png', dpi=150)
print('Grafica guardada en experiments/speedup.png')
