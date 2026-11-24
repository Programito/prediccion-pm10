"""Compare matched logistic PM10 models with and without GFS in 2023."""

import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from tfm_data.adapters.sklearn.base import backend_version
from tfm_data.adapters.sklearn.logistic import LogisticAdapter
from tfm_data.config import PROJECT_ROOT
from tfm_data.pipelines.train_pm10_classification import classification_metrics


LABEL = "pm10_elevado_objetivo"
KEY = ["codigo_estacion", "fecha_objetivo"]


def threshold_sweep(scores, elevated, today_high):
    """Count all distinct alert sets, adding tied scores together."""
    ranked = pd.DataFrame({"umbral": scores, "positivos_detectados": elevated,
                           "falsas_alarmas": ~elevated, "comienzos_detectados": elevated & ~today_high,
                           "falsas_alarmas_con_hoy_no_elevado": ~elevated & ~today_high})
    counts = ranked.groupby("umbral").sum().sort_index(ascending=False).cumsum()
    counts.loc[np.nextafter(float(ranked.umbral.max()), np.inf)] = 0
    return counts.sort_index(ascending=False).reset_index()


def main():
    inputs = PROJECT_ROOT / "data/interim/pm10_weather"
    source = inputs / "tabla_pm10_meteo.csv"
    schema = json.loads((inputs / "esquema_comparacion.json").read_text(encoding="utf-8"))
    table = pd.read_csv(source, parse_dates=["fecha_objetivo"], dtype={"codigo_estacion": "string"})
    common = table.loc[table[schema["criterio_cohorte"]]]
    training = common.loc[common.particion_meteo.eq("entrenamiento")]
    validation = common.loc[common.particion_meteo.eq("validacion")].reset_index(drop=True)
    if (training.empty or validation.empty or not training.fecha_objetivo.dt.year.isin([2021, 2022]).all()
            or not validation.fecha_objetivo.dt.year.eq(2023).all()
            or training.duplicated(KEY).any() or validation.duplicated(KEY).any()):
        raise ValueError("La comparación requiere filas únicas de entrenamiento 2021–2022 y validación 2023.")

    base_features = schema["predictores_base"]
    weather_features = schema["predictores_meteorologicos"]
    categorical = ["codigo_estacion"]
    predictors = {"logistica_sin_meteo": base_features, "logistica_con_meteo": base_features + weather_features}
    threshold_pm10 = schema["umbral_pm10_elevado_ug_m3"]
    for rows in (training, validation):
        numeric = rows[[field for field in base_features + weather_features if field not in categorical]]
        if (not np.isfinite(numeric.to_numpy(dtype=float)).all() or rows[LABEL].isna().any()
                or not rows[LABEL].eq(rows.pm10_objetivo.gt(threshold_pm10)).all()
                or set(rows[LABEL].unique()) != {0, 1}):
            raise ValueError("Las filas comunes deben tener predictores completos y etiquetas válidas de ambas clases.")

    cases = validation[KEY + ["NOMBRE", "pm10_t", "pm10_objetivo"]].copy()
    cases["observado"] = validation[LABEL].astype(int)
    elevated = cases.observado.eq(1)
    today_high = cases.pm10_t.gt(threshold_pm10)
    cases["contexto"] = np.where(today_high, "hoy_elevado", "hoy_no_elevado")
    false_alarm_budget = int((today_high & ~elevated).sum())
    predictions = [cases.assign(modelo="persistencia", aviso=today_high.astype(int), probabilidad_elevado=np.nan)]
    sweeps, cuts, models = [], {}, {}
    for name, features in predictors.items():
        numeric_features = [feature for feature in features if feature not in categorical]
        model = LogisticAdapter(numeric_features, categorical).fit(training[features], training[LABEL].astype(int))
        scores = model.predict_positive_probability(validation[features])
        if not pd.Series(scores).between(0, 1).all():
            raise ValueError(f"Probabilidades inválidas en {name}.")
        sweep = threshold_sweep(scores, elevated, today_high)
        candidate = sweep.loc[sweep.falsas_alarmas.le(false_alarm_budget)].sort_values(
            ["comienzos_detectados", "positivos_detectados", "falsas_alarmas", "umbral"],
            ascending=[False, False, True, False],
        ).iloc[0]
        cuts[name] = float(candidate.umbral)
        models[name] = model
        sweeps.append(sweep.assign(modelo=name))
        predictions.append(cases.assign(modelo=name, aviso=(scores >= cuts[name]).astype(int), probabilidad_elevado=scores))

    predictions = pd.concat(predictions, ignore_index=True)
    overall = classification_metrics(predictions, ["modelo"])
    context = classification_metrics(predictions, ["contexto", "modelo"])
    configuration = {
        "entrenamiento": "2021–2022", "validacion_y_seleccion_umbral": "2023", "filas_entrenamiento": len(training),
        "filas_validacion": len(validation), "predictores": predictors, "umbral_pm10_ug_m3": threshold_pm10,
        "limite_falsas_alarmas_validacion": false_alarm_budget, "origen_limite": "falsas alarmas de persistencia en las mismas filas",
        "orden_seleccion": ["más comienzos detectados", "más positivos detectados", "menos falsas alarmas", "corte más alto"],
        "cortes_probabilidad": cuts, "parametros_logistica": models["logistica_sin_meteo"].get_parameters(),
        "sha256_tabla": hashlib.sha256(source.read_bytes()).hexdigest(), "sklearn": backend_version(),
    }
    output = PROJECT_ROOT / "output/pm10_weather_validation"
    output.mkdir(parents=True, exist_ok=True)
    for name, result in [("metricas_validacion_2023", overall), ("metricas_por_contexto", context),
                         ("predicciones_validacion_2023", predictions), ("barrido_umbrales_2023", pd.concat(sweeps, ignore_index=True))]:
        result.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    (output / "configuracion.json").write_text(json.dumps(configuration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    model_folder = PROJECT_ROOT / "models/pm10/weather_validation_2023"
    model_folder.mkdir(parents=True, exist_ok=True)
    joblib.dump({"modelos": models, "configuracion": configuration}, model_folder / "logisticas_gfs.joblib", compress=3)
    print(overall.to_string(index=False))
    print(context.to_string(index=False))
    print(cuts)


if __name__ == "__main__":
    main()
