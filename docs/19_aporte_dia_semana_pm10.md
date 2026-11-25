# Aporte del día de la semana en Ridge

Se ajustaron dos versiones de Ridge con las mismas **6.096 filas de 2017–2022** y los mismos hiperparámetros (`alpha=10`, `solver=svd`). Una versión usa `semana_sin` y `semana_cos`, que representan el día de la semana de la fecha que se quiere predecir. La otra elimina esas dos variables. Ambas mantienen las variables de mes, los retardos, las ventanas y el código de estación. Se comparan en las mismas **1.039 observaciones de 2023**, con la persistencia del día anterior como referencia.

| Modelo | MAE general | RMSE general | MAE con PM10 > 27 | Sesgo con PM10 > 27 |
| --- | ---: | ---: | ---: | ---: |
| Persistencia | 5,140 | 8,352 | 14,705 | −6,100 |
| Ridge sin día de la semana | 4,880 | 7,564 | 15,696 | −13,549 |
| Ridge con día de la semana | **4,826** | **7,510** | 15,473 | −13,297 |

Las métricas se expresan en µg/m³. El tramo elevado incluye 93 observaciones y usa el umbral de 27 µg/m³ fijado en entrenamiento. El sesgo es la media de la predicción menos el valor observado.

Incluir el día de la semana reduce el MAE en **0,054 µg/m³** en el conjunto completo y en **0,223 µg/m³** en el tramo elevado. El MAE baja en las tres estaciones, tanto en el conjunto completo como en el tramo elevado. La persistencia conserva el menor MAE durante los días elevados.

La mejora es pequeña y consistente en las tres estaciones de esta validación. Se propone conservar las variables semanales en Ridge para la prueba final. La comparación cubre un solo año de validación y 2024 sigue reservado. [Métricas generales](../output/pm10_weekday_audit/metricas_validacion_2023.csv) · [Desglose por estación](../output/pm10_weekday_audit/metricas_por_estacion.csv)

Para regenerar la comparación desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pm10_data.pipelines.audit_pm10_weekday
```
