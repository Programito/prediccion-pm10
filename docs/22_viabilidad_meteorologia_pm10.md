# Viabilidad de añadir previsiones meteorológicas al PM10

La prueba de acceso obtuvo **12 filas de previsión** para cuatro fechas y tres estaciones. Se descargaron 16 mensajes GRIB2 de GFS mediante peticiones HTTP por rango, con un total de 11,66 MB transferidos. Se comprobó la fecha de inicio y de validez dentro de cada mensaje. El piloto verifica que podemos construir las variables de viento y precipitación y que dos estaciones comparten celda en la malla de 0,25°. [Muestra extraída](../output/pm10_weather_feasibility/muestra_gfs.csv) · [URLs, rangos y huellas de los mensajes](../output/pm10_weather_feasibility/mensajes_gfs.json)

| Fuente | Cobertura y resultado de la comprobación |
| --- | --- |
| GFS operativo en NCAR | Su catálogo incluye ciclos desde 2015 y cubre el periodo original de PM10. El acceso a los archivos antiguos desde este entorno queda por verificar. [Catálogo NCAR GDEX](https://gdex.ucar.edu/datasets/d084001/) |
| GFS operativo de NOAA en AWS | Se extrajeron los campos del piloto inicial y de 60 fechas mensuales de 2021 a 2025. La cobertura diaria de todo el periodo queda por comprobar. [Archivo NOAA GFS](https://registry.opendata.aws/noaa-gfs-bdp-pds/) |
| Open-Meteo Single Runs | Expone ciclos individuales. La primera cobertura documentada es IFS desde marzo de 2024 y usa retrospectivas para el inicio de la serie. El periodo es insuficiente para reproducir el entrenamiento original desde 2017. [Documentación Single Runs](https://open-meteo.com/en/docs/single-runs-api) |

## Endpoint utilizado y formato original

La muestra se descargó del archivo operativo de **NOAA GFS** alojado en el bucket público `noaa-gfs-bdp-pds` de Amazon S3. Se usó el ciclo `12` y la cuadrícula `0p25`. [Registro del archivo NOAA GFS](https://registry.opendata.aws/noaa-gfs-bdp-pds/)

| Petición HTTP | Formato y contenido |
| --- | --- |
| `GET https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{AAAAMMDD}/12/atmos/gfs.t12z.pgrb2.0p25.f{HHH}.idx` | Índice de texto ASCII delimitado por `:`. El piloto usa el desplazamiento inicial de cada mensaje en bytes y su identificador, nivel y descripción de plazo. El desplazamiento del siguiente mensaje permite calcular dónde termina el actual. |
| `GET https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{AAAAMMDD}/12/atmos/gfs.t12z.pgrb2.0p25.f{HHH}` con cabecera `Range: bytes=inicio-fin` | Mensaje binario GRIB2. La respuesta `206 Partial Content` entrega un campo de la cuadrícula para un ciclo y plazo. |

`AAAAMMDD` es la **fecha de inicio del ciclo**, el día anterior a la fecha objetivo en este piloto. `HHH` es el plazo desde el inicio, en horas con tres dígitos. Cada campo original contiene valores en una malla geográfica, además de la fecha y hora de inicio y de validez. Las fechas y horas se leen con ecCodes como enteros `AAAAMMDD` y `HHMM` y se comprueban en UTC. [Ejemplo del índice descargado](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20251230/12/atmos/gfs.t12z.pgrb2.0p25.f036.idx)

Los primeros ciclos de 2021 se recuperaron desde la ruta histórica, que omite `/atmos`. Si la primera ruta devuelve HTTP 404, el extractor comprueba la ruta histórica y usa el índice y los rangos del archivo que encuentre. [Ejemplo de la ruta histórica](https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20210114/12/gfs.t12z.pgrb2.0p25.f012.idx)

| Campo GRIB2 (`campo` en el manifiesto) | Nivel | Plazo utilizado | Tipo y unidad del valor en cada celda |
| --- | --- | --- | --- |
| `UGRD` (`wind_u`) | 10 m sobre el suelo | +24 h | Decimal con signo, m/s. Componente este del viento. |
| `VGRD` (`wind_v`) | 10 m sobre el suelo | +24 h | Decimal con signo, m/s. Componente norte del viento. |
| `APCP` (`rain_start`) | Superficie | Acumulado de 0 a +12 h | Decimal, kg/m². Equivale numéricamente a mm de lámina de agua. |
| `APCP` (`rain_end`) | Superficie | Acumulado de 0 a +36 h | Decimal, kg/m². Equivale numéricamente a mm de lámina de agua. |

El manifiesto JSON tiene un objeto por mensaje, con `campo`, `url` e `indice` como texto, `rango` como par de enteros inclusivos, `bytes` como entero, `sha256` como texto hexadecimal y `inicio_ciclo_utc` y `validez_utc` como fechas y horas ISO 8601 en UTC. [Peticiones y huellas de los 16 mensajes](../output/pm10_weather_feasibility/mensajes_gfs.json)

## Mapeo y columnas de salida

Para el día objetivo D, el piloto usa el ciclo GFS iniciado el día anterior a las **12:00 UTC**. El inicio del ciclo precede 12 horas a la emisión simulada de las 00:00 UTC de D. Es un margen de trabajo y la hora exacta de publicación de cada mensaje no figura en la extracción. La fecha de inicio del ciclo indica el instante de referencia del modelo. [Inicio de ciclo y disponibilidad de previsiones](https://open-meteo.com/en/docs/single-runs-api)

El script lee las coordenadas de `COD_LOCAL`, `LATITUD_G` y `LONGITUD_G` del Excel de MITECO. `fetch_fields()` selecciona los mensajes del índice y comprueba sus rangos. `decode()` valida las fechas y obtiene con ecCodes el valor de la celda más cercana a cada estación. `map_daily_weather()` comprueba la coherencia de las celdas y transforma los cuatro campos en las variables finales. [Extracción](../scripts/pilot_gfs_weather.py) · [Mapeador](../pm10_data/mappers/gfs_weather.py)

El CSV usa coma como separador, punto decimal y UTF-8 con BOM. Cada fila corresponde a una estación y una fecha objetivo. La clave para un futuro cruce con PM10 es `codigo_estacion` + `fecha_objetivo`.

| Columna | Construcción | Tipo lógico y unidad |
| --- | --- | --- |
| `codigo_estacion` | Identificador de estación del Excel de MITECO de 2024. | Texto identificador |
| `fecha_objetivo` | Día D en UTC. | Fecha ISO |
| `inicio_ciclo_utc` | Ciclo GFS del día anterior a las 12:00 UTC. | Fecha y hora ISO en UTC |
| `latitud_gfs` | Latitud de la celda GFS más cercana a la estación. | Decimal o nulo, grados |
| `longitud_gfs` | Longitud de la misma celda, expresada en el intervalo [−180, 180). | Decimal o nulo, grados |
| `viento_10m_mediodia_ms` | Magnitud de las componentes de viento a 10 m a las 12:00 UTC de D, plazo +24 h. | Decimal o nulo, m/s |
| `precipitacion_diaria_mm` | `APCP` a +36 h menos `APCP` a +12 h. Cubre de 00:00 UTC de D a 00:00 UTC del día siguiente. | Decimal o nulo, mm de equivalente de agua |
| `estado_viento` | Estado de calidad del viento. Se añadió después de la muestra inicial. | Texto |
| `estado_precipitacion` | Estado de calidad de la precipitación. Se añadió después de la muestra inicial. | Texto |

Tres Olivos y Majadahonda caen en la celda **40,50° N, 3,75° O**. San Martín de Valdeiglesias cae en **40,25° N, 4,50° O**. En este planteamiento, la meteorología puede distinguir días y las dos celdas, con el mismo valor de viento y precipitación para las dos estaciones de la primera celda en cada fecha.

## Nulos y valores extremos

La extracción comprueba la integridad de los mensajes, el ciclo y la validez. Si falla el acceso o la lectura de un mensaje, registra la incidencia con la fecha, el plazo y la URL. Se conserva la fila y el predictor afectado queda vacío. Para un GRIB2 con mapa de presencia se usa el indicador de la celda elegida. Si ecCodes informa valores ausentes sin mapa de presencia, se comprueba su valor de ausencia.

| Estado | Tratamiento |
| --- | --- |
| `valido` | Se conserva el valor calculado. |
| `sin_mensaje` | Faltó uno de los mensajes necesarios o falló su lectura. Se conserva como nulo. |
| `ausente_grib` | La celda contiene un valor señalado como ausente. Se conserva como nulo. |
| `no_finito` | Algún valor necesario o su resultado es `NaN` o infinito. Se conserva como nulo. |
| `celda_incoherente` | Los campos disponibles apuntan a celdas diferentes. Ambos predictores quedan nulos. |
| `acumulado_incoherente` | Algún acumulado o la diferencia del día es inferior a −0,01 mm. La precipitación queda nula. |
| `ajuste_tolerancia` | Algún acumulado o la diferencia presenta un negativo dentro de 0,01 mm. Una diferencia negativa se ajusta a cero y se registra la marca. |

Los valores altos finitos se conservan. La muestra permite comprobar magnitudes observadas, con alcance limitado para caracterizar los extremos de toda la serie. [Auditoría de huecos y picos de PM10](17_auditoria_huecos_y_picos_pm10.md)

## Auditoría mensual de 2021–2025

Se eligió el **día 15 de cada mes**, con el ciclo de las 12:00 UTC del día anterior. Se recuperaron **60 de 60 fechas** y **180 de 180 filas de estación** con ambas variables válidas. La ruta histórica permitió recuperar los tres ciclos de enero a marzo de 2021, que daban 404 bajo `/atmos`. [Cobertura por fecha](../output/pm10_weather_feasibility/monthly/cobertura_por_fecha.csv) · [Muestra mensual](../output/pm10_weather_feasibility/monthly/muestra_gfs.csv) · [Manifiesto de 240 mensajes](../output/pm10_weather_feasibility/monthly/mensajes_gfs.json)

En la muestra, el viento a mediodía va de **0,58 a 8,99 m/s** y la precipitación diaria de **0 a 18,69 mm**. El mapeador marcó las 180 filas como válidas. La comprobación de nulos se verificó además con un GRIB2 que tenía una celda ausente señalada en su mapa de presencia.

La ejecución final recibió **182,1 MB** entre los mensajes y los índices y duró **80,8 segundos** con cuatro fechas en paralelo. La media de **3,04 MB por fecha** equivale a unos **5,54 GB** para los 1.826 días de 2021–2025 si se mantiene el tamaño medio de la muestra. Los 60 días completos respaldan la viabilidad del acceso. Los huecos entre las fechas muestreadas se conocerán al ampliar la extracción. [Resumen de la ejecución](../output/pm10_weather_feasibility/monthly/resumen.json)

## Espacio en disco del histórico diario

Cada mensaje descargado contiene un campo de la cuadrícula mundial. El extractor lo procesa en memoria, selecciona las dos celdas de interés y guarda los valores correspondientes a las tres estaciones. Los mensajes GRIB2 se descartan después de procesarlos. El manifiesto conserva las URLs, los rangos de bytes, las fechas y las huellas SHA-256 de los mensajes utilizados.

La estimación escala los tamaños medidos en 60 fechas a los **1.826 días de 2021–2025** con el mismo esquema de nueve columnas. Con una fila por estación y fecha, el CSV tendría **5.478 filas** si se incluye todo el calendario.

| Concepto | Medido en el piloto mensual | Estimado para cinco años |
| --- | ---: | ---: |
| Datos transferidos, incluidos los índices | 182,1 MB | 5,54 GB |
| CSV final de las tres estaciones | 16.429 bytes | 500 KB |
| Manifiesto JSON con la procedencia | 121.661 bytes | 3,70 MB |
| Espacio en disco para el CSV y el manifiesto | 138.090 bytes | 4,20 MB |

Se usan unidades decimales. La transferencia real puede variar con el tamaño de los mensajes de cada fecha. El espacio estimado corresponde al CSV y al manifiesto con el formato actual. [CSV del piloto](../output/pm10_weather_feasibility/monthly/muestra_gfs.csv) · [Manifiesto del piloto](../output/pm10_weather_feasibility/monthly/mensajes_gfs.json)

## Extracción del histórico diario

La opción `--daily` solicita el ciclo del día anterior para cada fecha entre el 1 de enero de 2021 y el 31 de diciembre de 2025. Reutiliza las 60 fechas ya comprobadas en la auditoría mensual. Guarda un resultado temporal por fecha en `tmp/gfs_daily_2021_2025/` y lo reutiliza al ejecutar de nuevo el comando. Cada fecha conserva una fila para cada una de las tres estaciones, con campos vacíos y estados de calidad si faltan datos.

El destino es `data/interim/weather_forecasts/gfs_2021_2025/`. Incluye el CSV `previsiones_gfs_diarias.csv`, la cobertura y procedencia por fecha y las incidencias. Los bytes de la cobertura describen los mensajes e índices recibidos, incluidas las fechas recuperadas del piloto.

Se procesaron las **1.826 fechas** previstas. Se verificaron **5.478 filas únicas** por estación y fecha, de las que **5.463** tienen viento y precipitación válidos. Las **1.821 fechas completas** representan el **99,73 %** del calendario. El 1 de enero y el 4, 5, 7 y 8 de febrero de 2021 quedaron con ambos campos vacíos en las tres estaciones. Los índices de los tres plazos devolvieron HTTP 404 en las rutas probadas. De 2022 a 2025 se obtuvieron las dos variables para todas las fechas. [Tabla diaria](../data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv) · [Cobertura por fecha](../data/interim/weather_forecasts/gfs_2021_2025/cobertura_por_fecha.csv) · [Incidencias](../data/interim/weather_forecasts/gfs_2021_2025/incidencias.json)

Los **7.284 mensajes** y sus índices representan **5,52 GB transferidos**, incluidas las fechas recuperadas del piloto. El CSV ocupa **495 KB** y el conjunto de archivos de entrega ocupa **4,25 MB**. Las descargas originales de GRIB2 se procesaron en memoria. [Manifiesto](../data/interim/weather_forecasts/gfs_2021_2025/mensajes_gfs.json) · [Resumen de la ejecución](../data/interim/weather_forecasts/gfs_2021_2025/resumen.json)

```powershell
.\.venv\Scripts\python.exe -c "import sys, runpy; sys.path.append('tmp/weather_dependencies'); runpy.run_path('scripts/pilot_gfs_weather.py', run_name='__main__')" --daily --workers 24
```

## Alcance del siguiente experimento

Los portales oficiales regional y municipal ofrecen datos horarios de calidad del aire en 2025. Ese año es un candidato a evaluación independiente después de verificar códigos, técnicas, controles de validez, convención horaria y cobertura en las tres estaciones. Se pueden reservar las concentraciones de ese año hasta fijar las reglas del experimento. [Comunidad de Madrid](https://datos.comunidad.madrid/dataset/calidad_aire_datos_historico) · [Ayuntamiento de Madrid](https://datos.madrid.es/dataset/201200-0-calidad-aire-horario/downloads)

Al comparar la logística con y sin meteorología, ambas variantes deben usar las mismas filas y particiones del periodo que realmente tenga cobertura. La métrica de interés es cuántos comienzos anticipa cada una con un presupuesto de falsas alarmas fijado en validación. Este piloto verifica acceso y extracción. La utilidad predictiva queda por medir.

El cruce de 2021–2024 ya cuantifica la cobertura, las exclusiones y los comienzos de episodio disponibles para esa comparación. [Tabla común de PM10 y GFS](23_cruce_pm10_meteorologia.md)

## Reproducción de la auditoría mensual

Desde la raíz, instalar el lector GRIB2 en una carpeta temporal y ejecutar el script:

```powershell
.\.venv\Scripts\python.exe -m pip install --target tmp/weather_dependencies eccodes==2.50.1
.\.venv\Scripts\python.exe -c "import sys, runpy; sys.path.append('tmp/weather_dependencies'); runpy.run_path('scripts/pilot_gfs_weather.py', run_name='__main__')" --monthly
```
