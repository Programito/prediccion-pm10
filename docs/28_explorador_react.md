# Explorador React de datos y resultados de PM10

La aplicación muestra **42 archivos de fuentes y 201 tablas**. La barra lateral los reúne en **7 tipos de fuente**, agrupados en Calidad del aire, Sanidad, Demografía y Meteorología. Cada temática es desplegable y cada tipo muestra una sola tarjeta con su proveedor, formato y selector de año o periodo. Las copias de 2024 de la muestra inicial siguen disponibles como opciones identificadas, sin confundirse con los históricos completos. [Código del frontend](../explorer/src/main.tsx)

Seleccionar un año abre directamente su archivo y sus tablas. Al volver a un tipo de fuente durante la consulta se conserva el último año elegido; el grupo de la fuente seleccionada se abre automáticamente. La búsqueda y el filtro de área actúan sobre los archivos y años disponibles, abriendo los grupos de resultados sin cambiar por sí mismos el archivo consultado. Buscar por año, proveedor o nombre de tabla sigue disponible. El contador distingue tipos de fuente y archivos. La URL, el método, el uso y el diccionario de columnas se consultan en el panel principal.

## Pantalla de Inicio

**Experimentos → Madrid → PCA y LDA** incorpora varianza explicada, proyecciones por periodo y estación, pesos de PCA y distribuciones de LD1. Compara las dos variantes LDA con sus logísticas y persistencia en 2023, con tablas accesibles y descargas. Se ajusta solo con entrenamiento y no se reevalúan pruebas finales. [Método y resultados](44_pca_lda_pm10.md)

**Casos** reúne la predicción habitual de Tres Olivos del 10/04/2024, el pico del 31/10/2024 y el comienzo del 05/08/2025, con la falsa alarma del 22/02/2025 como contraste. Incluye contexto de siete días, tabla accesible, predicciones o probabilidades con sus cortes, meteorología anterior al objetivo y descargas CSV. La selección se conserva al navegar a Gráficos y volver. Inicio ofrece acceso directo al recorrido. [Guion y procedencia](43_casos_de_estudio.md)

**Experimentos → Importancia agrupada** muestra el cambio de MAE de los Ridge originales al alterar grupos en validación de 2023. Se elige el territorio en las pestañas superiores. Incluye rangos entre alteraciones, sensibilidad del historial conjunto y referencias de coeficientes e impureza. [Método y límites](42_importancia_agrupada_pm10.md)

**Experimentos → Comparación de ventanas** muestra la retirada de la media de 14 días, con el mismo entrenamiento y con entrenamiento ampliado, en validación de 2023. Las cohortes común, adicional y ampliada se consultan por separado. [Diseño y resultados](41_comparacion_ventanas_pm10.md)

**Experimentos → Auditoría de cobertura** muestra las causas de exclusión de 2024 para Madrid y Barcelona, con filtros de estación, cobertura mensual, variables ausentes, tramos elevados afectados y detalle diario paginado por mes y estado. [Método y resultados](39_auditoria_cobertura_territorial.md)

La sección **Experimentos** compara Madrid y Barcelona provincia. Permite elegir territorio, consultar sus series y alternar las muestras completas con las fechas compartidas. **Gráficos** incorpora un selector de territorio para mapa, observaciones, predicciones, resultados de regresión, errores e incertidumbre. Los comienzos de 2025 y la explicación individual siguen disponibles solo para Madrid. [Guía de gráficos territoriales](45_graficos_territoriales.md) · [Método y resultados](38_experimentos_madrid_barcelona.md)

La aplicación abre en **Inicio**. Presenta la pregunta predictiva, las tres estaciones, los periodos de entrenamiento, validación y prueba, los resultados principales y las limitaciones. El entrenamiento de regresión usa 2017–2022; la comparación con meteorología usa 2021–2022 por disponibilidad de GFS. La validación corresponde a 2023. La prueba de regresión es de 2024 y la comparación de clasificación con y sin meteorología se prueba en 2025.

Las tarjetas obtienen los datos de `GET /api/charts/metrics` y `GET /api/charts/uncertainty`. La primera muestra el MAE de Ridge y persistencia de todas las filas de prueba de 2024 y el de los días elevados. La segunda muestra el intervalo global del bootstrap con la longitud principal indicada en el archivo de análisis. La tercera muestra los comienzos detectados y falsas alarmas de 2025 en los 891 casos cuyo día previo no superaba el umbral; los recuentos de falsas alarmas de ese contexto difieren de los del conjunto completo de clasificación.

Los números proceden de las salidas existentes; abrir Inicio no entrena modelos ni vuelve a calcular experimentos. Si una petición falla se muestra su error y las otras secciones siguen disponibles. Las limitaciones explican cobertura, picos, umbral estadístico y disponibilidad real pendiente de verificar.

Los accesos a Errores e Incertidumbre seleccionan todas las estaciones para coincidir con el resumen global. El acceso al pico de Tres Olivos abre Explicabilidad el 31 de octubre de 2024. El acceso al Mapa conserva la selección actual. También se puede abrir el catálogo original, las tablas tratadas, el flujo y la documentación. [Componente de Inicio](../explorer/src/home.tsx)

En **Diccionario de columnas** se puede buscar por nombre, significado o tipo. Cada fila explica qué representa la columna, cómo interpretar sus valores y cómo vienen guardados. Cuando existe un valor en la página consultada se muestra como ejemplo. En las tablas tratadas también se marcan los campos que forman la clave. **Leyenda de términos** explica abreviaturas, formatos, unidades y conceptos como valores nulos, puntos de muestreo, ciclos GFS y retardos. [Definiciones de las columnas](../explorer/column_dictionary.py)

Las tablas de MITECO e INE proceden de los CSV, ZIP y Excel descargados para el proyecto. Para EEA se puede consultar el cuerpo de la petición `POST` que devuelve los enlaces y navegar por los registros originales de los tres Parquet. NOAA permite consultar los rangos GRIB2 solicitados y los valores derivados para las estaciones. Sus cuadrículas mundiales se procesaron en memoria y la vista conserva la distinción entre datos originales, manifiestos y valores derivados. [Documentación de endpoints](15_fuentes_endpoints_formatos.md) · [Extracción NOAA](22_viabilidad_meteorologia_pm10.md) · [Datos EEA](25_prueba_meteorologia_2025.md)

La aplicación lee las copias locales y permite cambiar el tamaño de página entre 10, 25 y 50 filas. La vista **Flujo de datos** dibuja en Mermaid el recorrido hacia las tablas predictivas y el panel sanitario. Indica las claves de cruce por estación y fecha objetivo, y por provincia y año. [Diagrama Mermaid](../explorer/src/lineage.mmd)

Cada llamada muestra el **formato de respuesta**. MITECO e INE pueden devolver un CSV, un Excel o un ZIP que contiene tablas. NOAA devuelve un índice de texto y bytes GRIB2. El manifiesto JSON de NOAA se genera en el proyecto. La consulta EEA recibe JSON y devuelve un CSV con enlaces a los Parquet originales. La API local del explorador sirve esos datos al navegador en JSON, conservando en la interfaz la procedencia y el formato de origen.

## Consultar los datos tratados

La pestaña **Estadísticas** resume todas las filas que cumplen los filtros mediante mínimo, P25, mediana, media, P75, máximo, desviación estándar y recuentos de ausentes e inválidos. Comparte los filtros con Registros y no depende de la paginación. [Método, función reutilizable y API](40_estadisticas_descriptivas.md)

En **Registros** de las tablas tratadas, el resumen de mínimo, P25, mediana, media, P75 y máximo aparece además debajo de la paginación. Se calculan todas las filas filtradas, no solo la página visible. Las cabeceras muestran primero un nombre legible uniforme y debajo la clave técnica y el tipo de dato. El acceso a estadísticas completas conserva el diagrama de caja y las medidas adicionales.

El resumen principal prioriza **PM10 válido** sobre Concentración si existen ambas columnas. Las **horas válidas** se consultan por separado en «Calidad de los datos · Cobertura horaria». El **año** aparece como periodo mínimo–máximo de las filas consultadas, sin medias ni percentiles. La misma selección de medidas se usa en la pestaña Estadísticas y en su boxplot; los datos y el cálculo de la API se conservan.

La columna **Válida** presenta `es_valido` como Sí/No, manteniendo los valores ausentes como guion. El filtro de esa columna ofrece Sí y No y consulta los valores booleanos originales. `estado` se conserva como categoría; se oculta en la tabla principal cuando ya existe `es_valido`. Los campos `archivo_origen`, `miembro_zip` y `origen_diario` también se ocultan en los registros tratados y se consultan desde el modal de información. Cuando existen `concentracion` y `pm10_valido`, la tabla principal muestra solo **PM10 válido**; ambos valores siguen disponibles en el modal, el diccionario, los filtros y los datos. No se presupone que siempre coincidan. Las tablas sin `pm10_valido` conservan su columna de concentración visible. Las fuentes originales conservan sus columnas.

Al final de cada fila tratada aparece un **icono de información** fijo a la derecha. Abre un modal con la identificación de la fila, validez, estado detallado, procedencia diaria, horas válidas y archivos de origen cuando están disponibles, junto con la tabla tratada y su mapeador. El acceso a fuentes y transformación abre el detalle de procedencia existente. El modal admite cierre con su botón y con Escape. No modifica ni infiere datos ausentes y utiliza los valores originales de la fila, incluso al filtrar o paginar. El diccionario y los filtros conservan las columnas ocultas para auditoría.

Incluye un diagrama de caja y bigotes por columna, con comparación por estación cuando está disponible. La caja muestra P25–P75, la línea la mediana, el rombo la media y los círculos los valores exteriores al criterio de 1,5 rangos intercuartílicos. Se conservan todos los valores y una tabla accesible permite consultar los números exactos.

**Tablas tratadas** permite navegar por siete salidas del procesamiento, con los mismos filtros y paginación que las tablas de origen. Cada ficha indica qué representa una fila, su clave, su utilidad y la transformación que la produce. [Catálogo de tablas tratadas](../explorer/treated_tables.py)

La vista **Esquema Mermaid** muestra dos diagramas entidad–relación con las claves lógicas y las columnas principales. La vista de registros incluye todas las columnas de cada CSV. En PM10 se distingue la fecha observada de la fecha objetivo usada para unir las previsiones. En sanidad se une por provincia y año tras elegir el diagnóstico. [Esquema de PM10 y GFS](../explorer/src/treated-pm10.mmd) · [Esquema sanitario](../explorer/src/treated-health.mmd)

## Filtrar registros

En **Registros**, se puede buscar un texto en cualquier columna y combinar la búsqueda con una condición sobre una columna. Las condiciones disponibles son **Contiene**, **Es igual a** y **Está vacío**. La comparación de texto ignora mayúsculas y tildes y conserva el formato de los valores mostrados. Los blancos, los nulos y la marca `..` de los archivos del INE cuentan como ausentes.

Los filtros se aplican sobre toda la tabla antes de paginar. Por ejemplo, en las previsiones GFS se puede buscar `2025-12` y pedir `codigo_estacion` igual a `28079060` para ver diciembre de 2025 en Tres Olivos. Al pulsar **Aplicar** o **Limpiar** se vuelve a la primera página. Al seleccionar otra tabla se empieza con los filtros vacíos.

## Consultar la procedencia de un valor

En **Registros**, selecciona una celda para abrir su ficha dentro de React. Se muestra el archivo local y el formato, el miembro del ZIP si corresponde y la hoja y la celda cuando se trata de Excel. El número de registro conserva la posición en el archivo aunque se aplique un filtro. En los CSV, se cuenta a partir del primer registro de datos, después de la cabecera.

Para una tabla tratada se indica la regla de cálculo y las referencias que conserva el proyecto. La concentración diaria permite identificar el ZIP y su columna diaria o sus horas. Los retardos y las ventanas muestran las fechas de entrada. La precipitación GFS muestra las dos peticiones GRIB2 con sus rangos de bytes. Para los agregados provinciales y de población se indican la fuente y la regla de agrupación. En los campos calculados por calendario se muestra la fecha o regla de la que salen.

La pestaña **Documentación** carga las guías Markdown del proyecto y el inventario de descargas dentro de React. Los enlaces a secciones disponibles en el explorador abren la guía correspondiente.

La guía **Propuesta conceptual de producción** describe la ejecución diaria, el corte temporal de las fuentes, las incidencias, la monitorización y la actualización de modelos.

## Explorar los gráficos de PM10

La navegación separa **Mapa**, **Observaciones**, **Predicciones**, **Resultados**, **Errores**, **Incertidumbre** y **Explicabilidad**. La estación y la fecha se comparten entre vistas y se conservan al visitar otras secciones de la aplicación y volver. La selección vive durante la sesión abierta; recargar la página restablece Tres Olivos y el 31 de octubre de 2024.

El selector de día y las barras actualizan la fecha compartida. Al cambiar de mes se conserva el número de día siempre que exista; por ejemplo, el 31 de enero pasa al 29 de febrero en 2024. Elegir un episodio en Predicciones selecciona su pico; elegir un mes selecciona su primer día.

Observaciones permite consultar 2017–2025. Predicciones y Explicabilidad corresponden a 2024 y muestran un aviso si la fecha queda fuera de ese año. Las fechas de 2024 excluidas de la prueba se identifican como ausentes. Errores e Incertidumbre usan la estación compartida y agregan toda la prueba de 2024. Resultados muestra los agregados globales de regresión de 2024 y avisos de 2025, por lo que no presenta filtros de estación ni fecha. La sensibilidad a fechas influyentes de Errores también es global y se indica en su título. Todas las estaciones puede utilizarse para los análisis agregados; las consultas diarias requieren elegir una estación concreta.

La sección de incertidumbre permite elegir estación y consultar el bootstrap de la diferencia de MAE con tres longitudes de bloque. Incluye intervalos numéricos y una representación de sus límites y del cero. [Método y resultados](36_incertidumbre_pm10.md)

La sección de análisis de errores combina estación y nivel observado para comparar MAE mensual de Ridge y persistencia. Otra sección muestra la sensibilidad global al retirar cinco fechas influyentes, con sus fechas y recuentos. [Método y resultados](35_analisis_errores_pm10.md)

- **PM10 diario por estación** permite elegir estación, año, mes y día. Usa el PM10 válido de MITECO de 2017 a 2024 y los agregados diarios de la EEA en 2025. Cada día sin dato válido queda marcado como un hueco. La línea discontinua marca el umbral estadístico de 27 µg/m³ que utiliza el estudio. Los resultados de las pruebas de los modelos se muestran por separado de esta serie observada.
- **PM10 observado y predicho en 2024** compara el observado y las predicciones de Ridge y persistencia por estación y fecha objetivo. Lee `output/pm10_final_2024/predicciones_regresion.csv` y permite elegir mes o episodio. Los episodios agrupan días consecutivos evaluados por encima de 27 µg/m³ y se ordenan por el pico observado. El gráfico incluye hasta tres días de contexto a cada lado y deja huecos en las fechas fuera de la prueba. Para leer los valores, selecciona el día en el gráfico o en **Día objetivo**.
- **Error de predicción en 2024** compara el error absoluto medio de Ridge con el de persistencia en todas las observaciones y en el subconjunto de días elevados. Los dos grupos usan la misma escala.
- **Avisos de inicio en 2025** compara cuántos comienzos detectó cada modelo y cuántos avisos resultaron falsos. Las dos métricas usan los 891 casos evaluables cuyo día anterior estaba en el umbral o por debajo, con 27 inicios observados.
- **Explicabilidad de los modelos** muestra los coeficientes de Ridge, las importancias de Random Forest y las aportaciones de cada variable a las predicciones de Ridge de 2024. Permite elegir estación y fecha, y reconstruir la predicción desde el intercepto. [Método y limitaciones](31_explicabilidad_pm10.md)

La API local lee los CSV de mediciones y resultados desde `data/interim/daily_pollution/`, `output/pm10_final_2024/` y `output/pm10_weather_test_2025/`. [Resultados y criterios de evaluación](26_resultados_pm10.md)

## Mapa de las estaciones

**Gráficos → Mapa** muestra siempre los tres puntos con el PM10 observado en la fecha compartida. Verde indica un valor de hasta 27 µg/m³, naranja un valor superior y gris la ausencia de una medición válida. El umbral es estadístico y pertenece al experimento de predicción. Las concentraciones se muestran también en una lista que permite seleccionar estaciones con el teclado. Seleccionar un punto actualiza la estación compartida y abre su ficha con valor, código y coordenadas. **Ver evolución** y, en 2024, **Ver predicción de este día** conservan estación y fecha. Una fecha excluida de la prueba puede tener una observación válida y carecer de predicción; la vista de predicciones indica esa ausencia.

El mapa representa mediciones puntuales y no interpola contaminación entre estaciones. En Madrid, las ubicaciones son la referencia fija de los metadatos MITECO de 2024, columnas `LATITUD_G` y `LONGITUD_G`, del CSV `data/interim/provincial_feasibility/history/seleccion_estaciones_pm10_2024.csv`. En Barcelona se usa `data/interim/experiments/barcelona/estaciones.csv`, columnas `latitud` y `longitud`. Los nombres se obtienen de `NOMBRE` y el cruce usa `codigo_estacion`. Consultar años anteriores no reconstruye posibles cambios históricos de ubicación.

`GET /api/charts/map?date=2024-10-31` devuelve JSON con fecha, umbral, proveedor de observaciones, archivo y año de coordenadas y una lista de tres estaciones. Cada estación contiene código y nombre (texto), latitud y longitud (números en grados) y concentración (número en µg/m³ o `null`). La fecha se valida en formato ISO entre 2017 y 2025; las inválidas reciben HTTP 400. Las concentraciones de 2017–2024 proceden de MITECO y las de 2025 del agregado diario EEA ya preparado. Los ausentes se mantienen como `null` y los valores elevados se muestran sin recortar, igual que en Observaciones.

El componente [station-map.tsx](../explorer/src/station-map.tsx) utiliza Leaflet 1.9.4 y se carga al abrir esta vista. El fondo solicita únicamente las teselas visibles a `https://tile.openstreetmap.org/{z}/{x}/{y}.png`, con atribución visible. Requiere Internet y sigue la [política de uso de OpenStreetMap](https://operations.osmfoundation.org/policies/tiles/). No se descargan teselas para la entrega. Los datos, la lista y las fichas son locales y siguen disponibles sin el fondo; un error de carga muestra un aviso.

## Ejecutarlo con Docker

Desde la raíz del proyecto:

```powershell
docker compose -f explorer/compose.yaml up --build
```

Abrir [el explorador local](http://127.0.0.1:8066/). Se montan `data/`, `docs/` y `output/` en modo de solo lectura. El contenedor sirve la interfaz y la API local con el mismo origen.

## Desarrollo local

Con Python 3.12, ejecutar desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r explorer/requirements.txt
.\.venv\Scripts\python.exe -m explorer.server
```

En otro terminal, con Node 24 y la versión de pnpm fijada en `explorer/package.json`:

```powershell
cd explorer
pnpm install --frozen-lockfile
pnpm run dev
```

Node 24 incluye Corepack. Si el comando `pnpm` no está disponible, usa `corepack pnpm` en su lugar.

El frontend usa TypeScript en modo estricto. `pnpm run typecheck` comprueba los tipos y `pnpm run build` ejecuta esa comprobación antes de compilar con Vite, también dentro de Docker. Los tipos de las respuestas de Flask se encuentran en [api.ts](../explorer/src/api.ts).

Vite redirige `/api` a Flask en el puerto 8066. `GET /api/sources` devuelve el catálogo original, `GET /api/treated-tables` devuelve el catálogo tratado y `GET /api/tables/{id}?page=1&size=10` devuelve un bloque con su esquema y un indicador de página siguiente. La ruta acepta `q` para la búsqueda global y `column`, `op` y `value` para la condición por columna. Los operadores son `contains`, `equals` y `missing`. Este último solo requiere la columna. Un archivo local ausente se indica al abrir su tabla. [Implementación de la API](../explorer/server.py)
