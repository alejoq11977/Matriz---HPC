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
| **`caso-de-estudio-2-openmp`** | **Caso 2 — añadiendo OpenMP como 5ta estrategia** |

Este README documenta **el caso 2 con OpenMP**, que es la continuación del caso 2. Aquí no se implementa código nuevo; se reutilizan los binarios de las ramas anteriores para comparar el rendimiento de las **5 estrategias**:

1. **Pthreads** (la mejor T de las 16 opciones)
2. **Fork** (la mejor T de las 15 opciones)
3. **Optimización por compilación** (`mm_full`: `-O3 -march=native -floop-interchange -funroll-loops -floop-nest-optimize`)
4. **Optimización por memoria** (kernel transpuesto de `matriz_monotonic_t`)
5. **OpenMP** (paralelización con directivas `#pragma omp parallel for`, compilado con `-fopenmp -O0`)

## Metodología

Para las dos primeras (pthreads, fork) se usaron los datos crudos con 10 corridas que ya existían en las ramas `pthreads` y `fork`. Para las dos últimas (optimización) se re-medieron con 10 corridas cada una, **variando N en cada iteración** dentro del mismo binario para evitar el problema de la cache.

El profe dijo: "para no tomar un tiempo específico, sino tomar el promedio o la base estadística que ustedes hayan escogido, que también eso ya lo explicamos, que el promedio es suficiente". Se toman **medianas** de las 10 corridas (no promedios) por N, lo que es robusto ante outliers.

La **base para calcular el speedup** es la misma en los cinco casos: la mediana de las 10 corridas del secuencial con T=1 de pthreads, es decir, la mediana de `T_seq`. Esto es exactamente lo que se usó en el caso 1.

## Cómo se ejecutó

1. `experiments/medir_optimizaciones.sh` corre 10 iteraciones de:
   ```
   N=500, N=1000, N=2000, N=4000
   ```
   para cada binario (`mm_full` y `matriz_monotonic_t`), todas con semilla 42.
2. `experiments/medir_openmp.sh` compila `matriz_monotonic.c` con `-fopenmp -O0` y corre 10 iteraciones de los mismos 4 Ns, todas con semilla 42. El `-O0` se eligió para medir el speedup *puro* de la paralelización, sin que el compilador reordene loops ni haga vectorización agresiva que enmascare el efecto de OpenMP.
3. `experiments/plot_caso2.py` lee los CSVs (los nuevos + los de las ramas pthreads y fork), calcula medianas y genera la tabla y la gráfica.
4. `experiments/plot_caso2_openmp.py` reusa el mismo flujo pero agrega la columna de OpenMP y la 5ta curva a la gráfica.

## Resultados

### Tabla comparativa de speedups (vs mismo secuencial)

| N | T_seq (s) | T_pth_best (s) | T_fork_best (s) | T_full (s) | T_mem (s) | T_openmp (s) | speedup_pth | speedup_fork | speedup_full | speedup_mem | speedup_openmp |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | 0.0440 | 0.0315 (T=16) | 0.0152 (T=8) | 0.0459 | 0.0377 | 0.0500 | 1.40 | 2.89 | 0.96 | 1.17 | 0.88 |
| 1000 | 0.4230 | 0.2043 (T=16) | 0.1169 (T=16) | 0.4301 | 0.3019 | 0.4500 | 2.07 | 3.62 | 0.98 | 1.40 | 0.94 |
| 2000 | 4.3626 | 1.6430 (T=16) | 1.9805 (T=8) | 5.8909 | 2.6586 | 4.8500 | 2.66 | 2.20 | 0.74 | 1.64 | 0.90 |
| 4000 | 75.6511 | 24.2927 (T=16) | 59.1421 (T=8) | 70.0332 | 21.3223 | 54.5000 | 3.11 | 1.28 | 1.08 | 3.55 | 1.39 |

### Gráfica

Comparativa de las 4 estrategias (rama `caso-de-estudio-2`):

![Comparativa de las 4 estrategias](experiments/resultados/caso_de_estudio_2.png)

Comparativa de las **5 estrategias** incluyendo OpenMP (esta rama):

![Comparativa de las 5 estrategias](experiments/resultados/caso_de_estudio_2_openmp.png)

### Conclusiones

- **A N chico (500)**: el speedup es modesto en general. Fork destaca con 2.89× por la baja latencia de la primera paralelización de procesos. OpenMP arranca con 0.88×, ligeramente *debajo* del secuencial — el overhead de crear el equipo de hilos y sincronizar domina sobre el cómputo en matrices chicas.
- **A N=4000** (problema grande):
  - **Optimización de memoria (transpuesto)** alcanza **3.55×**, la mayor de las cinco estrategias.
  - **Pthreads** alcanza **3.11×**.
  - **Fork** se queda en 1.28× (con el overhead de procesos no se justifica tanto en este equipo).
  - **Optimización de compilación sola** queda en 1.08× (casi no ayuda vs el secuencial).
  - **OpenMP** alcanza **1.39×**, mejor que fork y que `-O3` solo, pero claramente por debajo de pthreads y del transpuesto.

- **Conclusión principal**: la optimización de **patrón de acceso a memoria** (transponer B) es la que más impacto tiene en este problema, comparable o superior a la paralelización con pthreads. La optimización de compilación sola no escala bien con N. OpenMP queda como una opción intermedia: supera a fork y a `-O3` solo, pero la paralelización manual con pthreads y, sobre todo, la transposición de B siguen siendo más efectivas en este hardware.

## Archivos generados

| Archivo | Descripción |
|---|---|
| `bin/matriz_openmp_O0` | Binario de OpenMP compilado con `-fopenmp -O0` |
| `experiments/medir_optimizaciones.sh` | Script de 10 corridas para `mm_full` y `matriz_monotonic_t` |
| `experiments/medir_openmp.sh` | Script que compila y mide 10 corridas del binario OpenMP |
| `experiments/plot_caso2.py` | Genera la tabla CSV y la gráfica PNG de las 4 estrategias |
| `experiments/plot_caso2_openmp.py` | Genera la tabla CSV y la gráfica PNG de las 5 estrategias (incluye OpenMP) |
| `experiments/resultados/med_mm_full_raw.csv` | 10 corridas de `mm_full` (N=500,1000,2000,4000) |
| `experiments/resultados/med_matriz_monotonic_t_raw.csv` | 10 corridas de `matriz_monotonic_t` (mismos N) |
| `experiments/resultados/med_openmp_raw.csv` | 10 corridas de `matriz_openmp_O0` (mismos N) |
| `experiments/resultados/caso_de_estudio_2.csv` | Tabla comparativa de speedups (4 estrategias) |
| `experiments/resultados/caso_de_estudio_2.png` | Gráfica de las 4 estrategias |
| `experiments/resultados/caso_de_estudio_2_openmp.csv` | Tabla comparativa de speedups (5 estrategias) |
| `experiments/resultados/caso_de_estudio_2_openmp.png` | Gráfica de las 5 estrategias |
| `experiments/resultados/medir_log.txt` | Log de la corrida de medición |

## Cómo reproducir

```bash
make all
bash experiments/medir_optimizaciones.sh 500 1000 2000 4000 10 mm_full matriz_monotonic_t
python3 experiments/plot_caso2.py
bash experiments/medir_openmp.sh
python3 experiments/plot_caso2_openmp.py
```

Los datos de `pthreads` y `fork` se leen directamente de las ramas `origin/pthreads` y `origin/fork` mediante `git show`.
