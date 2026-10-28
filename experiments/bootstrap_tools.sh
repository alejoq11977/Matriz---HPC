#!/bin/bash
# bootstrap_tools.sh
# Prepara las herramientas de perfilado que NO vienen instaladas en el sistema
# (valgrind -> cachegrind, y time -> /usr/bin/time -v) SIN necesidad de root.
#
# Tecnica: `apt-get download` baja el .deb a la carpeta actual como usuario normal
# (no requiere sudo, no toca el sistema), y `dpkg-deb -x` lo extrae a un
# directorio local. Despues se usa VALGRIND_LIB para que valgrind encuentre sus
# archivos de soporte en la ruta local.
#
# Idempotente: si las herramientas ya estan disponibles en el sistema, no hace
# nada. Si ya estan descargadas en .tools/, tampoco.
#
# Uso:  bash experiments/bootstrap_tools.sh

set -e

RAIZ=$(cd "$(dirname "$0")/.." && pwd)
TOOLS="$RAIZ/.tools"
mkdir -p "$TOOLS"
cd "$TOOLS"

# --- 1) /usr/bin/time (para -v: max RSS, page faults, context switches) ---
if [ -x /usr/bin/time ]; then
    echo "[time]  ya disponible en el sistema: /usr/bin/time"
else
    if [ ! -x "$TOOLS/root/usr/bin/time" ]; then
        echo "[time]  descargando (sin sudo)..."
        apt-get download time 2>/dev/null || true
        for d in time_*.deb; do
            [ -e "$d" ] || continue
            dpkg-deb -x "$d" "$TOOLS/root/"
            rm -f "$d"
        done
    fi
    if [ -x "$TOOLS/root/usr/bin/time" ]; then
        echo "[time]  listo: $TOOLS/root/usr/bin/time"
    else
        echo "[time]  NO se pudo preparar (se continuara sin -v)"
    fi
fi

# --- 2) valgrind (para cachegrind: D1/LL misses) ---
if command -v valgrind >/dev/null 2>&1; then
    echo "[valgrind] ya disponible en el sistema: $(command -v valgrind)"
else
    if [ ! -x "$TOOLS/root/usr/bin/valgrind" ]; then
        echo "[valgrind] descargando (sin sudo, ~15 MB)..."
        apt-get download valgrind 2>/dev/null || true
        for d in valgrind_*.deb; do
            [ -e "$d" ] || continue
            dpkg-deb -x "$d" "$TOOLS/root/"
            rm -f "$d"
        done
    fi
    if [ -x "$TOOLS/root/usr/bin/valgrind" ]; then
        export VALGRIND_LIB="$TOOLS/root/usr/libexec/valgrind"
        if "$TOOLS/root/usr/bin/valgrind" --version >/dev/null 2>&1; then
            echo "[valgrind] listo: $TOOLS/root/usr/bin/valgrind ($(VALGRIND_LIB=$VALGRIND_LIB "$TOOLS/root/usr/bin/valgrind" --version 2>/dev/null))"
        else
            echo "[valgrind] ADVERTENCIA: se extrajo pero no arranca (faltan libs del sistema)"
        fi
    else
        echo "[valgrind] NO se pudo preparar (se continuara sin cachegrind)"
    fi
fi

echo ""
echo "Herramientas en $TOOLS:"
du -sh "$TOOLS" 2>/dev/null || true
echo ""
echo "Para usar valgrind manualmente:"
echo "  export VALGRIND_LIB=$TOOLS/root/usr/libexec/valgrind"
echo "  $TOOLS/root/usr/bin/valgrind --tool=cachegrind --cache-sim=yes ./prog"
