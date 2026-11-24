"""Paired descriptive error analysis of saved PM10 regression predictions."""

import numpy as np
import pandas as pd


KEYS = ["codigo_estacion", "fecha_objetivo"]


def pair_predictions(predictions):
    if set(predictions.modelo) != {"ridge", "persistencia"}:
        raise ValueError("Se requieren Ridge y persistencia.")
    if predictions.duplicated(KEYS + ["modelo"]).any():
        raise ValueError("Hay predicciones repetidas.")
    numeric = ["pm10_objetivo", "prediccion"]
    if not np.isfinite(predictions[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Hay observaciones o predicciones no finitas.")
    if predictions[numeric].lt(0).any().any():
        raise ValueError("Las concentraciones deben ser no negativas.")
    ridge = predictions.loc[predictions.modelo.eq("ridge"), KEYS + ["NOMBRE", *numeric]]
    baseline = predictions.loc[predictions.modelo.eq("persistencia"), KEYS + ["NOMBRE", *numeric]]
    paired = ridge.merge(baseline, on=KEYS, how="outer", validate="one_to_one",
                         indicator=True, suffixes=("_ridge", "_persistencia"))
    if (not paired._merge.eq("both").all()
            or not paired.pm10_objetivo_ridge.eq(paired.pm10_objetivo_persistencia).all()
            or not paired.NOMBRE_ridge.eq(paired.NOMBRE_persistencia).all()):
        raise ValueError("Los modelos deben compartir fechas, estaciones y observaciones.")
    paired = paired.rename(columns={"pm10_objetivo_ridge": "observado", "NOMBRE_ridge": "nombre"})
    paired["fecha_objetivo"] = pd.to_datetime(paired.fecha_objetivo, errors="raise")
    if not paired.fecha_objetivo.dt.year.eq(2024).all():
        raise ValueError("Esta auditoría describe la prueba de 2024.")
    for model in ("ridge", "persistencia"):
        paired[f"error_{model}"] = paired[f"prediccion_{model}"] - paired.observado
        paired[f"ae_{model}"] = paired[f"error_{model}"].abs()
    paired["ganancia_absoluta_ridge"] = paired.ae_persistencia - paired.ae_ridge
    return paired.sort_values(KEYS).reset_index(drop=True)


def summarize(paired):
    if paired.empty:
        raise ValueError("La muestra está vacía.")
    result = {"n": len(paired)}
    for model in ("ridge", "persistencia"):
        result[f"mae_{model}"] = float(paired[f"ae_{model}"].mean())
        result[f"rmse_{model}"] = float(np.sqrt(paired[f"error_{model}"].pow(2).mean()))
        result[f"sesgo_{model}"] = float(paired[f"error_{model}"].mean())
    result["delta_mae"] = result["mae_ridge"] - result["mae_persistencia"]
    return result


def grouped_errors(paired, threshold):
    rows = []
    stations = [("todas", "Todas las estaciones", paired)]
    stations += [(str(code), group.nombre.iloc[0], group) for code, group in paired.groupby("codigo_estacion")]
    for station, name, data in stations:
        for month in range(13):
            period = data if month == 0 else data.loc[data.fecha_objetivo.dt.month.eq(month)]
            for level in ("todos", "resto", "elevado"):
                subset = period
                if level == "resto":
                    subset = period.loc[period.observado.le(threshold)]
                if level == "elevado":
                    subset = period.loc[period.observado.gt(threshold)]
                if not subset.empty:
                    rows.append({"station": station, "name": name, "month": month, "level": level, **summarize(subset)})
    return pd.DataFrame(rows)


def date_sensitivity(paired, count=5):
    if count < 1:
        raise ValueError("El número de fechas debe ser positivo.")
    daily = paired.groupby("fecha_objetivo", as_index=False).agg(
        n=("observado", "size"), ganancia_absoluta_ridge=("ganancia_absoluta_ridge", "sum"))
    rows = [{"scenario": "muestra_completa", "excluded_dates": "", **summarize(paired)}]
    for scenario, favorable in (("sin_fechas_mas_favorables", True), ("sin_fechas_mas_desfavorables", False)):
        # Stable date order makes tied gains reproducible.
        selected = daily.sort_values("ganancia_absoluta_ridge", ascending=not favorable, kind="stable").head(count)
        remaining = paired.loc[~paired.fecha_objetivo.isin(selected.fecha_objetivo)]
        rows.append({
            "scenario": scenario,
            "excluded_dates": "|".join(selected.fecha_objetivo.dt.strftime("%Y-%m-%d")),
            **summarize(remaining),
        })
    return daily, pd.DataFrame(rows)
