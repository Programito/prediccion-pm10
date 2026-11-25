"""Cohorts for a 2023-only feature and training-availability ablation."""

import numpy as np
import pandas as pd

from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES

REDUCED_FEATURES = [field for field in NUMERIC_FEATURES if field != "media_14_dias"]
KEYS = ["codigo_estacion", "fecha_objetivo"]


def make_window_cohorts(original):
    table = original.copy()
    table["fecha_objetivo"] = pd.to_datetime(table.fecha_objetivo)
    table = table.loc[table.fecha_objetivo.between("2017-01-01", "2023-12-31")].copy()
    table["fecha_ultima_observacion"] = pd.to_datetime(table.fecha_ultima_observacion)
    if table.empty or table.duplicated(KEYS).any():
        raise ValueError("Se requieren claves únicas hasta 2023.")
    if not (table.fecha_objetivo - table.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all():
        raise ValueError("El horizonte debe ser un día.")
    training = table.fecha_objetivo.dt.year.le(2022)
    validation = table.fecha_objetivo.dt.year.eq(2023)
    if not table.loc[training, "particion"].eq("entrenamiento").all() or not table.loc[validation, "particion"].eq("validacion").all():
        raise ValueError("Las particiones no coinciden con las fechas objetivo.")
    present = table.pm10_objetivo.notna() & table.codigo_estacion.notna()
    full = present & table[NUMERIC_FEATURES].notna().all(axis=1)
    reduced = present & table[REDUCED_FEATURES].notna().all(axis=1)
    if not full.eq(table.fila_utilizable).all():
        raise ValueError("La cohorte original difiere de la tabla supervisada.")
    if not np.isfinite(table.loc[full, NUMERIC_FEATURES + ["pm10_objetivo"]].to_numpy(dtype=float)).all():
        raise ValueError("Hay valores no finitos en la cohorte original.")
    candidates = table.loc[reduced, REDUCED_FEATURES + ["pm10_objetivo"]]
    if not np.isfinite(candidates.to_numpy(dtype=float)).all():
        raise ValueError("Hay valores no finitos en las entradas de la variante.")
    result = dict(train_common=table.loc[training & full].copy(), train_expanded=table.loc[training & reduced].copy(),
                  validation_common=table.loc[validation & full].copy(), validation_additional=table.loc[validation & reduced & ~full].copy(),
                  validation_expanded=table.loc[validation & reduced].copy())
    if any(result[key].empty for key in ["train_common", "train_expanded", "validation_common", "validation_expanded"]):
        raise ValueError("Falta una cohorte necesaria de entrenamiento o validación.")
    stations = set(result["train_common"].codigo_estacion)
    if any(set(result[key].codigo_estacion) != stations for key in ["train_expanded", "validation_common", "validation_expanded"]):
        raise ValueError("Las cohortes deben conservar las estaciones del experimento.")
    result["calendar_validation"] = table.loc[validation].copy()
    return result


def score_prediction_cases(data, prediction, model):
    if len(data) != len(prediction) or not np.isfinite(prediction).all():
        raise ValueError("Predicciones incompatibles o no finitas.")
    result = data[["codigo_estacion", "NOMBRE", "fecha_objetivo", "fecha_ultima_observacion", "pm10_objetivo", "pm10_t"]].copy()
    result["modelo"] = model
    result["prediccion_negativa_corregida"] = np.asarray(prediction) < 0
    result["prediccion"] = np.maximum(prediction, 0)
    result["error"] = result.prediccion - result.pm10_objetivo
    result["error_absoluto"] = result.error.abs()
    result["error_cuadrado"] = result.error.pow(2)
    return result
