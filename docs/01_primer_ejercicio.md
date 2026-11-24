# Primer ejercicio: entender los datos sanitarios

## Objetivo

Leer una fuente real y crear una tabla intermedia pequeña. Todavía no entrenamos modelos ni unimos contaminación con salud.

El original está en `data/raw/health_air_feasibility/ine_morbilidad_residencia_2024_79536.csv`. Su procedencia y huella están en `sources.json`, en la misma carpeta. Fuente: https://ine.es/jaxi/Tabla.htm?L=0&tpx=79536

## Antes de ejecutar

Lee `scripts/01_explore_health.py`. Las tres columnas del original son diagnóstico, territorio de residencia y tasa. Una fila corresponde a una combinación de diagnóstico y territorio en 2024. El año figura en la ficha oficial, aunque no aparezca como columna en el CSV.

La tasa mide altas hospitalarias por cada 100.000 habitantes. No cuenta personas únicas con una enfermedad: una persona puede tener más de un alta. `1.234` representa 1234 en este archivo. `..` indica un dato ausente, no cero.

## Ejecutar

Con Python y pandas instalados, desde la carpeta del proyecto:

```powershell
python scripts/01_explore_health.py
```

Si falta pandas, instala la dependencia en tu entorno de Python con `python -m pip install pandas`. La configuración de un entorno virtual propio se hará en el siguiente paso de preparación del equipo.

El script conserva el original y crea `data/interim/health_respiratory_2024.csv`. Mantiene el texto original junto al valor numérico para poder comprobar la conversión.

## Qué contiene la selección

- `1000`: conjunto de enfermedades del sistema respiratorio.
- `1006`: EPOC y bronquiectasias.
- `1007`: asma.

Los subgrupos forman parte del total: no sumar las tres tasas. Conservamos el código como texto.

Hay territorios de distintos niveles: total nacional, comunidades autónomas y provincias. No usar todas las filas como si fueran provincias independientes. La tabla marca el nivel geográfico como pendiente de clasificar; las comunidades uniprovinciales necesitarán una correspondencia explícita.

## Tu parte del ejercicio

1. Localiza el bloque que lee el CSV e identifica para qué sirven `sep`, `encoding` y `dtype`.
2. Busca tu provincia o comunidad y compara sus tres tasas. Comprueba qué significa cada fila antes de interpretar diferencias.
3. Explica por qué no podemos sumar el total nacional, las comunidades y las provincias.

Lo siguiente será clasificar territorios y asignar códigos oficiales. Después repetiremos la lectura con contaminación y ampliaremos a varios años. Las tasas de esta tabla no están ajustadas por edad: no interpretar diferencias territoriales como efecto de contaminación.
