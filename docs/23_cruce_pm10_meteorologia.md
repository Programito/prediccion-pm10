# Cruce de PM10 observado con previsiones GFS

La tabla une la serie supervisada de PM10 de MITECO con las previsiones de NOAA GFS por **`codigo_estacion` y `fecha_objetivo`**. Conserva una fila por estación y día de 2021 a 2024, también cuando algún dato está ausente. [Tabla cruzada](../data/interim/pm10_weather/tabla_pm10_meteo.csv)

## Alineación y selección de filas

- El objetivo de PM10 corresponde al día siguiente de la última observación. La emisión simulada sigue a las 00:00 UTC del día objetivo.
- La previsión GFS debe corresponder al ciclo de las 12:00 UTC del día anterior. Se comprueba la clave única de ambas fuentes y la coherencia entre los valores meteorológicos y sus estados de calidad.
- `fila_comun_utilizable` identifica las filas con objetivo de PM10, predictores originales, viento previsto y precipitación prevista completos. El experimento debe aplicar el mismo filtro a las dos versiones de la logística. [Lista de predictores y criterio de selección](../data/interim/pm10_weather/esquema_comparacion.json)
- Se mantiene la definición original de PM10 elevado, estrictamente por encima de **27 µg/m³**. Un comienzo es el paso de un día de hasta 27 a un día por encima de 27 en la misma estación.

## Cobertura de la muestra común

| Año objetivo | Uso previsto | Filas de calendario | Completas con PM10 | Completas con PM10 y GFS | Días elevados en la muestra común | Comienzos en la muestra común |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 2021 | Entrenamiento | 1.095 | 1.019 | 1.004 | 90 | 30 |
| 2022 | Entrenamiento | 1.095 | 997 | 997 | 104 | 41 |
| 2023 | Validación | 1.095 | 1.039 | 1.039 | 93 | 36 |
| 2024 | Diagnóstico | 1.098 | 1.013 | 1.013 | 107 | 47 |

De las **4.383 filas** del calendario, **4.053** son completas para ambas versiones. GFS reduce la muestra utilizable de PM10 en **15 filas de 2021**, tres por cada fecha sin previsión, y deja fuera tres comienzos de ese año. Las 1.039 filas de validación coinciden con las observaciones ya evaluadas en la clasificación original. [Cobertura por estación y año](../data/interim/pm10_weather/cobertura_por_estacion_anio.csv) · [Totales por año](../data/interim/pm10_weather/cobertura_por_anio.csv)

Para la comparación hay **2.001 filas de entrenamiento con 71 comienzos** y **1.039 de validación con 36 comienzos**. 2024 queda identificado como diagnóstico porque ya se consultaron sus resultados. La confirmación en 2025 requiere incorporar y verificar el PM10 de ese año.

La comparación de las dos logísticas en estas filas ya está documentada. [Resultados con y sin meteorología](24_comparacion_logistica_meteorologia.md)

La tabla se reproduce desde la raíz con este comando.

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_pm10_weather
```
