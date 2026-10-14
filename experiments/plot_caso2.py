"""
plot_caso2.py - Genera la tabla comparativa y la grafica del Caso de Estudio 2.

Lee los datos crudos (10 corridas) de:
  - med_mm_full_raw.csv         (Lab 1: optimizacion de compilacion)
  - med_matriz_monotonic_t_raw.csv (Lab 2: optimizacion de memoria)
  - resultados_raw.csv de origin/pthreads (para pthreads y secuencial T=1)
  - resultados_fork_raw.csv de origin/fork (para fork)

Calcula mediana por N y velocidad de speedup contra la misma base
que uso el caso de estudio 1 (T=1 secuencial, mediana de 10 corridas con
semilla 42).

Genera:
  - caso_de_estudio_2.csv: tabla con todos los speedups
  - caso_de_estudio_2.png: grafica de 4 curvas (escala lineal)
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

def mediana_por_n(datos, ns_deseados):
    """Para cada N, devuelve la mediana de los tiempos sobre todas las corridas."""
    res = {}
    for n in ns_deseados:
        vals = [t for (nn, _), t in datos.items() if nn == n]
        if vals:
            res[n] = statistics.median(vals)
    return res

# --- 1) Obtener los CSVs de las ramas pthreads y fork via git show ---
print("[1/5] Leyendo CSVs de las ramas pthreads y fork...")

def get_csv_from_branch(branch, path):
    res = subprocess.run(
        ['git', 'show', f'{branch}:{path}'],
        capture_output=True, text=True, cwd='/home/Alejandro/U/HPC/mult_matriz'
    )
    if res.returncode != 0:
        return ""
    return res.stdout

# pthreads: resultados_raw.csv con T=1..16
pt_csv = get_csv_from_branch('origin/pthreads', 'experiments/resultados_raw.csv')
# fork: resultados_fork_raw.csv con T=2..16
fk_csv = get_csv_from_branch('origin/fork', 'experiments/resultados_fork_raw.csv')

# Guardar localmente para procesarlos
with open(f'{BASE}/_pt_raw.csv', 'w') as f:
    f.write(pt_csv)
with open(f'{BASE}/_fk_raw.csv', 'w') as f:
    f.write(fk_csv)

datos_pt = leer_csv(f'{BASE}/_pt_raw.csv')
datos_fk = leer_csv(f'{BASE}/_fk_raw.csv')

# --- 2) Leer los nuevos datos de optimizacion ---
print("[2/5] Leyendo CSVs de optimizacion...")
datos_full = leer_csv(f'{BASE}/med_mm_full_raw.csv')
datos_mem = leer_csv(f'{BASE}/med_matriz_monotonic_t_raw.csv')

if not datos_full or not datos_mem:
    print("ERROR: faltan CSVs de optimizacion. Ejecuta primero medir_optimizaciones.sh")
    raise SystemExit(1)

# --- 3) Calcular medianas por N para cada version ---
print("[3/5] Calculando medianas...")
NS = [500, 1000, 2000, 4000]

# pthreads y fork: para cada N, encontrar la T con la mediana minima
def mejor_mediana_por_n(datos, ns):
    res = {}
    for n in ns:
        ts = [t for (nn, _), t in datos.items() if nn == n]
        if not ts:
            continue
        # Todos los ts vienen de 10 corridas; los agrupamos por T
        # y encontramos el T con menor mediana
        # Pero los CSVs no tienen T, solo (N, run) y tiempo
        # En realidad necesitamos saber la T, asi que el CSV de pthreads
        # incluye T como segunda columna.
        pass
    return res

# Re-leer con la T incluida
def leer_csv_con_t(ruta):
    datos = {}
    if not os.path.exists(ruta):
        return datos
    with open(ruta) as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row['N'])
                t = int(row.get('threads', row.get('T', row.get('T', 0))))
                run = int(row.get('run', 1))
                tm = float(row['tiempo'])
                datos[(n, t, run)] = tm
            except (ValueError, KeyError):
                continue
    return datos

datos_pt = leer_csv_con_t(f'{BASE}/_pt_raw.csv')
datos_fk = leer_csv_con_t(f'{BASE}/_fk_raw.csv')

# Volver a calcular con T incluida
def mejor_mediana_con_t(datos, ns):
    res = {}
    for n in ns:
        ts_por_T = {}
        for (nn, t, _run), tm in datos.items():
            if nn != n:
                continue
            ts_por_T.setdefault(t, []).append(tm)
        for t, lst in ts_por_T.items():
            if lst:
                pass
        if not ts_por_T:
            continue
        # Mediana por cada T
        medianas_t = {t: statistics.median(vs) for t, vs in ts_por_T.items() if vs}
        if not medianas_t:
            continue
        mejor_t = min(medianas_t, key=medianas_t.get)
        res[n] = (mejor_t, medianas_t[mejor_t])
    return res

# pthreads: T=1 es el secuencial; T=2..16 son las optimizadas
# Para el secuencial del caso 2 (base), uso la mediana de T=1 de pthreads
secuencial = {}
for n in NS:
    vals_t1 = [tm for (nn, t, _r), tm in datos_pt.items() if nn == n and t == 1]
    if vals_t1:
        secuencial[n] = statistics.median(vals_t1)

# Para cada version, calcular la mejor T (con menor mediana) por N
pthreads_best = mejor_mediana_con_t(datos_pt, NS)
fork_best = mejor_mediana_con_t(datos_fk, NS)

# Optimizaciones: no hay T, solo N -> 10 corridas por N
full_med = mediana_por_n(datos_full, NS)
mem_med = mediana_por_n(datos_mem, NS)

# --- 4) Calcular speedups contra la base (mismo T=1 que pthreads) ---
print("[4/5] Calculando speedups...")

filas = ['N,T_seq(s),T_pth_best(s),T_fork_best(s),T_full(s),T_mem(s),speedup_pth,speedup_fork,speedup_full,speedup_mem']
for n in NS:
    ts = secuencial.get(n)
    pth = pthreads_best.get(n)
    fk = fork_best.get(n)
    fu = full_med.get(n)
    me = mem_med.get(n)
    if not ts:
        continue
    row = [str(n)]
    row.append(f'{ts:.4f}')  # T_seq
    row.append(f'{pth[1]:.4f}' if pth else 'N/A')  # T_pthreads
    row.append(f'{fk[1]:.4f}' if fk else 'N/A')      # T_fork
    row.append(f'{fu:.4f}' if fu else 'N/A')          # T_full
    row.append(f'{me:.4f}' if me else 'N/A')          # T_memoria
    # Speedups
    row.append(f'{ts/pth[1]:.2f}' if pth else 'N/A')
    row.append(f'{ts/fk[1]:.2f}' if fk else 'N/A')
    row.append(f'{ts/fu:.2f}' if fu else 'N/A')
    row.append(f'{ts/me:.2f}' if me else 'N/A')
    filas.append(','.join(row))

# Escribir CSV
csv_path = f'{BASE}/caso_de_estudio_2.csv'
with open(csv_path, 'w') as f:
    f.write('\n'.join(filas))
print(f"  -> {csv_path}")

# --- 5) Generar grafica ---
print("[5/5] Generando grafica...")

fig, ax = plt.subplots(figsize=(10, 6))

# Extraer datos para la grafica
ns_plot = []
su_pth = []
su_fork = []
su_full = []
su_mem = []

for row in filas[1:]:  # saltar header
    parts = row.split(',')
    n = int(parts[0])
    ns_plot.append(n)
    # El header es: N,T_seq,T_pth,T_fork,T_full,T_mem,speedup_pth,speedup_fork,speedup_full,speedup_mem
    # indices:       0  1     2      3      4      5     6            7            8            9
    su_pth.append(float(parts[6]))
    su_fork.append(float(parts[7]))
    su_full.append(float(parts[8]))
    su_mem.append(float(parts[9]))

ax.plot(ns_plot, su_pth, 'o-', label='Pthreads (mejor T)', linewidth=2)
ax.plot(ns_plot, su_fork, 's-', label='Fork (mejor T)', linewidth=2)
ax.plot(ns_plot, su_full, '^-', label='Optimizacion compilacion (mm_full)', linewidth=2)
ax.plot(ns_plot, su_mem, 'd-', label='Optimizacion memoria (transpuesto)', linewidth=2)

ax.set_xlabel('Tamano de matriz N')
ax.set_ylabel('Speedup (vs secuencial con -O0, semilla 42)')
ax.set_title('Caso de estudio 2: comparacion de las 4 estrategias de optimizacion')
ax.legend(loc='upper left')
ax.grid(True, alpha=0.3)
ax.set_xticks(ns_plot)
ax.set_xticklabels([f'N={n}' for n in ns_plot])

plt.tight_layout()
png_path = f'{BASE}/caso_de_estudio_2.png'
plt.savefig(png_path, dpi=120)
plt.close()
print(f"  -> {png_path}")

# Limpiar temporales
os.remove(f'{BASE}/_pt_raw.csv')
os.remove(f'{BASE}/_fk_raw.csv')

print("\nListo.")
print(f"  Tabla: {csv_path}")
print(f"  Grafica: {png_path}")
