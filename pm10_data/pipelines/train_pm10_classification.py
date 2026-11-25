"""Compare logistic regression and persistence for elevated PM10 in 2023."""

import json

import numpy as np
import pandas as pd

from pm10_data.models.artifacts import save_model
from pm10_data.adapters.sklearn.base import backend_version
from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.pm10_regression import split_dataset
from pm10_data.models.factory import FEATURES, create_classifier


LABEL = "pm10_elevado_objetivo"
PROBABILITY_THRESHOLD = 0.5


def classification_metrics(predictions, keys):
    counts = predictions.assign(
        vp=predictions.observado.eq(1) & predictions.aviso.eq(1),
        fp=predictions.observado.eq(0) & predictions.aviso.eq(1),
        fn=predictions.observado.eq(1) & predictions.aviso.eq(0),
        vn=predictions.observado.eq(0) & predictions.aviso.eq(0),
    ).groupby(keys, as_index=False).agg(n=("aviso", "size"), vp=("vp", "sum"), fp=("fp", "sum"),
                                        fn=("fn", "sum"), vn=("vn", "sum"))
    alerts = counts.vp + counts.fp
    positives = counts.vp + counts.fn
    counts["avisos"] = alerts
    counts["positivos"] = positives
    counts["precision"] = counts.vp / alerts.where(alerts.gt(0))
    counts["recall"] = counts.vp / positives.where(positives.gt(0))
    counts["f1"] = 2 * counts.vp / (alerts + positives).where((alerts + positives).gt(0))
    return counts


def main():
    inputs = PROJECT_ROOT / "data/interim/pm10_prediction"
    table = pd.read_csv(inputs / "tabla_modelos_completa.csv", dtype={"codigo_estacion": "string"},
                        parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    training, validation = split_dataset(table)
    protocol = json.loads((inputs / "protocolo.json").read_text(encoding="utf-8"))
    threshold = float(protocol["umbral_clasificacion"])
    for rows in (training, validation):
        if set(rows[LABEL].dropna().unique()) != {0, 1} or not rows[LABEL].eq(rows.pm10_objetivo.gt(threshold)).all():
            raise ValueError("Las etiquetas deben coincidir con el umbral de entrenamiento y contener ambas clases.")

    classifier = create_classifier().fit(training[FEATURES], training[LABEL].astype(int))
    probability = classifier.predict_positive_probability(validation[FEATURES])
    base = validation[["codigo_estacion", "NOMBRE", "fecha_objetivo", "fecha_ultima_observacion", "pm10_t", "pm10_objetivo"]].copy()
    base["observado"] = validation[LABEL].astype(int)
    today_high = base.pm10_t.gt(threshold)
    base["hoy_elevado"] = today_high
    base["contexto"] = np.where(today_high, "hoy_elevado", "hoy_no_elevado")
    predictions = pd.concat([
        base.assign(modelo="persistencia", aviso=today_high.astype(int), probabilidad_elevado=np.nan),
        base.assign(modelo="logistica", aviso=(probability >= PROBABILITY_THRESHOLD).astype(int), probabilidad_elevado=probability),
    ], ignore_index=True)
    overall = classification_metrics(predictions, ["modelo"])
    by_context = classification_metrics(predictions, ["contexto", "modelo"])
    by_station = classification_metrics(predictions, ["codigo_estacion", "NOMBRE", "modelo"])
    configuration = {
        "umbral_pm10_ug_m3": threshold, "regla_evento": "PM10 objetivo > umbral",
        "umbral_probabilidad_logistica": PROBABILITY_THRESHOLD, "regla_aviso_logistica": "probabilidad >= umbral",
        "regla_persistencia": "PM10 hoy > umbral", "ajuste_umbral_con_validacion": False,
        "parametros_logistica": classifier.get_parameters(), "variables": FEATURES, "sklearn": backend_version(),
        "periodo_entrenamiento_objetivo": "2017–2022", "periodo_validacion_objetivo": "2023",
        "filas_entrenamiento": len(training), "positivos_entrenamiento": int(training[LABEL].sum()),
        "filas_validacion": len(validation), "positivos_validacion": int(validation[LABEL].sum()),
        "prueba_2024_evaluada": False,
    }
    output = PROJECT_ROOT / "output/pm10_classification_validation"
    output.mkdir(parents=True, exist_ok=True)
    for name, result in [("predicciones_validacion_2023", predictions), ("metricas_validacion_2023", overall),
                         ("metricas_por_contexto", by_context), ("metricas_por_estacion", by_station)]:
        result.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    (output / "configuracion.json").write_text(json.dumps(configuration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    models = PROJECT_ROOT / "models/pm10/validation_2023"
    models.mkdir(parents=True, exist_ok=True)
    save_model({"pipeline": classifier, "configuracion": configuration, "modelo": "logistica"}, models / "logistica.joblib")
    print(overall.to_string(index=False))
    print(by_context.to_string(index=False))


if __name__ == "__main__":
    main()
