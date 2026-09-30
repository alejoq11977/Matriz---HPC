import csv
import math
import sys
from collections import defaultdict

INFILE = sys.argv[1] if len(sys.argv) > 1 else 'experiments/resultados_raw.csv'
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else 'experiments/resultados.csv'

grupos = defaultdict(list)
with open(INFILE) as f:
    for row in csv.DictReader(f):
        key = (int(row['N']), int(row['threads']))
        grupos[key].append(float(row['tiempo']))

with open(OUTFILE, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['N', 'threads', 'media', 'mediana', 'stddev', 'n'])
    for (n, t) in sorted(grupos):
        vals = sorted(grupos[(n, t)])
        m = sum(vals) / len(vals)
        if len(vals) % 2 == 1:
            med = vals[len(vals) // 2]
        else:
            med = (vals[len(vals) // 2 - 1] + vals[len(vals) // 2]) / 2
        var = sum((x - m) ** 2 for x in vals) / len(vals) if len(vals) > 1 else 0.0
        sd = math.sqrt(var)
        w.writerow([n, t, f'{m:.6f}', f'{med:.6f}', f'{sd:.6f}', len(vals)])

print(f'Agregado: {len(grupos)} configuraciones -> {OUTFILE}')
