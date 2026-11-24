# Explicabilidad de Ridge y Random Forest

## Versiones explicadas

Los dos modelos se ajustaron con objetivos de 2017 a 2022 y se compararon en validación de 2023. Los coeficientes e importancias proceden de los artefactos guardados en `models/pm10/validation_2023/`. El Ridge seleccionado es el mismo modelo congelado que se utilizó en la prueba final de 2024. [Configuración del ajuste](../output/pm10_regression_validation/configuracion.json) · [Protocolo de prueba](reference/pm10_final_protocol.json)

La exportación de explicaciones comprueba las huellas de la tabla y de Ridge contra el protocolo. También contrasta los coeficientes y las importancias exportadas con los dos modelos guardados. Se conservaron sus parámetros y los componentes ajustados.

## Coeficientes de Ridge

Ridge expresa la predicción mediante un intercepto y una suma de coeficientes multiplicados por sus variables transformadas. Las entradas numéricas se estandarizan usando la media y la desviación del entrenamiento. La estación se representa mediante tres indicadores de valor cero o uno.

Un coeficiente numérico describe el cambio de predicción asociado a una unidad estandarizada de esa variable, manteniendo las demás entradas fijas. Los coeficientes de estación describen aportaciones para el indicador activo y deben interpretarse junto al intercepto. [Coeficientes completos](../output/pm10_regression_validation/coeficientes_ridge.csv)

| Variable transformada | Coeficiente, en µg/m³ |
| --- | ---: |
| PM10 del día previo al objetivo | 6,937 |
| Variabilidad de los últimos siete días | −2,464 |
| Media de los últimos tres días | 2,030 |
| PM10 de dos días antes del objetivo | −1,928 |
| Media de los últimos siete días | 1,620 |

El último PM10 observado tiene el mayor coeficiente en valor absoluto. Las medias, la variabilidad y los retardos contienen información relacionada entre sí. Esa dependencia puede repartir el peso y producir signos que requieren interpretar el conjunto de entradas. Por ejemplo, el coeficiente negativo de variabilidad expresa cómo utiliza esa variable este ajuste cuando se mantienen fijas las demás entradas. Una alteración aislada puede representar una combinación poco frecuente de valores.

Las codificaciones seno y coseno del calendario se interpretan conjuntamente como pares cíclicos. La interpretación de los coeficientes describe asociaciones dentro del modelo y depende del escalado y la regularización.

## Importancia de Random Forest

Se utiliza la proporción de reducción de impureza acumulada en las divisiones de los árboles para cada variable. Las importancias suman uno y permiten describir qué entradas utilizó más el bosque durante el ajuste. [Importancias completas](../output/pm10_regression_validation/importancias_random_forest.csv)

| Variable | Importancia |
| --- | ---: |
| PM10 del día previo al objetivo | 61,3 % |
| PM10 de dos días antes del objetivo | 10,3 % |
| Media de los últimos catorce días | 4,7 % |
| Media de los últimos tres días | 4,2 % |
| Variabilidad de los últimos siete días | 3,4 % |

El 61,3 % corresponde a la proporción de reducción de impureza atribuida a esa variable durante el entrenamiento. La medida carece de signo y su magnitud puede verse afectada por la cantidad de valores posibles y por la correlación entre entradas. El gráfico sirve como descripción global del bosque ajustado. Una evaluación posterior mediante permutaciones sobre validación permitiría estudiar su relación con el error predictivo, considerando la dependencia entre variables.

## Descomposición exacta de una predicción

Para cada fila de prueba se aplica el preprocesamiento ya ajustado y se calcula la aportación de cada variable.

```text
valor numérico transformado = (entrada − media de entrenamiento) / escala de entrenamiento
aportación = valor transformado × coeficiente
predicción original = intercepto + suma de aportaciones
predicción publicada = máximo entre cero y predicción original
```

La implementación respeta la escala del transformador guardado, incluidos sus tratamientos de variables constantes. Los indicadores de estación toman valores cero o uno.

En **Tres Olivos, el 31 de octubre de 2024**, el valor observado fue 156 µg/m³ y Ridge predijo 45,726 µg/m³. El intercepto fue 15,401 µg/m³. El PM10 previo aportó aproximadamente +30,601 µg/m³, la variabilidad semanal −4,989 y la media de tres días +2,718. La tabla interactiva incluye todas las aportaciones que completan la suma. El error absoluto de este caso fue 110,274 µg/m³.

La reconstrucción muestra cómo el modelo llegó a su predicción y permite estudiar su infraestimación de ese pico. Cada aportación está referida al intercepto y a la codificación de las variables.

Se reconstruyeron las **1.013 predicciones de Ridge evaluadas en 2024**. La mayor diferencia entre la suma de aportaciones más el intercepto y la salida del modelo fue aproximadamente 7,1 × 10⁻¹⁵ µg/m³, dentro de la precisión numérica. También se comprobó la coincidencia con las predicciones guardadas tras la restricción de concentración no negativa.

## Consulta en React

La pestaña **Gráficos** incorpora la vista **Explicabilidad**. Comparte estación y fecha con Observaciones y Predicciones. Permite consultar el observado y la predicción y recorrer las entradas, valores transformados, coeficientes y aportaciones. La selección inicial es Tres Olivos el 31 de octubre de 2024. Cambiar de estación conserva la fecha; una fecha excluida de la prueba muestra un aviso.

Los gráficos globales muestran todos los coeficientes de Ridge y las importancias de Random Forest. La guía de explicabilidad también está disponible desde **Documentación**.

Flask sirve la explicación desde `GET /api/charts/explanations?station=28079060&date=2024-10-31`. La respuesta incluye la fecha seleccionada, las fechas evaluables y las descripciones globales. Lee las explicaciones previamente exportadas.

## Reproducción y evidencias

Desde la raíz del proyecto, ejecutar

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.explain_pm10_models
```

El [pipeline de exportación](../tfm_data/pipelines/explain_pm10_models.py) reutiliza el [adaptador de Ridge](../tfm_data/adapters/sklearn/ridge.py). Genera [las explicaciones](../output/pm10_explanations/explicaciones.json) y [las huellas y comprobaciones](../output/pm10_explanations/configuracion.json). El archivo de explicaciones ocupa aproximadamente 1 MB y conserva las 1.013 filas para consultar distintas fechas.

La prueba específica comprueba la transformación numérica y la reconstrucción de la predicción. El entorno `.venv` se reparó el 19 de noviembre de 2026 y se verificó la versión de scikit-learn 1.9.1 utilizada en los artefactos.
