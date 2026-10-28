#!/bin/bash
# Script para compilar el documento LaTeX a PDF.
# Necesita: texlive-latex-base, texlive-latex-recommended, texlive-fonts-recommended
# (o texlive-full). En Debian/Ubuntu: sudo apt install texlive-latex-recommended
# En Arch: sudo pacman -S texlive-latexrecommended

# pdflatex devuelve codigo de salida != 0 cuando hay warnings recuperables
# (por ejemplo, referencias cruzadas sin resolver en la primera pasada), lo
# que abortaria el script con "set -e" antes de generar el PDF. Por eso no
# usamos set -e y limpiamos los auxiliares con un trap que corre siempre.

limpiar() {
    rm -f *.aux *.bbl *.blg *.log *.out *.toc *.fls *.fdb_latexmk *.synctex.gz
}
trap limpiar EXIT

echo "[1/4] Primera pasada de pdflatex..."
pdflatex -interaction=nonstopmode main.tex > /dev/null

echo "[2/4] Procesando bibliografia..."
bibtex main > /dev/null

echo "[3/4] Segunda pasada de pdflatex..."
pdflatex -interaction=nonstopmode main.tex > /dev/null

echo "[4/4] Tercera pasada de pdflatex (resuelve referencias cruzadas)..."
pdflatex -interaction=nonstopmode main.tex > /dev/null

if [ ! -f main.pdf ]; then
    echo ""
    echo "ERROR: no se genero main.pdf. Revisa los errores con:"
    echo "  pdflatex -interaction=nonstopmode main.tex"
    exit 1
fi

PAGINAS=$(pdfinfo main.pdf 2>/dev/null | awk '/^Pages:/{print $2}')
echo ""
echo "Listo. El PDF final es: main.pdf (${PAGINAS:-?} paginas)"
