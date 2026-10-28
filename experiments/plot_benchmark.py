"""
plot_benchmark.py - Consolida los resultados del benchmark ejecutado en una o
varias maquinas y genera las tablas y graficas comparativas.

Cada maquina aporta:
  experiments/resultados/benchmark/<etiqueta>_raw.csv    (N,T,run,tiempo)
  experiments/resultados/benchmark/<etiqueta>_hardware.txt (descripcion)

Salidas:
  experiments/resultados/benchmark/resumen_maquinas.csv   tabla comparativa
  experiments/resultados/benchmark/benchmark_maquinas.png  grafica de speedup
  experiments/resultados/benchmark/benchmark_tiempos.png   grafica de tiempos

Uso:
  python3 experiments/plot_benchmark.py                      # todas las maquinas
  python3 experiments/plot_benchmark.py --maquina A          # solo la A (consolida)
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

BASE = 'experiments/resultados/benchmark'

# Orden y color por etiqueta de maquina
COLORES = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']


def leer_raw(ruta):
    """Lee un CSV N,T,run,tiempo -> {(N,T): [tiempos]}"""
    datos = {}
    if not os.path.exists(ruta):
        return datos
    with open(ruta) as f:
        for row in csv.DictReader(f):
            try:
                n = int(row['N'])
                t = int(row.get('T', row.get('threads', 1)))
                datos.setdefault((n, t), []).append(float(row['tiempo']))
            except (ValueError, KeyError):
                continue
    return datos


def leer_hardware(ruta):
    """Extrae los campos clave del archivo de hardware."""
    info = {}
    if not os.path.exists(ruta):
        return info
    with open(ruta, errors='replace') as f:
        for linea in f:
            if ':' in linea:
                k, _, v = linea.partition(':')
                k = k.strip()
                v = v.strip()
                # la linea "Mem:  15Gi ..." viene de free -h; nos interesa
                # solo el total (primer campo)
                if k == 'Mem':
                    v = v.split()[0] if v else ''
                info[k] = v
    return info


def info_maquina(etiqueta):
    """Reune la informacion de hardware de una maquina."""
    raw = leer_raw(f'{BASE}/{etiqueta}_raw.csv')
    hw = leer_hardware(f'{BASE}/{etiqueta}_hardware.txt')
    if not raw:
        return None

    ns = sorted(set(n for n, _ in raw))
    ts = sorted(set(t for _, t in raw))

    # mejor T por N (minimiza la mediana)
    mejores = {}
    for n in ns:
        medianas = {}
        for t in ts:
            vals = raw.get((n, t))
            if vals:
                medianas[t] = statistics.median(vals)
        if medianas:
            bt = min(medianas, key=medianas.get)
            mejores[n] = (bt, medianas[bt])

    # T=1 como base interna de cada maquina (para el speedup intra-maquina)
    base = {}
    for n in ns:
        vals = raw.get((n, 1))
        if vals:
            base[n] = statistics.median(vals)

    return {
        'etiqueta': etiqueta,
        'raw': raw,
        'hw': hw,
        'ns': ns,
        'ts': ts,
        'mejores': mejores,
        'base': base,
        'n_cores': hw.get('Nucleos logicos detectados', '?'),
        'cpu': hw.get('Model name', '?'),
        'ram': hw.get('Mem', '?'),
        'distro': hw.get('Distribucion', '?'),
        'hostname': hw.get('Hostname', '?'),
        'compiler': hw.get('Compiler', '?'),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maquina', help='etiqueta de la maquina a consolidar (opcional)')
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
        print("ERROR: no hay datos de benchmark. Ejecuta experiments/bench.sh primero.")
        return

    print(f"  Maquinas con datos: {[m['etiqueta'] for m in maquinas]}")

    # --- Tabla consolidada ---
    header = ['N', 'maquina', 'T_optimo', 'T_optimo_(s)', 'T_1_(s)',
              'speedup_interno', 'speedup_vs_maquina_A']
    filas = [header]

    # La primera maquina es la referencia
    ref = maquinas[0]
    ref_et = ref['etiqueta']

    for m in maquinas:
        for n in m['ns']:
            if n not in m['mejores']:
                continue
            bt, t_best = m['mejores'][n]
            t1 = m['base'].get(n, '')
            sp_int = (m['base'][n] / t_best) if n in m['base'] else ''
            # speedup cruzado: rendimiento relativo vs maquina A
            sp_cross = ''
            if n in ref['mejores']:
                t_ref = ref['mejores'][n][1]
                sp_cross = f'{t_ref / t_best:.2f}'
            filas.append([n, m['etiqueta'], bt, f'{t_best:.4f}',
                          f'{t1:.4f}' if t1 != '' else '',
                          f'{sp_int:.2f}' if sp_int != '' else '',
                          sp_cross])

    with open(f'{BASE}/resumen_maquinas.csv', 'w', newline='') as f:
        csv.writer(f).writerows(filas)
    print(f"  -> {BASE}/resumen_maquinas.csv")

    # --- Grafica: speedup interno por maquina ---
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, m in enumerate(maquinas):
        ns = [n for n in m['ns'] if n in m['base'] and n in m['mejores']]
        sp = [m['base'][n] / m['mejores'][n][1] for n in ns]
        ax.plot(ns, sp, 'o-', label=f"{m['etiqueta']} ({m['cpu'][:28]})",
                linewidth=2, color=COLORES[i % len(COLORES)], markersize=8)
    ax.set_xlabel('Tamano de matriz N')
    ax.set_ylabel('Speedup (vs T=1 de la misma maquina)')
    ax.set_title('Benchmark: speedup de OpenMP en cada maquina')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sorted(set(n for m in maquinas for n in m['ns'])))
    ax.set_xticklabels([f'N={n}' for n in sorted(set(n for m in maquinas for n in m['ns']))])
    plt.tight_layout()
    plt.savefig(f'{BASE}/benchmark_maquinas.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/benchmark_maquinas.png")

    # --- Grafica: tiempos absolutos por maquina ---
    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, m in enumerate(maquinas):
        ns = [n for n in m['ns'] if n in m['mejores']]
        ts = [m['mejores'][n][1] for n in ns]
        ax.plot(ns, ts, 's-', label=f"{m['etiqueta']} (mejor T)",
                linewidth=2, color=COLORES[i % len(COLORES)], markersize=8)
    ax.set_xlabel('Tamano de matriz N')
    ax.set_ylabel('Tiempo de multiplicacion (s)')
    ax.set_title('Benchmark: tiempo absoluto del mejor T en cada maquina')
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(sorted(set(n for m in maquinas for n in m['ns'])))
    ax.set_xticklabels([f'N={n}' for n in sorted(set(n for m in maquinas for n in m['ns']))])
    plt.tight_layout()
    plt.savefig(f'{BASE}/benchmark_tiempos.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/benchmark_tiempos.png")

    # --- Tabla de hardware lado a lado (para el documento) ---
    with open(f'{BASE}/comparativa_hardware.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['caracteristica'] + [m['etiqueta'] for m in maquinas])
        filas_hw = [
            ('Hostname', 'hostname'),
            ('CPU', 'cpu'),
            ('Nucleos logicos', 'n_cores'),
            ('Memoria RAM', 'ram'),
            ('Distribucion', 'distro'),
            ('Compilador', 'compiler'),
        ]
        for etiqueta_legible, clave in filas_hw:
            w.writerow([etiqueta_legible] + [m.get(clave, '?') for m in maquinas])
        w.writerow(['Flags de compilacion'] +
                   [m['hw'].get('Flags de compil.', '?') for m in maquinas])
    print(f"  -> {BASE}/comparativa_hardware.csv")

    print("Listo.")


if __name__ == '__main__':
    main()
