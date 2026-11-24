# Clasificación de PM10 elevado al día siguiente

El objetivo es anticipar si el PM10 medio de mañana superará **27 µg/m³**. El umbral se fijó con el percentil 90 de los objetivos disponibles de entrenamiento. La etiqueta indica un nivel elevado en esta muestra y su finalidad es comparar modelos.

## Experimento

Se usó la tabla predictiva completa con las mismas variables del experimento de regresión. La regresión logística se ajustó con **6.096 filas de 2017–2022**, de las cuales **585** son positivas. El escalado de las variables numéricas y la codificación de la estación se ajustaron con ese mismo conjunto.

Los dos métodos se evaluaron en las mismas **1.039 filas de 2023**, con **93 casos elevados**. Las reglas se fijaron antes de evaluar.

| Método | Regla para emitir un aviso |
| --- | --- |
| Persistencia | El PM10 observado hoy supera 27 µg/m³. |
| Regresión logística | La probabilidad estimada para mañana es al menos 0,50. Se usó `C=1`, regularización L2 y clases sin ponderación. |

La evaluación final de 2024 sigue reservada. La comparación de 2023 presupone que el PM10 de hoy está disponible al emitir el pronóstico y cubre las fechas con variables y objetivo completos.

## Resultados de validación

| Método | Avisos acertados (VP) | Falsas alarmas (FP) | Casos perdidos (FN) | Negativos correctos (VN) | Precisión | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Persistencia | 57 | 37 | 36 | 909 | 60,6 % | 61,3 % | 0,610 |
| Regresión logística | 35 | 11 | 58 | 935 | 76,1 % | 37,6 % | 0,504 |

La precisión mide qué proporción de avisos acierta. El *recall* mide qué proporción de casos elevados se detecta. La logística emitió 46 avisos frente a 94 de la persistencia. Consiguió mayor precisión y menos falsas alarmas a cambio de detectar 22 casos menos. La persistencia tuvo mayor *recall* y F1 en este experimento. [Métricas y matriz de confusión en CSV](../output/pm10_classification_validation/metricas_validacion_2023.csv)

## Comienzos y continuaciones

En cada estación, un **comienzo** es una transición de PM10 de hasta 27 hoy a más de 27 mañana. Una **continuación** ocurre cuando ambos días superan 27. Se cuentan las transiciones de las filas evaluadas, de modo que la unidad de recuento es estación y fecha objetivo.

| Casos elevados observados | Total | Detectados por persistencia | Detectados por logística |
| --- | ---: | ---: | ---: |
| Comienzos | 36 | 0 de 36 | 0 de 36 |
| Continuaciones | 57 | 57 de 57 | 35 de 57 |

En los días que partían de un nivel de hasta 27 µg/m³, ambos métodos emitieron cero avisos. La persistencia se comporta así por construcción. La logística también se quedó por debajo de 0,50 en todas esas fechas. Su precisión en ese grupo queda vacía porque no hizo ningún aviso. El resultado describe el punto de decisión evaluado. [Métricas por contexto](../output/pm10_classification_validation/metricas_por_contexto.csv)

## Qué cambia al bajar el umbral de probabilidad

Se reutilizaron las probabilidades de las mismas 1.039 filas de 2023. En cada fila cambia solo la decisión de emitir aviso. Se mantiene la definición de episodio por encima de 27 µg/m³.

| Regla de aviso | Días elevados detectados (de 93) | Falsas alarmas | Comienzos detectados (de 36) |
| --- | ---: | ---: | ---: |
| Persistencia | 57 | 37 | 0 |
| Logística al 50 % | 35 | 11 | 0 |
| Logística al 30 % | 49 | 20 | 1 |
| Logística al 25 % | 53 | 27 | 2 |
| Logística al 20,85 % aprox. | 60 | 35 | 6 |
| Logística al 15 % | 71 | 64 | 16 |
| Logística al 10 % | 81 | 108 | 24 |

Para encontrar un candidato comparable se usaron como límite las **37 falsas alarmas** de la persistencia. Se evaluaron todos los cortes observados y se priorizó detectar más comienzos, después detectar más días elevados y finalmente reducir las falsas alarmas. Con el corte candidato, de los 14 avisos emitidos cuando hoy aún no era elevado, **6 anticiparon un comienzo y 8 fueron falsas alarmas**. En el conjunto completo se detectaron **60 de 93** días elevados, con **35 falsas alarmas**. El CSV guarda el corte con su precisión completa.

El corte se eligió mirando 2023, por lo que sus cifras describen una comparación exploratoria en validación. Queda como candidato para una prueba independiente en 2024. [Comparación de umbrales](../output/pm10_classification_validation/comparacion_umbrales_2023.csv) · [Barrido completo](../output/pm10_classification_validation/barrido_umbrales_2023.csv)

## Reproducción

Desde la raíz del proyecto, con la tabla predictiva ya preparada:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.train_pm10_classification
```

El comando guarda las [predicciones por estación y fecha](../output/pm10_classification_validation/predicciones_validacion_2023.csv), las métricas, la configuración y el modelo ajustado en `models/pm10/validation_2023/logistica.joblib`.

Con las predicciones guardadas, se puede reproducir el barrido:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.audit_pm10_classification_thresholds
```
