# Auditoría de huecos y picos de PM10

La auditoría cubre las tres estaciones de Madrid de 2017 a 2023. El entrenamiento usa objetivos hasta 2022 y la validación usa objetivos de 2023. La evaluación final de 2024 sigue reservada.

## Huecos en la tabla predictiva

Los recuentos agrupan por estación y año de la **fecha objetivo**. Las tres columnas de motivos son excluyentes. El calendario de 2017 empieza con un objetivo el 2 de enero porque la primera observación de entrada disponible es del día 1.

| Periodo | Candidatas | Solo falta el objetivo | Solo faltan predictores | Faltan ambos | Utilizables con 14 días | Utilizables con 7 días |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2017–2022 | 6.570 | 27 | 432 | 15 | 6.096 | 6.305 |
| 2023 | 1.095 | 3 | 51 | 2 | 1.039 | 1.062 |

Las 56 exclusiones de 2023 corresponden a Tres Olivos. Quitar `media_14_dias` recupera 209 filas de entrenamiento y 23 de validación. La cobertura de validación sube del 94,9 % al 97,0 %. En el arranque también faltan predictores hasta acumular suficientes días de historia. [Desglose por estación y año](../output/pm10_quality_audit/huecos_por_estacion_anio.csv)

## Comparación de ventanas

Se reutilizan las predicciones del Ridge publicado y se ajusta un Ridge con los mismos hiperparámetros y las mismas variables salvo `media_14_dias`. Cada variante se ajusta con sus filas completas de entrenamiento. La comparación de error usa las mismas fechas de validación para ambos modelos. Este diseño mide el efecto conjunto del cambio de variable y de las filas adicionales de entrenamiento.

| Validación 2023 | Filas | MAE Ridge 14 días | MAE Ridge 7 días | MAE persistencia |
| --- | ---: | ---: | ---: | ---: |
| Fechas comunes | 1.039 | 4,826 | 4,852 | 5,140 |
| Todas las fechas completas con 7 días | 1.062 | — | 4,850 | 5,159 |
| Fechas recuperadas con 7 días | 23 | — | 4,745 | 6,044 |

Las unidades del MAE son µg/m³. La variante de siete días gana cobertura con una subida de MAE de 0,027 µg/m³ en fechas comunes. Las 23 fechas recuperadas proceden de una sola estación. Se conserva el Ridge de 14 días como referencia del experimento y se registra la variante de siete días para comparar cobertura. [Resultados y predicciones por fecha](../output/pm10_quality_audit/comparacion_ventanas.csv)

## Revisión de picos

Se eligieron las tres concentraciones diarias más altas por estación en cada periodo, con la fecha más temprana como desempate. Se consultaron los días vecinos y las medidas horarias del mismo punto y fecha en los ZIP originales. Los 18 casos contaban con 21 a 24 horas válidas.

- Los nueve valores diarios oficiales difieren como máximo **0,5 µg/m³** de la media horaria disponible. Los otros nueve valores ya procedían de las horas y se reprodujeron al recalcularlos.
- El 15 de marzo de 2022 las tres estaciones registraron **283, 371 y 522 µg/m³**. Las medias horarias fueron **282,5, 370,81 y 521,92 µg/m³**, respectivamente. El día siguiente también presentó valores de **85, 114 y 155 µg/m³** en las tres estaciones.

La coherencia de estos registros respalda conservar los picos examinados. Este contraste comprueba consistencia entre registros y no establece la causa de los episodios. [Fechas, vecinos y valores horarios agregados](../output/pm10_quality_audit/revision_picos.csv)

## Rendimiento en días elevados

En las 1.039 fechas de validación del experimento original, 93 superan **27 µg/m³**, el percentil 90 de los objetivos disponibles de entrenamiento. El sesgo es la media de `predicción − observado`. Ambos errores se expresan en µg/m³.

| PM10 observado en 2023 | Filas | MAE Ridge | MAE persistencia | Sesgo Ridge | Sesgo persistencia |
| --- | ---: | ---: | ---: | ---: | ---: |
| > 27 µg/m³ | 93 | 15,47 | 14,71 | −13,30 | −6,10 |
| ≤ 27 µg/m³ | 946 | 3,78 | 4,20 | +1,57 | +0,67 |

Ridge mejora el MAE general, pero en el tramo elevado tiene mayor MAE que la persistencia en las tres estaciones. Conviene incluir el MAE y el sesgo en el tramo elevado junto al MAE general en las próximas comparaciones. [Métricas por tramo y estación](../output/pm10_quality_audit/metricas_por_tramo_y_estacion.csv)

Se puede regenerar la auditoría con `python -m pm10_data.pipelines.audit_pm10_quality`. Los resultados se guardan en `output/pm10_quality_audit/`.
