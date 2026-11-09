"""
plot_montecarlo.py - Genera las graficas de resultados del Reto 2.

Lee:
  experiments/resultados/montecarlo_raw.csv          (barrido de desempeno)
  experiments/resultados/montecarlo_convergencia.csv (curva de convergencia)
  experiments/resultados/montecarlo_validacion.csv   (test de efectividad)

Genera:
  speedup_montecarlo.png    speedup frente al numero de hilos
  escalamiento_algoritmos.png  speedup por algoritmo en el mejor N
  convergencia_pi.png        estimacion de pi en funcion de N
  error_montecarlo.png       error frente a 1/sqrt(N)
  costo_por_muestra.png      costo por muestra de cada algoritmo
"""
import csv
import os
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = 'experiments/resultados'
RAW = f'{BASE}/montecarlo_raw.csv'
CONV = f'{BASE}/montecarlo_convergencia.csv'
VALID = f'{BASE}/montecarlo_validacion.csv'

ALGORITMOS = ['dartboard', 'buffon']
ETIQUETA = {'dartboard': 'Dartboard (dardos)', 'buffon': 'Buffon (agujas)'}
COLOR = {'dartboard': 'C0', 'buffon': 'C1'}
VARIANTES = ['serial', 'omp_reduccion', 'omp_privado', 'omp_alias']
COLOR_VAR = {
    'serial': 'C3',
    'omp_reduccion': 'C0',
    'omp_privado': 'C2',
    'omp_alias': 'C4',
}


def leer_raw():
    """-> {(algoritmo, variante, N, T): [tiempos]} y metadatos de la corrida."""
    datos = {}
    if not os.path.exists(RAW):
        return datos
    with open(RAW) as f:
        for row in csv.DictReader(f):
            clave = (row['algoritmo'], row['variante'], int(row['N']), int(row['T']))
            datos.setdefault(clave, []).append(float(row['tiempo']))
    return datos


def leer_convergencia():
    datos = {}
    if not os.path.exists(CONV):
        return datos
    with open(CONV) as f:
        for row in csv.DictReader(f):
            clave = row['algoritmo']
            datos.setdefault(clave, []).append({
                'N': int(row['N']),
                'pi_est': float(row['pi_est']),
                'error': float(row['error']),
                'sigma': float(row['sigma_teorica']),
            })
    return datos


def mejor_por_n(datos, algoritmo, variante):
    """Para cada N devuelve (mejor T, mediana del tiempo en ese T)."""
    por_n = {}
    for (algo, var, n, t), tiempos in datos.items():
        if algo != algoritmo or var != variante:
            continue
        por_n.setdefault(n, {})[t] = statistics.median(tiempos)
    salida = {}
    for n, por_t in por_n.items():
        bt = min(por_t, key=por_t.get)
        salida[n] = (bt, por_t[bt])
    return salida


def tiempo_minimo(datos, algoritmo, variante, n, t):
    clave = (algoritmo, variante, n, t)
    if clave in datos:
        return min(datos[clave])
    return None


datos = leer_raw()
if not datos:
    raise SystemExit(f"ERROR: no hay datos en {RAW}. Ejecuta experiments/medir_montecarlo.sh primero.")

ns_disponibles = sorted({n for (_, _, n, _) in datos})
ns_convergencia = [n for n in ns_disponibles if n >= 10_000_000]

print(f"  Algoritmos: {sorted({a for (a, _, _, _) in datos})}")
print(f"  N disponibles: {ns_disponibles}")


# ---------------------------------------------------------------------------
# 1) Speedup frente al numero de hilos
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

for idx, algoritmo in enumerate(ALGORITMOS):
    if algoritmo not in {a for (a, _, _, _) in datos}:
        continue
    ax = axes[idx]
    n_ref = max(ns_convergencia) if ns_convergencia else max(ns_disponibles)

    for variante in VARIANTES:
        if variante == 'serial':
            continue
        xs, ys = [], []
        for t in sorted({tt for (a, v, n, tt) in datos if a == algoritmo and v == variante}):
            tm = tiempo_minimo(datos, algoritmo, variante, n_ref, t)
            base = tiempo_minimo(datos, algoritmo, 'serial', n_ref, 1)
            if tm and base:
                xs.append(t)
                ys.append(base / tm)
        if xs:
            ax.plot(xs, ys, 'o-', label=variante, linewidth=2,
                    color=COLOR_VAR[variante], markersize=8)

    ax.plot([1], [1.0], 'k*', markersize=14, label='serial (referencia)')
    ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel('Cantidad de hilos (T)')
    ax.set_ylabel('Speedup')
    ax.set_title(f'{ETIQUETA[algoritmo]}  (N={n_ref:,})')
    ax.set_xticks(sorted({tt for (a, v, n, tt) in datos if a == algoritmo}))
    ax.set_ylim(0, max(2.0, ax.get_ylim()[1]))
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc='upper left')

plt.suptitle('Speedup de OpenMP en los algoritmos de Monte Carlo para pi',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(f'{BASE}/speedup_montecarlo.png', dpi=120, bbox_inches='tight')
plt.close()
print(f"  -> {BASE}/speedup_montecarlo.png")


# ---------------------------------------------------------------------------
# 2) Speedup por variante: efecto del aliasing y del contador privado
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5.5))
n_ref = max(ns_convergencia) if ns_convergencia else max(ns_disponibles)
ancho = 0.2

variantes_graf = ['omp_reduccion', 'omp_privado', 'omp_alias']
algoritmos_presentes = sorted({a for (a, _, _, _) in datos})
for j, variante in enumerate(variantes_graf):
    for i, algoritmo in enumerate(algoritmos_presentes):
        base = tiempo_minimo(datos, algoritmo, 'serial', n_ref, 1)
        tm = tiempo_minimo(datos, algoritmo, variante, n_ref, 8)
        if not (base and tm):
            continue
        sp = base / tm
        x = i * (len(variantes_graf) + 1) + j * ancho
        barra = ax.bar(x, sp, ancho, label=variante if i == 0 else None,
                       color=COLOR_VAR[variante], edgecolor='black', linewidth=0.6)
        ax.text(barra[0].get_x() + barra[0].get_width() / 2, barra[0].get_height(),
                f'{sp:.2f}x', ha='center', va='bottom', fontsize=9)

ax.set_xticks([i * (len(variantes_graf) + 1) + ancho for i in range(len(algoritmos_presentes))])
ax.set_xticklabels([ETIQUETA[a].split(' (')[0] for a in algoritmos_presentes])
ax.set_ylabel('Speedup con T=8')
ax.set_title('Efecto de las opciones de paralelizacion (T=8)')
ax.grid(True, axis='y', alpha=0.3)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(f'{BASE}/escalamiento_algoritmos.png', dpi=120)
plt.close()
print(f"  -> {BASE}/escalamiento_algoritmos.png")


# ---------------------------------------------------------------------------
# 3) Convergencia de pi_hat hacia el valor real
# ---------------------------------------------------------------------------
conv = leer_convergencia()
if conv:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    PI = 3.141592653589793

    ax = axes[0]
    for algoritmo in ALGORITMOS:
        if algoritmo not in conv:
            continue
        puntos = sorted(conv[algoritmo], key=lambda d: d['N'])
        ax.plot([d['N'] for d in puntos], [d['pi_est'] for d in puntos],
                'o-', label=ETIQUETA[algoritmo], linewidth=2,
                color=COLOR[algoritmo], markersize=7)
    ax.axhline(PI, color='black', linestyle='--', linewidth=1.2, label='pi exacto')
    ax.set_xscale('log')
    ax.set_xlabel('Numero de muestras (N)')
    ax.set_ylabel('Estimacion de pi')
    ax.set_title('Convergencia de la estimacion de pi')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    ax = axes[1]
    for algoritmo in ALGORITMOS:
        if algoritmo not in conv:
            continue
        puntos = sorted(conv[algoritmo], key=lambda d: d['N'])
        ax.plot([d['N'] for d in puntos], [abs(d['error']) for d in puntos],
                'o-', label=ETIQUETA[algoritmo], linewidth=2,
                color=COLOR[algoritmo], markersize=7)
        # Banda teorica +-2 sigma
        ax.plot([d['N'] for d in puntos], [2 * d['sigma'] for d in puntos],
                '--', linewidth=1, alpha=0.6, color=COLOR[algoritmo])
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Numero de muestras (N)')
    ax.set_ylabel('Error absoluto |pi_hat - pi|')
    ax.set_title('Error real frente a la banda teorica +-2 sigma')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    plt.suptitle('Convergencia y error de los algoritmos de Monte Carlo',
                 fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(f'{BASE}/convergencia_pi.png', dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {BASE}/convergencia_pi.png")


# ---------------------------------------------------------------------------
# 4) Error frente a 1/sqrt(N): la ley de los grandes numeros
# ---------------------------------------------------------------------------
if conv:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for algoritmo in ALGORITMOS:
        if algoritmo not in conv:
            continue
        puntos = sorted(conv[algoritmo], key=lambda d: d['N'])
        ax.plot([1 / (d['N'] ** 0.5) for d in puntos],
                [abs(d['error']) for d in puntos],
                'o', label=ETIQUETA[algoritmo], color=COLOR[algoritmo], markersize=8)
    ax.plot([1e-3, 1e-1], [1e-3, 1e-1], 'k--', linewidth=1.2,
            label='pendiente 1/sqrt(N)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('1 / sqrt(N)')
    ax.set_ylabel('Error absoluto |pi_hat - pi|')
    ax.set_title('El error decae como 1/sqrt(N)')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(f'{BASE}/error_montecarlo.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/error_montecarlo.png")


# ---------------------------------------------------------------------------
# 5) Costo por muestra de cada algoritmo
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5.5))
for algoritmo in ALGORITMOS:
    if algoritmo not in {a for (a, _, _, _) in datos}:
        continue
    n_ref = max(ns_convergencia) if ns_convergencia else max(ns_disponibles)
    base = tiempo_minimo(datos, algoritmo, 'serial', n_ref, 1)
    if not base:
        continue
    ns_muestra = base / n_ref * 1e9
    ax.bar(algoritmo, ns_muestra, 0.5,
           color=COLOR[algoritmo], edgecolor='black', linewidth=0.6)
    ax.text(algoritmo, ns_muestra, f'{ns_muestra:.2f} ns', ha='center',
            va='bottom', fontsize=10)
ax.set_ylabel('Costo por muestra (ns)')
ax.set_title('Costo por muestra de cada algoritmo (version serial)')
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(f'{BASE}/costo_por_muestra.png', dpi=120)
plt.close()
print(f"  -> {BASE}/costo_por_muestra.png")

print("Listo.")
