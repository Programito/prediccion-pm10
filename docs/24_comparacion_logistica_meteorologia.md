# Efecto del viento y la precipitación previstos en la clasificación de PM10

La logística con meteorología anticipó **10 de 36 comienzos** en 2023 frente a **8 de 36** sin meteorología. La diferencia neta fue de dos comienzos, con una falsa alarma total menos. [Métricas por contexto](../output/pm10_weather_validation/metricas_por_contexto.csv)

## Diseño

Ambas logísticas usan las mismas **2.001 filas completas de 2021–2022** (194 positivas) y se comparan en las mismas **1.039 filas de 2023** (93 positivas). Se mantienen el escalado, la codificación de estación y los hiperparámetros originales. La versión con meteorología añade `viento_10m_mediodia_ms` y `precipitacion_diaria_mm` del ciclo de NOAA del día anterior. Se mantiene el umbral de PM10 elevado de **más de 27 µg/m³**. [Preparación de la muestra común](23_cruce_pm10_meteorologia.md)

El límite común fue de **37 falsas alarmas totales**, las que obtuvo la persistencia en esas mismas fechas. Para cada logística se evaluaron todos los cortes de probabilidad distintos. Dentro del límite se priorizó detectar más comienzos, después más días elevados, después reducir las falsas alarmas y finalmente escoger el corte más alto en caso de empate. Los cortes elegidos en 2023 fueron **0,20072870154329542** sin meteorología y **0,19904472278306495** con meteorología. Se emite un aviso cuando la probabilidad es mayor o igual que el corte. [Configuración y cortes exactos](../output/pm10_weather_validation/configuracion.json) · [Barrido de umbrales](../output/pm10_weather_validation/barrido_umbrales_2023.csv)

## Resultados en 2023

| Método | Días elevados detectados (de 93) | Falsas alarmas totales | Comienzos detectados (de 36) | Falsas alarmas cuando hoy no es elevado | Precisión general |
| --- | ---: | ---: | ---: | ---: | ---: |
| Persistencia | 57 | 37 | 0 | 0 | 60,6 % |
| Logística sin meteorología | 63 | 36 | 8 | 11 | 63,6 % |
| Logística con meteorología | 65 | 35 | 10 | 10 | 65,0 % |

Las dos logísticas detectaron 55 de 57 continuaciones. De los 36 comienzos, siete fueron detectados por ambas, tres solo por la versión con meteorología y uno solo por la versión sin meteorología. Las 1.039 filas representan observaciones de estación y fecha, de modo que un episodio en varias estaciones puede aparecer más de una vez. [Métricas generales](../output/pm10_weather_validation/metricas_validacion_2023.csv) · [Avisos por estación y fecha](../output/pm10_weather_validation/predicciones_validacion_2023.csv)

La mejora de 2023 es pequeña y se observa en el mismo año que se usó para elegir los cortes. Las dos variantes y sus cortes se reutilizaron en la comprobación independiente de 2025. [Modelos guardados](../models/pm10/weather_validation_2023/logisticas_gfs.joblib) · [Resultados de 2025](25_prueba_meteorologia_2025.md)

El experimento se reproduce desde la raíz del proyecto.

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.compare_pm10_weather
```
