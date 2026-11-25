# Revisión de los 44 puntos de PM10 con baja cobertura en 2024

## Resultado

Se ha creado `data/interim/air/pm10_2024/revision_puntos_baja_cobertura.csv`. Contiene una fila por punto con la evidencia, la incidencia y el tratamiento propuesto. No se han eliminado registros ni modificado las tablas anteriores.

La tabla conserva la cobertura y las incidencias de la auditoría mensual y añade:

- Fechas declaradas de alta y baja de estación, en formato AAAA-MM-DD; una baja no informada sigue vacía.
- Indicadores de alta/baja durante el año y de si el intervalo declarado recorta el año natural.
- Red, provincia, municipio, tipo de estación y tipo de área.
- Lista de meses sin mediciones válidas y primera/última fecha válida observada.
- Mediana de días entre mediciones válidas y racha máxima de días consecutivos sin medida válida, incluidos los extremos del año.
- Archivos y miembros ZIP que permiten rastrear las mediciones, referencia de metadatos, motivo de revisión y tratamiento propuesto.

Las fechas son de la estación y su registro en la base oficial, no del inicio o fin de funcionamiento de cada equipo. La primera/última medida observada tampoco demuestra las fechas de actividad del punto.

## Evidencia encontrada

| Grupo | Puntos | Propuesta |
| --- | ---: | --- |
| Técnica manual gravimétrica (M) | 28 | Conservar y revisar el calendario de muestreo y la representatividad temporal antes de aplicar un umbral diario. |
| Otras técnicas, con meses completos sin mediciones válidas | 14 | Conservar y revisar los huecos y el historial del equipo; mantener pendiente su media anual principal. |
| Otras técnicas, con datos en todos los meses pero cobertura anual baja | 2 | Conservar y revisar frecuencia y distribución de ausencias; mantener pendiente su media anual principal. |

De los 28 manuales, 25 tienen alguna medida válida en todos los meses. Esto es compatible con un calendario discontinuo, pero no lo confirma. No se ha obtenido un calendario de muestreo programado por punto.

Ninguna de las 44 estaciones tiene un alta declarada durante 2024. Hay tres bajas declaradas el 31 de diciembre, que no reducen el denominador de días del año bajo una convención inclusiva. Las fechas de estación no explican por sí solas los huecos de estos puntos.

Los puntos pertenecen a estaciones de fondo (27), industriales (13) y de tráfico (4). Esa tipología debe conservarse al estudiar la representatividad provincial.

## Decisiones

- Cero exclusiones automáticas: todos los puntos siguen en las tablas intermedias.
- Los 44 casos continúan pendientes para la media anual principal. No se cambia el criterio anterior sin justificar el plan de muestreo o la selección de estaciones.
- El 75 % de días era un filtro exploratorio, no una regla universal para validar o descartar mediciones manuales.
- Una fecha de estación no demuestra que una ausencia sea una avería. La causa queda como no confirmada.
- No se ha completado todavía una evaluación normativa ni un cálculo de exposición provincial.

Fuente de metadatos: `data/raw/health_air_history/miteco_estaciones_2024.xlsx`, hojas `Estaciones_2024` y `Técnicas`. La segunda confirma que M identifica la técnica manual gravimétrica. La procedencia oficial y la huella del original están en `data/raw/health_air_history/sources.json`; el programa verifica la huella antes de usarlo.

## Reproducir

```powershell
python -m pm10_data.evaluation.station_review
python -m unittest discover -s tests
```

El resultado resumido se guarda también en `revision_puntos_baja_cobertura_resumen.json`. Antes de ampliar el histórico, conviene comparar una selección de estaciones automáticas de fondo con alternativas que incluyan series manuales temporalmente representativas, sin fusionar equipos automáticamente.
