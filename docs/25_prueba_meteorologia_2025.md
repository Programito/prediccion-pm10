# Prueba independiente de la clasificación con meteorología en 2025

Con los modelos y cortes fijados en 2023, la logística con meteorología anticipó **9 de 27 comienzos** en 2025, frente a **6 de 27** sin meteorología. También produjo **4 falsas alarmas totales más**. La señal de mayor detección se repite fuera de validación y viene acompañada de más avisos erróneos. [Protocolo fijado antes de evaluar](reference/pm10_weather_test_2025.json)

## Fuente de PM10 y comprobación de compatibilidad

Las concentraciones de 2025 proceden del archivo horario verificado E1a de la Agencia Europea de Medio Ambiente (EEA). El script de evaluación usa los tres archivos Parquet de los mismos puntos de muestreo de MITECO, con los identificadores `28079060_10_47`, `28080003_10_49` y `28133002_10_49`. El catálogo se consultó mediante `POST /ParquetFile/urls` y cada Parquet se descargó con `GET` desde la URL devuelta. [Documentación del proveedor](https://eeadmz1-downloads-webapp.azurewebsites.net/content/documentation/How_To_Downloads.pdf) · [Consulta, URLs y huellas de los archivos](../data/raw/eea_pm10/sources.json)

Cada archivo incluye `Samplingpoint`, `Unit`, `AggType` y `FkObservationLog` como texto, `Pollutant`, `Validity` y `Verification` como enteros, `Start`, `End` y `ResultTime` como marcas de tiempo, y `Value` y `DataCapture` como decimales. El mapeo usa `Pollutant=5` para PM10 y `Unit=ug.m-3`. Los intervalos `Start`–`End` duran una hora. El proveedor codifica las horas del Parquet en UTC+1 fijo, que se convierte a UTC restando una hora. [Esquema y convención horaria del proveedor](https://eeadmz1-downloads-webapp.azurewebsites.net/)

Se aceptan los códigos de validez 1, 2 y 3 si el registro está verificado (`Verification=1`) y su valor es finito y no negativo. El día se asigna por el inicio del intervalo en UTC. La media diaria requiere al menos **18 horas válidas**. Los días con menos horas quedan vacíos. [Códigos de validez](https://dd.eionet.europa.eu/vocabulary/aq/observationvalidity/view) · [Códigos de verificación](https://dd.eionet.europa.eu/vocabulary/aq/observationverification/view)

Antes de evaluar 2025, se cruzaron las horas válidas de 2024 con MITECO por punto y fin de intervalo UTC. Los conjuntos de horas válidas y los **25.969 valores** coincidieron exactamente. La serie de 2025 se construye íntegramente a partir de horas EEA. En el histórico anterior, la preparación de PM10 daba prioridad al dato diario oficial cuando estaba disponible. Para calcular los retardos de enero se reutilizaron los últimos 14 días del histórico de diciembre de 2024. [Contraste de 2024](../output/pm10_weather_test_2025/contraste_horario_2024.csv) · [PM10 diario de 2025](../output/pm10_weather_test_2025/pm10_diario_2025.csv)

## Resultados

Se compararon los tres métodos en las mismas **1.003 de 1.095 filas** del calendario (91,6 %). Se usaron los modelos entrenados con 2021–2022 y los cortes exactos elegidos en 2023. La categoría elevada sigue siendo PM10 de mañana estrictamente superior a 27 µg/m³. [Cobertura por estación](../output/pm10_weather_test_2025/cobertura_2025.csv)

| Indicador | Persistencia | Logística sin meteorología | Logística con meteorología |
| --- | ---: | ---: | ---: |
| Comienzos anticipados (de 27) | 0 | 6 | 9 |
| Continuaciones detectadas (de 86) | 86 | 81 | 85 |
| Días elevados detectados (de 113) | 86 | 87 | 94 |
| Falsas alarmas cuando hoy no es elevado | 0 | 13 | 18 |
| Falsas alarmas totales | 26 | 33 | 37 |
| Precisión de los avisos | 76,8 % | 72,5 % | 71,8 % |
| Recall | 76,1 % | 77,0 % | 83,2 % |

La meteorología aporta **tres comienzos más y siete días elevados más** frente a la logística base. En los días que partían de un PM10 bajo supuso **cinco falsas alarmas adicionales**. Los siete días elevados adicionales detectados se reparten entre Tres Olivos y Majadahonda. Con 27 comienzos, el tamaño de la mejora es incierto y su valor depende del coste de perder un episodio y del coste de un aviso erróneo. [Métricas generales](../output/pm10_weather_test_2025/metricas_2025.csv) · [Por contexto](../output/pm10_weather_test_2025/metricas_por_contexto.csv) · [Por estación](../output/pm10_weather_test_2025/metricas_por_estacion.csv) · [Predicciones](../output/pm10_weather_test_2025/predicciones_2025.csv)

El experimento es retrospectivo. Supone que el PM10 del día anterior está disponible a medianoche UTC. El archivo de GFS permite identificar el ciclo utilizado. La disponibilidad real a esa hora requiere comprobar las latencias de las fuentes.

Para reproducir la evaluación desde la raíz con los tres Parquet registrados en el manifiesto:

```powershell
.\.venv\Scripts\python.exe -m pip install pyarrow==19.0.1
.\.venv\Scripts\python.exe -m tfm_data.pipelines.evaluate_pm10_weather_2025
```
