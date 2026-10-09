import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

N_values = [500, 1000, 2000, 4000]
t_original = [0.047673629, 0.433506697, 4.804940850, 75.454912576]
t_full = [0.045156532, 0.433056126, 5.651678736, 70.065128896]
t_memoria = [0.036592883, 0.287701164, 2.668904515, 21.283509469]

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(N_values))
width = 0.27

bars1 = ax.bar(x - width, t_original, width, label='Original (gcc -O2)', color='C0')
bars2 = ax.bar(x, t_full, width, label='Full (-O3 -march=native -floop-interchange -funroll-loops -floop-nest-optimize)', color='C1')
bars3 = ax.bar(x + width, t_memoria, width, label='Memoria (-O2 + kernel transpuesto)', color='C2')

ax.set_yscale('log')
ax.set_xticks(x)
ax.set_xticklabels([f'N={n}' for n in N_values])
ax.set_ylabel('Tiempo (s) - escala log')
ax.set_title('Comparacion: Original vs Full vs Memoria')
ax.legend(loc='upper left', fontsize=8)
ax.grid(True, axis='y', alpha=0.3, which='both')

for bars, vals in [(bars1, t_original), (bars2, t_full), (bars3, t_memoria)]:
    for bar, val in zip(bars, vals):
        if val >= 1:
            label = f'{val:.1f}'
        else:
            label = f'{val:.3f}'
        ax.text(bar.get_x() + bar.get_width()/2, val, label,
                ha='center', va='bottom', fontsize=8, rotation=90)

plt.tight_layout()
plt.savefig('experiments/resultados/comparacion_grafica.png', dpi=120)
plt.close()
print("Guardado: experiments/resultados/comparacion_grafica.png")
