# Resultados

El objetivo principal fue predecir la concentración media de partículas PM10 del día siguiente en tres estaciones de Madrid: Tres Olivos, Majadahonda y San Martín de Valdeiglesias. La evaluación compara los modelos con la persistencia, que usa la última observación disponible como previsión. El estudio también examina si las previsiones de viento y precipitación ayudan a detectar el comienzo de días elevados. El análisis de altas hospitalarias se presenta por separado, a escala provincial y anual.

## Predicción de la concentración diaria de PM10

Se entrenaron los modelos con datos de 2017–2022. En la validación de 2023, Ridge obtuvo un error absoluto medio (MAE) de 4,83 µg/m³ frente a 4,95 de Random Forest y 5,14 de la persistencia. La comparación con y sin el día de la semana favoreció incluirlo, con un MAE de 4,83 frente a 4,88 µg/m³ en las mismas fechas. Se conservó ese Ridge y se evaluó en 2024 sin reajuste. El protocolo se fijó antes de calcular las métricas de ese año. [Validación de 2023](../output/pm10_regression_validation/metricas_validacion_2023.csv) · [Día de la semana](19_aporte_dia_semana_pm10.md) · [Protocolo de 2024](20_protocolo_prueba_final_pm10.md)

En 2024 se evaluaron **1.013 de 1.098 observaciones de estación y día** (92,3 %). Se utilizaron las mismas fechas para los dos métodos. El MAE mide la magnitud media del error, el RMSE da más peso a los errores grandes y el sesgo es la media de la predicción menos la observación. [Cobertura de 2024](../output/pm10_final_2024/cobertura_por_estacion.csv)

| Indicador en la prueba de 2024 (µg/m³) | Persistencia | Ridge |
| --- | ---: | ---: |
| MAE global | 6,06 | **5,96** |
| RMSE global | 11,72 | **10,47** |
| MAE en 107 observaciones con PM10 > 27 µg/m³ | **18,25** | 19,56 |
| Sesgo en esas 107 observaciones | −9,50 | −17,39 |

Ridge redujo el MAE global en **1,6 %** y el RMSE en **10,6 %**. La mejora del MAE se concentró en Tres Olivos, donde pasó de 7,50 a 7,03 µg/m³. Majadahonda pasó de 5,32 a 5,41 y San Martín de Valdeiglesias de 5,41 a 5,48. El RMSE de Ridge fue menor en las tres estaciones. Cuando el PM10 observado superó 27 µg/m³, Ridge subestimó la concentración en 17,39 µg/m³ de media y su MAE superó al de la persistencia. [Resultados por tramo](../output/pm10_final_2024/metricas_regresion.csv) · [Resultados por estación](../output/pm10_final_2024/metricas_regresion_por_estacion.csv)

El desglose posterior de errores muestra que la ventaja global del MAE se concentra en Tres Olivos y que Ridge presenta mayor MAE en días elevados en las tres estaciones. Al retirar las cinco fechas más favorables para Ridge, la diferencia de MAE frente a persistencia pasa de −0,099 a +0,338 µg/m³. La sensibilidad describe la concentración de la mejora en fechas concretas y mantiene como resultado principal la muestra completa. [Auditoría por estación, mes y nivel](35_analisis_errores_pm10.md)

La diferencia global de MAE de Ridge menos persistencia fue −0,099 µg/m³. Un bootstrap posterior por bloques de 14 días y 5.000 réplicas produjo un intervalo percentil nominal del 95 % de [−0,565; +0,288] µg/m³. Las longitudes de 7 y 28 días también incluyen cero. Esta evaluación condicionada a los errores de 2024 mantiene incierta la dirección de la mejora y requiere considerar estacionalidad, cobertura y selección previa. [Método y sensibilidad](36_incertidumbre_pm10.md)

## Clasificación de días elevados y aporte de la meteorología

Se definió un día elevado como aquel con PM10 medio estrictamente superior a **27 µg/m³**, el percentil 90 de los objetivos disponibles del entrenamiento original. El umbral es relativo a la muestra. Un comienzo ocurre cuando se pasa de un día con PM10 de hasta 27 µg/m³ a otro por encima de 27, en la misma estación. Para emitir avisos, la persistencia aplica ese límite a la concentración del día anterior. Su regla detecta continuaciones y produce cero avisos de comienzo por construcción. [Definición de la etiqueta y referencia](18_clasificacion_pm10_elevado.md)

La primera logística, basada en el historial de PM10 y el calendario, detectó **6 de 47 comienzos** en 2024 y produjo **55 falsas alarmas** en total, frente a 48 de la persistencia. El resultado motivó probar dos variables de GFS disponibles como previsión: la velocidad del viento a 10 m al mediodía y la precipitación acumulada del día objetivo. Ambas proceden del ciclo de las 12:00 UTC del día anterior. [Clasificación de 2024](21_resultados_prueba_final_pm10.md) · [Procedencia de GFS](22_viabilidad_meteorologia_pm10.md)

Para medir el aporte de esas variables se ajustaron dos logísticas sobre las mismas **2.001 filas de 2021–2022**. La única diferencia entre las entradas era la inclusión de viento y precipitación. Los cortes de probabilidad se eligieron por separado en 2023 con el mismo límite de 37 falsas alarmas, igual al recuento de la persistencia en ese año. En validación, la versión con meteorología anticipó 10 de 36 comienzos con 35 falsas alarmas totales. La versión sin meteorología anticipó 8 con 36 falsas alarmas. [Comparación y elección de cortes en 2023](24_comparacion_logistica_meteorologia.md)

En 2025 se aplicaron los mismos modelos y cortes a **1.003 de 1.095 observaciones** (91,6 %). Las concentraciones se construyeron a partir de las horas verificadas de la Agencia Europea de Medio Ambiente (EEA), con al menos 18 horas válidas por día UTC. Como comprobación previa, los **25.969 valores horarios válidos de 2024** coincidieron exactamente entre la EEA y MITECO una vez alineadas las horas UTC y los puntos de muestreo. La serie anterior daba prioridad al valor diario oficial cuando estaba disponible, mientras que en 2025 se usaron exclusivamente medias de horas. [Protocolo de 2025](reference/pm10_weather_test_2025.json) · [Contraste de fuentes](../output/pm10_weather_test_2025/contraste_horario_2024.csv)

| Indicador en la prueba de 2025 | Persistencia | Logística sin meteorología | Logística con meteorología |
| --- | ---: | ---: | ---: |
| Comienzos detectados (de 27) | 0 | 6 | **9** |
| Observaciones elevadas detectadas (de 113) | 86 | 87 | **94** |
| Falsas alarmas totales | **26** | 33 | 37 |
| Falsas alarmas cuando el día anterior no era elevado | 0 | 13 | 18 |
| Precisión de los avisos | **76,8 %** | 72,5 % | 71,8 % |
| Proporción de observaciones elevadas detectadas (recall) | 76,1 % | 77,0 % | **83,2 %** |

En 2025, añadir la meteorología permitió detectar **tres comienzos más y siete observaciones elevadas más** frente a la logística base, con **cuatro falsas alarmas totales adicionales**. La dirección del cambio en la detección de comienzos coincide con la observada en validación. El coste en falsas alarmas fue distinto, porque los cortes se mantuvieron fijos al pasar a 2025. Con 27 comienzos evaluados, la comparación describe el rendimiento en esta muestra y deja incertidumbre sobre el tamaño de la mejora. [Métricas de 2025](../output/pm10_weather_test_2025/metricas_2025.csv) · [Desglose por contexto](../output/pm10_weather_test_2025/metricas_por_contexto.csv)

## Interpretación de los modelos de regresión

En Ridge, el PM10 del día anterior al objetivo presenta el mayor coeficiente en valor absoluto entre las variables transformadas. Las entradas numéricas se estandarizaron con entrenamiento y las medias y retardos están correlacionados. En Random Forest, ese PM10 previo concentra el 61,3 % de la importancia por reducción de impureza del entrenamiento. La descomposición aditiva de Ridge reproduce las 1.013 predicciones de prueba de 2024 y permite examinar errores como el pico de Tres Olivos del 31 de octubre. [Método, casos y límites de interpretación](31_explicabilidad_pm10.md)

## Utilidad potencial de los avisos

Se exploró un caso de apoyo a la planificación de actividades exteriores utilizando los 891 casos de 2025 cuyo día previo estaba en 27 µg/m³ o menos. Al normalizar una falsa alarma a una unidad y suponer que omitir un comienzo cuesta cinco unidades, el coste simulado fue de 135 unidades para persistencia, 118 para la logística sin meteorología y 108 para la versión con meteorología. Con ambos errores valorados en una unidad, persistencia presentó el menor coste simulado. La versión con meteorología resulta más barata que persistencia cuando la relación entre ambos costes supera dos. El resultado describe los modelos y cortes fijados para esta muestra. [Supuestos, escenarios y reproducción](30_metricas_negocio_pm10.md)

## Análisis exploratorio de las altas hospitalarias

El objetivo sanitario fue la tasa anual de altas por enfermedades respiratorias por cada 100.000 habitantes. Se comparó repetir la tasa del año anterior con dos modelos Ridge. El primero usó el historial y la estructura demográfica del año anterior. El segundo añadió el indicador provincial de PM10 de ese mismo año. La evaluación retrospectiva comprendió 2023 y 2024 con entrenamiento que avanzaba un año en cada ajuste. La muestra principal tuvo **58 observaciones de territorio y año**, correspondientes a 29 territorios. [Diseño sanitario y análisis de sensibilidad](09_demografia_y_comparacion_inicial.md)

| Modelo sanitario | MAE (altas por 100.000 habitantes) | RMSE (altas por 100.000 habitantes) |
| --- | ---: | ---: |
| Persistencia de la tasa anterior | **136,21** | **156,66** |
| Ridge con historial y demografía | 163,52 | 188,52 |
| Ridge con historial, demografía y PM10 | 164,71 | 189,60 |

La persistencia obtuvo el menor error y añadir PM10 aumentó ligeramente el MAE frente al Ridge con demografía. Al retirar los puntos con alertas de ubicación o cambio de tipo de área, el orden se mantuvo en las 54 observaciones restantes. El resultado acota el rendimiento de esta formulación predictiva con datos agregados. El estudio carece de un diseño para estimar efectos causales o inferir exposición individual. [Métricas sanitarias](../data/interim/initial_comparison/metricas.csv)

## Alcance de los resultados

Las pruebas de PM10 describen tres estaciones seleccionadas por cobertura histórica y se calculan en fechas con observaciones completas. Las filas próximas en el tiempo y las correspondientes al mismo episodio en distintas estaciones pueden estar relacionadas. El estudio informa métricas descriptivas y hace explícito el denominador de cada comparación.

La evaluación diaria supone que el resumen de PM10 del día anterior puede usarse a medianoche UTC. GFS permite identificar el ciclo meteorológico empleado, pero la disponibilidad operativa de ambas fuentes a la hora de emisión requiere medir sus latencias. La utilidad de emitir avisos depende de cuánto cuesta pasar por alto un episodio frente a emitir una falsa alarma. Los avisos del experimento representan la superación de un umbral estadístico de esta muestra.

### Casos para la demostración

En Tres Olivos, el **5 de agosto de 2025** fue un comienzo que detectó solo la logística con meteorología. El PM10 pasó de **24,42 a 42,33 µg/m³**. En la misma estación, el **22 de febrero de 2025** ilustra una falsa alarma de esa versión, con un descenso de **26,75 a 5,42 µg/m³**. Mostrar ambos casos permite explicar cómo se aplica el umbral y qué implica el intercambio entre detección y falsas alarmas. [Predicciones por estación y fecha](../output/pm10_weather_test_2025/predicciones_2025.csv)
