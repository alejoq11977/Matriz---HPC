"""
plot_caso2_openmp.py - Genera la tabla comparativa y la grafica del Caso de
Estudio 2, anadiendo OpenMP como 5ta estrategia.

Lee los datos crudos (10 corridas) de:
  - med_mm_full_raw.csv            (Lab 1: optimizacion de compilacion)
  - med_matriz_monotonic_t_raw.csv (Lab 2: optimizacion de memoria)
  - med_openmp_raw.csv             (Lab 3: paralelizacion con OpenMP)
  - resultados_raw.csv de origin/pthreads (para pthreads y secuencial T=1)
  - resultados_fork_raw.csv de origin/fork (para fork)

Calcula mediana por N y velocidad de speedup contra la misma base
que uso el caso de estudio 1 (T=1 secuencial, mediana de 10 corridas
con semilla 42).

Genera:
  - caso_de_estudio_2_openmp.csv: tabla con todos los speedups (5 estrategias)
  - caso_de_estudio_2_openmp.png: grafica de 5 curvas (escala lineal)
"""
import csv
import statistics
import os
import subprocess
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE = 'experiments/resultados'
ROOT = '/home/Alejandro/U/HPC/mult_matriz'

def leer_csv(ruta):
    """Lee un CSV con header N,run,tiempo. Devuelve dict {(N, run): tiempo}."""
    datos = {}
    if not os.path.exists(ruta):
        return datos
    with open(ruta) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row['N'])
                run = int(row.get('run', 1))
                t = float(row['tiempo'])
                datos[(n, run)] = t
            except (ValueError, KeyError):
                continue
    return datos

def leer_csv_con_t(ruta):
    """Lee CSV con header N,T (o threads),run,tiempo. Devuelve {(N, T, run): tiempo}."""
    datos = {}
    if not os.path.exists(ruta):
        return datos
    with open(ruta) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row['N'])
                t = int(row.get('threads', row.get('T', 0)))
                run = int(row.get('run', 1))
                tm = float(row['tiempo'])
                datos[(n, t, run)] = tm
            except (ValueError, KeyError):
                continue
    return datos

def mediana_por_n(datos, ns_deseados):
    res = {}
    for n in ns_deseados:
        vals = [t for (nn, _), t in datos.items() if nn == n]
        if vals:
            res[n] = statistics.median(vals)
    return res

def mejor_mediana_con_t(datos, ns):
    res = {}
    for n in ns:
        ts_por_T = {}
        for (nn, t, _run), tm in datos.items():
            if nn != n:
                continue
            ts_por_T.setdefault(t, []).append(tm)
        if not ts_por_T:
            continue
        medianas_t = {t: statistics.median(vs) for t, vs in ts_por_T.items() if vs}
        if not medianas_t:
            continue
        mejor_t = min(medianas_t, key=medianas_t.get)
        res[n] = (mejor_t, medianas_t[mejor_t])
    return res

# --- 1) Obtener CSVs de pthreads y fork via git show ---
print("[1/5] Leyendo CSVs de las ramas pthreads y fork...")

def get_csv_from_branch(branch, path):
    res = subprocess.run(
        ['git', 'show', f'{branch}:{path}'],
        capture_output=True, text=True, cwd=ROOT
    )
    if res.returncode != 0:
        return ""
    return res.stdout

pt_csv = get_csv_from_branch('origin/pthreads', 'experiments/resultados_raw.csv')
fk_csv = get_csv_from_branch('origin/fork', 'experiments/resultados_fork_raw.csv')

with open(f'{BASE}/_pt_raw.csv', 'w') as f:
    f.write(pt_csv)
with open(f'{BASE}/_fk_raw.csv', 'w') as f:
    f.write(fk_csv)

# --- 2) Leer todos los CSVs de optimizacion y OpenMP ---
print("[2/5] Leyendo CSVs de optimizacion y OpenMP...")
datos_full = leer_csv(f'{BASE}/med_mm_full_raw.csv')
datos_mem = leer_csv(f'{BASE}/med_matriz_monotonic_t_raw.csv')
datos_openmp = leer_csv(f'{BASE}/med_openmp_raw.csv')

if not datos_openmp:
    print("ERROR: falta el CSV de OpenMP. Ejecuta primero medir_openmp.sh")
    raise SystemExit(1)

# --- 3) Calcular medianas ---
print("[3/5] Calculando medianas...")
NS = [500, 1000, 2000, 4000]
datos_pt = leer_csv_con_t(f'{BASE}/_pt_raw.csv')
datos_fk = leer_csv_con_t(f'{BASE}/_fk_raw.csv')

secuencial = {}
for n in NS:
    vals_t1 = [tm for (nn, t, _r), tm in datos_pt.items() if nn == n and t == 1]
    if vals_t1:
        secuencial[n] = statistics.median(vals_t1)

pthreads_best = mejor_mediana_con_t(datos_pt, NS)
fork_best = mejor_mediana_con_t(datos_fk, NS)
full_med = mediana_por_n(datos_full, NS)
mem_med = mediana_por_n(datos_mem, NS)
openmp_med = mediana_por_n(datos_openmp, NS)

# --- 4) Calcular speedups contra la base ---
print("[4/5] Calculando speedups...")

header = 'N,T_seq(s),T_pth_best(s),T_fork_best(s),T_full(s),T_mem(s),T_openmp(s),speedup_pth,speedup_fork,speedup_full,speedup_mem,speedup_openmp'
filas = [header]
for n in NS:
    ts = secuencial.get(n)
    pth = pthreads_best.get(n)
    fk = fork_best.get(n)
    fu = full_med.get(n)
    me = mem_med.get(n)
    om = openmp_med.get(n)
    if not ts:
        continue
    row = [str(n)]
    row.append(f'{ts:.4f}')  # T_seq
    row.append(f'{pth[1]:.4f}' if pth else 'N/A')
    row.append(f'{fk[1]:.4f}' if fk else 'N/A')
    row.append(f'{fu:.4f}' if fu else 'N/A')
    row.append(f'{me:.4f}' if me else 'N/A')
    row.append(f'{om:.4f}' if om else 'N/A')
    row.append(f'{ts/pth[1]:.2f}' if pth else 'N/A')
    row.append(f'{ts/fk[1]:.2f}' if fk else 'N/A')
    row.append(f'{ts/fu:.2f}' if fu else 'N/A')
    row.append(f'{ts/me:.2f}' if me else 'N/A')
    row.append(f'{ts/om:.2f}' if om else 'N/A')
    filas.append(','.join(row))

csv_path = f'{BASE}/caso_de_estudio_2_openmp.csv'
with open(csv_path, 'w') as f:
    f.write('\n'.join(filas))
print(f"  -> {csv_path}")

# --- 5) Generar grafica ---
print("[5/5] Generando grafica...")

fig, ax = plt.subplots(figsize=(11, 6))

ns_plot = []
su_pth = []
su_fork = []
su_full = []
su_mem = []
su_openmp = []

for row in filas[1:]:
    parts = row.split(',')
    n = int(parts[0])
    ns_plot.append(n)
    su_pth.append(float(parts[6]))
    su_fork.append(float(parts[7]))
    su_full.append(float(parts[8]))
    su_mem.append(float(parts[9]))
    su_openmp.append(float(parts[10]))

ax.plot(ns_plot, su_pth, 'o-', label='Pthreads (mejor T)', linewidth=2, color='C0')
ax.plot(ns_plot, su_fork, 's-', label='Fork (mejor T)', linewidth=2, color='C1')
ax.plot(ns_plot, su_full, '^-', label='Optimizacion compilacion (mm_full)', linewidth=2, color='C2')
ax.plot(ns_plot, su_mem, 'd-', label='Optimizacion memoria (transpuesto)', linewidth=2, color='C3')
ax.plot(ns_plot, su_openmp, '*-', label='OpenMP (-fopenmp -O0)', linewidth=2, color='C4', markersize=12)

ax.set_xlabel('Tamano de matriz N')
ax.set_ylabel('Speedup (vs secuencial con -O0, semilla 42)')
ax.set_title('Caso de estudio 2: comparacion de las 5 estrategias de paralelizacion y optimizacion')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_xticks(ns_plot)
ax.set_xticklabels([f'N={n}' for n in ns_plot])

plt.tight_layout()
png_path = f'{BASE}/caso_de_estudio_2_openmp.png'
plt.savefig(png_path, dpi=120)
plt.close()
print(f"  -> {png_path}")

# Limpiar temporales
os.remove(f'{BASE}/_pt_raw.csv')
os.remove(f'{BASE}/_fk_raw.csv')

print("\nListo.")
print(f"  Tabla: {csv_path}")
print(f"  Grafica: {png_path}")
