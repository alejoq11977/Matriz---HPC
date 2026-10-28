# Documento LaTeX — Caso de Estudio 2 (HPC)

Carpeta con el documento del caso de estudio 2 de Computación de Alto Rendimiento:
concurrencia con OpenMP, perfilado de CPU y memoria, y benchmark entre dos máquinas.

## Estructura

```
.
├── main.tex              # archivo principal
├── portada.tex           # página de título
├── secciones/            # 13 secciones, una por archivo
├── figuras/              # gráficas de resultados
├── bibliografia.bib      # referencias BibTeX
├── compilar.sh           # script de compilación
└── main.pdf              # PDF generado
```

## Secciones

| # | Archivo | Contenido |
|---|---|---|
| 1 | `01-introduccion.tex` | Presentación del trabajo y organización |
| 2 | `02-objetivos.tex` | Objetivo general y específicos |
| 3 | `03-marco-teorico.tex` | OpenMP, métricas de rendimiento, benchmark, perfilado, jerarquía de caché |
| 4 | `04-programa-base.tex` | El kernel secuencial y su patrón de acceso a memoria |
| 5 | `05-medicion-tiempo.tex` | Wall clock vs tiempo de CPU, `CLOCK_MONOTONIC_RAW` |
| 6 | `06-openmp.tex` | Implementación con OpenMP y justificación de las directivas |
| 7 | `07-benchmark.tex` | Protocolo de comparación entre máquinas |
| 8 | `08-perfilado.tex` | Herramientas de perfilado (GProf, Cachegrind, getrusage) |
| 9 | `09-diseno-experimental.tex` | Variables, metodología, validación de correctitud |
| 10 | `10-resultados.tex` | Resultados de perfilado, desempeño y benchmark |
| 11 | `11-analisis.tex` | Análisis integrado |
| 12 | `12-conclusiones.tex` | Hallazgos, limitaciones y trabajo futuro |
| 13 | `13-referencias.tex` | Referencias |

## Compilar

```bash
./compilar.sh
```

Genera `main.pdf`. Requisitos: `pdflatex`, `bibtex` y los paquetes
`texlive-latex-recommended` + `texlive-fonts-recommended`.

```bash
# Debian/Ubuntu
sudo apt install texlive-latex-recommended texlive-fonts-recommended
```

## Antes de entregar

1. **Completar la segunda máquina.** El benchmark y el perfilado se miden con
   `bash experiments/bench.sh <etiqueta> 500 1000 2000 4000` y
   `bash experiments/perfilar.sh <etiqueta>` en cada equipo
   (ver `experiments/REPRODUCIR_OTRA_MAQUINA.md`). Después, en el equipo
   principal: `python3 experiments/plot_benchmark.py` y
   `python3 experiments/plot_perfilado.py`.
2. **Rellenar la tabla de comparación** en `secciones/10-resultados.tex` con los
   datos de la máquina B y recalcular la columna `%\Delta`.
3. **Regenerar las figuras** de `figuras/benchmark_maquinas.png`,
   `figuras/benchmark_tiempos.png` y `figuras/cache_miss_rate_maquinas.png`
   copiándolas de `experiments/resultados/benchmark/` y
   `experiments/resultados/perfilado/`.
4. **Ajustar la portada** (`portada.tex`): fecha de entrega y, si cambia,
   el título.
5. **Renombrar la carpeta y el PDF** con los nombres finales de los integrantes:
   ```
   mv HPCG1-CE02-Quintero-Quintero_Alvarez HPCG1-CE02-<Nombre1>-<Nombre2>_<Nombre3>
   mv main.pdf HPCG1-CE02-<Nombre1>-<Nombre2>_<Nombre3>.pdf
   ```

## Figuras

| Archivo | Origen |
|---|---|
| `comparativa_5_estrategias.png` | `experiments/resultados/caso_de_estudio_2_openmp.png` |
| `comparativa_4_estrategias.png` | `experiments/resultados/caso_de_estudio_2.png` |
| `cache_miss_rate.png` | `experiments/resultados/perfilado/cache_miss_rate.png` |
| `cache_miss_rate_maquinas.png` | `experiments/resultados/perfilado/cache_miss_rate_maquinas.png` |
| `footprint_memoria.png` | `experiments/resultados/perfilado/footprint_memoria.png` |
| `benchmark_maquinas.png` | `experiments/resultados/benchmark/benchmark_maquinas.png` |
| `benchmark_tiempos.png` | `experiments/resultados/benchmark/benchmark_tiempos.png` |
