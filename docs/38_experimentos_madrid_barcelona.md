# Comparación de regresión entre Madrid y Barcelona

El estudio contiene dos experimentos territoriales independientes. Madrid conserva sus datos, modelos y resultados. Barcelona replica la regresión con historial de PM10 en tres estaciones de la provincia, fuera del municipio de Barcelona. Ambos entrenan en 2017–2022, validan en 2023 y evalúan 2024. Se comparan las muestras completas y una sensibilidad con fechas compartidas.

Ridge reduce el MAE frente a persistencia un 1,64 % en Madrid y un 10,61 % en Barcelona en sus respectivas muestras completas. Con solo las fechas completas compartidas, las mejoras son 3,84 % y 6,42 %. Cambiar de cohorte modifica la comparación; los resultados no atribuyen la diferencia a una causa territorial.

## Selección de las estaciones

Barcelona usa los puntos de fondo de la red constante provincial 2017–2024 ya preparada. Se exige presencia en los ocho años y ausencia de alertas por cambios de coordenadas mayores de 100 m o de tipo de área. Se eligen las tres mejores coberturas mínimas anuales; los desempates usan cobertura media y código. La selección no usa errores de predicción. El criterio incluye disponibilidad del año de prueba, igual que la selección histórica del proyecto, y limita la lectura prospectiva.

| Código | Estación | Área | Menor cobertura anual 2017–2024 |
| --- | --- | --- | ---: |
| 08184006 | Rubí · Ca n’Oriol | Urbana | 95,9 % |
| 08202001 | Sant Celoni · Carles Damm | Suburbana | 93,7 % |
| 08263001 | Sant Vicenç dels Horts · Ribot–Sant Miquel | Suburbana | 92,1 % |

L’Hospitalet aparece como candidata con cobertura mínima del 83,8 % y queda fuera al aplicar el límite de tres puntos. Barcelona no reproduce la combinación urbana, suburbana y rural de Madrid; no hay una estación rural en estas candidatas elegibles. Las muestras representan puntos concretos y no toda la exposición provincial.

Las candidatas, selección y coordenadas se conservan en [candidatas.csv](../data/interim/experiments/barcelona/candidatas.csv) y [estaciones.csv](../data/interim/experiments/barcelona/estaciones.csv). La base de selección es `data/interim/provincial_feasibility/history/puntos_red_constante.csv`, contrastada con `revision_coordenadas_red_constante.csv`. Las coordenadas se guardan como latitud y longitud en grados, desde `LATITUD_G` y `LONGITUD_G`.

## Fuentes y transformación

No fue necesario descargar nuevos originales. Se reutilizan los 16 ZIP nacionales de MITECO diarios y horarios de 2017–2024, con los endpoints, tamaños y SHA-256 del manifiesto `data/raw/health_air_history/sources.json`. Cada ZIP contiene el CSV PM10. El [manifiesto del experimento](../data/interim/experiments/barcelona/fuentes.json) conserva la información original, el miembro del ZIP y el número de filas seleccionadas.

`AirQualityReader.read_points` filtra los tres puntos por bloques antes de expandir las columnas diarias u horarias. `AirQualityMapper` valida códigos, fechas y concentraciones. `summarize_hours` obtiene un diario con al menos 18 horas válidas y `combine_daily_measurements` aplica la misma prioridad de la fuente diaria que en Madrid. Se completa el calendario por estación conservando los ausentes. [Mapeadores ambientales](../tfm_data/mappers/air.py)

La tabla diaria conserva valor original, estado, archivo y miembro del ZIP. `pm10_valido` queda nulo cuando la concentración no es válida o falta. Los negativos no se aceptan como concentraciones válidas. Los picos positivos válidos se conservan, sin recorte ni eliminación estadística. No se imputan ausencias. Las predicciones de regresión se restringen a cero como mínimo, igual que en Madrid.

`PM10ForecastMapper` construye el objetivo del día siguiente, retardos de PM10, medias de 3, 7 y 14 días, desviación de 7 días y calendario cíclico. Los cálculos se agrupan por estación y utilizan como máximo el día anterior al objetivo. El identificador de estación se codifica dentro del adaptador. Los transformadores se ajustan exclusivamente con entrenamiento. [Mapeador predictivo](../tfm_data/mappers/pm10_forecast.py)

| Salida en data/interim/experiments/barcelona/ | Qué representa una fila | Clave |
| --- | --- | --- |
| candidatas.csv | Punto candidato y criterio de selección | punto_muestreo |
| estaciones.csv | Punto seleccionado y coordenadas | codigo_estacion |
| diario_2017_2024.csv | Día observado por estación, incluido el ausente | codigo_estacion + fecha |
| cobertura_anual.csv | Cobertura y mayor ausencia consecutiva de un año | codigo_estacion + anio |
| cobertura_mensual.csv | Días válidos por mes | codigo_estacion + mes |
| tabla_supervisada.csv | Predicción potencial del siguiente día con sus entradas | codigo_estacion + fecha_objetivo |
| tabla_modelos_completa.csv | Fila con objetivo y todos los predictores disponibles | codigo_estacion + fecha_objetivo |
| cobertura_particiones.csv | Filas disponibles y utilizables de una partición | codigo_estacion + particion |

Las fechas diarias se exportan como ISO `AAAA-MM-DD`. La emisión simulada incluye zona UTC. Códigos y puntos son texto para conservar ceros iniciales; concentraciones, coordenadas, medias y proporciones son decimales; recuentos y año son enteros; indicadores de selección y disponibilidad son booleanos. Los CSV usan coma, punto decimal y UTF-8 con BOM. Las columnas heredadas mantienen el [diccionario de transformaciones](16_trazabilidad_mappers_tablas.md).

## Protocolo de entrenamiento y prueba

Se utilizan los mismos adaptadores y parámetros de Madrid: Ridge con alpha 10 y solver SVD, y Random Forest de 200 árboles con semilla 42 como candidato de validación. El pipeline comprueba la coincidencia de parámetros con la configuración original. El modelo de prueba de Barcelona se fija en Ridge antes del ajuste para comparar la misma especificación territorial. Random Forest obtiene un MAE de validación ligeramente menor en Barcelona, 4,459 frente a 4,510 de Ridge, pero no se cambia el modelo de la comparación tras ver ese resultado.

El [protocolo](../output/experiments/barcelona/protocolo.json) se escribe antes de entrenar e identifica variables, periodos, parámetros, filas, versiones y huella de la tabla. Los [modelos congelados](../output/experiments/barcelona/modelos_congelados.json) registran las huellas de los artefactos. La evaluación comprueba protocolo, modelo y datos antes de calcular las predicciones de 2024. No hay reajuste con validación ni prueba.

El umbral común para describir días elevados es **27 µg/m³**, fijado originalmente con el entrenamiento de Madrid. Se mantiene como corte numérico común para esta comparación de regresión. No corresponde al percentil 90 calculado de nuevo en Barcelona ni constituye un límite sanitario o legal. No se ha añadido clasificación ni meteorología de Barcelona en 2025.

## Cobertura y pérdida de filas

La [auditoría de exclusiones](39_auditoria_cobertura_territorial.md) contrasta cada fecha con las predicciones congeladas y permite consultar causas, variables, meses y tramos elevados en React.

Barcelona aporta 8.766 días-estación de calendario, de los que 8.540 tienen PM10 válido. Quedan 5.367 filas de entrenamiento, 889 de validación y 801 de prueba. Una ausencia interrumpe las ventanas completas y puede excluir varios días posteriores.

| Estación | Mediciones válidas en 2024 | Mayor ausencia consecutiva | Casos de prueba de 366 |
| --- | ---: | ---: | ---: |
| Rubí | 362 | 2 días | 334 |
| Sant Celoni | 359 | 2 días | 275 |
| Sant Vicenç dels Horts | 337 | 9 días | 192 |

El 73,0 % del calendario de prueba de Barcelona resulta evaluable, frente al 92,3 % de Madrid. La pérdida de filas es especialmente importante en Sant Vicenç. Los resultados describen las filas completas; no estiman el rendimiento en los días excluidos.

## Resultados de 2024

| Muestra completa | Madrid | Barcelona provincia |
| --- | ---: | ---: |
| Casos evaluados | 1.013 | 801 |
| MAE persistencia | 6,058 | 5,280 |
| MAE Ridge | 5,958 | 4,720 |
| Mejora relativa del MAE | 1,64 % | 10,61 % |
| RMSE Ridge | 10,475 | 7,012 |
| Sesgo Ridge | −0,190 | +0,067 |
| Días elevados evaluados | 107 | 145 |
| MAE Ridge en días elevados | 19,562 | 8,429 |
| MAE persistencia en días elevados | 18,252 | 8,221 |

Los errores y sesgos se expresan en µg/m³. La mejora relativa es `100 × (MAE persistencia − MAE Ridge) / MAE persistencia`. En ambos territorios Ridge tiene más MAE que persistencia en el subconjunto elevado, aunque mejore globalmente. El PM10 máximo observado en las muestras es 156 en Madrid y 78 µg/m³ en Barcelona; las distribuciones y episodios son diferentes.

El bootstrap utiliza el mismo calendario de 366 días, 5.000 réplicas, semilla 20261119 y bloques de 7, 14 y 28 días. Las estaciones de un territorio se remuestrean juntas; fechas sin casos aportan recuento y suma cero. El intervalo principal nominal del 95 % para MAE Ridge menos persistencia, con bloques de 14 días, es [−0,565; +0,288] en Madrid y [−0,766; −0,344] en Barcelona. Es un diagnóstico exploratorio condicionado a los modelos, la selección y la muestra. [Método y limitaciones del bootstrap](36_incertidumbre_pm10.md)

### Sensibilidad con fechas compartidas

Se intersectan las fechas con predicciones en las tres estaciones de cada territorio. Quedan **78 días y 234 casos por territorio**. Los mismos modelos congelados se evalúan en ese subconjunto; no se vuelven a ajustar. Las [fechas concretas](../output/experiments/comparacion/fechas_comunes.csv) permiten estudiar qué meses y episodios permanecen.

| Fechas completas compartidas | Madrid | Barcelona provincia |
| --- | ---: | ---: |
| MAE persistencia | 6,424 | 4,688 |
| MAE Ridge | 6,178 | 4,387 |
| Mejora relativa | 3,84 % | 6,42 % |

La sensibilidad iguala las fechas y el número de estaciones, pero reduce la muestra y puede cambiar la distribución de episodios. Los intervalos de las muestras completas no se aplican a este subconjunto. La comparación no mide transferencia del modelo de Madrid a Barcelona, ni demuestra superioridad general en un territorio.

## Consulta en React y API

**Experimentos** ofrece **Comparación**, **Madrid** y **Barcelona provincia**. La comparación alterna muestras completas y fechas compartidas, dibuja los MAE en una escala común y muestra incertidumbre y limitaciones. Cada territorio incluye cobertura por estación, errores mensuales, resultados elevados, candidatos de validación y una serie diaria con fechas de 2017–2024. Las predicciones de prueba solo se muestran en 2024. Las observaciones válidas se conservan incluso si falta predicción. Las tablas y la documentación muestran la procedencia local.

| Endpoint local | Respuesta | Contenido |
| --- | --- | --- |
| GET /api/experiments | JSON | Periodos, umbral, lista de experimentos, métricas, coberturas, intervalos, fechas compartidas, limitaciones y rutas con huellas |
| GET /api/experiments/barcelona/series?station=08184006&month=2024-10 | JSON | Serie mensual de una estación con observaciones y predicciones guardadas |
| GET /api/experiments/madrid/series?station=28079060&month=2024-10 | JSON | Mismo esquema para Madrid |

El endpoint de serie valida territorio, pertenencia de estación y mes de 2017–2024. Un territorio desconocido devuelve 404; una estación o mes incompatible devuelve 400. La respuesta contiene `experiment`, `station`, `month`, `source`, `observedSource` y `predictionsSource` como texto, `threshold` como número y `days` como lista. Cada día tiene `date` como fecha ISO, `evaluated` booleano y los números opcionales `observed`, `ridge` y `persistencia` en µg/m³. Un valor no disponible se omite del JSON y React lo presenta como «Sin dato»; el CSV diario mantiene los nulos. Los ceros observados se conservan como valores válidos.

En el resumen, cada experimento incluye `id` y `name` como texto; `trainingRows`, `validationRows` y `expectedStationDays` como enteros; `testCoverage` como proporción decimal; `summary`, `interval` y `observed` como objetos numéricos; y las listas `stations`, `monthly`, `levels` y `validationMetrics`. Las estaciones incluyen código y nombre, área, coordenadas decimales, recuentos de observación y prueba, mayor hueco y errores. `matchedDates` contiene fechas ISO y `matched` las métricas de esas fechas por territorio. [Frontend](../explorer/src/experiments.tsx) · [API](../explorer/server.py)

## Reproducción

Con los originales restaurados y las tablas históricas del proyecto disponibles, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.barcelona_experiment prepare
.\.venv\Scripts\python.exe -m tfm_data.pipelines.barcelona_experiment train
.\.venv\Scripts\python.exe -m tfm_data.pipelines.barcelona_experiment evaluate
.\.venv\Scripts\python.exe -m tfm_data.pipelines.barcelona_experiment compare
```

También se puede ejecutar `python -m tfm_data.pipelines.barcelona_experiment all`. Los resultados se guardan en `output/experiments/barcelona/`, los modelos en `models/experiments/barcelona/` y la comparación en `output/experiments/comparacion/`. El [pipeline](../tfm_data/pipelines/barcelona_experiment.py) registra la integridad de los artefactos protegidos de Madrid. El catálogo original sigue siendo el nacional ya documentado; no se necesita ampliar el paquete de fuentes.
