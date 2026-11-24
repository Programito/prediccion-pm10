# Tabla predictiva inicial y referencias de validación

Este paso ejecuta la preparación descrita en `11_enfoques_y_evaluacion.md`. No entrena todavía Ridge, árboles, clasificadores ni SARIMA.

## Qué representa una fila

Una estación y una fecha de última observación t, con variables disponibles hasta ese día y el objetivo PM10 de t+1. `fecha_objetivo` determina la partición. Por ejemplo, una fila con última observación del 31 de diciembre de 2022 y objetivo del 1 de enero de 2023 pertenece a validación, aunque sus predictores procedan de entrenamiento.

La emisión se registra en UTC al comienzo del día objetivo, como convención retrospectiva. No se ha demostrado disponibilidad inmediata de datos en vivo. Los originales anuales están revisados y la selección de estaciones observó la cobertura histórica completa.

## Tabla preparada

En `data/interim/pm10_prediction/`:

- `tabla_supervisada_pm10.csv`: conserva todas las filas de origen, incluidas las no utilizables, con banderas de objetivo disponible, predictores completos y partición.
- `tabla_modelos_completa.csv`: filas con todos los predictores iniciales y objetivo, dentro de entrenamiento, validación o prueba reservada.
- `cobertura_particiones.csv`: recuentos por estación y partición.
- `protocolo.json`: lista explícita de variables permitidas, reparto temporal y definición de clasificación.

Recuentos del conjunto completo:

| Partición por fecha objetivo | Filas utilizables |
| --- | ---: |
| Entrenamiento, 2017-2022 | 6.096 |
| Validación, 2023 | 1.039 |
| Prueba reservada, 2024 | 1.013 |

Las ausencias no se han rellenado. Exigir ventanas completas de hasta 14 días provoca pérdida de filas alrededor de huecos y durante el calentamiento. El último día de 2024 de cada serie apunta a 2025 sin objetivo observado: queda fuera del periodo y no se etiqueta como negativo.

`pm10_objetivo` es el resultado que queremos predecir, no una variable de entrada. No entrenar usando todas las columnas del CSV: la lista blanca está en `NUMERIC_FEATURES` y `protocolo.json`, con `codigo_estacion` como categórica. `fecha_objetivo` y otras columnas de auditoría se conservan para interpretar y validar, no para incluirlas automáticamente en el modelo.

## Clasificación preparada

El percentil 90 de los objetivos válidos de entrenamiento da **27 µg/m3**. La clase positiva se define como concentración objetivo estrictamente mayor que 27. Se congela ese umbral para validación y prueba. Es relativo al conjunto de entrenamiento y no es un umbral sanitario ni legal.

Entre las filas completas hay 585 positivos de 6.096 en entrenamiento, y 93 de 1.039 en validación. Las frecuencias por estación son diferentes y pueden consultarse en `balance_clasificacion_entrenamiento_validacion.csv`. Por empates en la concentración y la selección de filas completas, no se espera exactamente un 10 % de positivos.

No se ha evaluado todavía ningún clasificador ni calculado el balance objetivo de la prueba en los informes. Un objetivo ausente conserva la etiqueta vacía.

## Referencias de regresión, solo validación de 2023

Se utilizan las mismas 1.039 filas para las tres referencias. MAE, RMSE y sesgo se expresan en µg/m3.

| Referencia | MAE | RMSE | Sesgo medio |
| --- | ---: | ---: | ---: |
| Repetir el valor del día t | 5,14 | 8,35 | 0,06 |
| Media de los 7 días hasta t | 6,52 | 9,97 | -0,02 |
| Mismo día semanal de la semana anterior | 8,75 | 13,36 | -0,16 |

La persistencia es la referencia inicial más exigente de las tres en este conjunto de validación. No es todavía un resultado de prueba final ni garantiza que se mantenga la clasificación en otros años o episodios.

Archivos de resultados:

- `referencias_validacion_2023.csv`: métricas globales.
- `referencias_validacion_por_estacion.csv`: métricas separadas por estación.
- `predicciones_referencias_validacion.csv`: observaciones, predicciones y errores para reconstruir los cálculos.

## Reproducir y verificaciones

```powershell
python -m tfm_data.pipelines.prepare_pm10_forecast
python -m unittest discover -s tests
```

El mapeador está en `tfm_data/mappers/pm10_forecast.py`. Las pruebas comprueban que el objetivo es el día siguiente, que los retardos no cruzan estaciones, que se rechazan calendarios con saltos, que las ventanas no rellenan ausentes y que alterar valores futuros no modifica predictores pasados. También comprueban que el umbral de clasificación no cambia al modificar los objetivos de validación.

Las métricas de 2024 quedan sin calcular. El siguiente paso es ajustar Ridge y un modelo de árboles usando entrenamiento y comparar en 2023 con la persistencia, conservando 2024 para la evaluación final.
