import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import sys

BASE = 'experiments/resultados'
N_values = [500, 1000, 2000, 4000]

# ====== Lab 1 ======
print("Generando grafica Lab 1...")
versiones = ['O0', 'O1', 'O2', 'O3', 'full', 'sin_interchange', 'sin_nest']

tiempos = {v: [] for v in versiones}
with open(f'{BASE}/lab1_tabla.txt') as f:
    for line in f:
        for v in versiones:
            if line.startswith(f'mm_{v}'):
                parts = line.split()
                for i, n in enumerate(N_values):
                    val = parts[2 + i]
                    try:
                        tiempos[v].append(float(val))
                    except ValueError:
                        tiempos[v].append(np.nan)

if all(len(tiempos[v]) == len(N_values) for v in versiones):
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(N_values))
    width = 0.11
    colors = plt.cm.tab10(np.linspace(0, 1, len(versiones)))
    for i, v in enumerate(versiones):
        offset = (i - len(versiones)/2) * width + width/2
        ax.bar(x + offset, tiempos[v], width, label=v, color=colors[i])
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels([f'N={n}' for n in N_values])
    ax.set_ylabel('Tiempo (s, escala log)')
    ax.set_title('Lab 1: Optimizacion por compilacion con GCC')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE}/lab1_tiempos.png', dpi=120)
    plt.close()
    print(f"  Guardado: {BASE}/lab1_tiempos.png")
else:
    print("  No se encontraron datos para Lab 1")

# ====== Lab 2 ======
print("Generando grafica Lab 2...")
t_normal = []
t_trans = []
with open(f'{BASE}/lab2_tabla.txt') as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 3:
            try:
                n = int(parts[0])
                if n in N_values:
                    t_normal.append(float(parts[1]))
                    t_trans.append(float(parts[2]))
            except ValueError:
                pass

if len(t_normal) == len(N_values):
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(N_values))
    width = 0.35
    ax.bar(x - width/2, t_normal, width, label='Normal (B por columna)', color='C0')
    ax.bar(x + width/2, t_trans, width, label='Transpuesto (B por fila)', color='C1')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels([f'N={n}' for n in N_values])
    ax.set_ylabel('Tiempo (s, escala log)')
    ax.set_title('Lab 2: Optimizacion de memoria (cache line)')
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{BASE}/lab2_tiempos.png', dpi=120)
    plt.close()
    print(f"  Guardado: {BASE}/lab2_tiempos.png")
else:
    print(f"  No se encontraron datos para Lab 2 (encontrados: {len(t_normal)} de {len(N_values)})")
