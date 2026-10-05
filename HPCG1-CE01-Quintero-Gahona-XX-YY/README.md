# Documento LaTeX — Caso de Estudio 1 (HPC)

Esta carpeta contiene el documento del caso de estudio 1 de Computación de Alto Rendimiento.

## Estructura

```
.
├── main.tex              # archivo principal
├── portada.tex           # página de título (con placeholders para los nombres)
├── secciones/            # secciones del documento, una por archivo
├── figuras/              # imágenes (árbol del proyecto + 3 gráficas de speedup)
├── bibliografia.bib      # referencias BibTeX
├── compilar.sh           # script de compilación
└── main.pdf              # PDF generado (si compiló)
```

## Cómo compilar

### Opción 1 — Usando el script

```bash
chmod +x compilar.sh
./compilar.sh
```

### Opción 2 — Comandos manuales

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Requisitos

- **TeX Live** (cualquier distribución reciente):
  - Debian/Ubuntu: `sudo apt install texlive-latex-recommended texlive-fonts-recommended`
  - Arch: `sudo pacman -S texlive-latexrecommended`
  - macOS: instalar MacTeX

## Antes de entregar

1. Editar `portada.tex` y reemplazar:
   - `[Nombre integrante 2]` por el nombre del segundo integrante
   - `[Nombre integrante 3]` por el nombre del tercer integrante
   - `[Nombre del profesor]` por el nombre del profesor
   - `[Fecha de entrega]` por la fecha real

2. Renombrar la carpeta (opcional) para incluir los nombres reales:
   ```
   mv HPCG1-CE01-Quintero-Gahona-XX-YY HPCG1-CE01-Quintero-Gahona-Nombre2-Nombre3
   ```

3. Renombrar el PDF final:
   ```
   mv main.pdf HPCG1-CE01-Quintero-Gahona-Nombre2-Nombre3.pdf
   ```

## Salida esperada

Tras `./compilar.sh` se genera `main.pdf` con el documento completo. Si hay errores, revisar el `.log` que se genera.
