# Primer mapeador ambiental: PM10 de 2024

## Objetivo y ejecución

Convertir la estructura original de MITECO a tablas con una fila por punto de muestreo y periodo, manteniendo el valor y su procedencia. Esta primera ejecución trabaja únicamente con PM10 de 2024; no aplica todavía el proceso a todos los contaminantes o años.

```powershell
python -m pm10_data.pipelines.prepare_air
python -m unittest discover -s tests -v
```

El programa comprueba las huellas de los originales y verifica la magnitud y unidad en los metadatos. Requiere pandas y openpyxl para leer la metainformación Excel. Los resultados están en `data/interim/air/pm10_2024/`.

## Clases y funciones

En `pm10_data/mappers/air.py`:

- `AirContext`: año, contaminante, magnitud, unidad y procedencia.
- `AirQualityReader`: lectura de un CSV dentro de un ZIP, sin extraer ni cambiar el original.
- `AirQualityMapper`: conversión a filas, normalización de fechas, códigos y concentraciones.
- `AirQualityValidator`: claves completas y únicas y coherencia temporal.
- `summarize_hours`: calcula una media diaria por punto cuando hay horas suficientes.
- `combine_daily_measurements`: resuelve el solapamiento entre el diario original y el derivado horario.
- `summarize_year`: describe cobertura y media por punto de muestreo durante el año.

La lectura, la transformación y la escritura se mantienen separadas. Se procesan bloques horarios para limitar el consumo de memoria.

## El primer concepto: pasar columnas a filas

Original simplificado:

| Punto | Año | Mes | D01 | D02 |
| --- | --- | --- | --- | --- |
| 01022001_10_47 | 2024 | 2 | 12.5 | 8.0 |

Normalizado:

| Punto | Fecha | Concentración |
| --- | --- | --- |
| 01022001_10_47 | 2024-02-01 | 12.5 |
| 01022001_10_47 | 2024-02-02 | 8.0 |

Se utiliza `DataFrame.melt`. El ejemplo es didáctico y sus valores no son una cita de las mediciones originales.

## Fechas y ausencias

La documentación oficial indica decimales con punto, horas referidas a UTC y asignación al final del intervalo. Por tanto, `H01` de un día termina a la 01:00 UTC y `H24` termina a las 00:00 UTC del siguiente. Se conserva por separado el día de muestreo (`fecha`) para no atribuir esa última hora a otro día al agregar. Las fechas horarias exportadas conservan el desplazamiento UTC explícito.

Los días inexistentes al final de un mes se eliminan solo si están vacíos. Un valor en el 30 de febrero detiene la transformación. El 29 de febrero se conserva en años bisiestos. Una fecha horaria imposible siempre produce un error.

Una celda vacía puede significar ausencia de medida o dato invalidado en origen; no podemos distinguir ambos motivos. Se mantiene como ausente, sin sustituirla por cero. Los negativos se conservan con el estado `negativa_pendiente_revision` y se excluyen de medias por una decisión exploratoria conservadora. No se afirma que todos los negativos sean códigos de error. No se recortan las concentraciones altas por su magnitud.

Fuente de estas convenciones de intercambio: https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/formatodatoscsvmiteco_web_tcm30-501420.pdf

## Cobertura y solapamientos: decisiones del proyecto

Los siguientes criterios son configurables y exploratorios; no constituyen una evaluación del cumplimiento de límites legales:

1. La media derivada de horas se acepta con al menos 18 valores horarios válidos de 24. Se conserva el número de horas, también cuando no se acepta la media.
2. Para el mismo punto y día, se prioriza el diario original válido. Si falta o se ha marcado para revisión, se permite usar una media horaria con cobertura suficiente. Las diferencias entre ambas medidas se registran, sin ocultarlas ni afirmar que son equivalentes.
3. Equipos o técnicas diferentes de una estación conservan sus propios puntos de muestreo. No se promedian ni se fusionan como si fueran una única serie.
4. Se presenta una media anual para análisis cuando hay datos diarios aceptados para al menos el 75 % del año natural. En 2024 el denominador es 366 días. Este criterio no se adapta todavía a fechas de alta o baja de las estaciones.

El resumen anual usa días con el mismo peso. Conserva una media de los días disponibles incluso con baja cobertura, pero la columna `media_anual_analisis` queda vacía cuando no se cumple el criterio. Los metadatos se unen sin descartar puntos que no encuentren estación; se marcan para revisión.

## Archivos de salida

Las mediciones completas y los diarios derivados y combinados se guardan como CSV comprimidos (`.csv.gz`). Pandas puede abrirlos directamente con `pd.read_csv`, y conviene indicar `dtype` para conservar ceros iniciales al releer códigos. Los archivos con fechas requieren `parse_dates` al releerse; `fin_periodo_utc` debe conservar UTC.

- `mediciones_diarias.csv.gz`: días normalizados del original, incluidos ausentes reales.
- `mediciones_horarias.csv.gz`: horas normalizadas, con fin del intervalo en UTC.
- `diarias_derivadas_horarias.csv.gz`: medias y cobertura horaria.
- `diarias_combinadas.csv.gz`: un registro por punto y día después de aplicar la prioridad.
- `solapamientos.csv.gz`: coincidencias y diferencias entre fuentes del mismo punto.
- `resumen_anual_punto_muestreo.csv`: cobertura, medias y metadatos por serie.
- `incidencias_diarias.csv`: valores negativos pendientes de revisión.
- `resumen.json`: recuentos y criterios usados.

Todavía no existe una exposición provincial ni un cruce con sanidad. El siguiente paso será revisar incidencias, diferencias y representatividad de estaciones antes de ampliar a otros contaminantes y años.
