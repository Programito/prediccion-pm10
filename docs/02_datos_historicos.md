# Inventario inicial: salud y calidad del aire

Fecha de revisión: 15 de noviembre de 2026.

## Datos conseguidos

Se han descargado 36 archivos originales de fuentes oficiales, correspondientes a 2016-2024, por un total de 350.576.089 bytes (350,6 MB decimales). No se han descargado todavía los datos demográficos ni meteorológicos.

Por cada año se conservan:

- Un CSV del INE: tasas de altas hospitalarias por diagnóstico y territorio de residencia.
- Un ZIP de MITECO de mediciones diarias.
- Un ZIP de MITECO de mediciones horarias.
- Un archivo de metainformación de estaciones, magnitudes y técnicas.

Los originales se guardan en `data/raw/health_air_history/`. El manifiesto `sources.json` contiene las URLs exactas de descarga, la página de catálogo que identifica cada fuente anual, tamaños y huellas SHA-256. Los archivos originales de la primera muestra de 2024 se mantienen aparte.

Fuentes oficiales:

- INE, catálogos anuales de morbilidad hospitalaria: https://www.ine.es/dynt3/inebase/es/index.htm?capsel=8593&padre=2590
- MITECO, histórico 2001-2023: https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/evaluacion-y-datos-de-calidad-del-aire/datos/datos-historicos.html
- MITECO, 2024: https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/atmosfera-y-calidad-del-aire/evaluacion-y-datos-de-calidad-del-aire/datos/datos-oficiales-2024.html

## Comprobaciones realizadas

El script `scripts/03_audit_history.py` lee los nueve CSV sanitarios y los archivos diarios de PM10 y PM2,5 de los nueve años. También comprueba la integridad de los ZIP diarios y horarios.

En los nueve años aparecen los tres grupos seleccionados: enfermedades respiratorias (1000), EPOC/bronquiectasias (1006) y asma (1007). Cada año contiene 189 filas para estos tres grupos, sin tasas vacías ni marcadas como `..`. Esas filas mezclan nación, comunidades y provincias: no son 189 provincias ni ejemplos independientes. Las clasificaciones y definiciones deben contrastarse antes de comparar años.

Para 2017-2024 se han perfilado además los CSV horarios de PM10, PM2,5 y NO2: contienen 70.935.311 celdas horarias no vacías en conjunto. No confundir ese recuento con pacientes, muestras independientes o mediciones validadas por nuestra limpieza. Los tres Excel horarios de 2016 están descargados y su integridad ZIP comprobada, pero aún falta perfilar su contenido.

Se generan inventarios en `data/interim/history_audit/`:

- `cobertura_sanidad.csv`: dimensiones y presencia de los diagnósticos por año.
- `cobertura_aire.csv`: presencia de partículas en los archivos diarios.
- `cobertura_aire_horario.csv`: presencia en los archivos horarios, con estado explícito de lo no perfilado.
- `resumen.json`: resumen de descargas y limitaciones.

## Hallazgo importante sobre los archivos ambientales

En algunos años los archivos diarios contienen solo parte de las mediciones de partículas, mientras que otras aparecen en los horarios. Por ejemplo, el diario PM10 de 2023 tiene valores en 27 códigos provinciales, y el horario en 47. Estos conjuntos pueden solaparse: no sumar directamente sus coberturas.

Para preparar una serie comparable habrá que revisar la documentación de muestreo, obtener resúmenes diarios de las series horarias cuando corresponda y resolver solapamientos entre técnicas y puntos de muestreo. No concatenar y promediar ambos archivos sin control.

## Qué falta para confirmar el panel de modelos

1. Clasificar los territorios sanitarios y asignar códigos provinciales, con tratamiento explícito de las comunidades uniprovinciales, Ceuta y Melilla.
2. Completar el perfil horario de 2016 y revisar los metadatos y unidades de todos los años.
3. Comprobar fechas, valores inválidos, duplicados, cobertura temporal y cambios de estaciones. La presencia de una medición en una provincia no basta para representar un año completo ni la exposición de toda su población.
4. Añadir población y estructura por edad desde una fuente oficial. Las tasas descargadas no están ajustadas por edad.
5. Revisar cambios metodológicos y el tratamiento de 2020-2021 antes de comparar resultados sanitarios.
6. Calcular el número de provincias-año con cobertura suficiente y probar el cruce. No se ha construido todavía una tabla unida.

Con 52 territorios provinciales (incluyendo Ceuta y Melilla) y nueve años, el techo teórico sería 468 filas por diagnóstico antes de pérdidas por cobertura. Para predecir el año siguiente usando el anterior habría, como máximo, ocho transiciones por territorio (416 filas), y menos al introducir más retardos o restricciones por fecha real de publicación. Las millones de mediciones ambientales no aumentan ese número de resultados sanitarios independientes.

## Reproducir

```powershell
.\scripts\02_download_history.ps1
python scripts/03_audit_history.py
```

El descargador conserva los archivos existentes y registra sus huellas. La auditoría crea inventarios separados y no modifica los originales. Todavía no se han entrenado modelos ni calculado efectos causales.
