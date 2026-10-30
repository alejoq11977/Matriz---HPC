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
    # El benchmark entre maquinas compara el RENDIMIENTO R = 1/T (tiempo
    # absoluto y %Delta de rendimiento), que es lo que el profesor define.
    # El speedup interno es un dato complementario: dice que tan bien escala
    # la paralelizacion dentro de cada equipo.
    #
    # GOP/s: como el kernel trabaja con enteros no hay FLOPS, asi que se
    # reporta el analogo entero: 2*N^3 operaciones (una multiplicacion y una
    # suma por cada celda) por segundo.
    #
    # veces_A_sobre_B = t_B/t_A = R_A/R_B  (cuantas veces mas rapido es A)
    # %delta_B_vs_A  = (R_B-R_A)/R_A * 100 = (t_A/t_B - 1) * 100
    header = ['N', 'maquina', 'T_optimo', 'T_optimo_(s)', 'GOP/s (x1e9)',
              'speedup_interno', 'veces_sobre_la_otra', '%delta_rend_vs_otra']
    filas = [header]

    # La primera maquina es la referencia
    ref = maquinas[0]

    def gops(n, t):
        """Operaciones enteras por segundo, en miles de millones (GOP/s).

        El kernel hace N^3 multiplicaciones y N^3 sumas, asi que se cuentan
        2*N^3 operaciones. Como el trabajo es con enteros no hay FLOPS:
        esta es la analogia entera.
        """
        if not t:
            return ''
        return f'{2.0 * n ** 3 / t / 1e9:.2f}'

    for m in maquinas:
        for n in m['ns']:
            if n not in m['mejores']:
                continue
            bt, t_best = m['mejores'][n]
            t1 = m['base'].get(n, '')
            sp_int = (m['base'][n] / t_best) if n in m['base'] else ''
            # Comparacion cruzada contra la maquina de referencia
            veces = ''
            delta = ''
            if n in ref['mejores']:
                t_ref = ref['mejores'][n][1]
                if m is ref:
                    veces = '1.00'
                    delta = '0.0'
                else:
                    veces = f'{t_best / t_ref:.2f}'
                    delta = f'{(t_ref / t_best - 1) * 100:+.1f}'
            filas.append([n, m['etiqueta'], bt, f'{t_best:.4f}',
                          gops(n, t_best),
                          f'{sp_int:.2f}' if sp_int != '' else '',
                          veces, delta])

    with open(f'{BASE}/resumen_maquinas.csv', 'w', newline='') as f:
        csv.writer(f).writerows(filas)
    print(f"  -> {BASE}/resumen_maquinas.csv")

    # --- Tabla comparacion directa: quien gana en que ---
    # (encabezado por N, una fila por metrica)
    header2 = ['N', 'T_opt_A(s)', 'T_opt_B(s)', 'GOP/s_A', 'GOP/s_B',
               '%delta_rend_B_vs_A', 'gana_rendimiento', 'speedup_A',
               'speedup_B', 'gana_speedup']
    filas2 = [header2]
    if len(maquinas) >= 2:
        a = maquinas[0]
        b = maquinas[1]
        for n in sorted(set(a['ns']) & set(b['ns'])):
            if n not in a['mejores'] or n not in b['mejores']:
                continue
            ta = a['mejores'][n][1]
            tb = b['mejores'][n][1]
            sa = a['base'][n] / ta if n in a['base'] else 0
            sb = b['base'][n] / tb if n in b['base'] else 0
            filas2.append([
                n, f'{ta:.4f}', f'{tb:.4f}',
                gops(n, ta), gops(n, tb),
                f'{(ta / tb - 1) * 100:+.1f}',
                a['etiqueta'] if ta < tb else b['etiqueta'],
                f'{sa:.2f}', f'{sb:.2f}',
                a['etiqueta'] if sa > sb else b['etiqueta'],
            ])
        with open(f'{BASE}/comparacion_directa.csv', 'w', newline='') as f:
            csv.writer(f).writerows(filas2)
        print(f"  -> {BASE}/comparacion_directa.csv")

    # --- Grafica: speedup interno por maquina ---
    fig, ax = plt.subplots(figsize=(11, 6))
    for i, m in enumerate(maquinas):
        ns = [n for n in m['ns'] if n in m['base'] and n in m['mejores']]
        sp = [m['base'][n] / m['mejores'][n][1] for n in ns]
        ax.plot(ns, sp, 'o-', label=f"{m['etiqueta']}: {m['cpu']}",
                linewidth=2, color=COLORES[i % len(COLORES)], markersize=8)
    ax.set_xlabel('Tamano de matriz N')
    ax.set_ylabel('Speedup (vs T=1 de la misma maquina)')
    ax.set_title('Benchmark: speedup de OpenMP en cada maquina')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(sorted(set(n for m in maquinas for n in m['ns'])))
    ax.set_xticklabels([f'N={n}' for n in sorted(set(n for m in maquinas for n in m['ns']))])
    plt.tight_layout()
    plt.savefig(f'{BASE}/benchmark_maquinas.png', dpi=120)
    plt.close()
    print(f"  -> {BASE}/benchmark_maquinas.png")

    # --- Grafica: RENDIMIENTO (GOP/s) y punto de cruce entre maquinas ---
    # Esta es la grafica del benchmark: compara el rendimiento absoluto
    # (GOP/s) de cada equipo, que es lo que el profesor define como
    # comparacion entre maquinas.
    if len(maquinas) >= 2:
        a = maquinas[0]
        b = maquinas[1]
        ns_comunes = sorted(set(a['ns']) & set(b['ns']))
        ns_comunes = [n for n in ns_comunes
                      if n in a['mejores'] and n in b['mejores']]

        fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.5))

        # Panel izquierdo: GOP/s por maquina
        ax = axes[0]
        ancho = 0.38
        for k, m in enumerate([a, b]):
            vals = []
            for n in ns_comunes:
                t = m['mejores'][n][1]
                vals.append(2.0 * n ** 3 / t / 1e9)
            xs = [i + (k - 0.5) * ancho for i in range(len(ns_comunes))]
            barras = ax.bar(xs, vals, ancho, label=m['etiqueta'],
                            color=COLORES[k % len(COLORES)],
                            edgecolor='black', linewidth=0.6)
            for bar, v in zip(barras, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f'{v:.2f}', ha='center', va='bottom', fontsize=8)
        ax.set_xticks(range(len(ns_comunes)))
        ax.set_xticklabels([f'N={n}' for n in ns_comunes])
        ax.set_ylabel('GOP/s  (miles de millones de operaciones enteras/s)')
        ax.set_title('Rendimiento absoluto de cada maquina')
        ax.set_yscale('log')
        ax.legend(title='Máquina')
        ax.grid(True, axis='y', alpha=0.3)
        # Panel derecho: speedup interno, con el ganador resaltado
        ax = axes[1]
        for k, m in enumerate([a, b]):
            vals = []
            for n in ns_comunes:
                t = m['mejores'][n][1]
                t1 = m['base'].get(n)
                vals.append(t1 / t if t1 else 0)
            xs = [i + (k - 0.5) * ancho for i in range(len(ns_comunes))]
            barras = ax.bar(xs, vals, ancho, label=m['etiqueta'],
                            color=COLORES[k % len(COLORES)],
                            edgecolor='black', linewidth=0.6)
            for bar, v in zip(barras, vals):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                        f'{v:.2f}x', ha='center', va='bottom', fontsize=8)
        ax.set_xticks(range(len(ns_comunes)))
        ax.set_xticklabels([f'N={n}' for n in ns_comunes])
        ax.set_ylabel('Speedup (vs T=1 de la misma maquina)')
        ax.set_title('Escalamiento: quien paraleliza mejor')
        ax.legend()
        ax.grid(True, axis='y', alpha=0.3)
        # Deja espacio arriba para las anotaciones de "gana X"
        max_sp = max((a['base'][n] / a['mejores'][n][1]) if n in a['base'] else 0
                     for n in ns_comunes) if ns_comunes else 1
        ax.set_ylim(0, max_sp * 1.32)
        # Marca en que N gana cada maquina en escalamiento
        for i, n in enumerate(ns_comunes):
            sa = a['base'][n] / a['mejores'][n][1]
            sb = b['base'][n] / b['mejores'][n][1]
            if abs(sa - sb) / max(sa, sb) > 0.03:
                ganador = a['etiqueta'] if sa > sb else b['etiqueta']
                ax.annotate(f'gana {ganador}', xy=(i, max(sa, sb)),
                            xytext=(i, max(sa, sb) * 1.06),
                            ha='center', fontsize=8, color='black',
                            arrowprops=dict(arrowstyle='->', color='black', lw=0.8))

        plt.tight_layout()
        plt.savefig(f'{BASE}/benchmark_rendimiento.png', dpi=120)
        plt.close()
        print(f"  -> {BASE}/benchmark_rendimiento.png")

    # --- Grafica: tiempos absolutos por maquina ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # Panel izquierdo: tiempo absoluto del mejor T
    ax = axes[0]
    for i, m in enumerate(maquinas):
        ns = [n for n in m['ns'] if n in m['mejores']]
        ts = [m['mejores'][n][1] for n in ns]
        ax.plot(ns, ts, 's-', label=f"{m['etiqueta']}: {m['cpu']}",
                linewidth=2, color=COLORES[i % len(COLORES)], markersize=8)
    ax.set_xlabel('Tamano de matriz N')
    ax.set_ylabel('Tiempo de multiplicacion (s)')
    ax.set_title('Tiempo absoluto del mejor T en cada maquina')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_yscale('log')
    ax.set_xticks(sorted(set(n for m in maquinas for n in m['ns'])))
    ax.set_xticklabels([f'N={n}' for n in sorted(set(n for m in maquinas for n in m['ns']))])

    # Panel derecho: cuanto mas rapido es la maquina A respecto de la B
    ax = axes[1]
    if len(maquinas) >= 2:
        ref = maquinas[0]
        otra = maquinas[1]
        ns_comunes = [n for n in ref['ns']
                      if n in ref['mejores'] and n in otra['mejores']]
        razones = [otra['mejores'][n][1] / ref['mejores'][n][1] for n in ns_comunes]
        barras = ax.bar(range(len(ns_comunes)), razones,
                        color=COLORES[1 % len(COLORES)], edgecolor='black', linewidth=0.6)
        ax.set_xticks(range(len(ns_comunes)))
        ax.set_xticklabels([f'N={n}' for n in ns_comunes])
        ax.set_ylabel(f'Veces mas rapido {ref["etiqueta"]} que {otra["etiqueta"]}')
        ax.set_title('Ventaja en tiempo de la maquina de referencia')
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_ylim(0, max(razones) * 1.25 if razones else 1)
        for b, v in zip(barras, razones):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f'{v:.2f}x',
                    ha='center', va='bottom', fontsize=9)

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
