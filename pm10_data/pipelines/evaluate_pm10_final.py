"""Apply the frozen PM10 models and report results on the 2024 holdout."""

import hashlib
import json

import numpy as np
import pandas as pd

from pm10_data.models.artifacts import load_model
from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.pm10_regression import calculate_metrics
from pm10_data.pipelines.train_pm10_classification import classification_metrics


def export_tables(tables, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(destination / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")


def main():
    protocol_path = PROJECT_ROOT / "docs/reference/pm10_final_protocol.json"
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    paths = {}
    for key, entry in protocol["entradas"].items():
        path = PROJECT_ROOT / entry["ruta"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"El archivo difiere del registrado en el protocolo: {path.name}")
        paths[key] = path

    ridge = load_model(paths["ridge"])
    logistic = load_model(paths["logistica"])
    if (ridge["modelo"] != "ridge" or logistic["modelo"] != "logistica"
            or ridge["configuracion"]["fecha_maxima_entrenamiento"] != "2022-12-31"
            or logistic["configuracion"]["periodo_entrenamiento_objetivo"] != "2017–2022"):
        raise ValueError("Los modelos guardados no coinciden con el alcance fijado.")
    ridge_features = ridge["configuracion"]["variables"]
    logistic_features = logistic["configuracion"]["variables"]
    if not {"semana_sin", "semana_cos"}.issubset(ridge_features):
        raise ValueError("Se esperaba Ridge con las variables del día de la semana.")

    table = pd.read_csv(paths["tabla"], dtype={"codigo_estacion": "string"},
                        parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    year = protocol["anio_objetivo"]
    is_test = table.fecha_objetivo.dt.year.eq(year)
    if not is_test.eq(table.particion.eq(protocol["particion"])).all():
        raise ValueError("El año objetivo y la partición de prueba no coinciden.")
    test = table.loc[is_test].copy()
    if (set(test.codigo_estacion) != set(protocol["estaciones"])
            or test.duplicated(["codigo_estacion", "fecha_objetivo"]).any()
            or not (test.fecha_objetivo - test.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all()):
        raise ValueError("La prueba debe contener una observación por estación y fecha con horizonte de un día.")
    predictors = sorted((set(ridge_features + logistic_features) - {"codigo_estacion"}) | {"pm10_objetivo", "pm10_t"})
    if not np.isfinite(test[predictors].to_numpy(dtype=float)).all():
        raise ValueError("Hay valores numéricos no finitos en la cohorte completa.")

    threshold = protocol["umbral_pm10_ug_m3"]
    if logistic["configuracion"]["umbral_pm10_ug_m3"] != threshold:
        raise ValueError("La etiqueta del modelo logístico difiere del protocolo.")
    base = test[["codigo_estacion", "NOMBRE", "fecha_ultima_observacion", "fecha_objetivo", "pm10_t", "pm10_objetivo"]].copy()
    observed_elevated = base.pm10_objetivo.gt(threshold)
    today_elevated = base.pm10_t.gt(threshold)
    if test.pm10_elevado_objetivo.isna().any() or not test.pm10_elevado_objetivo.eq(observed_elevated).all():
        raise ValueError("Las etiquetas observadas difieren del umbral fijado.")

    ridge_raw = ridge["pipeline"].predict(test[ridge_features])
    if not np.isfinite(ridge_raw).all():
        raise ValueError("Ridge generó una predicción no finita.")
    regression = pd.concat([
        base.assign(modelo="ridge", prediccion=np.maximum(0, ridge_raw), prediccion_negativa_corregida=ridge_raw < 0),
        base.assign(modelo="persistencia", prediccion=base.pm10_t, prediccion_negativa_corregida=False),
    ], ignore_index=True)
    regression["error"] = regression.prediccion - regression.pm10_objetivo
    regression["error_absoluto"] = regression.error.abs()
    regression["error_cuadrado"] = regression.error.pow(2)
    regression["tramo"] = np.where(regression.pm10_objetivo.gt(threshold), "elevado", "resto")
    with_total = pd.concat([regression, regression.assign(tramo="todos")], ignore_index=True)

    probability = logistic["pipeline"].predict_positive_probability(test[logistic_features])
    if not ((probability >= 0) & (probability <= 1)).all():
        raise ValueError("La logística generó una probabilidad no válida.")
    label_base = base.assign(observado=observed_elevated.astype(int), hoy_elevado=today_elevated,
                             contexto=np.where(today_elevated, "hoy_elevado", "hoy_no_elevado"))
    classification = pd.concat([
        label_base.assign(modelo="logistica", aviso=(probability >= protocol["umbral_probabilidad_logistica"]).astype(int),
                          probabilidad_elevado=probability),
        label_base.assign(modelo="persistencia", aviso=today_elevated.astype(int), probabilidad_elevado=np.nan),
    ], ignore_index=True)

    coverage = base.groupby(["codigo_estacion", "NOMBRE"], as_index=False).agg(filas_evaluadas=("fecha_objetivo", "size"))
    coverage["dias_calendario"] = len(pd.date_range(f"{year}-01-01", f"{year}-12-31"))
    coverage["dias_excluidos"] = coverage.dias_calendario - coverage.filas_evaluadas
    coverage["proporcion_evaluada"] = coverage.filas_evaluadas / coverage.dias_calendario
    regression_metrics = calculate_metrics(with_total, ["tramo", "modelo"])
    class_metrics = classification_metrics(classification, ["modelo"])
    context_metrics = classification_metrics(classification, ["contexto", "modelo"])
    output = PROJECT_ROOT / "output/pm10_final_2024"
    export_tables({
        "cobertura_por_estacion": coverage, "predicciones_regresion": regression,
        "metricas_regresion": regression_metrics,
        "metricas_regresion_por_estacion": calculate_metrics(with_total, ["codigo_estacion", "NOMBRE", "tramo", "modelo"]),
        "predicciones_clasificacion": classification, "metricas_clasificacion": class_metrics,
        "metricas_clasificacion_por_contexto": context_metrics,
        "metricas_clasificacion_por_estacion": classification_metrics(classification, ["codigo_estacion", "NOMBRE", "modelo"]),
    }, output)
    metadata = {"anio_objetivo": year, "filas_evaluadas": len(test),
                "sha256_protocolo": hashlib.sha256(protocol_bytes).hexdigest(), "reajuste": False}
    (output / "ejecucion.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(coverage.to_string(index=False))
    print(regression_metrics.to_string(index=False))
    print(class_metrics.to_string(index=False))
    print(context_metrics.to_string(index=False))


if __name__ == "__main__":
    main()
