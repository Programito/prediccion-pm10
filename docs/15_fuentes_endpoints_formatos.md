# Fuentes, URLs de descarga y formatos

Este documento describe las descargas que constan en nuestros manifiestos y los archivos conservados en `data/raw/`. El [inventario de URLs exactas](reference/source_endpoints.md) permite consultar cada descarga por año. El [catálogo de fuentes](reference/source_catalog.csv) añade ruta local, catálogo oficial, contenido del ZIP, tamaño, fecha registrada y SHA-256.

Cada endpoint enlaza también las **tablas originales, columnas y tipos** en el [diccionario de esquemas](reference/source_schemas.md). Incluye todas las hojas Excel y todos los CSV de los ZIP, aunque todavía no los utilicemos en modelos. Para filtrar por descarga o tabla están el [catálogo de tablas originales](reference/source_tables.csv) y el [catálogo de columnas originales](reference/source_columns.csv).

El tipo lógico describe el significado esperado (texto, código, entero, decimal o fecha). Los CSV no declaran tipos: los leemos como texto antes de mapear. Para Excel, el catálogo registra además el dtype inferido en una muestra de hasta 30 filas; no representa una comprobación de toda la columna ni una garantía de ausencia de nulos. Los tipos de las tablas ya transformadas pertenecen a una etapa distinta.

Hay **37 archivos originales principales**: nueve años de sanidad, nueve ZIP diarios, nueve ZIP horarios y nueve archivos de metadatos ambientales, más el CSV demográfico. Se conservan además tres copias de la muestra inicial de 2024: **40 registros en el inventario**. Los manifiestos registran la descarga el 15 de noviembre de 2026.

Son descargas públicas mediante HTTP GET. Estas URLs pertenecen a los proveedores; todavía no tenemos una API propia. El inventario refleja las descargas guardadas, no un historial completo de consultas, errores o redirecciones.

## Qué formato recibimos

| Fuente | Periodo descargado | Archivo recibido | Contenido y lectura |
| --- | --- | --- | --- |
| INE: tasas de altas hospitalarias por residencia | 2016–2024 | CSV | Separador `;`, UTF-8 con BOM, números con formato español |
| MITECO: medidas diarias y horarias | 2017–2024 | ZIP | CSV separados por contaminante, separador `;`, punto decimal |
| MITECO: medidas diarias y horarias | 2016 | ZIP | Excel XLSX; no tiene el mismo formato que los años posteriores |
| MITECO: metadatos de estaciones y magnitudes | 2016–2024 | XLS en 2016; XLSX después | Hojas de estaciones, magnitudes y técnicas; nombres de hojas variables según año |
| INE: población por provincia y edad, tabla 56945 | Serie histórica en un archivo | CSV | Separador `;`, UTF-8 con BOM, números con formato español |
| NOAA GFS en Amazon S3 | Cuatro fechas del piloto | Índice `.idx` y fragmentos GRIB2 | Previsiones de viento y precipitación. [Endpoint y esquema del piloto](22_viabilidad_meteorologia_pm10.md) |

Por tanto, recordabas **CSV**. También descargamos ZIP y Excel. Un ZIP es un contenedor: primero identificamos su miembro y después leemos el CSV o Excel que contiene. Nuestros `.csv.gz` intermedios son CSV comprimidos con gzip, generados por el proyecto.

## INE: sanidad

Patrón de descarga: `https://www.ine.es/jaxi/files/tpx/csv_bdsc/{id}.csv`.

La página de catálogo usa `https://www.ine.es/jaxi/Tabla.htm?tpx={id}&L=0`. El identificador cambia entre años; las nueve correspondencias reales están en el [inventario](reference/source_endpoints.md). No se deduce el año del identificador.

El CSV presenta dos variantes: diagnóstico, territorio y `Total`, o diagnóstico, tres columnas geográficas jerárquicas y `Total`. El año se aporta desde el catálogo y el manifiesto porque estos archivos no contienen una fecha completa.

`Total` representa una **tasa de altas por 100.000 habitantes**, no un número de personas. El mapeador convierte `1.234,5` en `1234.5` y conserva `..` o blanco como ausente. Seleccionamos los códigos 1000, 1006 y 1007: enfermedades respiratorias, EPOC/bronquiectasias y asma. Hay solapamiento entre categorías; no deben sumarse.

## MITECO: contaminación

Las URLs varían entre años. No construimos una URL histórica suponiendo que la estructura de 2024 sirve para todos. Los enlaces efectivos y los nombres de todos los miembros de cada ZIP figuran en los catálogos adjuntos.

Ejemplo de [descarga diaria de 2024](https://www.miteco.gob.es/content/dam/miteco/es/calidad-y-evaluacion-ambiental/sgalsi/atm%C3%B3sfera-y-calidad-del-aire/evaluaci%C3%B3n-2024/Datos_DD_2024.zip). El miembro de PM10 es `PM10_DD_2024.csv`; el horario es `PM10_HH_2024.csv` dentro de su ZIP correspondiente.

Las columnas identificadoras son `PROVINCIA`, `MUNICIPIO`, `ESTACION`, `MAGNITUD`, `PUNTO_MUESTREO`, `ANNO` y `MES`. Los diarios traen columnas `D01` a `D31`; los horarios añaden `DIA` y columnas `H01` a `H24`.

- PM10 corresponde a magnitud 10 y unidad µg/m³, contrastadas con el Excel de magnitudes.
- Un punto de muestreo distingue la serie y su técnica. No equivale necesariamente a una estación única.
- Los blancos son ausencias; el archivo no permite separar siempre falta de medida de medida invalidada. No se convierten en cero.
- Las concentraciones negativas se conservan con una marca de revisión y no se aceptan como medidas válidas.
- Las horas expresan el **fin del intervalo en UTC**: H01 termina a la 01:00 UTC y H24 a las 00:00 del día siguiente. La fecha de muestreo sigue siendo la del día original.

Se descargaron los archivos multicomponente completos, pero la preparación actual trabaja con **PM10**. La serie diaria utilizada abarca 2017–2024; los Excel ambientales de 2016 se inspeccionaron en la auditoría histórica y no pasan por el lector CSV moderno.

## INE: demografía

[Descarga CSV de la tabla 56945](https://www.ine.es/jaxiT3/files/t/csv_bdsc/56945.csv), con [catálogo oficial](https://www.ine.es/jaxiT3/Tabla.htm?t=56945).

Columnas originales: `Edad simple`, `Provincias`, `Sexo`, `Periodo` y `Total`. Filtramos ambos sexos (`Sexo = Total`), provincias y 1 de enero de 2017–2024. `Total` representa población, a diferencia de la tasa sanitaria.

Es una serie revisada descargada en 2026, con cambios metodológicos; no demuestra qué datos estaban disponibles en cada fecha histórica. El grupo «85 y más años» es un subtotal y se excluye al sumar edades simples para evitar duplicaciones.

## Formato de nuestras tablas

Las tablas preparadas usan CSV con separador **coma**, números con punto decimal y codificación UTF-8; algunas incluyen BOM. Las tablas voluminosas se comprimen en `.csv.gz`. Las ausencias siguen siendo ausencias.

Las fechas diarias se guardan como `AAAA-MM-DD`. Los instantes horarios de fin se exportan como `AAAA-MM-DDTHH:MM:SSZ`. Los datos anuales mantienen `anio`; no se les inventa una fecha diaria. La población incluye su fecha real de referencia: 1 de enero. Los códigos territoriales deben leerse como texto para conservar ceros iniciales.

## Regenerar el inventario

Desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.document_sources
```

El comando verifica las huellas de los originales, inspecciona las cabeceras de los CSV y hojas Excel y cuenta las filas de las tablas principales existentes. Regenera los inventarios de `docs/reference/`; no descarga datos ni entrena modelos. `xlrd`, incluido en `requirements.txt`, permite inspeccionar el XLS antiguo de 2016. Falla si falta un original, cambia su huella o falta una tabla catalogada. Los recuentos describen la copia local actual, no garantizan que una futura descarga del proveedor sea idéntica.
