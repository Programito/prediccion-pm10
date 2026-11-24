# Casos de estudio para la defensa

La pantalla **Casos** del explorador recorre tres ejemplos de Madrid y una falsa alarma de contraste. Los materiales están preparados; el ensayo con el autor sigue pendiente. Son ejemplos retrospectivos de pruebas ya conocidas, no nuevos experimentos independientes. Barcelona conserva su experimento separado en **Experimentos**.

## Generación y procedencia

Ejecutar desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_case_studies
```

El exportador no carga ni entrena modelos. Lee predicciones y explicaciones guardadas, comprueba las decisiones con sus cortes, reconstruye Ridge y verifica que las fuentes y todos los archivos de modelos permanecen idénticos. Produce `output/case_studies/resumen.json` y 14 extractos CSV UTF-8 con BOM. El informe conserva rutas de origen, formatos y huellas SHA-256; no contiene una fecha de ejecución variable, por lo que es reproducible byte a byte.

| Origen local | Formato | Uso |
| --- | --- | --- |
| `output/pm10_final_2024/predicciones_regresion.csv` | CSV | Observaciones y predicciones originales de Ridge y persistencia |
| `output/pm10_explanations/explicaciones.json` | JSON | Intercepto, coeficientes, entradas transformadas y aportaciones por caso |
| `data/interim/pm10_prediction/tabla_modelos_completa.csv` | CSV | Entradas originales y fechas de disponibilidad simulada |
| `data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv` | CSV | Contexto observado MITECO de 2024 |
| `output/pm10_weather_test_2025/pm10_diario_2025.csv` | CSV | Contexto EEA de 2025, medias de al menos 18 observaciones horarias válidas |
| `output/pm10_weather_test_2025/predicciones_2025.csv` | CSV | Probabilidades, etiquetas y decisiones de las dos logísticas y persistencia |
| `data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv` | CSV | Previsiones archivadas de viento y precipitación |
| `docs/reference/pm10_weather_test_2025.json` | JSON | Cortes elegidos en 2023, entrenamiento y protocolo congelado |

Los endpoints y formatos públicos que originaron estas tablas se describen en [fuentes](15_fuentes_endpoints_formatos.md), [NOAA](22_viabilidad_meteorologia_pm10.md) y [EEA](25_prueba_meteorologia_2025.md). Aquí no se descarga de nuevo ningún original.

## Caso 1: concentración habitual

Regla fijada sin usar errores: entre los 906 casos evaluados en Madrid en 2024 con PM10 observado ≤ 27 µg/m³, elegir el de menor distancia a la mediana de concentración (10 µg/m³). Desempatar por código de estación y después por fecha, en orden ascendente. Se selecciona Tres Olivos, **10 de abril de 2024**.

- Observado: 10 µg/m³; día anterior y persistencia: 6,8.
- Ridge: 12,421895; error absoluto: 2,421895; persistencia: 3,2.
- Guion: explicar la fila, el momento de emisión, la referencia y ambos errores. Reconstruir Ridge con el intercepto y las 15 aportaciones.

El criterio usa el objetivo observado únicamente para escoger una ilustración retrospectiva; no ajusta el modelo. «Habitual» describe la concentración, no la representatividad multivariante ni un error típico. El contexto puede incluir días con concentraciones diferentes. Un acierto individual no prueba superioridad global.

## Caso 2: pico subestimado

Tres Olivos, **31 de octubre de 2024**. Observado: 156 µg/m³; persistencia: 77; Ridge: 45,726167. Error absoluto: 79 frente a 110,273833. Mostrar que una mejora global pequeña puede coexistir con infraestimación grave de un pico. Abrir la explicación completa de Ridge desde el caso.

Las aportaciones describen el cálculo aditivo del modelo sobre entradas transformadas; no identifican causas del episodio. La salida es `max(0, intercepto + suma de aportaciones)`.

## Caso 3: comienzo y falsa alarma

Ambas logísticas se entrenaron en 2021–2022 y sus cortes se seleccionaron en 2023. No hay reajuste en 2025. Se considera elevado PM10 **> 27 µg/m³**, umbral estadístico del proyecto, sin interpretación clínica.

| Caso de Tres Olivos | PM10 previo | PM10 objetivo | Probabilidad sin meteo | Probabilidad con meteo | Decisión con meteo |
| --- | --- | --- | --- | --- | --- |
| 5 de agosto de 2025 | 24,416667 | 42,333333 | 0,159116 | 0,211684 | Acierto: avisa |
| 22 de febrero de 2025 | 26,75 | 5,416667 | 0,192352 | 0,257977 | Falsa alarma: avisa |

El corte sin meteorología es 0,20072870154329542; con meteorología, 0,19904472278306495. La regla avisa cuando probabilidad ≥ corte. Persistencia avisa si PM10 previo > 27 y no produce una probabilidad estimada. En ambos ejemplos, persistencia y logística sin meteorología no avisan.

En los 891 casos con día previo no elevado hay 27 comienzos. Con meteorología se detectan 9 y se producen 18 falsas alarmas; sin meteorología, 6 y 13; persistencia, 0 y 0. React calcula este resumen desde las predicciones guardadas, no desde los dos ejemplos seleccionados.

Guion: distinguir concentración, probabilidad y corte. Relacionar más anticipación con falsas alarmas. No atribuir causalmente el acierto al viento: cambian variables, función ajustada y corte. Cambiar el corte para corregir estos ejemplos introduciría selección sobre una prueba conocida.

Se usa el ciclo GFS de D−1 a las 12:00 UTC para una emisión simulada D a las 00:00 UTC. El viento a 10 m es una previsión para mediodía (m/s) y la precipitación prevista es diaria (mm). Las coordenadas son de la celda GFS, no de la estación. Se comprueba fecha del ciclo y estado válido. No se ha verificado la latencia real de publicación del ciclo ni la disponibilidad inmediata del agregado observado de D−1; no se presenta como servicio operativo.

## Contexto, nulos y descargas

La gráfica abarca D−3 a D+3 e incluye una tabla accesible y un selector de fecha. Los días posteriores son contexto retrospectivo, nunca entradas de la predicción focal. Seleccionar otro día del contexto no cambia el caso. Los valores ausentes siguen siendo ausentes y se dibujan como huecos; no se interpolan ni rellenan con cero. No hay una nueva limpieza de outliers: los picos originales se conservan.

`GET /api/case-studies` devuelve JSON. `GET /api/case-studies/{id}/evidence/{archivo}` descarga únicamente los CSV permitidos del caso (`typical`, `peak`, `onset`, `false_alarm`); archivos o identificadores desconocidos devuelven 404.

| Extracto | Columnas y tipos | Interpretación |
| --- | --- | --- |
| `contexto.csv` | `date`: fecha ISO; `observed`: real nullable; solo regresión: `ridge`, `persistencia`: reales nullable | Siete días de contexto, concentraciones en µg/m³ |
| `predicciones.csv` | Conserva columnas originales: estación y nombre (texto), fechas ISO, PM10 y predicción (reales), modelo (texto) | Pareja Ridge/persistencia original; esquema completo en el CSV y diccionario de tablas |
| `entradas.csv` | Conserva fila supervisada completa: identificadores (texto), fechas ISO, PM10/retardos/medias/desviación y calendario cíclico (reales) | Entradas originales sin transformar; se verifica última observación D−1 |
| `aportes.csv` | `feature`: texto; `coefficient`, `transformed`, `contribution`: reales | Entrada transformada × coeficiente = aportación en µg/m³ |
| `avisos.csv` | `codigo_estacion`, `fecha_objetivo`, `NOMBRE`, `contexto`, `modelo`: textos; PM10: reales; `observado`, `aviso`: enteros 0/1; `probabilidad_elevado`: real nullable | Probabilidad nula para persistencia significa «no aplica», no probabilidad cero |
| `meteorologia.csv` | Estación y estados: texto; objetivo: fecha; ciclo: instante UTC ISO; coordenadas, viento y precipitación: reales | Previsión anterior al objetivo, no meteorología observada futura |

Las descargas incluyen la fila original de cada caso; React presenta unidades, objetivo, error o aviso, sus límites y la huella de cada extracto. Los nombres técnicos y las unidades de las variables se pueden ampliar en el diccionario de Tablas tratadas y en [explicabilidad](31_explicabilidad_pm10.md).

## Ensayo pendiente

Recorrer los tres casos y contrastar el tercero con la falsa alarma. El autor debe poder explicar qué sabía el modelo, qué predijo, cómo se evaluó y qué conclusión no permiten los datos. Revisar después MAE global e intervalo bootstrap en Gráficos. La preparación de materiales no sustituye este ensayo ni el recorrido guiado del notebook.
