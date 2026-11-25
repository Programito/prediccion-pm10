"""Explore removing media_14_dias using training through 2022 and validation 2023.

Retain all original models and test results. No new 2024 evaluation is produced.
"""

import json
import platform

import numpy as np
import pandas as pd

from pm10_data.models.artifacts import load_model, save_model
from pm10_data.config import PROJECT_ROOT as ROOT
from pm10_data.adapters.sklearn.ridge import RidgeAdapter
from pm10_data.adapters.sklearn.base import backend_version
from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES
from pm10_data.evaluation.window_ablation import REDUCED_FEATURES, KEYS, make_window_cohorts, score_prediction_cases
from pm10_data.evaluation.pm10_regression import calculate_metrics
from pm10_data.pipelines.barcelona_experiment import digest, save_csv, save_json

SOURCES = {
    "madrid": dict(table="data/interim/pm10_prediction/tabla_supervisada_pm10.csv", model="models/pm10/validation_2023/ridge.joblib",
                   validation="output/pm10_regression_validation/predicciones_validacion_2023.csv", test="output/pm10_final_2024/predicciones_regresion.csv"),
    "barcelona": dict(table="data/interim/experiments/barcelona/tabla_supervisada.csv", model="models/experiments/barcelona/ridge.joblib",
                      validation="output/experiments/barcelona/validacion/predicciones.csv", test="output/experiments/barcelona/prueba_2024/predicciones.csv"),
}
MODELS = {"ridge_actual": "Ridge actual · 14 días", "ridge_sin14_mismo_train": "Sin media de 14 días · mismo entrenamiento",
          "ridge_sin14_train_ampliado": "Sin media de 14 días · entrenamiento ampliado", "persistencia": "Persistencia"}


def territory(experiment, sources):
    output = ROOT / "output/experiments/window_ablation" / experiment
    model_dir = ROOT / "models/experiments/window_ablation" / experiment
    input_hashes = {path: digest(ROOT / path) for path in sources.values()}
    table = pd.read_csv(ROOT / sources["table"], dtype={"codigo_estacion": str})
    cohorts = make_window_cohorts(table)
    original = load_model(ROOT / sources["model"])
    full_features = NUMERIC_FEATURES + ["codigo_estacion"]
    short_features = REDUCED_FEATURES + ["codigo_estacion"]
    baseline = original["pipeline"]
    if baseline.numeric_features != NUMERIC_FEATURES or baseline.categorical_features != ["codigo_estacion"]:
        raise ValueError("El modelo original no utiliza las variables esperadas.")
    common_variant = RidgeAdapter(REDUCED_FEATURES, ["codigo_estacion"], **baseline.get_parameters())
    expanded_variant = RidgeAdapter(REDUCED_FEATURES, ["codigo_estacion"], **baseline.get_parameters())
    protocol = dict(experiment=experiment, train=["2017-01-01", "2022-12-31"], validation=["2023-01-01", "2023-12-31"],
                    featuresOriginal=full_features, featuresReduced=short_features, parameters=baseline.get_parameters(),
                    models=MODELS, inputHashes=input_hashes, cohorts={key: len(rows) for key, rows in cohorts.items()},
                    design="A: frozen original; B: reduced features with same training cases; C: reduced features with expanded training cases",
                    negativePredictions="max(0, prediction)", imputation=False, newTestEvaluation=False,
                    selection="Exploratory follow-up motivated by known 2024 coverage; 2023 has already been used as validation; not a new independent test",
                    versions=dict(python=platform.python_version(), sklearn=backend_version(), numpy=np.__version__, pandas=pd.__version__))
    save_json(output / "protocolo.json", protocol)
    common_variant.fit(cohorts["train_common"][short_features], cohorts["train_common"].pm10_objetivo)
    expanded_variant.fit(cohorts["train_expanded"][short_features], cohorts["train_expanded"].pm10_objetivo)
    model_dir.mkdir(parents=True, exist_ok=True)
    for name, model in [("ridge_sin14_mismo_train", common_variant), ("ridge_sin14_train_ampliado", expanded_variant)]:
        save_model(dict(pipeline=model, protocol=protocol, model=name), model_dir / (name + ".joblib"))
        save_csv(output / (name + "_coeficientes.csv"), model.feature_details())
    predictions = [score_prediction_cases(cohorts["validation_common"], baseline.predict(cohorts["validation_common"][full_features]), "ridge_actual")]
    validation = cohorts["validation_expanded"]
    for name, model in [("ridge_sin14_mismo_train", common_variant), ("ridge_sin14_train_ampliado", expanded_variant)]:
        predictions.append(score_prediction_cases(validation, model.predict(validation[short_features]), name))
    predictions.append(score_prediction_cases(validation, validation.pm10_t.to_numpy(), "persistencia"))
    predictions = pd.concat(predictions, ignore_index=True)
    common_keys = set(zip(cohorts["validation_common"].codigo_estacion, cohorts["validation_common"].fecha_objetivo))
    predictions["cohorte"] = ["comun" if key in common_keys else "adicional" for key in zip(predictions.codigo_estacion, predictions.fecha_objetivo)]
    if not predictions.fecha_objetivo.dt.year.eq(2023).all():
        raise ValueError("Se han producido predicciones fuera de 2023.")
    saved = pd.read_csv(ROOT / sources["validation"], dtype={"codigo_estacion": str}, parse_dates=["fecha_objetivo"])
    frozen = predictions.loc[predictions.modelo.eq("ridge_actual")]
    paired = frozen.merge(saved.loc[saved.modelo.eq("ridge")], on=KEYS, validate="one_to_one", how="outer", indicator=True, suffixes=("_new", "_saved"))
    if (not paired._merge.eq("both").all() or not np.allclose(paired.pm10_objetivo_new, paired.pm10_objetivo_saved, rtol=0, atol=1e-12)
            or not np.allclose(paired.prediccion_new, paired.prediccion_saved, rtol=0, atol=1e-10)):
        raise ValueError("La referencia original no coincide con su validación guardada.")
    for key in ["validation_common", "validation_additional"]:
        rows = cohorts[key].copy()
        rows["cohorte"] = "comun" if key.endswith("common") else "adicional"
        save_csv(output / (key + ".csv"), rows[KEYS + ["NOMBRE", "pm10_objetivo"]])
    save_csv(output / "predicciones_2023.csv", predictions)
    extended = predictions.loc[predictions.modelo.ne("ridge_actual")].assign(cohorte="ampliada")
    grouped = pd.concat([predictions, extended], ignore_index=True)
    metrics = calculate_metrics(grouped, ["cohorte", "modelo"])
    save_csv(output / "metricas_2023.csv", metrics)
    save_csv(output / "metricas_por_estacion.csv", calculate_metrics(grouped, ["codigo_estacion", "NOMBRE", "cohorte", "modelo"]))
    save_csv(output / "metricas_por_mes.csv", calculate_metrics(grouped.assign(mes=grouped.fecha_objetivo.dt.month), ["mes", "cohorte", "modelo"]))
    coverage = []
    for code, rows in cohorts["calendar_validation"].groupby("codigo_estacion"):
        count = lambda key: int(cohorts[key].codigo_estacion.eq(code).sum())
        coverage.append(dict(station=code, name=rows.NOMBRE.iloc[0].strip(), calendar=len(rows),
                             common=count("validation_common"), additional=count("validation_additional"), expanded=count("validation_expanded"),
                             trainingCommon=count("train_common"), trainingExpanded=count("train_expanded")))
    details = []
    for cohort in ["comun", "adicional", "ampliada"]:
        if cohort == "comun":
            rows = cohorts["validation_common"]
        elif cohort == "adicional":
            rows = cohorts["validation_additional"]
        else:
            rows = cohorts["validation_expanded"]
        details.append(dict(cohort=cohort, n=len(rows), elevated=int(rows.pm10_objetivo.gt(27).sum())))
    if any(digest(ROOT / path) != sha for path, sha in input_hashes.items()):
        raise ValueError("Ha cambiado una entrada o un resultado protegido.")
    summary = dict(id=experiment, name="Madrid" if experiment == "madrid" else "Barcelona (provincia)",
                   counts={key: len(rows) for key, rows in cohorts.items()}, coverage=coverage, metrics=metrics.to_dict("records"),
                   sampleLevels=details, threshold=27, originalValidationMatches=True,
                   maxTrainingDate=cohorts["train_expanded"].fecha_objetivo.max().strftime("%Y-%m-%d"),
                   maxValidationDate=validation.fecha_objetivo.max().strftime("%Y-%m-%d"),
                   sources=[dict(path=path, sha256=sha) for path, sha in input_hashes.items()],
                   modelHashes={name: digest(model_dir / (name + ".joblib")) for name in ["ridge_sin14_mismo_train", "ridge_sin14_train_ampliado"]})
    save_json(output / "resumen.json", summary)
    print(experiment, json.dumps(summary["counts"]), flush=True)
    print(metrics.to_string(index=False), flush=True)
    return summary


def main():
    protected_paths = list((ROOT / "models/pm10").rglob("*.joblib")) + list((ROOT / "models/experiments/barcelona").glob("*.joblib"))
    protected_paths += [ROOT / source["test"] for source in SOURCES.values()]
    protected = {path.relative_to(ROOT).as_posix(): digest(path) for path in protected_paths}
    summaries = [territory(experiment, source) for experiment, source in SOURCES.items()]
    if any(digest(ROOT / path) != sha for path, sha in protected.items()):
        raise ValueError("Cambió un modelo o resultado de prueba original.")
    save_json(ROOT / "output/experiments/window_ablation/resumen.json", dict(
        train="2017–2022", validation="2023", models=MODELS, experiments=summaries,
        originalArtifactsUnchanged=True, originalArtifactHashes=protected,
        interpretation="Comparación exploratoria de validación; ningún modelo se promueve automáticamente. 2024 ya es conocido y se conserva sin nueva evaluación."))


if __name__ == "__main__":
    main()
