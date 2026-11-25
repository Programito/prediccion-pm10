"""Deterministic selection and checks for retrospective defense examples."""

import math


def select_typical(paired, threshold=27):
    """Choose a central non-elevated target, never conditioning on prediction error."""
    candidates = paired.loc[paired.observado.le(threshold)].copy()
    if candidates.empty:
        raise ValueError("No hay casos no elevados.")
    median = float(candidates.observado.median())
    candidates["distance"] = (candidates.observado - median).abs()
    selected = candidates.sort_values(["distance", "codigo_estacion", "fecha_objetivo"]).iloc[0]
    return selected, {"candidates": len(candidates), "median": median,
                      "rule": "PM10 observado ≤ 27; menor distancia a la mediana; desempate por estación y fecha. No se usa el error."}


def validate_alerts(rows, cuts, threshold=27):
    expected = {"persistencia", "logistica_sin_meteo", "logistica_con_meteo"}
    if len(rows) != 3 or set(rows.modelo) != expected:
        raise ValueError("Se requieren tres decisiones únicas.")
    for column in ("pm10_t", "pm10_objetivo", "observado", "codigo_estacion", "fecha_objetivo"):
        if rows[column].nunique(dropna=False) != 1:
            raise ValueError("Las decisiones no comparten caso y observación.")
    for row in rows.itertuples():
        if not all(math.isfinite(value) and value >= 0 for value in (row.pm10_t, row.pm10_objetivo)):
            raise ValueError("Concentración inválida.")
        if row.observado != int(row.pm10_objetivo > threshold):
            raise ValueError("Etiqueta incompatible con el umbral.")
        if row.modelo == "persistencia":
            decision = int(row.pm10_t > threshold)
        else:
            probability = row.probabilidad_elevado
            cut = cuts[row.modelo]
            if not (math.isfinite(probability) and 0 <= probability <= 1 and 0 <= cut <= 1):
                raise ValueError("Probabilidad o corte inválido.")
            decision = int(probability >= cut)
        if row.aviso != decision:
            raise ValueError("El aviso no coincide con su regla congelada.")


def reconstruct(intercept, contributions, prediction):
    raw = intercept + sum(contributions)
    if not math.isfinite(raw) or not math.isclose(max(0, raw), prediction, abs_tol=1e-9, rel_tol=1e-12):
        raise ValueError("Las aportaciones no reconstruyen la predicción guardada.")
    return raw
