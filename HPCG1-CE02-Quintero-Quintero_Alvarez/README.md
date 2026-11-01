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
| 1 | `01-introduccion.tex` | Qué se hizo y objetivos |
| 2 | `02-marco-teorico.tex` | OpenMP, métricas, benchmark vs profiling, caché |
| 3 | `03-programa-y-medicion.tex` | El kernel, su patrón de acceso y la medición del tiempo |
| 4 | `04-openmp.tex` | La directiva y su justificación |
| 5 | `05-diseno-experimental.tex` | Variables, protocolo, validación y herramientas |
| 6 | `06-resultados.tex` | Perfilado, desempeño y benchmark |
| 7 | `07-analisis.tex` | Análisis integrado |
| 8 | `08-conclusiones.tex` | Hallazgos, limitaciones y trabajo futuro |
| 9 | `09-referencias.tex` | Referencias |

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

El benchmark entre las dos máquinas **ya está completo**: la máquina A (Intel
i5-12450HX, Debian) y la máquina B (AMD Ryzen 5 5500U, Fedora) tienen sus 200
corridas cada una, y la tabla comparativa de la sección 6 ya está rellenada.

Queda pendiente:

1. **Ajustar la portada** (`portada.tex`): fecha de entrega y, si cambia,
   el título.

2. **PDF final**: ya está generado con el nombre que pide el enunciado
   (`HPCG1-CE02-<Nombre1>-<Nombre2>_<Nombre3>.pdf`). Se regenera con:
   ```
   ./compilar.sh && cp main.pdf "HPCG1-CE02-JoseAlejandroQuinteroGahona-MeycolKleymQuinteroCastaño_MaríaAngélicaAlvarezGiraldo.pdf"
   ```
   Falta decidir el nombre de la **carpeta** (actualmente
   `HPCG1-CE02-Quintero-Quintero_Alvarez`).

## Figuras

| Archivo | Origen |
|---|---|
| `comparativa_5_estrategias.png` | `experiments/resultados/caso_de_estudio_2_openmp.png` |
| `cache_miss_rate.png` | `experiments/resultados/perfilado/cache_miss_rate.png` |
| `benchmark_rendimiento.png` | `experiments/resultados/benchmark/benchmark_rendimiento.png` |
