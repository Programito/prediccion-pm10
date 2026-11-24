# Primeros modelos: Ridge y Random Forest

## Qué hemos comparado

Se ajustan dos modelos con las 6.096 filas completas de entrenamiento de 2017-2022 y se evalúan en las mismas 1.039 filas de validación de 2023 usadas por las referencias. No se calculan predicciones ni métricas de prueba de 2024.

La lista de entrada está limitada a las 12 variables numéricas del protocolo y la identidad de estación. No se introducen el objetivo, la etiqueta de clasificación ni columnas de auditoría como predictores. El preprocesamiento se ajusta dentro de cada pipeline usando exclusivamente entrenamiento.

### Ridge: una regresión lineal regularizada

Combina variables mediante coeficientes y penaliza su tamaño. Esto ayuda cuando las variables están relacionadas entre sí, como la contaminación actual y las medias recientes. Las variables numéricas se estandarizan con media y desviación de entrenamiento. La estación se codifica en columnas binarias.

Configuración inicial, sin búsqueda de hiperparámetros: `alpha=10`, solver SVD. Se predice directamente PM10 de mañana; el modelo sanitario previo predecía una variación y es un experimento distinto.

### Random Forest: un conjunto de árboles

Cada árbol aprende reglas de decisión y las predicciones de los árboles se promedian. Puede recoger relaciones no lineales e interacciones entre historial, calendario y estación. No necesita estandarizar las variables numéricas; utiliza el mismo conjunto de información que Ridge.

Configuración inicial: 200 árboles, profundidad máxima 12, mínimo de 5 muestras en una hoja, todas las variables disponibles por división, bootstrap, semilla 42 y dos procesos de trabajo. Son valores fijados antes de calcular los resultados, no elegidos entre muchas ejecuciones con la validación.

Se fija para ambos una restricción física `predicción = máximo(0, predicción original)`. Se conserva la salida sin restricción y se contabilizan las correcciones. En esta validación no hubo predicciones negativas.

Documentación técnica: [Ridge](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html), [RandomForestRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html) y [ColumnTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html).

## Resultado de validación de 2023

Unidades de MAE y RMSE: µg/m3. Menor es mejor. La mejora es relativa al MAE de persistencia en las mismas filas.

| Modelo o referencia | MAE | RMSE | Mejora del MAE frente a persistencia |
| --- | ---: | ---: | ---: |
| Ridge | 4,83 | 7,51 | 6,11 % |
| Random Forest | 4,95 | 7,87 | 3,78 % |
| Persistencia | 5,14 | 8,35 | 0 % |
| Media móvil de 7 días | 6,52 | 9,97 | -26,95 % |
| Referencia semanal | 8,75 | 13,36 | -70,26 % |

Mejora del MAE por estación:

| Estación | Ridge | Random Forest |
| --- | ---: | ---: |
| Tres Olivos | 9,39 % | 7,52 % |
| Majadahonda | 5,43 % | 1,86 % |
| San Martín de Valdeiglesias | 2,72 % | 1,03 % |

Ridge es el mejor candidato inicial por MAE y RMSE en esta validación y mejora la persistencia en las tres estaciones. Su reducción global absoluta de MAE es de aproximadamente 0,31 µg/m3: una mejora modesta que necesita contrastarse en episodios altos y otros periodos. No es un resultado de prueba final ni se ha medido significación estadística o ahorro económico.

El sesgo medio global es 0,24 en Ridge y 0,49 en Random Forest. El sesgo cambia de signo entre estaciones; por eso el promedio global no basta para describir el comportamiento. Los detalles por estación y las predicciones completas se guardan para analizarlos.

## Artefactos y reproducibilidad

Código: `tfm_data/pipelines/train_pm10_regression.py`.

Resultados en `output/pm10_regression_validation/`:

- `configuracion.json`: parámetros fijados, lista de entrada, tamaños, fechas, versiones y huella del CSV utilizado. Se escribe antes de entrenar y evaluate.
- `metricas_validacion_2023.csv` y `metricas_por_estacion.csv`: errores globales y por estación.
- `predicciones_validacion_2023.csv`: observación, predicción original, predicción restringida y errores por fila.
- `coeficientes_ridge.csv`: coeficientes; los numéricos corresponden a variables estandarizadas y los indicadores de estación están en otra escala.
- `importancias_random_forest.csv`: importancias por reducción de impureza. Son una descripción inicial del modelo, no una atribución causal ni una evaluación independiente de importancia; las variables correlacionadas requieren cautela.

Los pipelines ajustados únicamente con entrenamiento están en `models/pm10/validation_2023/ridge.joblib` y `random_forest.joblib`, junto con su configuración. No son todavía modelos finales reentrenados con validación ni desplegados.

Las versiones directas utilizadas están fijadas en `requirements.txt`. La configuración registra Python 3.12 y las bibliotecas empleadas. Se ha creado un entorno local `.venv` y no se han modificado los originales.

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.train_pm10_regression
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Próximo análisis

Examinar dónde fallan los modelos, especialmente concentraciones elevadas y diferencias por estación. Después abordar la clasificación ya definida y el contraste temporal clásico. Evitar ajustar repetidamente modelos a 2023 hasta obtener un resultado favorable. 2024 continúa reservado para la evaluación final del enfoque seleccionado.
