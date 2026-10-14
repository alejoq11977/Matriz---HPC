# Caso de estudio 2

## Contexto y organización del repositorio

Este repositorio tiene varias ramas que corresponden a dos casos de estudio:

| Rama | Caso |
|---|---|
| `version-inicial` | Caso de estudio 1 — multiplicación de matrices (secuencial) |
| `clock-time` | Caso 1 — variante de medición de tiempo |
| `pthreads` | Caso 1 — paralelización con POSIX Threads |
| `fork` | Caso 1 — paralelización con `fork()` y memoria compartida |
| `lab-1-2-optimizacion` | Caso 1 — optimización por compilación (`-O3` y variantes) y por memoria (kernel transpuesto) |
| **`caso-de-estudio-2`** | **Caso 2 — comparación de las 4 estrategias** |

Este README documenta **el caso 2**, que es la continuación del caso 1. Aquí no se implementa código nuevo; se reutilizan los binarios de las ramas anteriores para comparar el rendimiento de las **4 estrategias**:

1. **Pthreads** (la mejor T de las 16 opciones)
2. **Fork** (la mejor T de las 15 opciones)
3. **Optimización por compilación** (`mm_full`: `-O3 -march=native -floop-interchange -funroll-loops -floop-nest-optimize`)
4. **Optimización por memoria** (kernel transpuesto de `matriz_monotonic_t`)

## Metodología

Para las dos primeras (pthreads, fork) se usaron los datos crudos con 10 corridas que ya existían en las ramas `pthreads` y `fork`. Para las dos últimas (optimización) se re-medieron con 10 corridas cada una, **variando N en cada iteración** dentro del mismo binario para evitar el problema de la cache.

El profe dijo: "para no tomar un tiempo específico, sino tomar el promedio o la base estadística que ustedes hayan escogido, que también eso ya lo explicamos, que el promedio es suficiente". Se toman **medianas** de las 10 corridas (no promedios) por N, lo que es robusto ante outliers.

La **base para calcular el speedup** es la misma en los cuatro casos: la mediana de las 10 corridas del secuencial con T=1 de pthreads, es decir, la mediana de `T_seq`. Esto es exactamente lo que se usó en el caso 1.

## Cómo se ejecutó

1. `experiments/medir_optimizaciones.sh` corre 10 iteraciones de:
   ```
   N=500, N=1000, N=2000, N=4000
   ```
   para cada binario (`mm_full` y `matriz_monotonic_t`), todas con semilla 42.
2. `experiments/plot_caso2.py` lee los CSVs (los nuevos + los de las ramas pthreads y fork), calcula medianas y genera la tabla y la gráfica.

## Resultados

### Tabla comparativa de speedups (vs mismo secuencial)

| N | T_seq (s) | T_pth_best (s) | T_fork_best (s) | T_full (s) | T_mem (s) | speedup_pth | speedup_fork | speedup_full | speedup_mem |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 0.0440 | 0.0315 (T=16) | 0.0152 (T=8) | 0.0459 | 0.0377 | 1.40 | 2.89 | 0.96 | 1.17 |
| 1000 | 0.4230 | 0.2043 (T=16) | 0.1169 (T=16) | 0.4301 | 0.3019 | 2.07 | 3.62 | 0.98 | 1.40 |
| 2000 | 4.3626 | 1.6430 (T=16) | 1.9805 (T=8) | 5.8909 | 2.6586 | 2.66 | 2.20 | 0.74 | 1.64 |
| 4000 | 75.6511 | 24.2927 (T=16) | 59.1421 (T=8) | 70.0332 | 21.3223 | 3.11 | 1.28 | 1.08 | 3.55 |

### Gráfica

![Comparativa de las 4 estrategias](experiments/resultados/caso_de_estudio_2.png)

### Conclusiones

- **A N chico (500)**: el speedup es modesto en general. Fork destaca con 2.89× por la baja latencia de la primera paralelización de procesos.
- **A N=4000** (problema grande):
  - **Optimización de memoria (transpuesto)** alcanza **3.55×**, la mayor de las cuatro estrategias.
  - **Pthreads** alcanza **3.11×**.
  - **Fork** se queda en 1.28× (con el overhead de procesos no se justifica tanto en este equipo).
  - **Optimización de compilación sola** queda en 1.08× (casi no ayuda vs el secuencial).

- **Conclusión principal**: la optimización de **patrón de acceso a memoria** (transponer B) es la que más impacto tiene en este problema, comparable o superior a la paralelización con pthreads. La optimización de compilación sola no escala bien con N.

## Archivos generados

| Archivo | Descripción |
|---|---|
| `experiments/medir_optimizaciones.sh` | Script de 10 corridas para `mm_full` y `matriz_monotonic_t` |
| `experiments/plot_caso2.py` | Genera la tabla CSV y la gráfica PNG desde los CSVs |
| `experiments/resultados/med_mm_full_raw.csv` | 10 corridas de `mm_full` (N=500,1000,2000,4000) |
| `experiments/resultados/med_matriz_monotonic_t_raw.csv` | 10 corridas de `matriz_monotonic_t` (mismos N) |
| `experiments/resultados/caso_de_estudio_2.csv` | Tabla comparativa de speedups |
| `experiments/resultados/caso_de_estudio_2.png` | Gráfica de las 4 estrategias |
| `experiments/resultados/medir_log.txt` | Log de la corrida de medición |

## Cómo reproducir

```bash
make all
bash experiments/medir_optimizaciones.sh 500 1000 2000 4000 10 mm_full matriz_monotonic_t
python3 experiments/plot_caso2.py
```

Los datos de `pthreads` y `fork` se leen directamente de las ramas `origin/pthreads` y `origin/fork` mediante `git show`.
