"""
plot_benchmark_montecarlo.py - Consolida los resultados del benchmark de
Monte Carlo ejecutado en una o varias maquinas.

Entrada (una por maquina):
  experiments/resultados/benchmark_reto2/<etiqueta>_raw.csv
  experiments/resultados/benchmark_reto2/<etiqueta>_hardware.txt

Salida:
  experiments/resultados/benchmark_reto2/resumen_maquinas.csv
  experiments/resultados/benchmark_reto2/comparativa_hardware.csv
  experiments/resultados/benchmark_reto2/benchmark_maquinas.png

Uso:
  python3 experiments/plot_benchmark_montecarlo.py
  python3 experiments/plot_benchmark_montecarlo.py --maquina MaquinaA
"""
import csv
import glob
import os
import re
import statistics
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = 'experiments/resultados/benchmark_reto2'
COLOR_MAQUINA = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']
ETIQUETA = {'dartboard': 'Dartboard', 'buffon': 'Buffon'}


def leer_raw(ruta):
    """-> {(algoritmo, N, T): [tiempos]}"""
    datos = {}
    if not os.path.exists(ruta):
        return datos
    with open(ruta) as f:
        for row in csv.DictReader(f):
            clave = (row['algoritmo'], int(row['N']), int(row['T']))
            datos.setdefault(clave, []).append(float(row['tiempo']))
    return datos


def leer_hardware(ruta):
    info = {}
    if not os.path.exists(ruta):
        return info
    with open(ruta, errors='replace') as f:
        for linea in f:
            if ':' in linea:
                k, _, v = linea.partition(':')
                info[k.strip()] = v.strip()
    return info


def info_maquina(etiqueta):
    datos = leer_raw(f'{BASE}/{etiqueta}_raw.csv')
    if not datos:
        return None
    hw = leer_hardware(f'{BASE}/{etiqueta}_hardware.txt')
    ns = sorted({n for (_, n, _) in datos})
    ts = sorted({t for (_, _, t) in datos})
    return {
        'etiqueta': etiqueta,
        'datos': datos,
        'hw': hw,
        'ns': ns,
        'ts': ts,
        'cpu': hw.get('Model name', '?'),
        'n_cores': hw.get('Nucleos logicos detectados', hw.get('CPU(s)', '?')),
        'distro': hw.get('Distribucion', '?'),
        'compiler': hw.get('Compiler', '?'),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maquina')
    args = ap.parse_args()

    etiquetas = sorted(
        os.path.basename(p)[:-len('_raw.csv')]
        for p in glob.glob(f'{BASE}/*_raw.csv')
    )
    if args.maquina:
        etiquetas = [args.maquina]

    maquinas = []
    for et in etiquetas:
        m = info_maquina(et)
        if m:
            maquinas.append(m)
        else:
            print(f"  AVISO: no hay datos para '{et}'")

    if not maquinas:
        print(f"ERROR: no hay datos en {BASE}. Ejecuta bench_montecarlo.sh primero.")
        return

    print(f"  Maquinas con datos: {[m['etiqueta'] for m in maquinas]}")

    # --- Tabla consolidada ---
    header = ['N', 'algoritmo', 'maquina', 'T_optimo', 'tiempo_min_(s)',
              'tiempo_mediana_(s)', 'ns_por_segundo']
    filas = [header]
    for m in maquinas:
        for algoritmo in ['dartboard', 'buffon']:
            for n in m['ns']:
                por_t = {}
                for (algo, nn, t), tiempos in m['datos'].items():
                    if algo == algoritmo and nn == n:
                        por_t[t] = tiempos
                if not por_t:
                    continue
                t_opt = min(por_t, key=lambda t: min(por_t[t]))
                filas.append([
                    n, algoritmo, m['etiqueta'], t_opt,
                    f'{min(por_t[t_opt]):.6f}',
                    f'{statistics.median(por_t[t_opt]):.6f}',
                    f'{n / min(por_t[t_opt]):.3e}',
                ])

    with open(f'{BASE}/resumen_maquinas.csv', 'w', newline='') as f:
        csv.writer(f).writerows(filas)
    print(f"  -> {BASE}/resumen_maquinas.csv")

    # --- Tabla de hardware ---
    with open(f'{BASE}/comparativa_hardware.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['caracteristica'] + [m['etiqueta'] for m in maquinas])
        for etiqueta_legible, clave in [
                ('Hostname', 'Hostname'), ('CPU', 'Model name'),
                ('Nucleos logicos', 'Nucleos logicos detectados'),
                ('Distribucion', 'Distribucion'), ('Compilador', 'Compiler'),
                ('Flags de compilacion', 'Flags de compil.')]:
            w.writerow([etiqueta_legible] + [m['hw'].get(clave, '?') for m in maquinas])
    print(f"  -> {BASE}/comparativa_hardware.csv")

    # --- Grafica: tiempo y speedup por maquina ---
    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    for idx, algoritmo in enumerate(['dartboard', 'buffon']):
        # Fila superior: tiempo absoluto
        ax = axes[0][idx]
        for i, m in enumerate(maquinas):
            xs, ys = [], []
            for n in m['ns']:
                clave = [(algo, n, t) for (a, nn, t) in m['datos'] if a == algo and nn == n]
                if not clave:
                    continue
                mejor = min(min(m['datos'][k]) for k in clave)
                xs.append(n)
                ys.append(mejor)
            if xs:
                ax.plot(xs, ys, 'o-', label=f"{m['etiqueta']}: {m['cpu'][:26]}",
                        linewidth=2, color=COLOR_MAQUINA[i % len(COLOR_MAQUINA)],
                        markersize=8)
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.set_xlabel('Numero de muestras (N)')
        ax.set_ylabel('Tiempo minimo (s)')
        ax.set_title(f'{ETIQUETA[algoritmo]} - tiempo por maquina')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

        # Fila inferior: speedup frente a la version serial de la misma maquina
        ax = axes[1][idx]
        for i, m in enumerate(maquinas):
            ts = sorted({t for (a, _, t) in m['datos'] if a == algoritmo})
            xs, ys = [], []
            for t in ts:
                base = m['datos'].get((algoritmo, m['ns'][0], 1))
                if not base:
                    continue
                for n in m['ns']:
                    clave = [(algoritmo, n, tt) for (a, nn, tt) in m['datos']
                             if a == algoritmo and nn == n and tt == t]
                    if clave:
                        b = min(m['datos'][(algoritmo, n, 1)])
                        v = min(min(m['datos'][k]) for k in clave)
                        xs.append(t)
                        ys.append(b / v)
                        break
            if xs:
                ax.plot(xs, ys, 'o-', label=f"{m['etiqueta']}",
                        linewidth=2, color=COLOR_MAQUINA[i % len(COLOR_MAQUINA)],
                        markersize=8)
        ax.axhline(1.0, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        ax.set_xlabel('Cantidad de hilos (T)')
        ax.set_ylabel('Speedup')
        ax.set_title(f'{ETIQUETA[algoritmo]} - escalamiento por maquina')
        ax.set_xticks(sorted({t for m in maquinas for (_, _, t) in m['datos']}))
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    plt.suptitle('Benchmark de los algoritmos de Monte Carlo entre maquinas',
                 fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(f'{BASE}/benchmark_maquinas.png', dpi=120, bbox_inches='tight')
    plt.close()
    print(f"  -> {BASE}/benchmark_maquinas.png")

    print("Listo.")


if __name__ == '__main__':
    main()
