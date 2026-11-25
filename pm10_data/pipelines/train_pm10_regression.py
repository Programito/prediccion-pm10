"""Train on 2017-2022 and compare in 2023. Keep 2024 reserved.

Run: python -m pm10_data.pipelines.train_pm10_regression
"""

import hashlib
import json
import platform

import joblib
import numpy as np
import pandas as pd

from pm10_data.models.artifacts import save_model
from pm10_data.config import PROJECT_ROOT
from pm10_data.adapters.sklearn.base import backend_version
from pm10_data.models.factory import FEATURES, create_models
from pm10_data.evaluation.pm10_regression import split_dataset, evaluate_models, calculate_metrics


def main():
    root = PROJECT_ROOT
    source = root / "data/interim/pm10_prediction/tabla_modelos_completa.csv"
    output = root / "output/pm10_regression_validation"
    model_folder = root / "models/pm10/validation_2023"
    table = pd.read_csv(source, dtype={"codigo_estacion": "string"}, parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    training, validation = split_dataset(table)
    models = create_models()
    versions = {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": backend_version(), "joblib": joblib.__version__}
    configuration = {
        "parametros_ridge": models["ridge"].get_parameters(), "parametros_random_forest": models["random_forest"].get_parameters(),
        "variables": FEATURES, "filas_entrenamiento": len(training), "filas_validacion": len(validation),
        "fecha_maxima_entrenamiento": training.fecha_objetivo.max().strftime("%Y-%m-%d"),
        "fecha_minima_validacion": validation.fecha_objetivo.min().strftime("%Y-%m-%d"),
        "fecha_maxima_validacion": validation.fecha_objetivo.max().strftime("%Y-%m-%d"),
        "busqueda_hiperparametros": False, "restriccion_fisica": "prediccion = max(0, prediccion_sin_restriccion)",
        "archivo_entrada": str(source.relative_to(root)), "sha256_entrada": hashlib.sha256(source.read_bytes()).hexdigest(),
        "versiones": versions, "prueba_2024_evaluada": False,
        "alcance": "Comparación retrospectiva en 2023. No se ajusta ningún componente con validación ni se evalúa 2024.",
    }
    output.mkdir(parents=True, exist_ok=True)
    # Guardar la configuración antes de ajustar o examinar los errores.
    (output / "configuracion.json").write_text(json.dumps(configuration, ensure_ascii=False, indent=2), encoding="utf-8")
    predictions = evaluate_models(training, validation, models)
    metrics = calculate_metrics(predictions, ["modelo"])
    by_station = calculate_metrics(predictions, ["modelo", "codigo_estacion", "NOMBRE"])
    reference = float(metrics.loc[metrics.modelo.eq("persistencia"), "mae"].iloc[0])
    metrics["mejora_mae_vs_persistencia_pct"] = 100 * (reference - metrics.mae) / reference
    referencia_estacion = by_station.loc[by_station.modelo.eq("persistencia"), ["codigo_estacion", "mae"]].rename(columns={"mae": "mae_persistencia"})
    by_station = by_station.merge(referencia_estacion, on="codigo_estacion", validate="many_to_one")
    by_station["mejora_mae_vs_persistencia_pct"] = 100 * (by_station.mae_persistencia - by_station.mae) / by_station.mae_persistencia
    metrics = metrics.sort_values("mae")
    for name, df in [("metricas_validacion_2023", metrics), ("metricas_por_estacion", by_station), ("predicciones_validacion_2023", predictions)]:
        df.to_csv(output / f"{name}.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    model_folder.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        save_model({"pipeline": model, "configuracion": configuration, "modelo": name}, model_folder / f"{name}.joblib")
    models["ridge"].feature_details().to_csv(output / "coeficientes_ridge.csv", index=False, encoding="utf-8-sig")
    models["random_forest"].feature_details().to_csv(output / "importancias_random_forest.csv", index=False, encoding="utf-8-sig")
    print(metrics.to_string(index=False))
    print(by_station.to_string(index=False))
    print("Modelos guardados. 2024 sigue reservado, sin predicciones ni métricas de prueba.")


if __name__ == "__main__":
    main()
