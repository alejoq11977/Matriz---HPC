"""
plot_perfilado.py - Consolida los resultados del perfilado (GProf + Cachegrind + RSS)
de una o varias maquinas y genera las tablas y graficas.

Estructura de entrada (una carpeta por maquina):
  experiments/resultados/perfilado/<maquina>/cachegrind_*.txt   (salida de cachegrind)
  experiments/resultados/perfilado/<maquina>/rss.csv
  experiments/resultados/perfilado/<maquina>/gprof_*.txt
  experiments/resultados/perfilado/<maquina>/hardware.txt

Salidas (en experiments/resultados/perfilado/):
  resumen_perfilado.csv         tabla consolidada de todas las maquinas
  cache_miss_rate.png            variantes del kernel dentro de cada maquina
  cache_miss_rate_maquinas.png   comparacion del miss rate entre maquinas
  footprint_memoria.png          footprint de memoria por variante

Nota importante: Cachegrind simula la jerarquia de cache REAL del equipo donde
corre (la lee del CPUID), por lo que las tasas de fallo son especificas de cada
maquina. Por eso el perfilado se guarda separado por maquina.
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
    'I_refs':       r'I\s+refs:\s+([\d,]+)',
    'D_refs':       r'D\s+refs:\s+([\d,]+)',
    'D_refs_rd':    r'D\s+refs:.*?\(\s*([\d,]+)\s+rd',
    'D_refs_wr':    r'D\s+refs:.*?\+.*?([\d,]+)\s+wr',
    'D1_misses':    r'D1\s+misses:\s+([\d,]+)',
    'D1_misses_rd': r'D1\s+misses:.*?\(\s*([\d,]+)\s+rd',
    'D1_misses_wr': r'D1\s+misses:.*?\+.*?([\d,]+)\s+wr',
    'D1_rate':      r'D1\s+miss rate:\s+([\d.]+)%',
    'D1_rate_rd':   r'D1\s+miss rate:.*?\(\s*([\d.]+)%',
    'D1_rate_wr':   r'D1\s+miss rate:.*?%\s*\(.*?\+.*?([\d.]+)%',
    'LLd_misses':   r'LLd\s+misses:\s+([\d,]+)',
    'LLd_rate':     r'LLd\s+miss rate:\s+([\d.]+)%',
}

ORDEN_VARIANTES = ['secuencial', 'transpuesto', 'openmp']
ETIQUETAS_OPENMP = ['T1', 'T8', 'T16']
COLORES = {'secuencial': 'C0', 'transpuesto': 'C2', 'openmp': 'C4'}
COLOR_MAQUINA = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']


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


def leer_rss(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta) as f:
        return list(csv.DictReader(f))


def leer_gprof(ruta):
    """Extrae las funciones mas costosas del flat profile de gprof.

    Advertencia: con OpenMP, gprof solo instrumenta el hilo principal, asi
    que el tiempo de la region paralela se atribuye mal.
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
    """Devuelve (nombre, pct) de la funcion con mas tiempo propio."""
    if not gprof:
        return '', ''
    candidatas = [g for g in gprof if g['self_s'] > 0]
    if not candidatas:
        return '', ''
    top = max(candidatas, key=lambda x: x['self_s'])
    return top['funcion'], f"{top['pct']:.2f}"


def leer_hardware(ruta):
    """Extrae el CPU y la jerarquia de cache del equipo."""
    info = {}
    if not os.path.exists(ruta):
        return info
    with open(ruta, errors='replace') as f:
        for linea in f:
            if ':' in linea:
                k, _, v = linea.partition(':')
                info[k.strip()] = v.strip()
    return info


def listar_maquinas():
    """Devuelve las carpetas que parecen ser maquinas (tienen datos)."""
    if not os.path.isdir(BASE):
        return []
    found = []
    for nombre in sorted(os.listdir(BASE)):
        ruta = os.path.join(BASE, nombre)
        if os.path.isdir(ruta) and any(
                f.startswith('cachegrind_') and f.endswith('.txt')
                for f in os.listdir(ruta)):
            found.append(nombre)
    return found


# --- Recolectar datos de todas las maquinas ---
maquinas = listar_maquinas()
if not maquinas:
    print(f"ERROR: no hay datos de perfilado en {BASE}/<maquina>/")
    print("       Ejecuta experiments/perfilar.sh <maquina> primero.")
    raise SystemExit(1)

print(f"  Maquinas con datos: {maquinas}")

datos_por_maquina = {}
for maq in maquinas:
    carpeta = f'{BASE}/{maq}'
    variantes = []
    for archivo in sorted(os.listdir(carpeta)):
        if archivo.startswith('cachegrind_') and archivo.endswith('.txt'):
            partes = archivo[len('cachegrind_'):-len('.txt')].split('_')
            if len(partes) >= 2:
                variante = '_'.join(partes[:-1])
                etiqueta = partes[-1]
                d = parse_cachegrind(f'{carpeta}/{archivo}')
                if d:
                    variantes.append({'variante': variante, 'etiqueta': etiqueta, **d})
    datos_por_maquina[maq] = {
        'variantes': variantes,
        'rss': leer_rss(f'{carpeta}/rss.csv'),
        'hw': leer_hardware(f'{carpeta}/hardware.txt'),
    }


def buscar(maq, variante, etiqueta, clave):
    """Devuelve el valor de una metrica, o None."""
    for v in datos_por_maquina[maq]['variantes']:
        if v['variante'] == variante and v['etiqueta'] == etiqueta:
            return v.get(clave)
    return None


# --- Tabla consolidada ---
header = ['maquina', 'variante', 'threads', 'I_refs', 'D_refs', 'D1_misses',
          'D1_miss_rate_pct', 'D1_rate_read_pct', 'D1_rate_write_pct',
          'LLd_misses', 'LLd_miss_rate_pct', 'max_rss_kb', 'max_rss_mb',
          'funcion_mas_costera', 'pct_tiempo_gprof']
filas = [header]

for maq in maquinas:
    rss_por = {}
    for r in datos_por_maquina[maq]['rss']:
        rss_por[(r['variante'], r['threads'])] = (r['max_rss_kb'], r['max_rss_mb'])

    for v in datos_por_maquina[maq]['variantes']:
        threads = v['etiqueta'].replace('T', '')
        gprof = leer_gprof(f'{BASE}/{maq}/gprof_{v["variante"]}.txt')
        func, pct = funcion_mas_costera(gprof)
        if v['variante'] == 'openmp':
            func = f'{func} (no representativo con OpenMP)'
        kb, mb = rss_por.get((v['variante'], threads), ('', ''))
        filas.append([
            maq, v['variante'], threads,
            v.get('I_refs', ''), v.get('D_refs', ''),
            v.get('D1_misses', ''), v.get('D1_rate', ''),
            v.get('D1_rate_rd', ''), v.get('D1_rate_wr', ''),
            v.get('LLd_misses', ''), v.get('LLd_rate', ''),
            kb, mb, func, pct,
        ])

with open(f'{BASE}/resumen_perfilado.csv', 'w', newline='') as f:
    csv.writer(f).writerows(filas)
print(f"  -> {BASE}/resumen_perfilado.csv")


# --- Grafica 1: variantes del kernel (dentro de cada maquina) ---
def etiquetas_de_variantes(maq):
    """Devuelve [(variante, etiqueta)] en un orden estable."""
    out = []
    for variante in ORDEN_VARIANTES:
        for etiqueta in ETIQUETAS_OPENMP:
            if buscar(maq, variante, etiqueta, 'D1_rate_rd') is not None:
                out.append((variante, etiqueta))
    return out


n_maquinas = len(maquinas)
fig, axes = plt.subplots(n_maquinas, 2, figsize=(12, 4.2 * n_maquinas), squeeze=False)

for i, maq in enumerate(maquinas):
    pares = etiquetas_de_variantes(maq)
    nombres = [f'{v}\nT={t[1:]}' for v, t in pares]

    # Panel izquierdo: tasa de fallo de lectura
    ax = axes[i][0]
    valores = [buscar(maq, v, t, 'D1_rate_rd') for v, t in pares]
    colores = [COLORES[v] for v, _ in pares]
    barras = ax.bar(range(len(pares)), valores, color=colores,
                    edgecolor='black', linewidth=0.6)
    ax.set_xticks(range(len(pares)))
    ax.set_xticklabels(nombres, fontsize=8)
    ax.set_ylabel('D1 miss rate en lecturas (%)')
    ax.set_title(f'Tasa de fallo de cache L1 - {maq}')
    ax.grid(True, axis='y', alpha=0.3)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.1f}%',
                ha='center', va='bottom', fontsize=8)

    # Panel derecho: fallos absolutos
    ax = axes[i][1]
    valores = [(buscar(maq, v, t, 'D1_misses_rd') or 0) / 1e6 for v, t in pares]
    barras = ax.bar(range(len(pares)), valores, color=colores,
                    edgecolor='black', linewidth=0.6)
    ax.set_xticks(range(len(pares)))
    ax.set_xticklabels(nombres, fontsize=8)
    ax.set_ylabel('D1 misses en lecturas (millones)')
    ax.set_title(f'Fallos de cache L1 - {maq}')
    ax.grid(True, axis='y', alpha=0.3)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.1f}M',
                ha='center', va='bottom', fontsize=8)

plt.tight_layout()
plt.savefig(f'{BASE}/cache_miss_rate.png', dpi=120)
plt.close()
print(f"  -> {BASE}/cache_miss_rate.png")


# --- Grafica 2: comparacion del miss rate entre maquinas ---
# Compara secuencial vs transpuesto en cada maquina: muestra cuanto le afecta
# a cada hardware el patron de acceso a memoria.
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

variantes_interes = ['secuencial', 'transpuesto']
ancho = 0.35
ETIQUETA_Y = {
    'D1_rate_rd': 'Tasa de fallo L1 en lecturas (%)',
    'D1_misses_rd': 'Fallos de cache L1 en lecturas (millones)',
}

for panel, (clave, titulo, unidad) in enumerate([
        ('D1_rate_rd', 'Tasa de fallo de cache L1 (lecturas)', '%'),
        ('D1_misses_rd', 'Fallos de cache L1 (lecturas)', 'M')]):
    ax = axes[panel]
    for i, maq in enumerate(maquinas):
        for j, variante in enumerate(variantes_interes):
            valor = buscar(maq, variante, 'T1', clave)
            if valor is None:
                continue
            if clave == 'D1_misses_rd':
                valor = valor / 1e6
            x = i + (j - 0.5) * ancho
            barra = ax.bar(x, valor, ancho, label=f'{maq} - {variante}',
                           color=COLORES[variante], edgecolor='black', linewidth=0.6,
                           alpha=0.85 if j == 0 else 0.55)
            ax.text(barra[0].get_x() + barra[0].get_width() / 2, valor,
                    f'{valor:.1f}{unidad}', ha='center', va='bottom', fontsize=8)
    ax.set_xticks(range(len(maquinas)))
    ax.set_xticklabels(maquinas, fontsize=9)
    ax.set_ylabel(ETIQUETA_Y[clave])
    ax.set_title(titulo)
    ax.grid(True, axis='y', alpha=0.3)

axes[0].legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=2)
plt.tight_layout()
plt.savefig(f'{BASE}/cache_miss_rate_maquinas.png', dpi=120, bbox_inches='tight')
plt.close()
print(f"  -> {BASE}/cache_miss_rate_maquinas.png")


# --- Grafica 3: footprint de memoria ---
filas_rss = []
for maq in maquinas:
    for r in datos_por_maquina[maq]['rss']:
        filas_rss.append((maq, r))

if filas_rss:
    fig, ax = plt.subplots(figsize=(9, 5))
    nombres = [f"{maq}\n{r['variante']}\nT={r['threads']}" for maq, r in filas_rss]
    valores = [float(r['max_rss_mb']) for _, r in filas_rss]
    colores = [COLORES.get(r['variante'], 'C0') for _, r in filas_rss]
    barras = ax.bar(range(len(nombres)), valores, color=colores,
                    edgecolor='black', linewidth=0.6)
    ax.set_xticks(range(len(nombres)))
    ax.set_xticklabels(nombres, fontsize=7)
    ax.set_ylabel('Memoria maxima residente (MB)')
    ax.set_title('Footprint de memoria (max RSS)')
    ax.grid(True, axis='y', alpha=0.3)
    for b, v in zip(barras, valores):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.1f}',
                ha='center', va='bottom', fontsize=7)
    plt.tight_layout()
    plt.savefig(f'{BASE}/footprint_memoria.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/footprint_memoria.png")

print("Listo.")
