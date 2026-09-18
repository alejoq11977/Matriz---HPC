# Segunda entrega: medición del tiempo de ejecución

En esta segunda versión del proyecto se mantuvo el programa original de multiplicación de matrices y se incorporó la medición del tiempo empleado exclusivamente en la operación de multiplicación. El objetivo fue comenzar a analizar el rendimiento del programa y establecer una medida que posteriormente pueda utilizarse para comparar las diferentes versiones y técnicas que se desarrollen durante el curso.

La medición se realizó únicamente alrededor de los tres ciclos `for` anidados responsables de la multiplicación de las matrices. De esta manera, la generación de los valores aleatorios, la reserva de memoria, la impresión de resultados y la liberación de memoria no hacen parte del tiempo medido.

Para experimentar con diferentes mecanismos de medición, se crearon tres archivos `.c`. Los tres contienen esencialmente la misma implementación de la multiplicación de matrices, pero utilizan diferentes funciones para obtener el tiempo. Mantenerlos en archivos separados permite comparar las alternativas sin modificar o reemplazar las implementaciones entre sí.

---

## Métodos utilizados

* **`matriz_clock.c`**  
  Esta versión utiliza la función `clock()`, perteneciente a la biblioteca estándar de C mediante `<time.h>`. Esta función mide el tiempo de CPU utilizado por el programa, por lo que no debe confundirse directamente con el tiempo real transcurrido desde el inicio hasta el final de la operación.

* **`matriz_timespec.c`**  
  Esta versión utiliza `timespec_get()` con `TIME_UTC`, también mediante la biblioteca estándar de C. En este caso se obtiene un valor de tiempo asociado al reloj de tiempo real del sistema, que permite calcular cuánto tiempo transcurrió entre el inicio y el final de la multiplicación.

* **`matriz_monotonic.c`**  
  Esta versión utiliza `clock_gettime()` con `CLOCK_MONOTONIC`. Esta función corresponde a una interfaz POSIX disponible en Linux y permite consultar un reloj monotónico, diseñado para medir el tiempo transcurrido sin depender de modificaciones que puedan hacerse sobre la hora del sistema. Por esta razón, resulta especialmente interesante para mediciones de duración de una operación.

---

## Pruebas realizadas

Las tres versiones fueron compiladas y ejecutadas utilizando los mismos parámetros para poder realizar una comparación inicial. Se utilizaron matrices de $1000 \times 1000$ y valores aleatorios entre 1 y 10.

En la primera ejecución se obtuvieron los siguientes tiempos:

| Método | Tiempo |
| :--- | :--- |
| `clock()` | 2.575131 s |
| `timespec_get()` | 2.692591016 s |
| `CLOCK_MONOTONIC` | 2.669110611 s |

Posteriormente se realizó una segunda ejecución con los mismos parámetros:

| Método | Tiempo |
| :--- | :--- |
| `clock()` | 2.567447 s |
| `timespec_get()` | 2.770594437 s |
| `CLOCK_MONOTONIC` | 2.745318825 s |

Los resultados muestran que las mediciones no son exactamente iguales entre ejecuciones, aun cuando se utilizaron los mismos tamaños y valores máximos. Esto evidencia que existen variaciones naturales en el tiempo de ejecución y que una sola medición no debería utilizarse por sí misma para establecer una conclusión definitiva.

---

## Propósito de esta experimentación

En esta etapa no se busca determinar todavía cuál de las tres alternativas es definitivamente la mejor. El propósito es conocer y experimentar con diferentes mecanismos de medición del tiempo y observar las diferencias que producen al medir la misma operación.

La existencia de tres archivos permite conservar las tres implementaciones y utilizarlas como referencia para el análisis posterior. Más adelante, cuando se introduzcan nuevas técnicas de optimización o paralelización, estas mediciones podrán servir como punto de comparación para determinar cómo cambia el rendimiento de la multiplicación de matrices.

Esta versión, por tanto, constituye una primera aproximación experimental a la medición del rendimiento del programa, manteniendo sin cambios el algoritmo de multiplicación utilizado en la versión inicial.