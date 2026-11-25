# Importancia por permutación agrupada de los Ridge originales

En la validación de 2023, los dos Ridge dependen principalmente del PM10 reciente y sus retardos. Alterar conjuntamente esas entradas aumenta el MAE medio aproximadamente 1,924 µg/m³ en Madrid y 1,721 en Barcelona. Las medias y la variabilidad también aportan señal. El resultado describe sensibilidad de modelos congelados ante entradas artificialmente alteradas; no identifica efectos causales ni porcentajes de contribución.

Se conservan las cohortes originales de validación: 1.039 casos en Madrid y 889 en Barcelona. Los modelos fueron ajustados hasta 2022 y no se reajustan. El MAE original, con predicciones restringidas a cero como mínimo, es 4,826 en Madrid y 4,510 µg/m³ en Barcelona. Se verifica por estación y fecha su coincidencia con las predicciones guardadas.

## Grupos definidos antes del cálculo

| Grupo principal | Variables que se alteran juntas |
| --- | --- |
| PM10 reciente y retardos | pm10_t, pm10_t_menos_1, pm10_t_menos_2, pm10_t_menos_6 |
| Medias y variabilidad | media_3_dias, media_7_dias, media_14_dias, desviacion_7_dias |
| Calendario | semana_sin, semana_cos, mes_sin, mes_cos |
| Estación | codigo_estacion |

Los cuatro grupos cubren las doce variables numéricas y el identificador de estación exactamente una vez. Las columnas de un grupo se mueven juntas para preservar sus relaciones internas, incluidos los pares de seno y coseno. Las relaciones entre grupos pueden romperse.

Se añade una sensibilidad de **historial completo**, con los ocho predictores de los dos primeros grupos desplazados conjuntamente. Conserva las relaciones internas de retardos, medias y variabilidad que proceden de una misma fila real. Se solapa con los grupos principales y no constituye una quinta contribución independiente. Los incrementos de los grupos no deben sumarse.

## Alteración temporal y categórica

Dentro de cada estación se ordenan las filas evaluables de 2023 por fecha objetivo. Cada repetición desplaza circularmente el grupo numérico un número de posiciones entre 14 y n−14, incluidos ambos extremos. Se mantiene el orden de la secuencia salvo el punto de cierre, y se evita una correspondencia trivial de filas cercanas en posición. Las estaciones se desplazan de forma independiente.

Las filas completas pueden tener huecos entre fechas. Una separación de catorce posiciones evaluables no equivale necesariamente a catorce días naturales. El desplazamiento altera la alineación con el objetivo y con los grupos que permanecen fijos, y puede romper estacionalidad o generar combinaciones físicas poco realistas. Incluso puede llevar valores de fechas posteriores a un objetivo: esto es una perturbación artificial de interpretación y no una entrada de entrenamiento ni una predicción temporal operativa.

Se realizan **50 desplazamientos por grupo numérico**, con semilla 20261120 en Madrid y 20261121 en Barcelona. Los mismos planes se reutilizan entre grupos numéricos dentro de cada repetición. Se conservan el número de casos, los objetivos y las identidades originales de los registros de evaluación. No se imputan valores ni se descartan casos después de alterar las entradas.

La estación no se altera dentro de sí misma, porque su código sería constante. Se enumeran las dos rotaciones cíclicas no idénticas de los tres códigos, aplicando una sustitución coherente a toda la serie de cada estación. No hay códigos nuevos para el codificador del modelo. Este procedimiento tiene solo dos resultados por territorio y no resume todas las alteraciones categóricas posibles. Cuando los tamaños de las estaciones son distintos, las frecuencias asociadas a las etiquetas pueden cambiar al rotarlas.

## Medida de importancia y resultados

Para cada alteración se calcula MAE alterado menos MAE original sobre las mismas filas. Un valor positivo significa que el modelo pierde precisión cuando se perturba el grupo. Un valor negativo significa menor error bajo esa alteración concreta; no demuestra que el grupo sea inútil ni justifica retirarlo sin otra evaluación.

| Grupo | Madrid · aumento medio de MAE | Barcelona · aumento medio de MAE | Alteraciones |
| --- | ---: | ---: | ---: |
| PM10 reciente y retardos | +1,924 | +1,721 | 50 |
| Medias y variabilidad | +0,874 | +0,498 | 50 |
| Calendario | +0,103 | +0,246 | 50 |
| Estación | −0,002 | +0,053 | 2 |
| Historial completo · sensibilidad conjunta | +3,355 | +2,896 | 50 |

Los valores están en µg/m³. En Madrid, las dos rotaciones de estación producen diferencias entre −0,011 y +0,006 µg/m³; el promedio próximo a cero es especialmente limitado por ese diseño. En Barcelona ambas rotaciones incrementan el error, entre +0,033 y +0,073 µg/m³. No se interpreta ninguna cifra como un efecto geográfico causal.

El rango mínimo–máximo y la desviación muestral entre alteraciones describen variabilidad del diagnóstico. Si solo hubiera una alteración, la desviación quedaría indefinida y se mostraría como nula. **No son intervalos de confianza**, no miden incertidumbre de muestreo y no proporcionan una prueba de significación. Las diferencias entre territorios también dependen de sus modelos, muestras, distribuciones y planes de desplazamiento.

## Relación con los coeficientes y el bosque

Los coeficientes de Ridge describen su función ajustada, con entradas numéricas estandarizadas mediante entrenamiento e indicadores de estación cero o uno. La importancia por impureza de Random Forest corresponde a las divisiones realizadas durante el entrenamiento de otro modelo. La permutación agrupada mide cambios de error de Ridge en una validación conocida. Sus unidades, signos y usos no son intercambiables.

React muestra los coeficientes y las importancias originales en tablas separadas para complementar la lectura, sin normalizar los incrementos de MAE como porcentajes de contribución. La correlación entre predictores puede repartir coeficientes, ofrecer sustitutos de información y modificar la importancia observada. [Explicabilidad original](31_explicabilidad_pm10.md)

## Entradas, protocolo y salidas

El [evaluador](../pm10_data/evaluation/grouped_permutation.py) recibe una función de predicción y las filas de validación. Comprueba claves, año 2023, horizonte de un día y valores completos y finitos. Crea copias de las entradas para alterarlas y no dispone de una operación de ajuste. El [pipeline](../pm10_data/pipelines/interpret_pm10_permutation.py) carga los Ridge originales y reutiliza la cohorte común original del experimento de ventanas. No utiliza las variantes B o C.

Las tablas, modelos y validaciones son los [originales de Madrid y Barcelona](38_experimentos_madrid_barcelona.md). Se leen además `coeficientes_ridge.csv` e `importancias_random_forest.csv` de `output/pm10_regression_validation/` para Madrid y `variables_ridge.csv` y `variables_random_forest.csv` de `output/experiments/barcelona/validacion/` para Barcelona. Sus rutas y huellas se registran. Los modelos guardados y las predicciones originales de prueba se contrastan por SHA-256 al terminar.

Antes de calcular errores alterados se escribe un protocolo por territorio con grupos, sensibilidad, semillas, repeticiones, separación de filas, método categórico, MAE, restricción de predicción, versiones y huellas. No se produce una nueva evaluación de 2024 o 2025.

Cada territorio escribe en `output/experiments/grouped_permutation/{territorio}/`:

| Archivo | Filas y contenido |
| --- | --- |
| protocolo.json | Configuración y trazabilidad del experimento |
| repeticiones.csv | 202 alteraciones: 50 para cada uno de tres grupos numéricos y la sensibilidad conjunta, más 2 rotaciones de estación |
| desplazamientos.csv | 150 combinaciones de repetición y estación con tamaño y desplazamiento en filas evaluables |
| resumen.csv | Cinco grupos con aumento medio, mediana, desviación, mínimo, máximo, MAE alterado medio y variables |
| resumen.json | Resumen, rotaciones categóricas, referencias de coeficientes e importancias, estaciones y huellas |

Los códigos de grupo, método, estación y variables son texto. Repetición, número de filas y desplazamiento son enteros. MAE y diferencias son decimales en µg/m³. En `resumen.csv`, las variables se serializan con `|`. Los CSV usan coma, punto decimal y UTF-8 con BOM. El resumen global reúne ambos territorios y las limitaciones del método.

## React y API

**Experimentos → Importancia agrupada** permite elegir territorio. El punto y la barra indican el incremento medio y la línea horizontal el mínimo–máximo entre alteraciones. La tabla accesible conserva los resultados numéricos. Una casilla incorpora la sensibilidad conjunta con color distinto y su aviso de solapamiento. También se consultan variables, tamaños por estación, semillas, rotaciones y las referencias de los modelos originales.

`GET /api/experiments/grouped-permutation` sirve el JSON local de `output/experiments/grouped_permutation/resumen.json`, sin cargar ni ajustar modelos desde Flask. Si no existe devuelve 404 con el comando necesario. La respuesta contiene `year`, `repeats`, `minimumShiftRows`, `experiments`, `originalArtifactsUnchanged`, `protectedHashes` y `limitations`.

Cada experimento incluye identificador y nombre textuales, n entero, MAE original decimal, semilla y separación enteras, estaciones, rotaciones, referencias y huellas. Cada fila de importancia tiene `group`, `label`, `kind` y `method` textuales, lista `features`, recuento entero `repetitions` y decimales `mean`, `median`, `std`, `minimum`, `maximum` y `meanPermutedMae`. `kind` distingue `primary` y `sensitivity`. Las referencias conservan los nombres y columnas de los CSV de coeficientes e impureza. [Componente](../explorer/src/grouped-permutation.tsx)

## Reproducción y alcance

```powershell
.\.venv\Scripts\python.exe -m pm10_data.pipelines.interpret_pm10_permutation
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Las pruebas comprueban reproducibilidad y separación de los desplazamientos, conservación de estación y orden circular, movimiento conjunto de columnas, protección de las entradas originales, rechazo de objetivos futuros o claves repetidas, un predictor de dependencia conocida y la lectura de resultados desde la API. Los modelos se mantienen congelados y la interpretación sigue siendo exploratoria sobre una validación ya utilizada.
