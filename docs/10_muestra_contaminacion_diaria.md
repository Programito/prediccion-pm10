# Muestra inicial para predecir PM10 del día siguiente

## Enfoque adoptado

La predicción diaria de contaminación será el núcleo del proyecto. El cruce sanitario provincial y anual se conserva como complemento exploratorio, con sus resultados negativos de la primera comparación predictiva y sus limitaciones. No se trasladarán las asociaciones provinciales a personas ni a enfermedades individuales.

## Selección de territorio y estaciones

Madrid tiene 17 estaciones de fondo elegibles durante 2017-2024 después de apartar de esta selección los puntos con alertas de ubicación o cambios de tipo de área. Es la provincia con más estaciones en esta selección constante sin alertas.

Para empezar con un tamaño manejable, se escoge una estación urbana, una suburbana y una rural. Dentro de cada tipo, se prioriza la mayor cobertura anual mínima en el periodo; en caso de empate, la cobertura media y el código de estación. Esta selección mira el historial completo y es exploratoria: no reproduce una selección hecha en 2017 sin información futura.

| Código | Estación | Tipo de área | Cobertura mínima anual |
| --- | --- | --- | ---: |
| 28079060 | Tres Olivos | Urbana | 96,44 % |
| 28080003 | Majadahonda | Suburbana | 97,81 % |
| 28133002 | San Martín de Valdeiglesias | Rural | 98,63 % |

Las tres estaciones figuran como de fondo en el histórico seleccionado. Tener tres contextos permite comparar comportamientos; no representa toda la exposición de la provincia.

## Tabla preparada

`data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv`

Una fila por estación y día natural: 8.766 filas en total, con 8.705 concentraciones aceptadas y 61 días sin valor aceptado. El calendario está completo y las ausencias se conservan. No se ha aplicado imputación.

Columnas principales:

- `codigo_estacion`, `punto_muestreo`, `NOMBRE`, `TIPO_AREA`: identificación de la serie.
- `fecha`, `anio`: día muestreado, normalizado como AAAA-MM-DD al exportar.
- `concentracion`: valor diario seleccionado; puede incluir una incidencia marcada para revisión.
- `estado`, `es_valido`: distinguen valores aceptados, ausentes e incidencias.
- `pm10_valido`: concentración utilizable; queda vacía cuando no se acepta la medición.
- `origen_diario`: dato diario original o derivado del horario con cobertura suficiente.
- `n_horas_validas`: cobertura horaria cuando la fila procede de esa agregación; una celda vacía no significa cero horas en el dato diario oficial.
- `archivo_origen`, `miembro_zip`: procedencia para contrastar el original. Si falta completamente el registro del día, estos campos quedan vacíos.
- `unidad`: µg/m3.

Los datos horarios utilizan el convenio UTC de fin de muestreo. La media se asigna al día muestreado, no al día de fin de H24. Se mantiene el mismo tratamiento de solapamientos y cobertura documentado en el mapeador ambiental.

Otros archivos en la carpeta:

- `estaciones_muestra_madrid.csv`: criterio y resultado de selección.
- `cobertura_muestra_por_anio.csv`: 24 filas, una por estación y año.
- `resumen_muestra.json`: recuentos generales.

## Reproducir

```powershell
python -m tfm_data.pipelines.pollution_sample
python -m unittest discover -s tests
```

El programa comprueba las huellas originales, reconstruye las tres series, valida claves únicas y comprueba que no haya saltos en el calendario. La tabla no contiene todavía objetivo desplazado ni variables predictivas.

## Siguiente ejercicio

Crear el objetivo del día siguiente y variables calculadas solo con el pasado de cada estación. Antes de entrenar se fijará el momento de emisión de la previsión y la disponibilidad de sus entradas. Las ausencias del objetivo no se imputarán para evaluate.

Como reparto inicial a fijar antes de mirar resultados: entrenamiento 2017-2022, validación 2023 y prueba final 2024. La primera referencia será repetir el último día observado; la selección de estaciones por cobertura retrospectiva y el carácter revisado de las fuentes deberán seguir declarados. No usar meteorología observada del día futuro como si fuera una previsión disponible.
