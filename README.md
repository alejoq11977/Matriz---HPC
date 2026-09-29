# Tercera entrega: paralelización con pthreads

## Resumen

En esta tercera entrega se extendió el programa de multiplicación de matrices para incorporar una versión concurrente/paralela implementada con **POSIX Threads (pthreads)** en C. La versión secuencial original — basada en el reloj monotónico `CLOCK_MONOTONIC_RAW` — se conserva como referencia y se somete a un experimento sistemático en el que se varía el tamaño de la matriz (`N ∈ {500, 1000, 2000, 4000, 8000}`) y la cantidad de hilos (`T ∈ {2, 4, 8, 16}`), repitiendo cada configuración 10 veces para obtener promedios estadísticamente significativos. A partir de los tiempos medios se calcula el *speedup* y se analiza experimentalmente el comportamiento del programa bajo paralelismo real.

---

## 1. Marco teórico

### 1.1 Concurrencia y paralelismo

Un **proceso** es una unidad de ejecución que posee, entre otros recursos, su propio espacio de direcciones. Un **hilo** (*thread*) es un flujo de ejecución que corre dentro de un proceso y comparte con los demás hilos del mismo proceso la memoria, los archivos abiertos y otros recursos del proceso; cada hilo tiene, en cambio, su propia pila y sus propios registros.

- **Concurrencia** se refiere a la propiedad de un programa de componerse de varias tareas que pueden progresar solapadas en el tiempo, sin implicar que avancen simultáneamente.
- **Paralelismo** se refiere a la ejecución **simultánea** de varias tareas sobre distintos núcleos del procesador.

Un programa concurrente implementado con pthreads puede aprovechar paralelismo real cuando se ejecuta en una máquina con varios núcleos; en una máquina de un solo núcleo, los hilos se intercalan y el programa es concurrente pero no paralelo.

### 1.2 POSIX Threads (pthreads)

`pthreads` es la API estándar POSIX para crear y manipular hilos en sistemas tipo Unix. Su cabecera es `<pthread.h>` y los programas que la usan deben enlazarse con la biblioteca pthread mediante el flag `-lpthread` en `gcc`. Las primitivas básicas utilizadas en este trabajo son:

| Función | Propósito |
|---|---|
| `pthread_create(&tid, NULL, fn, arg)` | crea un nuevo hilo que ejecuta `fn(arg)`; retorna inmediatamente |
| `pthread_join(tid, NULL)` | bloquea al hilo que llama hasta que `tid` termine |
| `pthread_t` | tipo opaco que identifica a un hilo creado |

### 1.3 Wall clock, tiempo de CPU y tiempo de sistema

En Unix, la salida del comando `time programa` desglosa el tiempo consumido en:

- **Wall clock** (tiempo transcurrido total): tiempo real desde que arranca hasta que termina. Incluye quantum preemptions, esperas por E/S, y tiempo de otros procesos que compartieron el CPU.
- **Tiempo de CPU**: tiempo que la CPU pasó realmente ejecutando nuestro proceso. Se subdivide en:
  - **Tiempo de usuario**: tiempo que la CPU pasó en código de nuestro programa.
  - **Tiempo del sistema**: tiempo que la CPU pasó en el kernel atendiendo llamadas al sistema de nuestro proceso.

El profesor de la materia indicó explícitamente que **la métrica correcta para evaluar rendimiento de una aplicación es el wall clock**, porque refleja lo que el usuario percibe como "cuánto tardó". Las otras dos métricas son útiles para *profiling* interno pero no para comparar rendimiento global.

### 1.4 Mecanismos disponibles en C para medir tiempo

| Mecanismo | Qué cuenta | ¿Wall clock? |
|---|---|---|
| `clock()` | CPU time (usuario + sistema) | ❌ No |
| `timespec_get(TIME_UTC)` | Wall clock, pero susceptible a saltos del reloj del sistema (NTP, cambios manuales) | ⚠️ Sí, pero frágil |
| `clock_gettime(CLOCK_MONOTONIC)` | Wall clock monotónico (no retrocede) | ✅ Sí |
| `clock_gettime(CLOCK_MONOTONIC_RAW)` | Igual al anterior, pero excluye ajustes finos de NTP | ✅ Sí, **el más preciso** |

En este proyecto se usa **`clock_gettime(CLOCK_MONOTONIC_RAW)`**, que es la opción recomendada en benchmarking HPC: es wall clock monotónico y no se ve afectado por las correcciones graduales que NTP aplica sobre el reloj del sistema.

### 1.5 Speedup y Ley de Amdahl

El *speedup* mide cuántas veces más rápida es la versión paralela respecto a la secuencial:

$$S_T(N) = \frac{T_{\text{secuencial}}(N)}{T_{\text{paralelo},\,T}(N)}$$

donde `T` es la cantidad de hilos. El speedup ideal es lineal: $S_T = T$. La **Ley de Amdahl** establece que el speedup está acotado por la fracción secuencial no paralelizable del programa:

$$S_T \le \frac{1}{f_s + \dfrac{1-f_s}{T}}$$

donde $f_s$ es la fracción del trabajo que no puede paralelizarse. En la práctica, además, aparecen otros factores que degradan el speedup: contención por ancho de banda de memoria, fallos de caché y sobrecarga de planificación del sistema operativo.

---

## 2. Diseño de la implementación

### 2.1 Estrategia de partición del trabajo

El programa paralelo reutiliza exactamente el mismo bucle triple anidado de la versión secuencial:

```c
for (int i = 0; i < N; i++)
  for (int j = 0; j < N; j++)
    for (int k = 0; k < N; k++)
      C[i*N + j] += A[i*N + k] * B[k*N + j];
```

La paralelización se hace **repartiendo filas de la matriz resultado `C`** entre los `T` hilos. Si $N$ es divisible por $T$, cada hilo recibe exactamente $N/T$ filas; si no lo es, los primeros $N \bmod T$ hilos reciben una fila extra para equilibrar la carga. Por ejemplo, con $N = 1000$ y $T = 4$ la partición es:

| Hilo | Filas asignadas (inclusivo, exclusivo) | Cantidad |
|---|---|---|
| 0 | [0, 250) | 250 |
| 1 | [250, 500) | 250 |
| 2 | [500, 750) | 250 |
| 3 | [750, 1000) | 250 |

### 2.2 Por qué no hace falta sincronización

Cada hilo escribe exclusivamente en su propio rango de filas de `C`, por lo que **no hay condición de carrera sobre `C`**. Los hilos leen simultáneamente las matrices `A` y `B`; la lectura concurrente sin escritura es segura y no requiere exclusión mutua. En consecuencia, el programa no utiliza mutex, barreras ni variables de condición; la única sincronización necesaria es el `pthread_join` final, que garantiza que el hilo principal espere a que todos los hilos terminen antes de continuar.

### 2.3 Medición del tiempo

Se utiliza `clock_gettime(CLOCK_MONOTONIC_RAW, ...)` con `struct timespec`. El intervalo medido en la versión paralela abarca explícitamente la creación de los hilos, el trabajo paralelo y el `pthread_join` — es decir, **se mide el wall clock total que tarda el usuario en obtener el resultado paralelo**, incluyendo el *overhead* real de utilizar múltiples hilos. Esto es coherente con la versión secuencial, que mide únicamente el trabajo de multiplicación.

### 2.4 Algoritmo del worker

La función `worker(args)` que ejecuta cada hilo es el triple bucle anidado original, sustituyendo `0` por `args->inicio` y `N` por `args->fin` en el bucle externo. Manteniendo el mismo cuerpo algorítmico se garantiza que las diferencias observadas entre la versión secuencial y la paralela se deban exclusivamente al particionamiento y a los hilos, y no a optimizaciones adicionales.

---

## 3. Estructura del proyecto

```
mult_matriz/
├── Makefile
├── README.md
├── .gitignore
├── src/                   # archivos .c con los main() de cada versión
│   ├── matriz_monotonic.c # versión secuencial (referencia)
│   └── matriz_pthreads.c  # versión paralela con pthreads
├── include/               # cabeceras públicas de los módulos
│   ├── memoria.h
│   ├── llenado.h
│   ├── tiempo_mult.h
│   └── pthread_mult.h
├── modules/               # implementaciones (.c) de los módulos
│   ├── memoria.c
│   ├── llenado.c
│   ├── tiempo_mult.c
│   └── pthread_mult.c
├── experiments/
│   ├── run.sh             # automatiza el experimento completo (resumible)
│   ├── aggregate.py       # calcula media, mediana, stddev por (N, T)
│   ├── plot.py            # genera las dos gráficas de speedup
│   ├── resultados_raw.csv # datos crudos (1 fila por corrida individual)
│   ├── resultados.csv     # datos agregados (1 fila por configuración)
│   ├── speedup_vs_N.png   # gráfica 1: speedup vs N, curvas por T
│   ├── speedup_vs_T.png   # gráfica 2: speedup vs T, curvas por N
│   └── speedup.png        # copia de la primera, para compatibilidad
└── bin/                   # binarios compilados (no versionados)
```

### 3.1 Tipos de archivo

- **`.c`**: implementación. Contiene el código que efectivamente realiza el trabajo.
- **`.h`**: cabecera. Contiene las **declaraciones** de funciones, tipos y constantes que otros archivos pueden usar. Es el "contrato público" del módulo.
- **`Makefile`**: script que define las reglas de compilación.
- **`.gitignore`**: lista de archivos y carpetas que el repositorio ignora (binarios, datos generados, gráficas).

### 3.2 Modularización

Ambas versiones comparten los módulos `memoria` y `llenado`, lo que evita duplicación:

- **`memoria`** (`modules/memoria.c`, `include/memoria.h`): calcula `N*N`, reserva memoria para las tres matrices con `malloc` y verifica que las reservas se realizaron correctamente. Devuelve una struct `Matrices` con los tres punteros y el total de elementos.
- **`llenado`** (`modules/llenado.c`, `include/llenado.h`): inicializa la semilla del generador de números aleatorios (`srand(time(NULL))`) y llena `A` y `B` con valores aleatorios en `[1, valor_maximo]`, además de poner `C` en cero.
- **`tiempo_mult`** (`modules/tiempo_mult.c`, `include/tiempo_mult.h`): mide y ejecuta la multiplicación secuencial con `CLOCK_MONOTONIC_RAW`.
- **`pthread_mult`** (`modules/pthread_mult.c`, `include/pthread_mult.h`): mide y ejecuta la multiplicación paralela con pthreads y `CLOCK_MONOTONIC_RAW`.

---

## 4. Compilación y ejecución

Toda la gestión del proyecto se realiza desde la raíz del repositorio mediante `make`.

| Comando | Efecto |
|---|---|
| `make` o `make all` | Compila ambas versiones; deja los binarios en `bin/`. |
| `make run <N> <valor_maximo>` | Compila (si hace falta) y ejecuta la versión **secuencial**. |
| `make run_par <N> <valor_maximo> <num_hilos>` | Compila (si hace falta) y ejecuta la versión **paralela**. |
| `make clean` | Elimina los binarios generados. |

Ejemplos puntuales:

```bash
make clean
make all
make run 500 10           # secuencial
make run_par 500 10 4     # paralelo con 4 hilos
```

`make run_par` enlaza con `-lpthread` automáticamente gracias a la regla correspondiente del Makefile.

---

## 5. Diseño experimental

### 5.1 Hardware y entorno

Las mediciones se realizaron sobre un equipo con las siguientes características:

- **CPU**: Intel Core i5-12450HX (12.ª generación).
- **Núcleos lógicos disponibles**: 12 (8 núcleos físicos con *hyperthreading* activo).
- **Sistema operativo**: Linux.
- **Compilador**: `gcc` con flags `-Wall -Wextra -O2`.

### 5.2 Variables y métricas

- **Variable independiente 1 — tamaño de la matriz `N`**: 500, 1000, 2000, 4000 y 8000 (incremento exponencial para cubrir un amplio espectro del comportamiento).
- **Variable independiente 2 — número de hilos `T`**: 1 (secuencial), 2, 4, 8 y 16 (incremento cuadrático).
- **Variable dependiente — tiempo de ejecución**: medido en segundos con `clock_gettime(CLOCK_MONOTONIC_RAW)`.
- **Métrica derivada — speedup**: $S_T = \bar{T}_{\text{sec}} / \bar{T}_{\text{par}}$, calculado sobre las medias aritméticas de las 10 corridas.

En total se realizan **250 mediciones**: 5 tamaños × 5 configuraciones × 10 corridas.

### 5.3 Metodología estadística: 10 corridas por configuración

Para cada combinación `(N, T)` se ejecutan **10 corridas independientes** y se reporta:

- **Media aritmética** ($\bar{T}$) — medida central principal del rendimiento.
- **Mediana** — útil para detectar asimetrías o valores atípicos.
- **Desviación estándar** ($\sigma$) — cuantifica la variabilidad entre corridas.

Esta repetición es necesaria porque una sola medición puede estar contaminada por ruido del sistema operativo (quantum preemptions, otros procesos, decisiones de caché). Como explicó el profesor en clase, una medición única no es estadísticamente válida; el promedio estadístico de varias corridas es la forma estándar de aislar ese ruido.

### 5.4 Orden de los `for` en el script y envenenamiento de caché

Una decisión clave del script `experiments/run.sh` es el **orden de los bucles**:

```bash
for run_id in {1..10}; do            # outer = repeticiones
    for n in "${TAMANOS[@]}"; do     # inner = tamaños
        ...
    done
done
```

Es decir: para cada corrida (`run_id = 1, 2, ..., 10`), se recorren **todos los tamaños** antes de pasar a la siguiente repetición.

La razón, explicada por el profesor, es que si invirtiéramos el orden y corrieramos las 10 repeticiones de `N=500` consecutivamente, los datos quedarían *calientes* en las cachés L1/L2 del procesador y el sistema operativo "sería perezoso" de volver a RAM a regenerarlos. El resultado sería una medición **irrealmente rápida** por contaminación de caché. Al intercalar tamaños, cada corrida se ve forzada a traer datos nuevos desde RAM, lo que produce mediciones más realistas.

Adicionalmente, el script inserta un `sleep 1` entre mediciones para garantizar que la semilla `srand(time(NULL))` cambie entre corridas, evitando que dos corridas consecutivas generen exactamente las mismas matrices.

### 5.5 Automatización y resumibilidad

El script `experiments/run.sh` implementa las siguientes características:

- **Loop order profesor**: outer = repeticiones, inner = tamaños.
- **Append inmediato**: cada medición individual se escribe al CSV en el momento en que termina. Si el proceso se interrumpe (Ctrl+C, `kill`, corte de energía), los datos ya escritos no se pierden.
- **Resumible**: al re-ejecutarse, el script detecta qué configuraciones `(N, T)` ya tienen 10 corridas completas y las salta. Las que tienen corridas parciales (entre 1 y 9) se truncan y rehacen desde cero.
- **Agregación progresiva**: al final de cada bloque de `T`, se recalculan las estadísticas. Al final del experimento se regenera `resultados.csv`.

### 5.6 Gráficas generadas

El script `experiments/plot.py` genera **dos variantes** de gráfica, ambas con barras de error (±1 σ propagada al speedup):

1. **`speedup_vs_N.png`** — eje X = tamaño de la matriz `N`, una curva por cada cantidad de hilos `T`. Variante A del profesor.
2. **`speedup_vs_T.png`** — eje X = cantidad de hilos `T`, una curva por cada tamaño `N`. Variante B del profesor.

Ambas son análisis válidos y muestran aspectos complementarios del speedup.

---

## 6. Cómo reproducir el experimento

### 6.1 Compilar

```bash
make clean
make all
```

### 6.2 Arrancar el experimento en background

El experimento completo (250 mediciones) puede tardar **varias horas** dependiendo del hardware. Se recomienda lanzarlo en background con `nohup` para que sobreviva al cierre de la terminal:

```bash
cd /home/Alejandro/U/HPC/mult_matriz
nohup bash experiments/run.sh > experiments/run.log 2>&1 &
```

### 6.3 Monitorear progreso

```bash
tail -f experiments/run.log                  # últimas líneas en tiempo real
wc -l experiments/resultados_raw.csv        # cuántas corridas lleva
awk -F, 'NR>1 {print $1","$2}' experiments/resultados_raw.csv | sort -u | wc -l
                                              # cuántos (N, T) ya están completos
```

### 6.4 Detener y reanudar

Para detener:

```bash
pkill -f "bash experiments/run.sh"
```

Para reanudar (los datos previos ya quedaron escritos):

```bash
cd /home/Alejandro/U/HPC/mult_matriz
nohup bash experiments/run.sh > experiments/run.log 2>&1 &
```

El script detecta automáticamente las corridas ya realizadas y continúa donde se detuvo.

### 6.5 Cuando termine

Una vez que el script haya completado las 250 mediciones (puede verse en `experiments/run.log` con un mensaje de fin), ejecutar:

```bash
python3 experiments/aggregate.py            # por si no se actualizó al final
python3 experiments/plot.py                 # genera las dos PNG
cat experiments/resultados.csv              # tabla con media, mediana, stddev
```

---

## 7. Resultados

> **Estado**: esta sección se actualizará con las tablas y el análisis una vez que el experimento completo haya finalizado. Los archivos `experiments/resultados.csv`, `experiments/speedup_vs_N.png` y `experiments/speedup_vs_T.png` se regeneran al correr `experiments/plot.py`.
>
> Mientras el experimento no haya terminado, se pueden ver los datos parciales en `experiments/resultados_raw.csv` (1 fila por medición individual) y los agregados parciales en `experiments/resultados.csv`.

---

## 8. Conclusiones metodológicas

Independientemente de los valores numéricos que arroje el experimento, el trabajo realizado establece las siguientes conclusiones metodológicas:

1. **Wall clock es la métrica correcta**. Se descartó `clock()` (mide CPU time), `timespec_get(TIME_UTC)` (wall clock frágil) y se eligió `clock_gettime(CLOCK_MONOTONIC_RAW)` (wall clock monotónico de alta precisión).
2. **Una sola medición no es válida estadísticamente**. Se realizan 10 corridas por configuración y se reporta media, mediana y desviación estándar.
3. **El orden de los bucles afecta la validez experimental**. Intercalar tamaños entre repeticiones evita el envenenamiento de caché que produciría mediciones optimistas.
4. **El script debe ser resumible**. Con 250 mediciones que pueden tardar horas, la capacidad de pausar y reanudar es esencial.
5. **Ambas variantes de gráfica (X=N y X=T) son válidas** y muestran aspectos complementarios del speedup, como explicó el profesor.

---

## 9. Referencias técnicas

- `pthread_create`, `pthread_join`: POSIX.1-2008, `<pthread.h>`.
- `clock_gettime(CLOCK_MONOTONIC_RAW)`: POSIX.1-2008, `<time.h>`. `CLOCK_MONOTONIC_RAW` excluye ajustes de NTP, lo que lo hace más estable que `CLOCK_MONOTONIC` para mediciones de corta duración.
- Ley de Amdahl, G. M. (1967). *Validity of the single processor approach to achieving large scale computing capabilities*. AFIPS Spring Joint Computer Conference.
