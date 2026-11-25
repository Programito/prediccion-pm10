# Auditoría mensual de PM10, 2024

Se genera con `python -m pm10_data.pipelines.audit_air_coverage`. El cálculo está en la clase `AirCoverageAuditor`, dentro de `pm10_data/evaluation/air_coverage.py`.

## Tablas generadas

En `data/interim/air/pm10_2024/`:

- `auditoria_cobertura_mensual.csv`: 5.868 filas, una por cada combinación de los 489 puntos y los 12 meses. Incluye meses completamente ausentes del fichero de mediciones.
- `auditoria_mensual_puntos_baja_cobertura.csv`: los 12 meses de cada uno de los 44 puntos con cobertura anual inferior al criterio del 75 %.
- `auditoria_resumen_puntos_baja_cobertura.csv`: una fila por cada uno de esos 44 puntos, con cobertura anual y recuentos mensuales.
- `auditoria_cobertura_resumen.json`: resumen de resultados y comprobaciones.

## Cómo interpretar las columnas

| Campo | Significado |
| --- | --- |
| `periodo` | Mes en formato AAAA-MM. |
| `dias_del_mes` | Días naturales; febrero de 2024 tiene 29. |
| `dias_con_registro` | Hay una fila en la tabla diaria combinada, tenga o no medida válida. |
| `dias_sin_registro` | No hay fila para ese punto y día en la tabla diaria combinada. |
| `dias_validos` | Hay una concentración aceptada para el análisis. Incluye valores cero reales. |
| `dias_ausentes` | Hay fila, pero la medición está vacía o invalidada en origen; no se distingue el motivo. |
| `dias_negativos` | Concentración negativa conservada para revisión y excluida del análisis. |
| `dias_horas_insuficientes` | El diario seleccionado procede de horas y no llega al mínimo exigido. |
| `dias_no_validos_con_registro` | Suma de ausentes, negativos y horas insuficientes. |
| `dias_validos_oficiales` / `dias_validos_derivados` | Separan el origen de las medidas aceptadas. |
| `cobertura_mensual` | Días válidos divididos entre días naturales; 0,8 representa el 80 %. |
| `media_dias_validos` | Media de los valores aceptados de ese mes. Si no hay ninguno queda vacía, no cero. |
| `mes_sin_mediciones_validas` | No hay ninguna medida aceptada durante el mes. |
| `archivos_origen` / `miembros_zip` | Archivos que sustentan la serie del punto durante el año; no garantizan que exista registro en cada mes. |

Las columnas de nombres y tipos de estación proceden de los metadatos ya incorporados al resumen anual. Los códigos se deben leer como texto para conservar ceros iniciales.

## Resultado inicial

De los 44 puntos con baja cobertura anual:

- 17 tienen al menos un mes completo sin mediciones válidas.
- 27 tienen alguna medición válida en cada mes, pero no alcanzan la cobertura anual exigida. Esto no garantiza que sus ausencias sean pequeñas, aleatorias o equilibradas.

La suma de días válidos de los 12 meses coincide con el resumen anual para los 489 puntos. También coinciden los denominadores y las coberturas anuales. Las categorías de días suman exactamente los días naturales de cada mes.

Esta auditoría describe los datos que tenemos. No identifica por sí sola fallos de sensores ni fechas de funcionamiento. Un mes vacío puede estar fuera del periodo de actividad del punto; habría que contrastarlo con metadatos antes de atribuir una causa. Tampoco certifica la exactitud física de las medidas.

La auditoría se basa en `diarias_combinadas.csv.gz`: ya incorpora la prioridad entre el diario oficial y el derivado horario. Para reconstruir una decisión concreta se puede contrastar con `mediciones_diarias.csv.gz`, `diarias_derivadas_horarias.csv.gz`, `solapamientos.csv.gz` y los originales.
