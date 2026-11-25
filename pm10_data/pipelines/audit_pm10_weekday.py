"""Compare Ridge with and without weekday features on the same 2023 rows."""

import json

import pandas as pd

from pm10_data.adapters.sklearn.ridge import RidgeAdapter
from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.pm10_regression import calculate_metrics, evaluate_models, split_dataset
from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES


def main():
    inputs = PROJECT_ROOT / "data/interim/pm10_prediction"
    table = pd.read_csv(inputs / "tabla_modelos_completa.csv", dtype={"codigo_estacion": "string"},
                        parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    training, validation = split_dataset(table)
    threshold = json.loads((inputs / "protocolo.json").read_text(encoding="utf-8"))["umbral_clasificacion"]
    without_weekday = [feature for feature in NUMERIC_FEATURES if feature not in {"semana_sin", "semana_cos"}]
    models = {"ridge_con_dia_semana": RidgeAdapter(NUMERIC_FEATURES, ["codigo_estacion"]),
              "ridge_sin_dia_semana": RidgeAdapter(without_weekday, ["codigo_estacion"])}
    predictions = evaluate_models(training, validation, models)
    predictions = predictions.loc[predictions.modelo.isin([*models, "persistencia"])].copy()
    predictions["tramo"] = predictions.pm10_objetivo.gt(threshold).map({True: "elevado", False: "resto"})
    all_groups = pd.concat([predictions, predictions.assign(tramo="todos")], ignore_index=True)
    metrics = calculate_metrics(all_groups, ["tramo", "modelo"])
    by_station = calculate_metrics(all_groups, ["codigo_estacion", "NOMBRE", "tramo", "modelo"])
    output = PROJECT_ROOT / "output/pm10_weekday_audit"
    output.mkdir(parents=True, exist_ok=True)
    for name, result in [("metricas_validacion_2023", metrics), ("metricas_por_estacion", by_station),
                         ("predicciones_validacion_2023", predictions)]:
        result.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    config = {
        "filas_entrenamiento": len(training), "filas_validacion": len(validation),
        "parametros_ridge": models["ridge_con_dia_semana"].get_parameters(),
        "variables_numericas_con_dia_semana": NUMERIC_FEATURES,
        "variables_numericas_sin_dia_semana": without_weekday, "variable_categorica": "codigo_estacion",
        "umbral_pm10_elevado_ug_m3": threshold, "regla_elevado": "PM10 observado > umbral",
        "prueba_2024_evaluada": False,
    }
    (output / "configuracion.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(metrics.to_string(index=False))
    print(by_station.loc[by_station.tramo.isin(["todos", "elevado"])].to_string(index=False))


if __name__ == "__main__":
    main()
