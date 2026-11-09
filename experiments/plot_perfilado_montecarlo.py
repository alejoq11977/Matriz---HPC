"""
plot_perfilado_montecarlo.py - Consolida los resultados del perfilado de los
algoritmos de Monte Carlo (GProf + Cachegrind + max RSS).

Entrada:
  experiments/resultados/perfilado_reto2/gprof_<algoritmo>.txt
  experiments/resultados/perfilado_reto2/cachegrind_<algoritmo>.txt
  experiments/resultados/perfilado_reto2/rss.csv

Salida:
  experiments/resultados/perfilado_reto2/resumen_perfilado.csv
  experiments/resultados/perfilado_reto2/cache_miss_rate.png
"""
import csv
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = 'experiments/resultados/perfilado_reto2'
ALGORITMOS = ['dartboard', 'buffon']
COLOR = {'dartboard': 'C0', 'buffon': 'C1'}

PATRONES = {
    'I_refs':      r'I\s+refs:\s+([\d,]+)',
    'D_refs':      r'D\s+refs:\s+([\d,]+)',
    'D1_misses':   r'D1\s+misses:\s+([\d,]+)',
    'D1_rate':     r'D1\s+miss rate:\s+([\d.]+)%',
    'D1_rate_rd':  r'D1\s+miss rate:.*?\(\s*([\d.]+)%',
    'LLd_misses':  r'LLd\s+misses:\s+([\d,]+)',
    'LLd_rate':    r'LLd\s+miss rate:\s+([\d.]+)%',
}


def parse_cachegrind(ruta):
    if not os.path.exists(ruta):
        return {}
    with open(ruta, errors='replace') as f:
        texto = f.read()
    out = {}
    for clave, patron in PATRONES.items():
        mm = re.search(patron, texto)
        if mm:
            val = mm.group(1).replace(',', '')
            out[clave] = float(val) if '.' in val else int(val)
    return out


def leer_gprof(ruta):
    """-> lista de (funcion, pct_tiempo_propio, ms_por_llamada)"""
    if not os.path.exists(ruta):
        return []
    filas = []
    with open(ruta, errors='replace') as f:
        for linea in f:
            mm = re.match(
                r'\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\S+)',
                linea)
            if mm:
                filas.append({
                    'pct': float(mm.group(1)),
                    'self_s': float(mm.group(2)),
                    'calls': int(mm.group(4)),
                    'ms_call': float(mm.group(5)),
                    'funcion': mm.group(7),
                })
    return filas


def leer_rss():
    ruta = f'{BASE}/rss.csv'
    if not os.path.exists(ruta):
        return []
    with open(ruta) as f:
        return list(csv.DictReader(f))


# --- Recolectar ---
datos = {}
for algo in ALGORITMOS:
    cg = parse_cachegrind(f'{BASE}/cachegrind_{algo}.txt')
    gp = leer_gprof(f'{BASE}/gprof_{algo}.txt')
    datos[algo] = {'cachegrind': cg, 'gprof': gp}

rss = leer_rss()

# --- Tabla consolidada ---
header = ['algoritmo', 'I_refs', 'D_refs', 'D1_misses', 'D1_miss_rate_pct',
          'D1_rate_read_pct', 'LLd_misses', 'LLd_miss_rate_pct',
          'max_rss_kb', 'max_rss_mb', 'funcion_mas_costera', 'pct_tiempo_gprof']
filas = [header]

rss_por = {}
for r in rss:
    # se toma la variante serial: es la referencia de footprint
    if r.get('variante', 'serial') == 'serial':
        rss_por[r.get('algoritmo', '?')] = (r['max_rss_kb'], r['max_rss_mb'])

for algo in ALGORITMOS:
    cg = datos[algo]['cachegrind']
    gp = datos[algo]['gprof']
    top = max((g for g in gp if g['self_s'] > 0), key=lambda x: x['self_s'],
              default=None)
    func = top['funcion'] if top else ''
    pct = f"{top['pct']:.2f}" if top else ''
    kb, mb = rss_por.get(algo, ('', ''))
    filas.append([
        algo,
        cg.get('I_refs', ''), cg.get('D_refs', ''),
        cg.get('D1_misses', ''), cg.get('D1_rate', ''),
        cg.get('D1_rate_rd', ''),
        cg.get('LLd_misses', ''), cg.get('LLd_rate', ''),
        kb, mb, func, pct,
    ])

with open(f'{BASE}/resumen_perfilado.csv', 'w', newline='') as f:
    csv.writer(f).writerows(filas)
print(f"  -> {BASE}/resumen_perfilado.csv")

# --- Grafica: miss rate de cache ---
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

ax = axes[0]
nombres, valores, colores = [], [], []
for algo in ALGORITMOS:
    v = datos[algo]['cachegrind'].get('D1_rate_rd')
    if v is None:
        continue
    nombres.append(algo)
    valores.append(v)
    colores.append(COLOR[algo])
barras = ax.bar(range(len(nombres)), valores, color=colores,
                edgecolor='black', linewidth=0.6)
ax.set_xticks(range(len(nombres)))
ax.set_xticklabels(nombres, fontsize=10)
ax.set_ylabel('D1 miss rate en lecturas (%)')
ax.set_title('Tasa de fallo de cache L1 (matrices: 22.4%)')
ax.grid(True, axis='y', alpha=0.3)
for b, v in zip(barras, valores):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.2f}%',
            ha='center', va='bottom', fontsize=10)

ax = axes[1]
nombres, valores, colores = [], [], []
for algo in ALGORITMOS:
    v = datos[algo]['cachegrind'].get('D1_misses')
    if v is None:
        continue
    nombres.append(algo)
    valores.append(v)
    colores.append(COLOR[algo])
barras = ax.bar(range(len(nombres)), valores, color=colores,
                edgecolor='black', linewidth=0.6)
ax.set_xticks(range(len(nombres)))
ax.set_xticklabels(nombres, fontsize=10)
ax.set_ylabel('D1 misses en lecturas')
ax.set_title('Fallos absolutos de cache L1')
ax.grid(True, axis='y', alpha=0.3)
for b, v in zip(barras, valores):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:,}',
            ha='center', va='bottom', fontsize=10)

plt.suptitle('Perfilado de memoria de los algoritmos de Monte Carlo',
             fontsize=13, y=1.02)
plt.tight_layout()
plt.savefig(f'{BASE}/cache_miss_rate.png', dpi=120, bbox_inches='tight')
plt.close()
print(f"  -> {BASE}/cache_miss_rate.png")

print("Listo.")
