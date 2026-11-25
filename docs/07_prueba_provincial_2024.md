# Prueba provincial de viabilidad: PM10 y sanidad en 2024

## Qué se ha probado

Se construye un indicador ambiental provincial provisional y se comprueba su cruce por código de provincia y año con la tasa sanitaria del grupo 1000 (enfermedades respiratorias). Es un cruce descriptivo del mismo año, no una previsión ni un análisis causal.

La selección provisional exige simultáneamente:

- Estación de tipo FONDO según metadatos.
- Presencia del punto en el archivo horario, con técnica distinta de M.
- Cumplir el criterio exploratorio ya aplicado de al menos un 75 % de días aceptados durante el año.

Se conservan todas las estaciones en la tabla de selección con banderas que explican el resultado. No se eliminan datos originales ni se declara inválido el muestreo manual. Para una revisión futura debe confirmarse el significado y el calendario de las técnicas específicas.

## Cómo se calcula el indicador

Se promedian las medias anuales aceptadas de las estaciones seleccionadas de cada provincia, asignando el mismo peso a cada estación. Si una estación tuviera varios puntos seleccionados, el proceso se detendría para resolver su peso antes de agregar.

No es una estimación de exposición de toda la población. No se pondera por población, superficie ni distribución urbana y rural. La tabla muestra los números de estaciones por tipo de área, sus coberturas y el mínimo/máximo de sus medias para que estas limitaciones sean visibles.

## Resultado

- 144 estaciones seleccionadas entre 489 puntos revisados.
- 43 territorios provinciales con indicador y correspondencia sanitaria.
- 14 cuentan con una sola estación seleccionada; 29 tienen dos o más. No se ha adoptado todavía un mínimo de dos estaciones.
- 9 territorios quedan sin indicador bajo esta selección: Girona, Huesca, Palencia, Segovia, Soria, Tarragona, Teruel, Valladolid y Zamora. Esto no implica que no existan mediciones ambientales allí.

Se mantienen los 52 territorios sanitarios en el resultado: la concentración sin correspondencia permanece vacía, nunca se sustituye por cero. Los recuentos de estaciones de esos territorios sí son cero.

## Archivos y ejecución

```powershell
python -m pm10_data.evaluation.provincial_prototype
```

En `data/interim/provincial_feasibility/`:

- `seleccion_estaciones_pm10_2024.csv`: evidencia de selección de los 489 puntos.
- `prototipo_pm10_sanidad_2024.csv`: los 52 territorios y el cruce, con indicadores de ausencia y de estación única.
- `resumen_2024.json`: recuentos generales.

## Decisión que permite tomar

Es posible realizar el cruce técnico y conservar un número apreciable de territorios en 2024. Todavía falta comprobar cuántos mantienen cobertura comparable durante varios años y qué peso tienen las estaciones de área urbana frente a rural. No entrenar un modelo con estas 43 observaciones de un único año.

La siguiente prueba es repetir el análisis para varios años con criterios coherentes y estudiar una red estable de estaciones, evitando atribuir a contaminación los cambios que procedan de cambios de red. Después deben añadirse población y estructura de edad. Para una previsión del año siguiente se usarán únicamente datos disponibles en el momento de predecir, teniendo en cuenta el retraso de publicación de las fuentes.
