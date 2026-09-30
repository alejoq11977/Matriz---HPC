import csv
import math
import sys
from collections import defaultdict
import matplotlib.pyplot as plt

PTHREADS_CSV = 'experiments/resultados.csv'
FORK_CSV     = 'experiments/resultados_fork.csv'


def cargar(path):
    filas = []
    with open(path) as f:
        for row in csv.DictReader(f):
            filas.append({
                'N': int(row['N']),
                'threads': int(row['threads']),
                'media': float(row['media']),
                'mediana': float(row['mediana']),
                'stddev': float(row['stddev']),
                'n': int(row['n']),
            })
    return {(r['N'], r['threads']): r for r in filas}


def speedup_desde(by, n, t):
    seq = by.get((n, 1))
    par = by.get((n, t))
    if seq is None or par is None:
        return None
    s = seq['mediana'] / par['mediana']
    sigma_s = s * math.sqrt((seq['stddev'] / seq['media']) ** 2 +
                            (par['stddev'] / par['media']) ** 2)
    return (s, sigma_s)


def graficar_speedup_vs_N(by, metodo, path):
    plt.figure(figsize=(10, 6))
    for t in [2, 4, 8, 16]:
        pares = []
        for n in sorted({k[0] for k in by}):
            r = speedup_desde(by, n, t)
            if r is not None:
                pares.append((n, r))
        if not pares:
            continue
        xs = [n for n, _ in pares]
        ys = [v[0] for _, v in pares]
        es = [v[1] for _, v in pares]
        plt.errorbar(xs, ys, yerr=es, marker='o', capsize=4, label=f'{t} {metodo}')
    plt.xlabel('Tamano N')
    plt.ylabel('Speedup (mediana T_sec / mediana T_par)')
    plt.title(f'Speedup vs N ({metodo})')
    plt.legend()
    plt.grid(True)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f'Grafica guardada en {path}')


def graficar_speedup_vs_T(by, metodo, path):
    plt.figure(figsize=(10, 6))
    for n in sorted({k[0] for k in by}):
        pares = []
        for t in [2, 4, 8, 16]:
            r = speedup_desde(by, n, t)
            if r is not None:
                pares.append((t, r))
        if not pares:
            continue
        xs = [t for t, _ in pares]
        ys = [v[0] for _, v in pares]
        es = [v[1] for _, v in pares]
        plt.errorbar(xs, ys, yerr=es, marker='o', capsize=4, label=f'N = {n}')
    plt.xlabel('Cantidad de hilos / procesos')
    plt.ylabel('Speedup (mediana T_sec / mediana T_par)')
    plt.title(f'Speedup vs cantidad de hilos ({metodo})')
    plt.legend()
    plt.grid(True)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f'Grafica guardada en {path}')


def graficar_comparativa(by_pt, by_fk, path):
    plt.figure(figsize=(10, 6))
    for t in [2, 4, 8, 16]:
        xs, ys_pt, ys_fk = [], [], []
        for n in sorted({k[0] for k in by_pt} & {k[0] for k in by_fk}):
            pt = speedup_desde(by_pt, n, t)
            fk = speedup_desde(by_fk, n, t)
            if pt is not None and fk is not None:
                xs.append(n)
                ys_pt.append(pt[0])
                ys_fk.append(fk[0])
        if not xs:
            continue
        plt.plot(xs, ys_pt, marker='o', linestyle='-',  label=f'{t} hilos (pthreads)')
        plt.plot(xs, ys_fk, marker='s', linestyle='--', label=f'{t} procesos (fork)')
    plt.xlabel('Tamano N')
    plt.ylabel('Speedup (mediana T_sec / mediana T_par)')
    plt.title('Comparativa de speedup: pthreads vs fork')
    plt.legend()
    plt.grid(True)
    plt.savefig(path, dpi=150)
    plt.close()
    print(f'Grafica guardada en {path}')


def main():
    by_pt = cargar(PTHREADS_CSV)

    graficar_speedup_vs_N(by_pt, 'pthreads', 'experiments/speedup_vs_N.png')
    graficar_speedup_vs_T(by_pt, 'pthreads', 'experiments/speedup_vs_T.png')

    import os, shutil
    shutil.copyfile('experiments/speedup_vs_N.png', 'experiments/speedup.png')

    if os.path.exists(FORK_CSV):
        by_fk = cargar(FORK_CSV)
        graficar_speedup_vs_N(by_fk, 'fork', 'experiments/speedup_vs_N_fork.png')
        graficar_speedup_vs_T(by_fk, 'fork', 'experiments/speedup_vs_T_fork.png')
        graficar_comparativa(by_pt, by_fk, 'experiments/speedup_comparativa.png')
    else:
        print(f'Aviso: {FORK_CSV} no existe aun; graficas de fork omitidas.')


if __name__ == '__main__':
    main()
