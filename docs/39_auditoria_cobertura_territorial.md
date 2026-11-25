# Auditoría de los días excluidos en Madrid y Barcelona

La evaluación de regresión de 2024 utiliza 1.013 de 1.098 días-estación en Madrid y 801 de 1.098 en Barcelona. La auditoría explica cada exclusión mediante las tablas supervisadas y los calendarios diarios, sin imputar datos, ajustar modelos ni modificar las predicciones existentes.

En Barcelona, 40 días-estación carecen de objetivo y otros 257 tienen medición objetivo pero historial incompleto. Quedan fuera 46 de los 191 días elevados observados. Los casos calculados como evaluables se contrastan por estación y fecha con las predicciones guardadas de ambos modelos. Las entradas se registran con SHA-256 y se comprueba que no cambien durante la auditoría.

## Qué se cuenta

Cada fila del detalle corresponde a una estación y una fecha objetivo de 2024. Se exige el calendario completo de 366 días por estación. La concentración objetivo se contrasta con la observación diaria de esa fecha. La disponibilidad se recalcula a partir del objetivo y de las doce variables numéricas del protocolo y se compara con `fila_utilizable`.

Una predicción para D puede necesitar las mediciones entre D−14 y D−1. El detalle registra las variables ausentes y todas las fechas sin medición válida dentro de ese intervalo. Nunca utiliza D o una fecha posterior como entrada histórica. Una ausencia de un solo día puede afectar al objetivo de ese día y a las siguientes catorce predicciones potenciales.

Las causas se asignan por el primer bloque que falla, con este orden fijo: falta del objetivo, falta del último día observado, historial de 3 días, historial de 7 días, media de 14 días y otras variables. Las categorías son excluyentes y su suma, junto a las filas evaluables, coincide con el calendario. No identifican una causa exclusiva: una fila puede carecer de varias variables correlacionadas.

## Resultados del calendario de 2024

| Situación o primer bloque que falla | Madrid | Barcelona |
| --- | ---: | ---: |
| Calendario completo | 1.098 | 1.098 |
| Fila evaluable | 1.013 | 801 |
| Objetivo ausente | 14 | 40 |
| Último día observado ausente | 7 | 21 |
| Bloque de 3 días incompleto | 14 | 41 |
| Bloque de 7 días incompleto | 22 | 77 |
| Solo queda por completar la media de 14 días | 28 | 118 |
| Otras variables | 0 | 0 |
| Total excluido | 85 | 297 |

La columna `missingWithTarget` del análisis por variable cuenta ausencias cuando sí existe la medición objetivo. Estos recuentos se solapan y no deben sumarse. `soleMissingWithTarget` cuenta filas donde esa es la única variable numérica ausente. En Barcelona la media de 14 días falta en las 257 exclusiones con objetivo conocido y es la única variable ausente en 118 de ellas. Esto mide disponibilidad; no demuestra que retirar esa variable mejore la precisión.

## Estaciones y meses de Barcelona

| Estación | Días excluidos | Días elevados observados | Días elevados excluidos |
| --- | ---: | ---: | ---: |
| Rubí · Ca n’Oriol | 32 | 32 | 6 |
| Sant Celoni · Carles Damm | 91 | 70 | 13 |
| Sant Vicenç dels Horts | 174 | 89 | 27 |

Sant Vicenç concentra 174 de las 297 exclusiones. Los meses con más exclusiones, agregando las tres estaciones, son octubre con 46, noviembre con 44, julio con 31 y junio con 30. El desglose mensual conserva la diferencia entre objetivo ausente y objetivo conocido sin entradas completas.

## Días elevados y tramos afectados

El corte común es mayor de 27 µg/m³, el umbral estadístico del estudio. Las proporciones se calculan únicamente sobre objetivos observados; los días sin medición no pueden clasificarse.

| Grupo observado | Madrid | Barcelona |
| --- | ---: | ---: |
| Elevados excluidos / elevados observados | 10 / 117 = 8,5 % | 46 / 191 = 24,1 % |
| Otros excluidos / otros observados | 61 / 967 = 6,3 % | 211 / 867 = 24,3 % |

En el agregado de Barcelona la proporción excluida es parecida en ambos grupos, pero varía por estación. Esta comparación descriptiva no prueba que las ausencias sean aleatorias ni permite estimar el error de los días excluidos.

El informe agrupa tramos consecutivos observados por encima del umbral. En Sant Celoni queda fuera todo el tramo del 15 al 20 de noviembre, seis días y pico de 46 µg/m³ el día 18. En Sant Vicenç queda fuera el tramo del 17 al 20 de junio, cuatro días y pico de 42 µg/m³ el día 18. Los huecos y los límites del año pueden fragmentar episodios reales; los tramos no son una identificación completa de episodios ni de sus comienzos.

## Archivos y mapeo

El [pipeline](../pm10_data/pipelines/audit_regional_coverage.py) lee la tabla supervisada, el calendario diario y las predicciones de cada experimento. El [módulo de auditoría](../pm10_data/evaluation/coverage_audit.py) calcula las exclusiones y agregados. No importa modelos ni entrena estimadores.

Las entradas de Barcelona son `data/interim/experiments/barcelona/tabla_supervisada.csv`, `diario_2017_2024.csv` del mismo directorio y `output/experiments/barcelona/prueba_2024/predicciones.csv`. Madrid utiliza sus tablas originales en `data/interim/pm10_prediction/` y `data/interim/daily_pollution/`, junto con `output/pm10_final_2024/predicciones_regresion.csv`. Los CSV y ZIP originales conservan la [procedencia del experimento territorial](38_experimentos_madrid_barcelona.md).

Cada experimento escribe en `output/experiments/{territorio}/coverage_audit/`:

| Archivo | Granularidad y contenido |
| --- | --- |
| detalle.csv | Estación y fecha objetivo, concentración, estado de evaluación, causa y trazas de ausencias |
| cobertura.csv | Territorio o estación y mes, incluido mes 0 como agregado anual |
| variables.csv | Territorio o estación, mes y variable; ausencias totales, con objetivo conocido y como única variable ausente |
| episodios.csv | Estación y tramo consecutivo elevado observado, con pico y recuentos de evaluación y exclusión |
| resumen.json | Los agregados, tramos, etiquetas y rutas de entrada con sus huellas |

En `detalle.csv`, `codigo_estacion` y `NOMBRE` son texto, `fecha_objetivo` es una fecha ISO, `pm10_objetivo` es decimal o nulo en µg/m³ y `mes` es entero. `evaluada`, `objetivo_disponible`, `elevado_observado` y cada `ausente__{variable}` son booleanos. `motivo` es una categoría textual. `variables_ausentes` y `fechas_historial_ausentes` son listas serializadas con separador `|`; una lista vacía queda en blanco. Los CSV usan coma, punto decimal y UTF-8 con BOM. Los agregados son recuentos enteros y las concentraciones de los picos son decimales.

## Consulta en React y API

**Experimentos → Auditoría de cobertura** permite elegir Madrid o Barcelona y una estación o todas. Los resúmenes, causas, variables y tramos corresponden a todo 2024 para esa selección. La tabla de detalle añade filtros de mes y estado, con páginas de diez registros. Las fechas sin medición y los ceros se distinguen. Los filtros se aplican antes de paginar.

| Endpoint | Respuesta y parámetros |
| --- | --- |
| GET /api/experiments/barcelona/coverage?station=todas | JSON con año, umbral, etiquetas de causas, resumen anual, meses, variables, tramos con exclusiones y fuentes |
| GET /api/experiments/barcelona/coverage/rows?station=todas&month=0&status=excluded&page=1&size=10 | JSON con filas filtradas, total entero, página y tamaño enteros, indicador booleano hasNext y archivo de origen |

Las mismas rutas aceptan `madrid`. `station` debe ser una estación del experimento o `todas`; `month` es 0 para todo el año o un entero de 1 a 12; `status` es `all`, `excluded` o `evaluated`; `page` es un entero positivo y `size` puede ser 10, 25 o 50. Parámetros inválidos devuelven 400. Un territorio desconocido o una auditoría no generada devuelve 404. Los registros del detalle conservan los textos del CSV; React interpreta los números para mostrarlos. Los valores no disponibles aparecen como «Sin dato».

En el resumen JSON, `calendar`, `evaluated`, `excluded`, `unknownTarget`, `observedExcluded`, `elevatedObserved`, `elevatedExcluded`, `otherObserved` y `otherExcluded` son enteros. `reasons` relaciona códigos de causa con recuentos. Los tramos incluyen estación y nombre textuales, inicio, fin y fecha del pico ISO, pico decimal y días observados, evaluados y excluidos enteros.

## Reproducción y próximos experimentos

```powershell
.\.venv\Scripts\python.exe -m pm10_data.pipelines.audit_regional_coverage
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

La auditoría se ejecuta después de preparar y evaluar los experimentos. Las pruebas comprueban que una ausencia produce el patrón esperado de exclusiones, que la atribución no duplica casos, que las trazas son anteriores al objetivo, que se cuentan días elevados excluidos, que se rechazan entradas incoherentes y que la API filtra antes de paginar.

Una posible investigación posterior es medir disponibilidad y precisión con ventanas más cortas en validación de 2023, manteniendo explícita la distinción entre cambio de variables y cambio de cohorte. Los resultados de 2024 ya se conocen: cualquier modificación guiada por ellos debe tratarse como análisis posterior, con una nueva evaluación temporal independiente para sostener conclusiones adicionales.
