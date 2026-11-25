# Comparación exploratoria de ventanas en validación de 2023

Retirar la media de 14 días permite evaluar 90 casos adicionales en Barcelona y 23 en Madrid durante 2023. Sobre las mismas filas que el modelo original, y manteniendo el mismo entrenamiento, el MAE aumenta ligeramente: +0,016 µg/m³ en Barcelona y +0,022 en Madrid. La variante ofrece más cobertura evaluable a cambio de una pequeña pérdida descriptiva de precisión en la cohorte común.

Se mantienen los modelos originales y sus resultados de 2024. Este análisis nace después de conocer la auditoría de cobertura de 2024 y vuelve a utilizar un año ya empleado para validar. Es una exploración posterior, no una nueva prueba independiente ni una selección basada en un periodo de prueba desconocido. No se promueve automáticamente una variante.

## Diseño para separar variables y cohortes

Se parte de las tablas supervisadas existentes y se restringe el análisis a fechas objetivo entre 2017 y 2023. El entrenamiento termina el 31 de diciembre de 2022 y la validación corresponde a 2023. El horizonte sigue siendo un día. No se calculan nuevas predicciones de 2024 ni se añaden datos meteorológicos o clasificación.

| Diseño | Variables y entrenamiento | Interpretación sobre las filas comunes de 2023 |
| --- | --- | --- |
| A · Ridge actual | Artefacto original congelado, con las doce variables numéricas | Referencia; no se vuelve a ajustar |
| B · Sin media de 14 días | Once variables, exactamente las mismas filas de entrenamiento que A | B menos A aísla la retirada de la variable, manteniendo la cohorte de entrenamiento |
| C · Sin media de 14 días y entrenamiento ampliado | Las mismas once variables que B, con las filas adicionales de entrenamiento que ahora son utilizables | C menos B mide el efecto de ampliar el entrenamiento y reajustar su transformación, manteniendo las variables |

Los tres Ridge usan alpha 10 y solver SVD. Las variables numéricas se estandarizan y la estación se codifica con el adaptador existente. B y C ajustan su transformador exclusivamente con sus respectivas filas de entrenamiento. Las predicciones negativas se restringen a cero. No hay imputación ni búsqueda de hiperparámetros.

La persistencia usa el último PM10 observado como referencia en cada cohorte. Las once variables restantes incluyen medias y desviación de siete días y un retardo de seis días respecto al último observado; por tanto, la nueva condición requiere hasta siete días completos antes del objetivo. No se eliminan otras variables junto con la media de 14 días.

## Definición de las cohortes

Las filas comunes tienen objetivo y todas las variables originales. Las adicionales tienen objetivo y las once variables de la variante, pero carecen de algún requisito original. La cohorte ampliada es la unión disjunta de ambas. Un objetivo ausente sigue excluido de las métricas, aunque pudieran existir entradas para emitir una predicción.

| Recuento | Madrid | Barcelona provincia |
| --- | ---: | ---: |
| Entrenamiento original de A y B | 6.096 | 5.367 |
| Entrenamiento ampliado de C | 6.305 | 5.852 |
| Calendario de validación | 1.095 | 1.095 |
| Validación común | 1.039 | 889 |
| Casos adicionales evaluables | 23 | 90 |
| Validación ampliada | 1.062 | 979 |
| Cobertura evaluada original | 94,9 % | 81,2 % |
| Cobertura evaluada de la variante | 97,0 % | 89,4 % |

Los recuentos describen disponibilidad retrospectiva de filas completas con objetivo conocido. No acreditan latencias ni disponibilidad de fuentes para avisos operativos. Los modelos B y C se evalúan tanto en las filas comunes como en las adicionales. A no se evalúa en las adicionales porque faltan entradas que exige su especificación.

## Precisión sobre las mismas filas

| Modelo · MAE en µg/m³ | Madrid, 1.039 casos | Barcelona, 889 casos |
| --- | ---: | ---: |
| Persistencia | 5,140 | 5,019 |
| A · Ridge actual | 4,826 | 4,510 |
| B · Sin media de 14 días, mismo entrenamiento | 4,847 | 4,526 |
| C · Sin media de 14 días, entrenamiento ampliado | 4,852 | 4,536 |

B aumenta el MAE frente a A aproximadamente 0,0219 en Madrid y 0,0164 µg/m³ en Barcelona. Ampliar además el entrenamiento con C aumenta el MAE frente a B aproximadamente 0,0047 y 0,0099 µg/m³, respectivamente, sobre estas mismas filas. Son estimaciones puntuales de una validación conocida; no se afirma que diferencias pequeñas sean estadísticamente sólidas ni que tengan el mismo efecto en otro periodo.

## Rendimiento sobre los casos recuperados

| Modelo · MAE en µg/m³ | Madrid, 23 casos adicionales | Barcelona, 90 casos adicionales |
| --- | ---: | ---: |
| Persistencia | 6,044 | 4,253 |
| B · Sin media de 14 días, mismo entrenamiento | 4,737 | 3,735 |
| C · Sin media de 14 días, entrenamiento ampliado | 4,745 | 3,762 |

Las variantes superan a persistencia en estos subconjuntos, pero no existe una predicción comparable de A en ellos. En Madrid los 23 casos proceden de Tres Olivos. En Barcelona se recuperan 66 casos de Rubí, 3 de Sant Celoni y 21 de Sant Vicenç.

Con el corte común de 27 µg/m³, Barcelona tiene 275 días elevados entre los 889 casos comunes y 18 entre los 90 adicionales. La composición de los grupos difiere. El MAE de B sobre las 979 filas ampliadas es 4,453 µg/m³, menor que el 4,510 de A sobre 889 filas, pero esa comparación mezcla el efecto de variables y el cambio de muestra. Sobre las mismas 889 filas, B tiene más MAE que A. Esta distinción es el motivo de mostrar las cohortes por separado.

## Fuentes, comprobaciones y salidas

El [módulo de cohortes](../pm10_data/evaluation/window_ablation.py) filtra primero las fechas hasta 2023 y comprueba claves únicas, horizonte, particiones, valores finitos y coherencia con la marca original de fila utilizable. Las pruebas alteran valores y duplican registros de 2024 y comprueban que no cambien las cohortes de entrenamiento o validación.

El [pipeline](../pm10_data/pipelines/compare_pm10_windows.py) lee las tablas supervisadas, los Ridge originales y las predicciones de validación conservadas. Antes de ajustar B y C escribe el protocolo con variables, parámetros, periodos, tamaños, versiones y huellas. Verifica por estación y fecha que A reproduce su validación guardada. Las pruebas de 2024 solo se identifican por huella para comprobar su integridad; no se leen como datos de evaluación de este experimento.

| Territorio | Tabla supervisada | Modelo original | Predicciones originales de validación |
| --- | --- | --- | --- |
| Madrid | data/interim/pm10_prediction/tabla_supervisada_pm10.csv | models/pm10/validation_2023/ridge.joblib | output/pm10_regression_validation/predicciones_validacion_2023.csv |
| Barcelona | data/interim/experiments/barcelona/tabla_supervisada.csv | models/experiments/barcelona/ridge.joblib | output/experiments/barcelona/validacion/predicciones.csv |

Los originales mantienen la [procedencia de los experimentos territoriales](38_experimentos_madrid_barcelona.md) y los controles de la [auditoría de cobertura](39_auditoria_cobertura_territorial.md). No se requieren nuevas descargas ni cambios de mapeador.

Cada territorio escribe en `output/experiments/window_ablation/{territorio}/` el protocolo, las predicciones de 2023, las claves de las cohortes común y adicional, las métricas agregadas, por estación y por mes, los coeficientes de B y C y un resumen JSON. Los nuevos artefactos B y C se guardan en `models/experiments/window_ablation/{territorio}/`. Los artefactos originales se conservan.

En `predicciones_2023.csv`, la clave es `codigo_estacion + fecha_objetivo + modelo`. Códigos, nombre, modelo y cohorte son texto; fechas son ISO; objetivo, último PM10, predicción y errores son decimales; la marca de predicción negativa corregida es booleana. `cohorte` vale `comun` o `adicional`. Las métricas añaden `ampliada` para B, C y persistencia sobre la unión, sin inventar una métrica ampliada para A. `n` y los recuentos de corrección son enteros; MAE, RMSE y sesgo son decimales. Los CSV usan coma, punto decimal y UTF-8 con BOM.

## React y API

**Experimentos → Comparación de ventanas** permite elegir Madrid o Barcelona y alternar filas comunes, adicionales y ampliadas. Muestra cobertura, el diseño A/B/C, diferencias sobre las filas comunes, métricas, barras de MAE en escala común y casos recuperados por estación. Las limitaciones y los límites temporales aparecen junto a los resultados. [Componente](../explorer/src/window-ablation.tsx)

`GET /api/experiments/window-ablation` devuelve el JSON guardado en `output/experiments/window_ablation/resumen.json`, sin cargar modelos ni entrenar desde Flask. Si no existe devuelve 404 con el comando de preparación. Incluye periodos textuales, diccionario de nombres de modelos, lista de experimentos, interpretación e indicador booleano de integridad original.

Cada experimento contiene identificador y nombre textuales; `counts` con recuentos enteros de entrenamiento y validación; `coverage` por estación; `metrics` con cohorte, modelo, n, MAE, RMSE, sesgo y correcciones; `sampleLevels` con recuentos de casos y elevados por cohorte; fechas máximas ISO; e indicadores y huellas de entradas y modelos. Los ficheros se leen en JSON local para la API y los modelos nuevos permanecen como artefactos de la entrega.

## Reproducción y conclusión

```powershell
.\.venv\Scripts\python.exe -m pm10_data.pipelines.compare_pm10_windows
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Se repitió el pipeline y coincidieron byte a byte los 25 artefactos generados, incluidos los cuatro modelos B/C, predicciones, métricas y protocolos. Las huellas de los modelos y pruebas originales permanecieron iguales. La suite comprueba la separación de cohortes, la recuperación esperada tras una ausencia, la exclusión de datos futuros, la restricción de predicciones no negativas y la lectura de resultados desde la API.

El experimento documenta un intercambio entre cobertura y precisión. B es una candidata para investigar mayor disponibilidad, mientras que ampliar el entrenamiento con C no mejora los MAE observados en estas cohortes. Se conservan los modelos de referencia. Una conclusión adicional de generalización requeriría fijar la variante y evaluarla en un periodo temporal independiente que no haya guiado sus decisiones.
