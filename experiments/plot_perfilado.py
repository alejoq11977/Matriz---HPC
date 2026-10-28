"""
plot_perfilado.py - Consolida los resultados del perfilado (GProf + Cachegrind + RSS)
en una tabla y genera las graficas de metricas de cache y memoria.

Entra:
  experiments/resultados/perfilado/cachegrind_*.txt   (salida de cachegrind)
  experiments/resultados/perfilado/rss.csv
  experiments/resultados/perfilado/gprof_*.txt

Sale:
  experiments/resultados/perfilado/resumen_perfilado.csv
  experiments/resultados/perfilado/cache_miss_rate.png
  experiments/resultados/perfilado/footprint_memoria.png
"""
import csv
import os
import re
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = 'experiments/resultados/perfilado'

# Cachegrind reporta estas lineas:
#   D   refs:      200,043,410  (100,031,614 rd   + 100,011,796 wr)
#   D1  misses:       58,050,484  ( 58,003,140 rd   +      47,344 wr)
#   D1  miss rate:          14.9% (       22.4%     +         0.0%  )
#   LLd misses:           48,332
#   LLd miss rate:           0.0%
#   I   refs:        1,600,138,736

PATRONES = {
    'I_refs':      r'I\s+refs:\s+([\d,]+)',
    'D_refs':      r'D\s+refs:\s+([\d,]+)',
    'D_refs_rd':   r'D\s+refs:.*?\(\s*([\d,]+)\s+rd',
    'D_refs_wr':   r'D\s+refs:.*?\+.*?([\d,]+)\s+wr',
    'D1_misses':   r'D1\s+misses:\s+([\d,]+)',
    'D1_misses_rd': r'D1\s+misses:.*?\(\s*([\d,]+)\s+rd',
    'D1_misses_wr': r'D1\s+misses:.*?\+.*?([\d,]+)\s+wr',
    'D1_rate':     r'D1\s+miss rate:\s+([\d.]+)%',
    'D1_rate_rd':  r'D1\s+miss rate:.*?\(\s*([\d.]+)%',
    'D1_rate_wr':  r'D1\s+miss rate:.*?%\s*\(.*?\+.*?([\d.]+)%',
    'LLd_misses':  r'LLd\s+misses:\s+([\d,]+)',
    'LLd_rate':    r'LLd\s+miss rate:\s+([\d.]+)%',
}


def parse_cachegrind(ruta):
    """Extrae las metricas de un archivo de salida de cachegrind."""
    if not os.path.exists(ruta):
        return None
    with open(ruta, errors='replace') as f:
        texto = f.read()
    m = {}
    for clave, patron in PATRONES.items():
        mm = re.search(patron, texto)
        if mm:
            val = mm.group(1).replace(',', '')
            m[clave] = float(val) if '.' in val else int(val)
    return m if m else None


def leer_rss():
    ruta = f'{BASE}/rss.csv'
    if not os.path.exists(ruta):
        return []
    with open(ruta) as f:
        return list(csv.DictReader(f))


def leer_gprof(ruta):
    """Extrae las funciones mas costosas del flat profile de gprof.

    Advertencia: con OpenMP, gprof solo instrumenta el hilo principal, asi
    que el tiempo de la region paralela se atribuye mal. Para las variantes
    con OpenMP el reporte no es representativo del reparto real de trabajo.
    """
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


def funcion_mas_costera(gprof):
    """Devuelve (nombre, pct) de la funcion con mas tiempo propio.

    Para OpenMP se descarta `reservar_matrices` porque gprof solo perfila el
    hilo principal y la atribucion del tiempo de la region paralela es
    enganosa (el tiempo del equipo de hilos se contabiliza en el hilo que
    la crea).
    """
    if not gprof:
        return '', ''
    candidatas = [g for g in gprof if g['self_s'] > 0]
    if not candidatas:
        return '', ''
    top = max(candidatas, key=lambda x: x['self_s'])
    return top['funcion'], f"{top['pct']:.2f}"


# --- Recolectar datos ---
variantes = []
for archivo in sorted(os.listdir(BASE)) if os.path.isdir(BASE) else []:
    if archivo.startswith('cachegrind_') and archivo.endswith('.txt'):
        partes = archivo[len('cachegrind_'):-len('.txt')].split('_')
        if len(partes) >= 2:
            variante = '_'.join(partes[:-1])
            etiqueta = partes[-1]
            datos = parse_cachegrind(f'{BASE}/{archivo}')
            if datos:
                variantes.append({'variante': variante, 'etiqueta': etiqueta, **datos})

rss = leer_rss()

# --- Tabla consolidada ---
header = ['variante', 'threads', 'I_refs', 'D_refs', 'D1_misses', 'D1_miss_rate_pct',
          'D1_rate_read_pct', 'D1_rate_write_pct', 'LLd_misses', 'LLd_miss_rate_pct',
          'max_rss_kb', 'max_rss_mb', 'funcion_mas_costera', 'pct_tiempo_gprof']
filas = [header]

rss_por = {}
for r in rss:
    rss_por[(r['variante'], r['threads'])] = (r['max_rss_kb'], r['max_rss_mb'])

for v in variantes:
    threads = v['etiqueta'].replace('T', '')
    gprof = leer_gprof(f'{BASE}/gprof_{v["variante"]}.txt')
    func, pct = funcion_mas_costera(gprof)
    if v['variante'] == 'openmp':
        # gprof no es representativo con OpenMP (solo perfila el hilo principal)
        func = f'{func} (no representativo con OpenMP)'
    kb, mb = rss_por.get((v['variante'], threads), ('', ''))
    filas.append([
        v['variante'], threads,
        v.get('I_refs', ''), v.get('D_refs', ''),
        v.get('D1_misses', ''), v.get('D1_rate', ''),
        v.get('D1_rate_rd', ''), v.get('D1_rate_wr', ''),
        v.get('LLd_misses', ''), v.get('LLd_rate', ''),
        kb, mb, func, pct,
    ])

with open(f'{BASE}/resumen_perfilado.csv', 'w', newline='') as f:
    csv.writer(f).writerows(filas)

print(f"  -> {BASE}/resumen_perfilado.csv")

# --- Grafica 1: D1 miss rate por variante ---
ORDEN = ['secuencial', 'transpuesto', 'openmp']
ETIQUETAS = {'secuencial': ['T1'], 'transpuesto': ['T1'], 'openmp': ['T1', 'T8', 'T16']}
COLORES = {'secuencial': 'C0', 'transpuesto': 'C2', 'openmp': 'C4'}

def _dato(variante, etiqueta, clave):
    for v in variantes:
        if v['variante'] == variante and v['etiqueta'] == etiqueta:
            return v.get(clave, 0)
    return None

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# Panel 1: D1 miss rate (lecturas)
ax = axes[0]
nombres, valores, colores = [], [], []
for variante in ORDEN:
    for etiqueta in ETIQUETAS[variante]:
        d = _dato(variante, etiqueta, 'D1_rate_rd')
        if d is None:
            continue
        nombres.append(f'{variante}\nT={etiqueta[1:]}')
        valores.append(d)
        colores.append(COLORES[variante])
barras = ax.bar(range(len(nombres)), valores, color=colores, edgecolor='black', linewidth=0.6)
ax.set_xticks(range(len(nombres)))
ax.set_xticklabels(nombres, fontsize=8)
ax.set_ylabel('D1 miss rate en lecturas (%)')
ax.set_title('Tasa de fallos de cache L1 (lecturas)')
ax.grid(True, axis='y', alpha=0.3)
for b, v in zip(barras, valores):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.1f}%',
            ha='center', va='bottom', fontsize=8)

# Panel 2: D1 misses absolutos
ax = axes[1]
nombres, valores, colores = [], [], []
for variante in ORDEN:
    for etiqueta in ETIQUETAS[variante]:
        d = _dato(variante, etiqueta, 'D1_misses_rd')
        if d is None:
            continue
        nombres.append(f'{variante}\nT={etiqueta[1:]}')
        valores.append(d / 1e6)
        colores.append(COLORES[variante])
barras = ax.bar(range(len(nombres)), valores, color=colores, edgecolor='black', linewidth=0.6)
ax.set_xticks(range(len(nombres)))
ax.set_xticklabels(nombres, fontsize=8)
ax.set_ylabel('D1 misses en lecturas (millones)')
ax.set_title('Fallos de cache L1 (lecturas)')
ax.grid(True, axis='y', alpha=0.3)
for b, v in zip(barras, valores):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.1f}M',
            ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(f'{BASE}/cache_miss_rate.png', dpi=120)
plt.close()
print(f"  -> {BASE}/cache_miss_rate.png")

# --- Grafica 2: footprint de memoria ---
if rss:
    fig, ax = plt.subplots(figsize=(8, 5))
    nombres = [f"{r['variante']}\nT={r['threads']}" for r in rss]
    valores = [float(r['max_rss_mb']) for r in rss]
    colores = [COLORES.get(r['variante'], 'C0') for r in rss]
    barras = ax.bar(range(len(nombres)), valores, color=colores, edgecolor='black', linewidth=0.6)
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, fontsize=9)
    ax.set_ylabel('Memoria maxima residente (MB)')
    ax.set_title('Footprint de memoria (max RSS)')
    ax.grid(True, axis='y', alpha=0.3)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.0f}',
                ha='center', va='bottom', fontsize=8)
    plt.tight_layout()
    plt.savefig(f'{BASE}/footprint_memoria.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/footprint_memoria.png")

print("Listo.")
