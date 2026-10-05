#!/bin/bash
# Script para compilar el documento LaTeX a PDF.
# Necesita: texlive-latex-base, texlive-latex-recommended, texlive-fonts-recommended
# (o texlive-full). En Debian/Ubuntu: sudo apt install texlive-latex-recommended
# En Arch: sudo pacman -S texlive-latexrecommended

set -e

echo "[1/4] Primera pasada de pdflatex..."
pdflatex -interaction=nonstopmode main.tex

echo "[2/4] Procesando bibliografia..."
bibtex main

echo "[3/4] Segunda pasada de pdflatex..."
pdflatex -interaction=nonstopmode main.tex

echo "[4/4] Tercera pasada de pdflatex (resuelve referencias cruzadas)..."
pdflatex -interaction=nonstopmode main.tex

# Limpiar archivos auxiliares
rm -f *.aux *.bbl *.blg *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz

echo ""
echo "Listo. El PDF final es: main.pdf"
