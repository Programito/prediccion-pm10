# Estadísticas descriptivas reutilizables para las tablas

La pestaña **Estadísticas** de las tablas tratadas resume las medidas numéricas sobre todas las filas que cumplen los filtros, antes de paginar. El cálculo es descriptivo: no modifica datos, filtros de calidad, modelos ni entrenamiento. Incluye mínimo, P25, mediana, media, P75, máximo y desviación estándar, junto a recuentos de valores válidos, ausentes e inválidos.

El resumen también aparece directamente debajo de los registros y su paginación, sin abrir otra pestaña. Esta vista compacta ordena mínimo, P25, mediana, media, P75 y máximo, seguidos de válidos, ausentes e inválidos. Comparte los filtros, utiliza todas las filas coincidentes y no se recalcula al cambiar solo de página o tamaño. El botón «Ver estadísticas completas y diagrama de caja» abre la vista detallada, que conserva desviación estándar, porcentaje de ausentes y boxplot. P75 es el percentil 75.

El botón principal **Ver diagrama de caja**, junto al título del resumen, abre la misma vista detallada que el acceso inferior. Al cargar los datos se desplaza y enfoca el diagrama para que el cambio sea visible incluso al abrirlo desde el final de la página. Los filtros se conservan y aplicar otros filtros dentro de Estadísticas no vuelve a desplazar ni roba el foco. Las cifras del resumen se presentan con un máximo de dos decimales; los valores no nulos inferiores a 0,01 conservan tres cifras significativas para evitar mostrarlos falsamente como cero. La precisión del cálculo y de la API no se modifica. El resumen de PM10 indica explícitamente µg/m³.

Las cabeceras de los registros tratados y los nombres del resumen usan etiquetas legibles y homogéneas. Debajo se conservan el identificador técnico y el tipo de valor, por ejemplo «Tipo de área» / `TIPO_AREA`. Los filtros presentan ambas denominaciones pero envían la clave técnica original. CSV, API, mapeadores y nombres de las fuentes originales no se modifican.

## Presentación por finalidad

En el resumen principal de React, cuando existe `pm10_valido` se prioriza sobre `concentracion`, tanto bajo Registros como en Estadísticas y en el selector de medida del boxplot. No se presupone que las dos columnas sean iguales en todos los conjuntos; se elige la concentración aceptada por el control de calidad. Si no existe `pm10_valido`, la concentración sigue disponible como medida principal.

Los campos `anio`, `anio_objetivo` y `year` se presentan como rango mínimo–máximo de años de las filas filtradas, no como medias o percentiles. Se prioriza `anio_objetivo` cuando existe. Un filtro sin filas muestra que no hay años disponibles. `n_horas_validas` y `horas_validas` se muestran en el apartado desplegable **Calidad de los datos · Cobertura horaria**, con los recuentos y estadísticas ya calculados. Un nulo no equivale a cero horas; la ausencia de recuento para un dato diario oficial no lo convierte por sí sola en inválido.

Esta separación afecta a la presentación: los CSV, la respuesta estadística de la API y el cálculo reutilizable conservan sus columnas y valores. No se modifican datos ni modelos. La cobertura horaria y las medidas principales usan la misma tabla reutilizable de estadísticas.

## Función de cálculo

`summarize_numeric_columns(rows, columns, missing_values=("", ".."), include_boxplot=False)` recibe un iterable de registros con acceso por nombre de columna y una lista explícita de columnas numéricas. Está en [descriptive_statistics.py](../explorer/descriptive_statistics.py), utiliza únicamente la biblioteca estándar de Python y puede importarse desde scripts, pipelines o la API sin depender de Flask, pandas ni scikit-learn.

```python
from explorer.descriptive_statistics import summarize_numeric_columns

rows = [{"pm10": 0}, {"pm10": 10}, {"pm10": None}]
result = summarize_numeric_columns(rows, ["pm10"])
# Válidos: 2; ausentes: 1; mínimo: 0; P25: 2.5;
# mediana y media: 5; P75: 7.5; máximo: 10.
```

La función consume los registros una vez y mantiene en memoria los valores numéricos aceptados para ordenar y calcular los cuartiles exactos. No es un algoritmo de cuantiles aproximados para archivos arbitrariamente grandes. El alcance inicial del endpoint son las siete tablas tratadas, con esquemas conocidos. Los originales requieren adaptar previamente sus formatos numéricos y marcas de ausencia; todavía no muestran esta pestaña.

`numeric_measurement_columns(columns)` selecciona columnas a partir del tipo lógico del diccionario: Entero, Decimal y Proporción. Excluye campos de clave, identificadores y booleanos. No deduce que una columna es una medida porque sus valores parezcan números. Los componentes del calendario y las etiquetas enteras pueden aparecer si el esquema los declara numéricos y no forman parte de la clave; su significado sigue disponible en la tabla.

## Valores ausentes, inválidos y extremos

`None`, NaN, los blancos y los marcadores explícitos se cuentan como ausentes. Los textos numéricos se interpretan con punto decimal. Un formato como `1,5` no se convierte silenciosamente en otro valor: se cuenta como inválido. Los booleanos y los infinitos tampoco entran en las medidas. La suma de válidos, ausentes e inválidos coincide con la cantidad de filas resumidas para cada columna.

Válido significa numérico finito, no aprobado por el control ambiental. Por ejemplo, `concentracion` conserva el valor numérico almacenado, mientras que `pm10_valido` refleja la aceptación ambiental del mapeador. Los números negativos y los picos no se eliminan mediante esta función; el tratamiento previo de cada columna determina qué valores contiene. Los ceros se conservan como valores numéricos.

## Definiciones y casos especiales

| Medida | Cálculo |
| --- | --- |
| Media | Suma dividida por el número de valores numéricos válidos |
| P25, mediana y P75 | Valores ordenados; interpolación lineal en la posición `(n−1)×p` con p igual a 0,25, 0,5 y 0,75 |
| Desviación estándar | Versión muestral, con divisor n−1 |
| Ausentes (%) | 100 × ausentes / todas las filas coincidentes, incluidos los inválidos en el denominador |

Con un único valor, mínimo, cuartiles, media y máximo coinciden y la desviación queda indefinida. Una columna constante con al menos dos valores tiene desviación cero. Sin valores válidos, las medidas son nulas. Sin filas coincidentes, también es nulo el porcentaje de ausentes. Una medida que desborde la representación numérica queda nula y se registra en `calculation_errors`. React muestra los nulos con un guion y conserva los ceros visibles.

P25 y P75 son puntos de la distribución, no porcentajes de contaminación. La interpolación hace que el cuartil pueda situarse entre dos observaciones. Las medidas usan las unidades de la columna; la descripción del diccionario se consulta en **Significado**.

## API y alcance de los filtros

`GET /api/tables/{table_id}/statistics` devuelve JSON para una tabla tratada. Acepta los mismos parámetros `q`, `column`, `op` y `value` de Registros. Reutiliza `requested_filter`, por lo que aplica la misma búsqueda y condición sobre todas las filas antes del cálculo. `page` y `size` no afectan las estadísticas. Una tabla original devuelve 400 indicando el alcance actual; un identificador desconocido devuelve 404. Los filtros inválidos devuelven 400.

El endpoint valida la cabecera CSV contra el esquema y obtiene las columnas numéricas del diccionario enriquecido. Los registros filtrados se entregan como iterador a la función genérica. La respuesta conserva el archivo de origen y los filtros aplicados. No combina unidades de columnas diferentes ni compara grupos que no estén seleccionados explícitamente mediante los filtros.

| Campo de respuesta | Tipo y significado |
| --- | --- |
| row_count | Entero; filas de toda la selección |
| columns | Lista de resúmenes numéricos |
| columns[].name, type, description | Texto; nombre, tipo lógico y significado |
| valid_count, missing_count, invalid_count | Enteros por columna |
| missing_pct | Decimal de 0 a 100 o nulo |
| minimum, p25, median, mean, p75, maximum, std_dev | Decimales o nulos; unidades de la columna |
| calculation_errors | Lista de nombres de medidas que no pudieron representarse |
| excluded_columns | Lista de columnas no seleccionadas por su tipo o función |
| quantile_method | Texto que identifica la interpolación lineal |
| std_dev_ddof | Entero; 1 para la desviación muestral |
| source, table, scope | Textos; archivo, identificador y ámbito all_filtered_rows |
| filters | Objeto con los filtros textuales aplicados |

## React y comprobaciones

### Diagrama de caja y bigotes

Estadísticas incluye un diagrama por columna numérica con opción de resumir toda la selección o comparar por `codigo_estacion` cuando exista. Por defecto selecciona `pm10_valido` si está disponible y compara estaciones. Utiliza todos los registros filtrados y conserva la columna y agrupación al aplicar nuevos filtros mientras se mantiene la pestaña abierta. Las tablas sin identificador de estación muestran una caja de toda la selección. No se mezclan columnas con unidades diferentes en una misma figura.

La caja va de P25 a P75, la línea marca la mediana y el rombo la media. Los límites teóricos son P25−1,5×IQR y P75+1,5×IQR, con IQR igual a P75−P25. Los bigotes terminan en los valores observados más extremos dentro de esos límites inclusivos. Los valores exteriores se dibujan como círculos; se conservan todos, incluidas las repeticiones, y el eje común incluye los mínimos y máximos reales. Una ligera separación vertical facilita la lectura de los círculos y no codifica otra variable.

Los puntos exteriores pueden ser mediciones válidas. El diagrama no los elimina ni modifica las medidas. La tabla accesible del gráfico muestra recuentos, cuartiles, media, extremos de los bigotes y cantidad de exteriores. Una columna constante o con un único valor tiene caja colapsada; cuando no hay valores numéricos válidos aparece un mensaje y se conservan sus recuentos de ausentes e inválidos.

`tukey_boxplot(ordered_values)` calcula los límites, bigotes y valores exteriores de una muestra numérica ordenada. `summarize_numeric_columns(..., include_boxplot=True)` añade esos datos a cada resumen. `summarize_boxplot_groups(rows, column, group_by=None, label_by=None)` reutiliza las reglas de conversión y ausencias y calcula un resumen por grupo, conservando identificadores textuales con ceros iniciales.

```python
from explorer.descriptive_statistics import summarize_boxplot_groups

groups = summarize_boxplot_groups(
    rows, "pm10_valido", group_by="codigo_estacion", label_by="NOMBRE"
)
```

`GET /api/tables/{table_id}/boxplot?field=pm10_valido&group_by=codigo_estacion` acepta los mismos filtros `q`, `column`, `op` y `value`. `field` debe ser una columna numérica de medida; `group_by` es `none` o `codigo_estacion` si está presente. La respuesta JSON contiene `column`, `group_by`, `source`, `scope`, `quantile_method`, `whisker_iqr_multiplier` igual a 1,5, el recuento entero `row_count` y la lista `groups`. Cada grupo conserva código y etiqueta textuales, recuentos, medidas del resumen y `boxplot`, con límites, bigotes y una lista numérica de exteriores. Los valores indefinidos son nulos. Las columnas o agrupaciones incompatibles devuelven 400. El filtrado se aplica antes de agrupar, sobre toda la selección.

Se contrastaron cuartiles, media, bigotes y exteriores con `matplotlib.cbook.boxplot_stats`, con `whis=1.5` y `autorange=False`, en las 185 combinaciones numéricas y de grupo de las siete tablas tratadas. Matplotlib se utiliza para verificación; la API y React no añaden esta dependencia. Las pruebas cubren bigotes distintos de los máximos, valores exteriores repetidos, grupos y ceros, columnas vacías y constantes, y filtros anteriores a la agrupación. [Componente del gráfico](../explorer/src/boxplot.tsx)

**Tablas tratadas → Estadísticas** utiliza los mismos filtros aplicados que Registros. Cambiar el tamaño de página no cambia la población resumida. La cabecera indica cuántas filas y columnas entran en el resumen. La tabla muestra los recuentos, cuartiles y demás medidas; se puede consultar el significado de una columna y las reglas de cálculo. Los valores inválidos se señalan y las columnas excluidas se enumeran. [Componente](../explorer/src/statistics.tsx)

Se contrastaron las siete medidas numéricas con pandas para las 79 columnas seleccionadas de las siete tablas tratadas, usando cuantiles lineales y desviación con ddof 1. La función de producción no depende de pandas. Las pruebas incluyen cuartiles interpolados, desviación muestral, ceros, extremos, ausentes, inválidos, columnas constantes, muestras vacías o unitarias, exclusión de códigos y claves, y filtros aplicados a más filas que una página.

La construcción Docker incluye el módulo de cálculo sin añadir dependencias al contenedor. Las estadísticas se calculan al abrir la pestaña y no se guardan como nuevas tablas de entrenamiento.
