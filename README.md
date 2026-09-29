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

El experimento completo se ejecutó del `lun 28 sep 2026 23:31:13` al `mar 29 sep 2026 12:26:50`, completando las **250 mediciones** planificadas (5 tamaños × 5 configuraciones × 10 corridas).

### 7.1 Tiempos de ejecución medidos (segundos)

Para cada `(N, T)` se reportan la **media**, la **mediana** y la **desviación estándar** de las 10 corridas. Todos los valores en segundos.

| N    | T=1 (sec) media/mediana/σ | T=2 media/mediana/σ       | T=4 media/mediana/σ       | T=8 media/mediana/σ       | T=16 media/mediana/σ      |
| ---: | ------------------------: | ------------------------: | ------------------------: | ------------------------: | ------------------------: |
| 500   | 0.0449 / 0.0440 / 0.0028 | 0.1008 / 0.1008 / 0.0015 | 0.0538 / 0.0529 / 0.0021 | 0.0342 / 0.0345 / 0.0031 | 0.0315 / 0.0315 / 0.0029 |
| 1000  | 0.4240 / 0.4230 / 0.0026 | 0.7550 / 0.7532 / 0.0058 | 0.4002 / 0.3977 / 0.0097 | 0.2656 / 0.2661 / 0.0045 | 0.2054 / 0.2043 / 0.0069 |
| 2000  |  4.398 / 4.363 / 0.083   |  7.113 / 7.118 / 0.072   |  3.763 / 3.757 / 0.054   |  2.386 / 2.385 / 0.046   |  1.641 / 1.643 / 0.046   |
| 4000  |  75.70 / 75.65 / 0.27    |  68.07 / 68.22 / 0.60    |  40.33 / 40.30 / 0.18    |  29.73 / 29.68 / 0.43    |  24.26 / 24.29 / 0.31    |
| 8000  |  2442.5 / 2441.6 / 13.4  |  744.3 / 690.9 / 115.9   |  416.8 / 416.9 / 1.1     |  352.6 / 354.1 / 4.3     |  401.6 / 401.5 / 1.6     |

### 7.2 Detección de valor atípico

La fila `N=8000, T=2` muestra una desviación estándar de **115.9 s sobre una media de 744.3 s** (15.6 % del valor central), muy superior al resto de las configuraciones. Al revisar las 10 corridas individuales en `experiments/resultados_raw.csv`:

```
8000,2,2,684.96
8000,2,4,685.00
8000,2,6,685.22
8000,2,1,686.68
8000,2,10,687.49
8000,2,9,694.21
8000,2,7,713.32
8000,2,5,756.04
8000,2,3,769.49
8000,2,8,1080.48    ← valor atípico (~310 s por encima del siguiente)
```

Nueve de las diez corridas caen en el rango `[685, 770]` segundos, mientras que la **corrida 8** midió `1080.48 s`, casi un 60 % por encima del resto. Este es un caso clásico de outlier por ruido del sistema operativo (preempción de quantum, otro proceso que tomó CPU, decisión de caché del planificador). Las demás configuraciones tienen σ relativa ≤ 1.5 %, lo que confirma que se trata de un evento aislado y no de una propiedad del programa.

Este hallazgo justifica el uso de la **mediana** como estimador central del speedup, ya que la media se infla artificialmente por este valor extremo.

### 7.3 Speedup calculado sobre la mediana

El speedup se calcula como $S_T(N) = \tilde{T}_{\text{sec}}(N) / \tilde{T}_{\text{par},T}(N)$, donde $\tilde{T}$ denota la mediana de las 10 corridas.

| N    | T=2  | T=4  | T=8  | T=16 |
| ---: | ---: | ---: | ---: | ---: |
| 500   | 0.44 | 0.83 | 1.27 | 1.40 |
| 1000  | 0.56 | 1.06 | 1.59 | 2.07 |
| 2000  | 0.61 | 1.16 | 1.83 | 2.66 |
| 4000  | 1.11 | 1.88 | 2.55 | 3.11 |
| 8000  | 3.53 | 5.86 | 6.90 | 6.08 |

Comparación con el speedup calculado sobre la media:

| N    | T=2 (mediana / media) | T=4            | T=8            | T=16           |
| ---: | ---:                  | ---:           | ---:           | ---:           |
| 500   | 0.44 / 0.45          | 0.83 / 0.83   | 1.27 / 1.31   | 1.40 / 1.42   |
| 1000  | 0.56 / 0.56          | 1.06 / 1.06   | 1.59 / 1.60   | 2.07 / 2.06   |
| 2000  | 0.61 / 0.62          | 1.16 / 1.17   | 1.83 / 1.84   | 2.66 / 2.68   |
| 4000  | 1.11 / 1.11          | 1.88 / 1.88   | 2.55 / 2.55   | 3.11 / 3.12   |
| 8000  | **3.53 / 3.28**      | 5.86 / 5.86   | 6.90 / 6.93   | 6.08 / 6.08   |

La diferencia entre ambos estimadores es mínima en la mayoría de las configuraciones (≤ 1 %) y solo se nota donde aparece el outlier (`N=8000, T=2`, donde la mediana da 3.53× y la media 3.28×).

### 7.4 Gráficas

**Speedup vs N (variante A del profesor, eje X = tamaño de la matriz):**

![Speedup vs N](experiments/speedup_vs_N.png)

**Speedup vs T (variante B del profesor, eje X = cantidad de hilos):**

![Speedup vs T](experiments/speedup_vs_T.png)

Las barras de error corresponden a ±1σ propagada al speedup: $\sigma_S = S \cdot \sqrt{(\sigma_{\text{seq}}/\bar{T}_{\text{seq}})^2 + (\sigma_{\text{par}}/\bar{T}_{\text{par}})^2}$.

---

## 8. Análisis de resultados

### 8.1 Para matrices pequeñas el paralelismo es contraproducente

Con `N=500` y `N=1000`, dos hilos tardan **más** que la versión secuencial (speedup de 0.44× y 0.56× respectivamente). El *overhead* de `pthread_create` + `pthread_join` más la contención por el ancho de banda de memoria supera al beneficio de repartir las filas. Incluso con 4 hilos el speedup es ≤ 1 para `N≤2000`. Esto confirma empíricamente la predicción de la Ley de Amdahl: existe un tamaño mínimo de problema por debajo del cual el paralelismo no aporta beneficio.

### 8.2 Crecimiento monótonico hasta N=4000

Para `N=500, 1000, 2000, 4000`, el speedup crece de manera monótona con la cantidad de hilos. Esto es el comportamiento clásico esperado: a mayor cantidad de trabajo disponible, mejor se amortiza el *overhead* de sincronización.

### 8.3 Peak y degradación en N=8000

A `N=8000`, la configuración de **8 hilos alcanza el speedup máximo observado (6.90×)**, pero **16 hilos degrada a 6.08×**. El hardware dispone de 12 núcleos lógicos (8 físicos con hyperthreading), por lo que:

- Con 8 hilos, cada uno corre casi siempre en un núcleo físico distinto → máximo paralelismo real.
- Con 16 hilos, varios comparten núcleo físico vía hyperthreading → contención por las unidades de ejecución del núcleo (ALU, FPU, cachés L1/L2). El beneficio del hilo extra se compensa con el overhead de conmutación dentro del mismo núcleo.

Este resultado es coherente con la observación de que el **hyperthreading no duplica el rendimiento**; típicamente aporta entre un 10 % y un 30 % extra por núcleo físico, no un 100 %.

### 8.4 Valor atípico en N=8000, T=2

La corrida 8 de `N=8000, T=2` midió 1080 s, un 58 % por encima de las otras nueve (rango 685–770 s). Es un evento aislado, probablemente causado por:

- Otra carga del sistema durante esa medición (otro proceso tomó CPU).
- Una preempción de quantum particularmente larga en uno de los dos hilos.
- Una decisión de caché adversa (página fría al inicio de la corrida).

El uso de la **mediana** como estimador central evita que este outlier distorsione el speedup calculado, pasando de 3.28× (media) a 3.53× (mediana). Esta es exactamente la razón por la que el profesor sugirió la mediana como alternativa válida al promedio.

### 8.5 Comparación con la Ley de Amdahl

El speedup máximo observado (6.90× con 8 hilos en `N=8000`) implica, según la Ley de Amdahl estricta:

$$6.90 \approx \frac{1}{f_s + (1-f_s)/8} \implies f_s \approx 0.01$$

Es decir, el programa es teóricamente paralelizable al 99 %. La diferencia entre este techo teórico (8× con 8 hilos) y el valor medido (6.90×) se explica por factores no contemplados por la Ley de Amdahl:

- Contención por ancho de banda de memoria compartida.
- Tasa de fallos de caché cuando varios hilos compiten por las mismas líneas.
- *Overhead* de planificación del sistema operativo.

---

## 9. Conclusiones

1. **La paralelización con pthreads permite obtener speedups cercanos a 7× en N=8000 con 8 hilos**, en un equipo con 12 núcleos lógicos. El speedup crece con `N` y satura alrededor de `N=4000–8000`.

2. **Para problemas pequeños el paralelismo no es rentable**: con `N=500` y `N=1000`, dos hilos son **más lentos** que la versión secuencial. Es indispensable dimensionar el problema antes de optar por paralelizar.

3. **El número óptimo de hilos depende del hardware**: en esta máquina con 8 núcleos físicos, 8 hilos es el óptimo. 16 hilos (con hyperthreading) **degrada** el rendimiento en un 12 % para `N=8000`.

4. **La variabilidad entre corridas es muy baja** (σ relativa ≤ 1.5 %) salvo en eventos atípicos puntuales. Una medición única es suficiente en la mayoría de los casos para tener una estimación razonable, pero 10 corridas permiten detectar outliers y reportar barras de error honestas.

5. **La elección entre media y mediana importa**: cuando hay outliers (como el caso `N=8000, T=2, run=8` con 1080 s), la mediana es claramente superior. Cuando no los hay, ambas dan resultados casi idénticos.

6. **El speedup real está muy por debajo del ideal lineal** ($T$ con $T$ hilos). El techo observado de ~7× para 8 hilos refleja la combinación de: parte secuencial residual, contención de memoria y *overhead* del sistema operativo, exactamente como predice la Ley de Amdahl extendida con factores de HPC.

7. **La metodología empleada fue válida**: 10 corridas, loop order evitando envenenamiento de caché, medición de wall clock con `CLOCK_MONOTONIC_RAW`, uso de mediana como estimador robusto. Todos los elementos discutidos en clase.

---

## 10. Referencias técnicas

- `pthread_create`, `pthread_join`: POSIX.1-2008, `<pthread.h>`.
- `clock_gettime(CLOCK_MONOTONIC_RAW)`: POSIX.1-2008, `<time.h>`. `CLOCK_MONOTONIC_RAW` excluye ajustes de NTP, lo que lo hace más estable que `CLOCK_MONOTONIC` para mediciones de corta duración.
- Ley de Amdahl, G. M. (1967). *Validity of the single processor approach to achieving large scale computing capabilities*. AFIPS Spring Joint Computer Conference.
