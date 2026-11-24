# Resultados de la prueba final de PM10 en 2024

Ridge redujo el error medio absoluto global frente a la persistencia en **1,6 %**. El efecto dependió de la estación y los días elevados siguieron favoreciendo a la persistencia. La logística anticipó **6 de 47 comienzos**, con más falsas alarmas totales que la referencia. Se aplicaron los dos modelos ajustados con objetivos de 2017–2022 y las reglas fijadas tras la validación de 2023. [Protocolo de evaluación](20_protocolo_prueba_final_pm10.md)

## Cobertura de la prueba

Se evaluaron las mismas **1.013 de 1.098 observaciones posibles** en las dos tareas (92,3 %). Las 85 restantes tenían predictores incompletos, objetivo ausente o ambos. Los resultados corresponden a las fechas completas de las tres estaciones seleccionadas y a una simulación que presupone la disponibilidad del PM10 del día anterior. [Cobertura por estación](../output/pm10_final_2024/cobertura_por_estacion.csv)

## Regresión del PM10 del día siguiente

| Indicador (µg/m³) | Ridge | Persistencia |
| --- | ---: | ---: |
| MAE general (1.013 observaciones) | **5,96** | 6,06 |
| RMSE general | **10,47** | 11,72 |
| MAE con PM10 observado > 27 (107 observaciones) | 19,56 | **18,25** |
| Sesgo en ese tramo | −17,39 | −9,50 |

El MAE general de Ridge mejoró un 6,1 % frente a la persistencia en 2023 y un 1,6 % en 2024. El RMSE general bajó un 10,6 % en 2024. En los días elevados, Ridge subestimó la concentración en 17,39 µg/m³ de media y tuvo mayor MAE. [Métricas por tramo](../output/pm10_final_2024/metricas_regresion.csv)

| Estación | Filas | MAE Ridge | MAE persistencia |
| --- | ---: | ---: | ---: |
| Tres Olivos | 329 | **7,03** | 7,50 |
| Majadahonda | 335 | 5,41 | **5,32** |
| San Martín de Valdeiglesias | 349 | 5,48 | **5,41** |

La mejora global del MAE procede de Tres Olivos. Ridge reduce el RMSE en las tres estaciones. [Métricas por estación](../output/pm10_final_2024/metricas_regresion_por_estacion.csv)

## Clasificación de PM10 elevado

| Indicador | Logística | Persistencia |
| --- | ---: | ---: |
| Casos detectados, de 107 | 62 | 60 |
| Casos perdidos | 45 | 47 |
| Falsas alarmas | 55 | 48 |
| Negativos correctos | 851 | 858 |
| Precisión | 53,0 % | 55,6 % |
| Recall | 57,9 % | 56,1 % |
| F1 | 0,554 | 0,558 |
| Comienzos detectados, de 47 | 6 | 0 |
| Continuaciones detectadas, de 60 | 56 | 60 |

Cuando hoy el PM10 aún no superaba 27 µg/m³, la logística emitió **23 avisos**. Se anticiparon 6 comienzos y hubo 17 falsas alarmas en ese contexto. El corte elegido en 2023 volvió a detectar algunos comienzos, con una tasa de detección del 12,8 % y siete falsas alarmas más que la persistencia en el conjunto de 2024. [Métricas por contexto](../output/pm10_final_2024/metricas_clasificacion_por_contexto.csv) · [Métricas por estación](../output/pm10_final_2024/metricas_clasificacion_por_estacion.csv)

La regresión ofrece una mejora global pequeña en el error absoluto y la clasificación ofrece cierta capacidad de anticipar comienzos. La subestimación de días elevados y el equilibrio entre avisos acertados y falsas alarmas delimitan el alcance de ambos resultados. Los CSV de predicciones permiten rastrear cada caso por estación y fecha. [Predicciones de regresión](../output/pm10_final_2024/predicciones_regresion.csv) · [Predicciones de clasificación](../output/pm10_final_2024/predicciones_clasificacion.csv)
