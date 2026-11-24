# Métricas de negocio para los avisos de PM10

## Decisión que se quiere apoyar

Como caso de uso para el TFM se propone una organización que programa actividades exteriores en los entornos de las tres estaciones del estudio. Un aviso para el día siguiente activaría una revisión anticipada de la programación y la preparación de alternativas. La decisión requiere conocer cuánto cuesta una revisión innecesaria y cuánto cuesta reaccionar tarde al comienzo de un episodio.

Este caso de uso es una propuesta de aplicación. Los datos del proyecto contienen mediciones ambientales y predicciones. Para explorar sensibilidad, se normaliza el coste de una falsa alarma a una unidad y se varía el coste relativo de omitir un comienzo. Una organización interesada tendría que aportar sus costes reales de planificación, sus criterios operativos y la relación entre cada estación y sus actividades.

## Qué se cuenta

Se utilizan las predicciones fijas de 2025 para persistencia y las dos regresiones logísticas. La muestra se restringe a las **891 observaciones de estación y fecha objetivo cuyo día anterior estaba en 27 µg/m³ o menos**. En ellas se observaron **27 comienzos**, definidos por un valor objetivo estrictamente superior a 27 µg/m³. El umbral procede del protocolo estadístico del TFM.

| Método | Comienzos detectados | Comienzos omitidos | Falsas alarmas | Avisos emitidos |
| --- | ---: | ---: | ---: | ---: |
| Persistencia | 0 | 27 | 0 | 0 |
| Logística sin meteorología | 6 | 21 | 13 | 19 |
| Logística con meteorología | 9 | 18 | 18 | 27 |

La unidad de recuento es estación y fecha objetivo. Un episodio que afecte a dos estaciones puede generar dos casos. Los días sin las variables necesarias quedan fuera de la evaluación. La política ilustrada se limita a anticipar comienzos, por lo que el coste de gestionar continuaciones de episodios queda pendiente de una formulación operativa.

La persistencia emite cero avisos en este contexto porque el valor del día previo está en el umbral o por debajo. Sirve para representar el punto de comparación sin anticipación de comienzos.

## Supuestos y cálculo

Se asigna una unidad de coste a la falsa alarma por la revisión innecesaria. El parámetro r expresa cuántas veces cuesta omitir un comienzo respecto a una falsa alarma. Los escenarios r = 1, 2 y 5 son ejemplos elegidos para explorar sensibilidad. Se toma como referencia un coste incremental cero para las decisiones correctas y se utiliza la misma regla para todos los modelos.

```text
coste simulado en unidades = falsas alarmas + r × comienzos omitidos
```

La diferencia respecto a persistencia es el coste simulado del modelo menos el coste simulado de persistencia. Un valor negativo representa un menor coste bajo los supuestos elegidos.

| Escenario | Coste de falsa alarma | Coste de comienzo omitido | Persistencia | Logística sin meteo | Logística con meteo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Errores con igual coste | 1 | 1 | 27 | 34 | 36 |
| Omisión con coste doble | 1 | 2 | 54 | 55 | 54 |
| Omisión con coste quíntuple | 1 | 5 | 135 | 118 | 108 |

Todas las cifras de coste de la tabla se expresan en unidades equivalentes al coste de una falsa alarma. Corresponden al conjunto de casos evaluados y sumados entre las tres estaciones. El cálculo omite costes de infraestructura, mantenimiento y acciones posteriores a avisos correctos. Los resultados describen una simulación retrospectiva y necesitan validación con la organización para estimar su impacto económico.

## Interpretación para la decisión

En el escenario donde omitir un comienzo cuesta cinco veces lo que cuesta una falsa alarma, la versión con meteorología reduce el coste simulado en **27 unidades respecto a persistencia**, equivalentes a un 20 % del coste de esa referencia. Frente a la logística sin meteorología, la reducción es de **10 unidades**. Detecta tres comienzos adicionales y genera cinco falsas alarmas adicionales dentro de este contexto.

Con costes iguales, persistencia presenta el menor coste simulado. Con un coste de omisión doble, persistencia y la logística con meteorología empatan. La utilidad depende del equilibrio entre anticipación y revisiones innecesarias.

Si el coste de una falsa alarma es positivo, la versión con meteorología resulta más barata que persistencia cuando el coste de omitir un comienzo supera **dos veces** el de una falsa alarma. La igualdad procede de comparar sus 18 falsas alarmas adicionales con sus nueve omisiones evitadas.

Frente a la logística sin meteorología, la versión con meteorología resulta más barata cuando esa relación supera **5/3**, aproximadamente 1,67. La igualdad corresponde a cinco falsas alarmas adicionales y tres omisiones evitadas.

Para cualquier valor de r, los costes de persistencia, logística sin meteorología y logística con meteorología son respectivamente 27r, 13 + 21r y 18 + 18r. Entre los tres métodos, persistencia minimiza el coste para 0 ≤ r < 2, empata con la logística con meteorología en r = 2 y esta última minimiza el coste para r > 2. En esta muestra, la logística sin meteorología queda por encima del mínimo de esas dos alternativas.

Estas relaciones describen los modelos y cortes ya fijados en la muestra de 2025. La elección de los escenarios se hizo después de disponer de los resultados. Para elegir o ajustar una nueva política de avisos se necesitaría un criterio acordado previamente y una evaluación independiente posterior.

## Reproducción y trazabilidad

El proceso utiliza la biblioteca estándar de Python y lee las [predicciones de 2025](../output/pm10_weather_test_2025/predicciones_2025.csv). Comprueba que los tres modelos compartan las claves, los contextos y las etiquetas observadas y que cada predicción sea única por modelo, estación y fecha.

Desde la raíz, con el entorno Python del proyecto disponible, ejecutar

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_business
```

El [pipeline](../tfm_data/pipelines/evaluate_pm10_business.py) genera el [resumen de avisos](../output/pm10_business_2025/resumen_avisos.csv), los [costes por escenario](../output/pm10_business_2025/escenarios_coste.csv) y la [configuración y huella de la fuente](../output/pm10_business_2025/configuracion.json). Los recuentos coinciden con el contexto `hoy_no_elevado` de las [métricas de clasificación](../output/pm10_weather_test_2025/metricas_por_contexto.csv).

En la ejecución del 19 de noviembre de 2026 se utilizó el Python disponible en el runtime de Codex, porque el entorno `.venv` conserva una ruta a una versión anterior que requiere reparación. Esta incidencia está recogida en la revisión de requisitos.
