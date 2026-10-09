import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

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
    # Dos subplots: N=500/1000 (rapido) y N=2000/4000 (lento) con escala lineal
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x = np.arange(len(N_values) // 2)
    width = 0.11
    colors = plt.cm.tab10(np.linspace(0, 1, len(versiones)))

    # Subplot 1: N=500, 1000
    x_short = np.arange(2)
    for i, v in enumerate(versiones):
        offset = (i - len(versiones)/2) * width + width/2
        ax1.bar(x_short + offset, [tiempos[v][0], tiempos[v][1]], width, label=v, color=colors[i])
    ax1.set_xticks(x_short)
    ax1.set_xticklabels([f'N={N_values[0]}', f'N={N_values[1]}'])
    ax1.set_ylabel('Tiempo (s)')
    ax1.set_title('Lab 1: N=500 y N=1000')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, axis='y', alpha=0.3)

    # Anotar valores encima de las barras mas altas
    for i, v in enumerate(versiones):
        for j, val in enumerate([tiempos[v][0], tiempos[v][1]]):
            offset = (i - len(versiones)/2) * width + width/2
            if val > 0.1:
                ax1.text(j + offset, val, f'{val:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)

    # Subplot 2: N=2000, 4000
    x_long = np.arange(2)
    for i, v in enumerate(versiones):
        offset = (i - len(versiones)/2) * width + width/2
        ax2.bar(x_long + offset, [tiempos[v][2], tiempos[v][3]], width, label=v, color=colors[i])
    ax2.set_xticks(x_long)
    ax2.set_xticklabels([f'N={N_values[2]}', f'N={N_values[3]}'])
    ax2.set_ylabel('Tiempo (s)')
    ax2.set_title('Lab 1: N=2000 y N=4000')
    ax2.legend(loc='upper left', fontsize=8)
    ax2.grid(True, axis='y', alpha=0.3)

    for i, v in enumerate(versiones):
        for j, val in enumerate([tiempos[v][2], tiempos[v][3]]):
            offset = (i - len(versiones)/2) * width + width/2
            ax2.text(j + offset, val, f'{val:.1f}', ha='center', va='bottom', fontsize=6, rotation=90)

    plt.suptitle('Lab 1: Optimizacion por compilacion con GCC')
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
    # Dos subplots: N=500/1000 y N=2000/4000 con escala lineal
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    x_short = np.arange(2)
    width = 0.35
    ax1.bar(x_short - width/2, [t_normal[0], t_normal[1]], width, label='Normal (B por columna)', color='C0')
    ax1.bar(x_short + width/2, [t_trans[0], t_trans[1]], width, label='Transpuesto (B por fila)', color='C1')
    ax1.set_xticks(x_short)
    ax1.set_xticklabels([f'N={N_values[0]}', f'N={N_values[1]}'])
    ax1.set_ylabel('Tiempo (s)')
    ax1.set_title('Lab 2: N=500 y N=1000')
    ax1.legend()
    ax1.grid(True, axis='y', alpha=0.3)
    for i, val in enumerate([t_normal[0], t_normal[1]]):
        ax1.text(i - width/2, val, f'{val:.3f}', ha='center', va='bottom', fontsize=8, rotation=90)
    for i, val in enumerate([t_trans[0], t_trans[1]]):
        ax1.text(i + width/2, val, f'{val:.3f}', ha='center', va='bottom', fontsize=8, rotation=90)

    x_long = np.arange(2)
    ax2.bar(x_long - width/2, [t_normal[2], t_normal[3]], width, label='Normal (B por columna)', color='C0')
    ax2.bar(x_long + width/2, [t_trans[2], t_trans[3]], width, label='Transpuesto (B por fila)', color='C1')
    ax2.set_xticks(x_long)
    ax2.set_xticklabels([f'N={N_values[2]}', f'N={N_values[3]}'])
    ax2.set_ylabel('Tiempo (s)')
    ax2.set_title('Lab 2: N=2000 y N=4000')
    ax2.legend()
    ax2.grid(True, axis='y', alpha=0.3)
    for i, val in enumerate([t_normal[2], t_normal[3]]):
        ax2.text(i - width/2, val, f'{val:.2f}', ha='center', va='bottom', fontsize=8, rotation=90)
    for i, val in enumerate([t_trans[2], t_trans[3]]):
        ax2.text(i + width/2, val, f'{val:.2f}', ha='center', va='bottom', fontsize=8, rotation=90)

    plt.suptitle('Lab 2: Optimizacion de memoria (cache line)')
    plt.tight_layout()
    plt.savefig(f'{BASE}/lab2_tiempos.png', dpi=120)
    plt.close()
    print(f"  Guardado: {BASE}/lab2_tiempos.png")
else:
    print(f"  No se encontraron datos para Lab 2 (encontrados: {len(t_normal)} de {len(N_values)})")
