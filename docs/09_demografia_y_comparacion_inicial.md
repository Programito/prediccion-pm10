# Demografía y primera comparación sanitaria retrospectiva

## Datos demográficos conseguidos

Se descarga la tabla INE ECP 56945, población residente por fecha, sexo y edad desde 1971, con detalle provincial. Original: `data/raw/demographics/ine_poblacion_provincias_edad_56945.csv`; procedencia y SHA-256 en `source.json`.

Fuente: https://www.ine.es/jaxiT3/Tabla.htm?t=56945

La selección usa el 1 de enero de 2017-2024, ambos sexos y los 52 territorios provinciales. Se preparan 416 filas con población total, población de 0-14, 65 y más y 80 y más, y sus proporciones. Los dos últimos grupos se solapan: son variables descriptivas y no deben sumarse.

El original incluye tanto edades simples como el subtotal 85 y más. El mapeador excluye este subtotal al sumar edades 0-99 y 100 y más, y comprueba que su suma coincide exactamente con el total oficial en las 416 claves. Los códigos provinciales permanecen como texto y la fecha de referencia se exporta como AAAA-MM-DD.

La serie oficial no es metodológicamente uniforme por el mero hecho de proceder de una sola tabla: el INE explica que combina estimaciones intercensales históricas y la ECP desde 2021. Se emplea la versión revisada disponible al descargarla, no las publicaciones que se conocían en cada momento histórico. Véase la descripción de la operación: https://www.ine.es/dyngs/INEbase/operacion.htm?c=Estadistica_C&cid=1254736177095&idp=1254735572981&menu=ultiDatos

## Pregunta de la prueba

¿Un modelo sencillo que añade demografía y PM10 del año anterior mejora una referencia que repite la tasa respiratoria del año anterior?

Objetivo: tasa de altas por enfermedades respiratorias por cada 100.000 habitantes. No mide personas únicas ni prevalencia. La población añadida no se usa para recalcular las tasas oficiales y añadir proporciones de edad como variables no equivale a una estandarización epidemiológica por edad.

## Diseño fijado

- Red constante de PM10 ya preparada, con 29 territorios en ocho años.
- Datos de t-1 para estimar el resultado sanitario de t. No se utiliza contaminación ni demografía del año del resultado.
- Prueba en 2023 y 2024. Para 2023 se ajusta con resultados 2018-2022, y para 2024 con 2018-2023, siguiendo un origen móvil. La observación de 2023 entra en el segundo ajuste, sin modificar el algoritmo ni elegir hiperparámetros según su resultado.
- Tres alternativas: persistencia, regresión Ridge con historial y demografía, y la misma regresión añadiendo PM10.
- Los modelos Ridge predicen la variación sobre la referencia. Incluyen tasa anterior, logaritmo de población anterior y proporciones anteriores de 0-14, 65+ y 80+. La tercera alternativa añade PM10 anterior.
- Penalización alpha=10 fijada antes de ejecutar la comparación, sin búsqueda de hiperparámetros. Estandarización de variables e intercepto ajustados exclusivamente con entrenamiento. El intercepto no se penaliza.
- La regresión se implementa con NumPy resolviendo el sistema lineal regularizado; no necesita instalar scikit-learn. Los coeficientes de cada ajuste se guardan y son predictivos, no efectos causales.
- Sensibilidad: repetir retirando de la selección ambiental los nueve puntos con alertas de coordenadas superiores a 100 m o cambios de tipo de área. Las banderas pueden solaparse y se toma su unión. Son exclusiones solo para este escenario: los originales y la selección principal se conservan. En este escenario quedan 27 territorios.

## Resultado conjunto de los dos años

MAE y RMSE se expresan en altas por cada 100.000 habitantes.

| Selección | Modelo | Observaciones de evaluación | MAE | RMSE |
| --- | --- | ---: | ---: | ---: |
| Red constante | Repetir la tasa anterior | 58 | 136,21 | 156,66 |
| Red constante | Historial y demografía | 58 | 163,52 | 188,52 |
| Red constante | Historial, demografía y PM10 | 58 | 164,71 | 189,60 |
| Sin puntos con alertas | Repetir la tasa anterior | 54 | 136,04 | 156,59 |
| Sin puntos con alertas | Historial y demografía | 54 | 160,24 | 186,52 |
| Sin puntos con alertas | Historial, demografía y PM10 | 54 | 160,34 | 186,54 |

En la red constante, la referencia también gana por MAE en cada año por separado: 178,07 frente a 195,74 con PM10 en 2023 y 94,34 frente a 133,69 en 2024. El error de la referencia varía considerablemente entre años, lo que refuerza la necesidad de interpretar este experimento como limitado.

## Interpretación y límites

Este modelo no aporta mejora respecto a la persistencia en los dos años evaluados. Añadir PM10 tampoco mejora el MAE conjunto de la variante con demografía. La sensibilidad a las alertas geográficas no cambia esa conclusión concreta.

Esto no demuestra ausencia de relación entre contaminación y salud ni descarta todas las formulaciones predictivas. Solo se ha probado una especificación, un contaminante, un resultado sanitario agregado y dos años de evaluación. Las observaciones territoriales y temporales están relacionadas; no son 58 muestras independientes. No se han calculado intervalos de confianza ni significación estadística. Los años de pandemia forman parte del entrenamiento y todavía no se ha evaluado de forma separada su influencia.

No se trata de un backtest operativo: las publicaciones sanitarias tienen retraso, las series demográficas están revisadas y la red constante se eligió observando cobertura del periodo completo. Una previsión emitida históricamente necesitaría las fechas reales de disponibilidad, versiones originales y una selección de estaciones hecha sin información futura. Los buenos resultados, si los hubiera, tampoco salvarían estas limitaciones.

## Decisión recomendada

No invertir ahora en modelos sanitarios más complejos o en ajustar muchos hiperparámetros a esta muestra. Para asegurar un proyecto manejable con más observaciones, se recomienda que la previsión diaria de contaminación sea el núcleo predictivo y que el cruce sanitario permanezca como análisis complementario con estas limitaciones. Si se desea mantener salud como objetivo central, haría falta reformular y validar sus datos y diseño antes de prometer utilidad predictiva.

## Archivos y reproducción

```powershell
.\scripts\04_download_demographics.ps1
python -m pm10_data.pipelines.prepare_demographics
python -m pm10_data.evaluation.initial_health_comparison
python -m unittest discover -s tests
```

Salida demográfica en `data/interim/demographics/demografia_provincial_2017_2024.csv`. Resultados en `data/interim/initial_comparison/`:

- `panel_con_demografia.csv`: panel descriptivo con población y estructura de edad.
- `tabla_retardos_red_constante.csv` y `tabla_retardos_sin_alertas_ubicacion_area.csv`: variables anteriores y resultado para el año siguiente, preparados retrospectivamente.
- `predicciones.csv`: valores reales, previsiones y errores de cada territorio, año, modelo y escenario.
- `metricas.csv` y `metricas_por_anio.csv`: resultados conjuntos y anuales.
- `coeficientes.csv`: coeficientes estandarizados e interceptos de variación por ajuste.
- `resumen.json`: configuración, métricas y advertencias.

Los tests incluyen control de solapamiento de edades, consistencia de totales, retardos que no saltan años ausentes y comprobación de que cambiar el objetivo de prueba no modifica las predicciones de ese mismo año.
