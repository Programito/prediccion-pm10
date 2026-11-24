"""Compare alert thresholds using saved PM10 predictions for 2023."""

import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT


def main():
    folder = PROJECT_ROOT / "output/pm10_classification_validation"
    predictions = pd.read_csv(folder / "predicciones_validacion_2023.csv", parse_dates=["fecha_objetivo"])
    if not predictions.fecha_objetivo.dt.year.eq(2023).all():
        raise ValueError("El análisis requiere exclusivamente predicciones de 2023.")
    logistic = predictions.loc[predictions.modelo.eq("logistica")]
    baseline = predictions.loc[predictions.modelo.eq("persistencia")]
    keys = ["codigo_estacion", "fecha_objetivo"]
    paired = logistic.merge(baseline[keys + ["observado", "aviso"]], on=keys, validate="one_to_one", suffixes=("", "_base"))
    if len(paired) != len(logistic) or len(paired) != len(baseline) or not paired.observado.eq(paired.observado_base).all():
        raise ValueError("Ambos métodos deben cubrir las mismas observaciones.")
    score = paired.probabilidad_elevado
    if not score.between(0, 1).all():
        raise ValueError("Se requieren probabilidades completas entre 0 y 1.")
    positive = paired.observado.eq(1)
    onset_context = ~paired.hoy_elevado
    total_positive = int(positive.sum())
    total_onsets = int((positive & onset_context).sum())

    def metrics(model, threshold, alert):
        tp = int((alert & positive).sum())
        fp = int((alert & ~positive).sum())
        onsets = int((alert & positive & onset_context).sum())
        fp_onsets = int((alert & ~positive & onset_context).sum())
        return {
            "modelo": model, "umbral_probabilidad": threshold, "avisos": tp + fp,
            "positivos_totales": total_positive, "positivos_detectados": tp, "falsas_alarmas": fp,
            "precision": tp / (tp + fp) if tp + fp else np.nan,
            "recall": tp / total_positive, "f1": 2 * tp / (tp + fp + total_positive),
            "comienzos_totales": total_onsets, "comienzos_detectados": onsets,
            "falsas_alarmas_con_hoy_no_elevado": fp_onsets,
        }

    reference = metrics("persistencia", np.nan, paired.aviso_base.eq(1))
    grid = [0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10, 0.05]
    thresholds = sorted(set(grid).union(score), reverse=True)
    sweep = pd.DataFrame(metrics("logistica", threshold, score.ge(threshold)) for threshold in thresholds)
    comparable = sweep.loc[sweep.falsas_alarmas.le(reference["falsas_alarmas"])]
    candidate = comparable.sort_values(
        ["comienzos_detectados", "positivos_detectados", "falsas_alarmas", "umbral_probabilidad"],
        ascending=[False, False, True, False],
    ).iloc[0].to_dict()
    summary = pd.concat([
        pd.DataFrame([reference], index=["persistencia"]),
        sweep.loc[sweep.umbral_probabilidad.isin(grid)].set_axis([f"umbral_{value:.2f}" for value in grid]),
        pd.DataFrame([candidate], index=["candidato_con_limite_de_falsas_alarmas"]),
    ]).rename_axis("comparacion")
    sweep.to_csv(folder / "barrido_umbrales_2023.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(folder / "comparacion_umbrales_2023.csv", encoding="utf-8-sig")
    print(summary[["umbral_probabilidad", "positivos_detectados", "falsas_alarmas", "comienzos_detectados",
                   "falsas_alarmas_con_hoy_no_elevado"]].to_string())


if __name__ == "__main__":
    main()
