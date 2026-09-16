# Primera Entrega: Versión Inicial del Programa

Para esta primera entrega se desarrolló un programa en lenguaje C cuyo propósito es realizar la multiplicación de dos matrices cuadradas de tamaño `N × N`. Esta implementación corresponde a una versión inicial que servirá como punto de partida para las diferentes modificaciones, optimizaciones y técnicas de computación de alto rendimiento que se aplicarán posteriormente durante el desarrollo del curso.

---

## Características Principales

* **Parámetros por línea de comandos:** El programa fue diseñado para recibir mediante parámetros de línea de comandos el tamaño de las matrices (`N`) y un valor máximo para los números aleatorios que serán utilizados para llenar sus elementos. De esta manera, la ejecución no requiere interacción del usuario mediante teclado y permite modificar fácilmente el tamaño de las matrices y los valores en cada ejecución.
* **Gestión dinámica de memoria:** Las matrices se manejan utilizando memoria dinámica. Se reservan espacios independientes para las dos matrices de entrada y para la matriz de resultado. Además, se verifica que la memoria haya sido reservada correctamente y, al finalizar la ejecución, se libera mediante `free()`.
* **Generación de datos aleatorios:** Los valores de las matrices de entrada son enteros positivos generados aleatoriamente. El programa permite establecer un valor máximo para estos números, con el objetivo de controlar los valores utilizados durante la operación y reducir el riesgo de desbordamiento de los tipos enteros.
* **Algoritmo de multiplicación:** La multiplicación se realiza mediante tres ciclos anidados que recorren las filas y columnas de las matrices. Para cada posición de la matriz resultado se calculan los productos correspondientes entre los elementos de una fila de la primera matriz y una columna de la segunda matriz, acumulando los resultados.
* **Salida de ejecución:** No se muestran las matrices completas en pantalla, debido a que el programa está pensado para trabajar con tamaños relativamente grandes. En su lugar, al finalizar se informa que la multiplicación fue completada y se muestran los parámetros principales utilizados durante la ejecución.

---

## Objetivo y Propósito

El objetivo de esta primera versión no es todavía aplicar técnicas de optimización o paralelización, sino establecer una **implementación base y funcional** de la multiplicación de matrices. 

Esta versión permitirá posteriormente comparar los cambios realizados mediante diferentes técnicas de computación de alto rendimiento y analizar cómo dichas modificaciones afectan el funcionamiento y el rendimiento del programa. También se mantuvo esta versión como una referencia inicial dentro del repositorio del proyecto, de manera que las modificaciones posteriores puedan ser identificadas y comparadas con respecto a la implementación original.