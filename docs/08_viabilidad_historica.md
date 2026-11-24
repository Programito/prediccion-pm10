# Viabilidad provincial de PM10: 2017-2024

## Alcance

Se ha repetido el criterio provisional de 2024 para ocho años, de 2017 a 2024. Se utilizan originales diarios y horarios, metadatos anuales y tasas sanitarias del grupo respiratorio 1000 por residencia. Las huellas originales se comprueban antes de procesar cada año. Las unidades de PM10 se verifican en los metadatos anuales.

2016 permanece fuera de esta prueba: los datos horarios tienen un formato Excel distinto. No se ha sustituido ese año por ceros ni se ha afirmado disponer de nueve años procesados.

## Criterio aplicado

Se seleccionan puntos de estaciones de FONDO, presentes en el archivo horario, con técnica distinta de M y cobertura diaria aceptada de al menos el 75 % del año natural. Las medias horarias derivadas necesitan 18 valores válidos. Se prioriza el dato diario original válido cuando existe para el mismo punto y fecha. La falta de puntos automáticos en un archivo diario de ciertos años se trata utilizando los registros horarios, sin inventar filas oficiales.

Las medias provinciales son medias simples de medias anuales de estaciones seleccionadas, sin ponderación poblacional. Se conservan las diferencias entre áreas urbanas, suburbanas y rurales y el número de estaciones de apoyo. Este indicador no equivale a la exposición de la población provincial.

## Cobertura obtenida

| Año | Territorios con indicador | Estaciones seleccionadas | Territorios con la selección constante |
| --- | ---: | ---: | ---: |
| 2017 | 31 | 99 | 29 |
| 2018 | 41 | 123 | 29 |
| 2019 | 43 | 126 | 29 |
| 2020 | 38 | 120 | 29 |
| 2021 | 39 | 128 | 29 |
| 2022 | 39 | 136 | 29 |
| 2023 | 42 | 138 | 29 |
| 2024 | 43 | 144 | 29 |

La selección disponible en cada año da 316 filas provinciales anuales con indicador. Hay 31 territorios con indicador en los ocho años, aunque la composición de sus estaciones puede cambiar.

Al conservar solo los mismos puntos de muestreo elegibles en todos los años, quedan 82 puntos en 29 territorios y 232 filas con indicador. De esos 29 territorios, 15 tienen dos o más estaciones en toda esta selección. Cada panel mantiene las 416 claves de los 52 territorios por ocho años: las concentraciones ausentes siguen vacías.

## Comprobar la estabilidad más allá del código

El mismo identificador no garantiza la misma ubicación o instrumentación. Se han comparado coordenadas y tipo de área declarados en los metadatos de los 82 puntos constantes:

- 33 tienen alguna diferencia en coordenadas entre años, incluidas correcciones muy pequeñas.
- 5 presentan diferencias máximas superiores a 100 metros según distancia esférica entre coordenadas declaradas.
- Uno de esos casos presenta una diferencia de unos 6,8 km (`01051001_10_49`). No se ha determinado si es una corrección del metadato o un traslado real.
- 4 puntos cambian el tipo de área declarado.

Los 100 metros son una señal exploratoria de revisión, no un umbral normativo ni una regla de exclusión. Estas incidencias se conservan en `revision_coordenadas_red_constante.csv`. No se han eliminado automáticamente esos puntos ni se ha confirmado una red físicamente invariable.

La tabla `cambios_seleccion_por_provincia.csv` identifica entradas y salidas de puntos respecto al año anterior. Son cambios de selección, no necesariamente aperturas, cierres o averías. En el primer año la comparación queda vacía.

## Archivos

En `data/interim/provincial_feasibility/history/`:

- `panel_red_variable.csv`: cruce sanitario-ambiental usando la selección de cada año.
- `panel_red_constante.csv`: cruce usando los mismos puntos elegibles en los ocho años.
- `continuidad_provincial_red_variable.csv` y `continuidad_provincial_red_constante.csv`: años con indicador y mínimos de estaciones por territorio.
- `cobertura_por_anio.csv`: recuentos anuales.
- `cambios_seleccion_por_provincia.csv`: cambios en los puntos que contribuyen al indicador.
- `puntos_red_constante.csv`: detalle anual de los 82 puntos.
- `revision_coordenadas_red_constante.csv`: variación de coordenadas y de tipo de área.
- `seleccion_estaciones_pm10_AAAA.csv` y `auditoria_AAAA.json`: puntos candidatos y controles de cada año.
- `resumen_historico.json`: resumen del periodo completo.

## Reproducir y comprobaciones

```powershell
python -m tfm_data.evaluation.historical_feasibility
python -m unittest discover -s tests
```

La ejecución completa procesa las horas por bloques y guarda solo resultados anuales para esta prueba. Se ha verificado que no hay claves provinciales anuales repetidas, que los puntos de la selección constante aparecen en los ocho años y que no se duplica el peso de una estación. El resultado de 2024 coincide con el prototipo anterior, dentro de tolerancia numérica.

## Qué permite concluir

El cruce multianual es técnicamente posible y permite un estudio exploratorio acotado. Aún no demuestra utilidad predictiva ni efectos causales. El tamaño de la selección constante es modesto, sus filas están relacionadas temporal y espacialmente y la cobertura territorial está condicionada por las estaciones disponibles.

Antes de entrenar: revisar las cinco alertas de coordenadas y los cambios de área, añadir demografía y contrastar la comparabilidad de las tasas sanitarias. Para una predicción del año siguiente solo podrán usarse datos publicados y disponibles al emitirla; los cruces actuales son descriptivos del mismo año. Mantener una separación temporal para evaluate y tratar explícitamente 2020-2021.
