# Documento LaTeX — Reto 2 (HPC)

Caso de estudio 2: algoritmos de Monte Carlo para estimar π (método del
dartboard y aguja de Buffon), con concurrencia OpenMP, perfilado de CPU y
memoria, y benchmark entre dos máquinas.

## Estructura

```
.
├── main.tex              # archivo principal
├── portada.tex           # página de título
├── secciones/            # 9 secciones, una por archivo
├── figuras/              # gráficas de resultados
├── bibliografia.bib      # referencias BibTeX
├── compilar.sh           # script de compilación
└── main.pdf              # PDF generado
```

## Secciones

| # | Archivo | Contenido |
|---|---|---|
| 1 | `01-introduccion.tex` | Qué se hizo y objetivos |
| 2 | `02-algoritmos.tex` | Modelo matemático y distribución del error de cada algoritmo |
| 3 | `03-implementacion.tex` | Implementación serial, generador de números aleatorios, determinismo |
| 4 | `04-paralelizacion.tex` | Análisis de opciones de paralelización y optimización |
| 5 | `05-diseno-experimental.tex` | Variables, protocolo, validación de efectividad |
| 6 | `06-resultados.tex` | Validación, convergencia, perfilado, desempeño, benchmark |
| 7 | `07-analisis.tex` | Análisis integrado de los resultados |
| 8 | `08-conclusiones.tex` | Hallazgos, limitaciones y trabajo futuro |
| 9 | `09-referencias.tex` | Referencias |

## Compilar

```bash
./compilar.sh
```

Requiere `pdflatex` y `bibtex`:
```bash
sudo apt install texlive-latex-recommended texlive-fonts-recommended
```

## Código fuente

| Archivo | Contenido |
|---|---|
| `src/montecarlo.c` | Programa principal y modo de validación |
| `modules/rng.c` | Generador xoshiro256** con mezcla de semillas SplitMix64 |
| `modules/pi_dartboard.c` | Kernel del dartboard (serial y OpenMP) |
| `modules/pi_buffon.c` | Kernel de Buffon (serial y OpenMP) |
| `modules/pi_common.c` | Despacho entre variantes, estimador y σ teórica |
| `include/pi.h`, `include/rng.h` | Interfaces |

## Scripts de experimento

| Script | Función |
|---|---|
| `experiments/medir_montecarlo.sh` | Barrido completo: validación + convergencia + desempeño + gráficas |
| `experiments/bench_montecarlo.sh` | Benchmark portable entre dos máquinas |
| `experiments/perfilar_montecarlo.sh` | Perfilado: GProf (CPU) + Cachegrind (memoria) + max RSS |
| `experiments/plot_montecarlo.py` | Gráficas de desempeño, convergencia y costo |
| `experiments/plot_benchmark_montecarlo.py` | Comparación entre máquinas |
| `experiments/plot_perfilado_montecarlo.py` | Tabla y gráfica de perfilado de memoria |

## Antes de entregar

El benchmark entre las dos máquinas **ya está completo** (máquina A: Intel
i5-12450HX / Debian 13; máquina B: AMD Ryzen 7 7735HS / Debian 13, mismo
gcc 14.2.0).

Queda pendiente:

1. **Repetir la medición de la máquina A con el equipo en reposo.** La
   corrida actual se hizo con procesos ajenos en ejecución y eso subestima
   su speedup. Es el único ajuste pendiente de datos:
   ```bash
   bash experiments/bench_montecarlo.sh MaquinaA 100000000 1000000000
   python3 experiments/plot_benchmark_montecarlo.py
   ```
   Después copiar la figura regenerada a `figuras/benchmark_maquinas.png`.

2. **Opcional**: perfilar en la máquina B para comparar la tasa de fallo de
   caché entre las dos jerarquías:
   ```bash
   bash experiments/perfilar_montecarlo.sh
   ```

3. **Ajustar la portada** (`portada.tex`): fecha de entrega.

4. **Regenerar el PDF final** con el nombre del enunciado:
   ```bash
   ./compilar.sh && cp main.pdf "HPCG1-Reto2-JoseAlejandroQuinteroGahona-MeycolKleymQuinteroCastaño_MaríaAngélicaAlvarezGiraldo.pdf"
   ```

## Figuras

| Archivo | Origen |
|---|---|
| `convergencia_pi.png` | `experiments/resultados/convergencia_pi.png` |
| `error_montecarlo.png` | `experiments/resultados/error_montecarlo.png` |
| `cache_montecarlo.png` | `experiments/resultados/perfilado_reto2/cache_miss_rate.png` |
| `speedup_montecarlo.png` | `experiments/resultados/speedup_montecarlo.png` |
| `escalamiento_algoritmos.png` | `experiments/resultados/escalamiento_algoritmos.png` |
| `costo_por_muestra.png` | `experiments/resultados/costo_por_muestra.png` |
| `benchmark_maquinas.png` | `experiments/resultados/benchmark_reto2/benchmark_maquinas.png` |
