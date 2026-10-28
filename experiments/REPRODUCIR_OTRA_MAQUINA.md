# Reproducir el experimento en la segunda máquina

Guía paso a paso para ejecutar el **benchmark** y el **perfilado** en el otro
equipo con Linux, de forma que los resultados sean comparables con los de esta
máquina.

---

## 0. Qué hay que llevar

El repositorio completo, en la rama `caso-de-estudio-2-openmp`. Opciones:

- **Clonar desde GitHub** (recomendado):
  ```bash
  git clone -b caso-de-estudio-2-openmp git@github.com:alejoq11977/Matriz---HPC.git
  cd Matriz---HPC
  ```
- **Copiar la carpeta** por USB / red a la otra máquina.

---

## 1. Requisitos en la máquina nueva

```bash
# Compilador
gcc --version          # debe existir

# Herramientas de profiling (GProf viene con gcc; valgrind se descarga solo)
gprof --version        # debe existir

# Python para las graficas
python3 --version
python3 -c "import matplotlib"   # si falla: pip install matplotlib
```

**No hace falta `sudo` ni instalar nada a mano.** El script
`experiments/bootstrap_tools.sh` baja `valgrind` y `time` como usuario normal
(usando `apt-get download` + `dpkg-deb -x`) y los deja en `.tools/`.

Si el otro equipo no tiene `apt` (ej. es Fedora/Arch), el script simplemente
avisa que no pudo prepararlos y el perfilado de cache queda omitido. En ese
caso instalalos con el gestor de paquetes de esa distro:

```bash
# Fedora / RHEL
sudo dnf install valgrind time
# Arch
sudo pacman -S valgrind time
```

---

## 2. Benchmark en la máquina nueva (OBLIGATORIO)

Este es el comando principal. Corre el barrido completo de la multiplicación
con OpenMP y captura toda la información del hardware:

```bash
cd Matriz---HPC
bash experiments/bench.sh MaquinaB 500 1000 2000 4000
```

**Qué hace:**

1. Compila `src/matriz_monotonic_openmp.c` con `-Wall -O2 -fopenmp` (exactamente
   los mismos flags que la máquina A).
2. Captura el hardware en `experiments/resultados/benchmark/MaquinaB_hardware.txt`:
   CPU, modelo, núcleos lógicos, cachés, RAM, kernel, distribución, versión de gcc.
3. Corre **5 valores de T** (1, 2, 4, 8, 16) × **4 valores de N** (500, 1000,
   2000, 4000) × **10 iteraciones** = **200 mediciones**.
4. Escribe las corridas crudas en `experiments/resultados/benchmark/MaquinaB_raw.csv`.

**Duración estimada**: entre 15 y 40 minutos según el equipo. Con `N=4000` la
matriz de resultado ocupa 64 MB por matriz (192 MB el total), así que
asegurate de tener al menos 1 GB de RAM libre.

### Atajos si tenés poco tiempo

```bash
# Solo N=500 y 1000 (5 minutos)
bash experiments/bench.sh MaquinaB 500 1000

# Menos iteraciones (menos estadísticamente sólido, pero rápido)
ITERACIONES=3 bash experiments/bench.sh MaquinaB 500 1000 2000 4000
```

---

## 3. Perfilado en la máquina nueva (recomendado)

```bash
cd Matriz---HPC
bash experiments/perfilar.sh
```

Genera en `experiments/resultados/perfilado/`:

| Archivo | Contenido |
|---|---|
| `gprof_secuencial.txt`, `gprof_transpuesto.txt`, `gprof_openmp.txt` | Perfil de CPU (GProf) |
| `cachegrind_*.txt` | Métricas de cache: D1 misses, miss rate, LL misses |
| `rss.csv` | Footprint de memoria (max RSS) por variante |
| `resumen_perfilado.csv` | Tabla consolidada |
| `cache_miss_rate.png`, `footprint_memoria.png` | Gráficas |
| `hardware.txt` | Info del equipo |

El perfilado con Cachegrind es **muy lento** (simula la cache instrucción a
instrucción). Usa `N=500` (el default). Para más N:

```bash
N_PERFILADO=1000 bash experiments/perfilar.sh    # tarda mucho más
```

---

## 4. Traerse los resultados

Los archivos que hay que copiar de vuelta al equipo principal son **todos** los
de `experiments/resultados/benchmark/` y `experiments/resultados/perfilado/`:

```bash
# Desde la maquina nueva, por scp (ajustar usuario@ip)
scp -r experiments/resultados/benchmark/*  usuario@IP_PRINCIPAL:~/U/HPC/mult_matriz/experiments/resultados/benchmark/
scp -r experiments/resultados/perfilado/*  usuario@IP_PRINCIPAL:~/U/HPC/mult_matriz/experiments/resultados/perfilado/
```

Alternativa: pasarlos por USB o comprimirlos:

```bash
tar czf benchmark.tar.gz experiments/resultados/benchmark experiments/resultados/perfilado
```

**No** copies la carpeta `.tools/` (83 MB de binarios que no sirven en otra
máquina).

---

## 5. Consolidar en la máquina principal

```bash
cd mult_matriz
python3 experiments/plot_benchmark.py
python3 experiments/plot_perfilado.py
```

`plot_benchmark.py` detecta automáticamente todos los archivos `*_raw.csv` y
genera:

- `experiments/resultados/benchmark/resumen_maquinas.csv` — tabla con el T
  óptimo, el speedup interno y el speedup cruzado entre máquinas
- `experiments/resultados/benchmark/comparativa_hardware.csv` — tabla de
  hardware lado a lado
- `experiments/resultados/benchmark/benchmark_maquinas.png` — speedup por máquina
- `experiments/resultados/benchmark/benchmark_tiempos.png` — tiempos absolutos

**Importante**: la etiqueta que le pases a `bench.sh` es la que aparece en las
tablas y gráficas. Usá la misma que en la máquina A para que las comparativas
sean legibles (en este repo la de esta máquina quedó como `MaquinaA`).

---

## 6. Checklist antes de medir

En la máquina nueva, antes de correr:

- [ ] Cerrar el navegador y todas las aplicaciones (el ruido del sistema
      afecta las mediciones, especialmente las chicas).
- [ ] Si el equipo está en modo batería, conectarlo a la corriente (los
      procesadores de los portátiles bajan la frecuencia).
- [ ] Verificar que no hay otros usuarios ni procesos pesados corriendo.
- [ ] Verificar la temperatura: si el equipo está muy caliente, las térmicas
      del CPU van a hacer bajar el rendimiento.

---

## 7. Resumen de una línea

```bash
git clone -b caso-de-estudio-2-openmp git@github.com:alejoq11977/Matriz---HPC.git && \
cd Matriz---HPC && \
bash experiments/bench.sh MaquinaB 500 1000 2000 4000 && \
bash experiments/perfilar.sh
```

Después: copiar `experiments/resultados/benchmark/` y
`experiments/resultados/perfilado/` de vuelta, y correr
`python3 experiments/plot_benchmark.py` en la máquina principal.
