# Primer mapeador: sanidad del INE

## Qué hace cada pieza

El módulo `pm10_data/mappers/health.py` separa tres responsabilidades:

```python
original = lector.read(ruta)
normalizado = mapeador.transform(original, contexto)
validador.validate(normalizado)
```

`INEHealthReader` lee el CSV como texto. `INEHealthMapper` transforma un DataFrame y devuelve otro, sin cambiar el original. `INEHealthValidator` comprueba claves, tasas y códigos. La escritura de resultados pertenece al programa `pm10_data/pipelines/prepare_health.py`.

`HealthContext` agrupa el año, la tabla del INE y el nombre del archivo. Es inmutable: no se cambia accidentalmente mientras se procesa una fuente. El programa obtiene este contexto del manifiesto de descargas y comprueba la huella SHA-256 del archivo antes de leerlo.

## Transformaciones

- Acepta los dos formatos reales: geografía en una columna o separada en tres columnas jerárquicas.
- Selecciona por defecto los códigos 1000, 1006 y 1007. Rechaza una selección si falta un diagnóstico.
- Convierte números españoles: `1.268` pasa a 1268 y `1.234,5` a 1234.5. Conserva el texto original. `..` y blancos siguen siendo ausentes. Un formato numérico desconocido produce un error.
- Unifica territorios mediante `data/reference/territorios_ine.csv`. Normaliza mayúsculas, acentos y espacios para buscar, conservando la denominación original.
- Mantiene los códigos como texto: `01` no se convierte en `1`.
- Conserva el nivel territorial original. Para el análisis provincial, asigna código provincial a las comunidades uniprovinciales, Ceuta y Melilla. No duplica sus filas.
- Conserva el año como entero, sin inventar un día o mes para datos anuales. La normalización de fechas diarias y horarias se implementará en el mapeador ambiental.

La referencia territorial toma nombres y códigos jerárquicos del original sanitario de 2016, tabla INE 28285, conservado en el manifiesto. Las equivalencias añadidas para comunidades uniprovinciales son Asturias 03→33, Baleares 04→07, Cantabria 06→39, Madrid 13→28, Murcia 14→30, Navarra 15→31 y La Rioja 17→26. Ceuta 18→51 y Melilla 19→52 se tratan como territorios provinciales para el cruce; esto no cambia su condición de ciudades autónomas. Los dos espacios de códigos (comunidad y provincia) son distintos.

El resto de comunidades y el total nacional se conservan solo en el archivo de todos los niveles. No se mezclan con las provincias en el archivo provincial. Una denominación nueva o un código jerárquico incoherente detiene el proceso para revisión.

## Ejecutar desde la raíz

Requiere Python con pandas, igual que el ejercicio anterior:

```powershell
python -m pm10_data.pipelines.prepare_health
python -m unittest discover -s tests -v
```

Resultados:

- `data/interim/health/tasas_respiratorias_todos_niveles.csv`
- `data/interim/health/tasas_respiratorias_provincias.csv`

El programa valida el histórico completo antes de exportar. Estas tablas siguen siendo intermedias: falta añadir contaminación y demografía, revisar comparabilidad temporal y tratar los factores de confusión. Las tres categorías respiratorias se solapan: no sumar el total con sus subgrupos.

## Para aprender

Empieza leyendo `HealthContext` y después `transform`. Localiza dónde se seleccionan columnas, dónde se transforma la tasa y dónde se consulta la referencia territorial. En las pruebas puedes ver ejemplos pequeños del formato plano, del jerárquico y de los errores que queremos detectar.
