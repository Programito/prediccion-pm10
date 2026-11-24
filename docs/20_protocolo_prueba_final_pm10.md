# Protocolo de prueba final de PM10 en 2024

Este protocolo fija la evaluación antes de calcular las predicciones de prueba. Se reutilizan los modelos ajustados con objetivos de 2017–2022. En 2023 se eligieron las variables de Ridge y el corte de la logística.

## Observaciones y referencias

La fecha objetivo pertenece a 2024. Se usan las filas con predictores y objetivo completos de Tres Olivos, Majadahonda y San Martín de Valdeiglesias. Los cuatro métodos se comparan sobre las mismas claves estación y fecha objetivo. Se informa de la cobertura sobre el calendario completo de cada estación. Los huecos se tratan como en validación.

| Tarea | Modelo fijado | Persistencia | Métricas |
| --- | --- | --- | --- |
| Regresión | Ridge original, con `semana_sin` y `semana_cos`. Las predicciones negativas se limitan a cero. | PM10 observado hoy. | MAE, RMSE y sesgo, globales y por estación. Se informa por separado de los días con PM10 observado por encima de 27 µg/m³. |
| Clasificación | Logística ya ajustada. Aviso cuando la probabilidad estimada es ≥ **0,2085124546747814**. | Aviso cuando el PM10 de hoy supera 27 µg/m³. | Matriz de confusión, precisión, recall y F1. Se informa por estación y por contexto del día anterior. |

Un positivo en clasificación significa PM10 de mañana **estrictamente mayor que 27 µg/m³**. Hay un comienzo si hoy hay como máximo 27 µg/m³ y mañana se supera ese valor. Una continuación requiere superar el umbral ambos días. Se informa de aciertos y falsas alarmas en cada contexto. El criterio de validación que limitaba las falsas alarmas se usó para elegir el corte en 2023. En 2024 se aplica el mismo corte y se cuentan las falsas alarmas resultantes.

La prueba es retrospectiva y supone que el PM10 de hoy está disponible al emitir la previsión. La selección inicial de estaciones consideró su cobertura histórica, incluida la de 2024. Los resultados permiten estudiar el rendimiento en esas tres estaciones y entre las fechas evaluables.

El [protocolo ejecutable](reference/pm10_final_protocol.json) conserva las reglas y las huellas SHA-256 de los modelos y de la tabla. El comando aplica el protocolo con los modelos guardados.

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_final
```
