# De los originales a las tablas preparadas

El recorrido general es: **original conservado → lector → mapeador → validación → tabla normalizada → agregaciones y cruces → tabla para modelos**. Los mapeadores transforman DataFrames; los pipelines coordinan la lectura y escritura. No todas las tablas son una salida directa de un mapper: algunas proceden de auditorías, agregaciones o uniones.

El [catálogo de tablas](reference/table_catalog.csv) recoge las 22 tablas principales: ruta, productor, etapa, significado de una fila, filas y **lista completa de columnas**. Es un inventario del flujo principal, no de todos los archivos auxiliares o resultados de entrenamiento del repositorio.

## 1. Sanidad: `INEHealthMapper`

Código: [health.py](../tfm_data/mappers/health.py). Pipeline: [prepare_health.py](../tfm_data/pipelines/prepare_health.py).

Entrada: nueve CSV del INE, 2016–2024. `INEHealthReader` los lee como texto; `HealthContext` aporta año, tabla oficial y archivo. El mapeador admite las dos estructuras geográficas originales, selecciona los tres diagnósticos y normaliza territorios con `data/reference/territorios_ine.csv`. `INEHealthValidator` comprueba claves, duplicados, códigos y tasas.

| Entrada | Salida normalizada |
| --- | --- |
| Diagnóstico principal | `codigo_diagnostico`, `diagnostico_original` |
| Territorio único o jerarquía geográfica | `territorio`, `codigo_provincia`, `codigo_ccaa`, niveles geográficos |
| `Total` con formato español | `tasa_original`, `tasa_altas_por_100000` numérica |
| Contexto del manifiesto | `anio`, `fuente_tabla`, `archivo_origen` |

Salidas en `data/interim/health/`:

| Tabla | Filas | Qué representa una fila |
| --- | ---: | --- |
| `tasas_respiratorias_todos_niveles.csv` | 1.701 | Territorio, año y diagnóstico; incluye agregados |
| `tasas_respiratorias_provincias.csv` | 1.404 | Territorio provincial, año y diagnóstico: 52 × 9 × 3 |

Se conserva el nivel geográfico original. Las comunidades uniprovinciales se hacen corresponder con su provincia; Ceuta y Melilla conservan sus códigos territoriales. No se suman tasas de distintos territorios ni diagnósticos.

## 2. Aire: `AirQualityMapper`

Código: [air.py](../tfm_data/mappers/air.py). Pipeline detallado de 2024: [prepare_air.py](../tfm_data/pipelines/prepare_air.py).

Entrada: CSV de PM10 dentro de los ZIP diarios y horarios. `AirQualityReader` abre el miembro seleccionado; `AirContext` aporta procedencia, contaminante y unidad. `AirQualityValidator` comprueba las tablas normalizadas.

| Entrada | Transformación y salida |
| --- | --- |
| Provincia, municipio y estación | Códigos con ceros iniciales y `codigo_estacion` de ocho caracteres |
| `PUNTO_MUESTREO` | `punto_muestreo` y `tecnica`, conservando series distintas |
| `ANNO`, `MES`, `D01`…`D31` | De columnas a filas: una `fecha` y `concentracion` por punto y día |
| `ANNO`, `MES`, `DIA`, `H01`…`H24` | Una fila por hora, con `fin_periodo_utc` |
| Valor textual | `valor_original`, concentración numérica y `estado` |
| Archivo y miembro del ZIP | `archivo_origen`, `miembro_zip` |

Los días imposibles de relleno, como D31 de febrero, se eliminan si están vacíos; si contienen una medida se genera un error. Las fechas válidas con medidas ausentes se conservan.

Salidas en `data/interim/air/pm10_2024/`:

| Tabla | Filas | Productor y significado |
| --- | ---: | --- |
| `mediciones_diarias.csv.gz` | 178.304 | Mapper: punto y día, incluidos ausentes |
| `mediciones_horarias.csv.gz` | 3.326.208 | Mapper: punto y hora, incluidos ausentes |
| `diarias_derivadas_horarias.csv.gz` | 138.592 | `summarize_hours`: resumen diario de las horas |
| `diarias_combinadas.csv.gz` | 178.304 | `combine_daily_measurements`: selección diaria entre fuentes |
| `resumen_anual_punto_muestreo.csv` | 489 | `summarize_year` y unión con metadatos de estación |
| `solapamientos.csv.gz` | 138.592 | Auditoría de días presentes en ambas fuentes |
| `incidencias_diarias.csv` | 1 | Medida diaria negativa conservada para revisión |

Se requieren 18 horas válidas para aceptar un día derivado de horas. Se prefiere la medida diaria oficial válida; si falta, se utiliza la derivada válida del mismo punto y día. No se mezclan técnicas diferentes. El umbral anual del 75 % es un criterio exploratorio y no una evaluación normativa.

Las auditorías posteriores generan `auditoria_cobertura_mensual.csv` (5.868 filas), `auditoria_mensual_puntos_baja_cobertura.csv` (528) y `revision_puntos_baja_cobertura.csv` (44). Las explican [la auditoría mensual](05_auditoria_mensual.md) y [la revisión de puntos](06_revision_baja_cobertura.md).

## 3. Demografía: `INEDemographicsMapper`

Código: [demographics.py](../tfm_data/mappers/demographics.py). Pipeline: [prepare_demographics.py](../tfm_data/pipelines/prepare_demographics.py).

Entrada: selección del CSV INE 56945, filtrada previamente por sexo total, provincias y enero de 2017–2024. El mapper extrae códigos y años, convierte recuentos, excluye subtotales al sumar y comprueba que la suma de edades coincide con el total oficial en cada provincia y año.

Salidas en `data/interim/demographics/`:

| Tabla | Filas | Significado |
| --- | ---: | --- |
| `seleccion_original_enero_2017_2024.csv` | 42.848 | Filtrado previo: provincia, año y etiqueta de edad; todavía incluye subtotales |
| `demografia_provincial_2017_2024.csv` | 416 | Mapper: 52 territorios × 8 años |

La segunda contiene `codigo_provincia`, `anio`, `poblacion_total`, recuentos y proporciones de 0–14, 65 o más y 80 o más, `fecha_referencia_poblacion` y `fuente_demografia`. Los grupos 65+ y 80+ se solapan; no deben sumarse entre sí.

## 4. Agregaciones y cruces entre dominios

Estas tablas las elaboran funciones de evaluación y pipelines, después del mapeo:

| Tabla bajo `data/interim/` | Filas | Contenido |
| --- | ---: | --- |
| `provincial_feasibility/history/panel_red_variable.csv` | 416 | Provincia y año, sanidad y PM10 con selección de puntos variable |
| `provincial_feasibility/history/panel_red_constante.csv` | 416 | Mismas claves, indicador con puntos elegibles en todos los años |
| `initial_comparison/panel_con_demografia.csv` | 416 | Panel provincial cruzado con demografía |
| `daily_pollution/estaciones_muestra_madrid.csv` | 3 | Estaciones de la muestra predictiva y criterios de selección |
| `daily_pollution/pm10_madrid_diario_2017_2024.csv` | 8.766 | Tres estaciones × 2.922 días; calendario completo sin imputación |
| `daily_pollution/cobertura_muestra_por_anio.csv` | 24 | Cobertura de cada estación y año |

**416 filas no significan 416 medidas ambientales disponibles**: el panel variable tiene indicador en 316 filas y el constante en 232, correspondientes a 29 territorios durante ocho años. La media de una red de estaciones tampoco mide por sí sola la exposición de toda una provincia. El alcance y la sensibilidad están en [viabilidad histórica](08_viabilidad_historica.md).

La muestra diaria tiene 8.705 valores válidos y 61 ausencias. Se conservaron los huecos para que los retardos representen días de calendario reales.

## 5. Predicción: `PM10ForecastMapper`

Código: [pm10_forecast.py](../tfm_data/mappers/pm10_forecast.py). Pipeline: [prepare_pm10_forecast.py](../tfm_data/pipelines/prepare_pm10_forecast.py).

Entrada: muestra diaria con `codigo_estacion`, `fecha` y `pm10_valido`. El mapper comprueba claves, continuidad diaria y valores; ordena cada serie y construye:

- Observación del día t y retardos de 1, 2 y 6 días.
- Medias móviles de 3, 7 y 14 días y desviación de 7 días, usando información hasta t.
- Calendario del día objetivo, conocido de antemano.
- `fecha_objetivo = t+1` y `pm10_objetivo`, que se usa como etiqueta, no como predictor.
- Partición por año objetivo: entrenamiento 2017–2022, validación 2023 y prueba reservada 2024.
- Marcas de disponibilidad y de fila utilizable, sin rellenar ausencias.

La función adicional `label_elevated_pm10` incorpora la etiqueta de clasificación con umbral de 27 µg/m³, percentil 90 de objetivos disponibles de entrenamiento. Es una categoría relativa para el proyecto, no una alerta sanitaria o legal. El instante de emisión es una simulación retrospectiva: no acredita disponibilidad inmediata de datos reales.

Salidas en `data/interim/pm10_prediction/`:

| Tabla | Filas | Significado |
| --- | ---: | --- |
| `tabla_supervisada_pm10.csv` | 8.766 | Todas las filas de origen con variables, etiquetas y marcas, incluso las no utilizables |
| `tabla_modelos_completa.csv` | 8.148 | Filas utilizables: 6.096 de entrenamiento, 1.039 de validación y 1.013 de prueba reservada |

El entrenamiento utiliza una lista explícita de predictores. La partición de 2024 se evaluó después de fijar los modelos y umbrales. [Resultados de la prueba final](21_resultados_prueba_final_pm10.md)

Para consultar todas las columnas y actualizar los recuentos, utiliza el [catálogo de tablas](reference/table_catalog.csv) y el comando de regeneración descrito en [fuentes y formatos](15_fuentes_endpoints_formatos.md).

## 6. Piloto de previsiones meteorológicas GFS

El extractor localiza los mensajes GRIB2 de NOAA y lee los valores de la celda más próxima a cada estación. `map_daily_weather()` combina las componentes del viento, resta dos acumulados de precipitación y conserva los nulos con estados de calidad. La salida de la auditoría mensual contiene 180 filas, una por estación y fecha objetivo muestreada. [Campos originales, mapeo y tipos](22_viabilidad_meteorologia_pm10.md) · [Código del mapeador](../tfm_data/mappers/gfs_weather.py)
