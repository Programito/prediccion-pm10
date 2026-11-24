# Estructura en inglés y adaptadores de modelos

## Responsabilidades

| Carpeta | Responsabilidad |
| --- | --- |
| `tfm_data/mappers/` | Lectura y normalización de fuentes y preparación de variables. |
| `tfm_data/evaluation/` | Auditorías, viabilidad histórica y comparación de modelos. |
| `tfm_data/pipelines/` | Coordinar la ejecución y guardar resultados. |
| `tfm_data/models/` | Contrato `Regressor` y selección de modelos mediante una fábrica. |
| `tfm_data/adapters/sklearn/` | Importar y configurar scikit-learn, preprocesar y exponer la interfaz propia. |
| `tfm_data/config.py` | Resolver la raíz del proyecto sin depender de la profundidad de cada módulo. |

El paquete se llama ahora `tfm_data`. Los módulos, clases principales y funciones públicas usan nombres en inglés. Por ejemplo, `INEHealthMapper.transform`, `AirQualityMapper.transform`, `AirCoverageAuditor.audit` y `PM10ForecastMapper.transform`.

Las carpetas de datos y resultados también se han pasado a inglés, como `data/raw/health_air_history/`, `data/interim/daily_pollution/`, `data/interim/pm10_prediction/` y `output/pm10_regression_validation/`. Los nombres de los archivos originales, los esquemas de las tablas y sus valores se conservan; los nombres de columnas de las tablas históricas siguen en español. No confundir un cambio de organización con una nueva versión de los datos.

## Qué hace un adaptador

`RidgeAdapter` importa `Ridge` dentro de `adapters/sklearn/ridge.py`. `RandomForestAdapter` hace lo mismo con `RandomForestRegressor`. Su base compartida encapsula `Pipeline`, `ColumnTransformer`, `StandardScaler` y `OneHotEncoder`. La función de versión del backend también está dentro de esa carpeta.

El resto del código utiliza nuestro contrato:

```python
from tfm_data.models.factory import create_models

model = create_models()["ridge"]
model.fit(x_train, y_train)
predictions = model.predict(x_validation)
```

`fit` ajusta el preprocesamiento y el modelo con entrenamiento. `predict` reutiliza lo aprendido. Las operaciones `get_parameters()` y `feature_details()` permiten guardar configuración y explicaciones sin que el pipeline coordinador importe clases del proveedor.

La fábrica permite elegir las implementaciones. El contrato se declara como `Protocol`: otro adaptador puede cumplirlo sin heredar de scikit-learn. La evaluación solo exige esa interfaz. La regresión histórica sanitaria implementada en NumPy sigue siendo un experimento separado; no importa scikit-learn.

## Ejecución actualizada

```powershell
.\.venv\Scripts\python.exe -m tfm_data.pipelines.prepare_pm10_forecast
.\.venv\Scripts\python.exe -m tfm_data.pipelines.train_pm10_regression
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Otros ejemplos: `tfm_data.pipelines.prepare_health`, `tfm_data.pipelines.prepare_demographics`, `tfm_data.pipelines.prepare_air`, `tfm_data.pipelines.audit_air_coverage` y `tfm_data.pipelines.pollution_sample`. Las guías anteriores se han actualizado con las nuevas rutas y comandos.

Los modelos guardados en `models/pm10/validation_2023/` contienen ahora los adaptadores del proyecto, que incorporan su pipeline ajustado. El campo histórico `pipeline` del contenedor serializado se mantiene, pero su valor implementa la interfaz propia. Las predicciones se han contrastado con las anteriores al refactor, dentro de tolerancia numérica estricta. Los imports de scikit-learn están protegidos por una prueba de arquitectura.

El cambio no introduce nuevos algoritmos ni ajusta hiperparámetros. Se sigue entrenando solo con 2017-2022 y evaluando en 2023; 2024 permanece reservado. Las huellas de los 43 archivos originales se han verificado tras mover sus carpetas.
