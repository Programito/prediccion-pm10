"""Temporal split, regression evaluation and metrics, independent of sklearn."""

import numpy as np
import pandas as pd

from pm10_data.models.base import Regressor
from pm10_data.models.factory import FEATURES
from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES


def split_dataset(table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = set(FEATURES + ["particion", "fecha_objetivo", "fecha_ultima_observacion", "pm10_objetivo", "NOMBRE"])
    if not required.issubset(table.columns):
        raise ValueError("Faltan columnas de entrenamiento o auditoría.")
    if table.duplicated(["codigo_estacion", "fecha_objetivo"]).any():
        raise ValueError("Hay estación y fecha objetivo duplicadas.")
    training = table.loc[table.particion.eq("entrenamiento")].copy()
    validation = table.loc[table.particion.eq("validacion")].copy()
    if training.empty or validation.empty:
        raise ValueError("Falta entrenamiento o validación.")
    for df, inicio, fin in [(training, "2017-01-01", "2022-12-31"), (validation, "2023-01-01", "2023-12-31")]:
        if not df.fecha_objetivo.between(inicio, fin).all():
            raise ValueError("La partición no coincide con sus fechas objetivo.")
        if not (df.fecha_objetivo - df.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all():
            raise ValueError("El horizonte no es un día.")
        if df[FEATURES + ["pm10_objetivo"]].isna().any().any():
            raise ValueError("Hay valores ausentes en el conjunto completo.")
        if not np.isfinite(df[NUMERIC_FEATURES + ["pm10_objetivo"]].to_numpy(dtype=float)).all():
            raise ValueError("Hay valores numéricos no finitos.")
    if training.fecha_objetivo.max() >= validation.fecha_objetivo.min():
        raise ValueError("Las fechas de entrenamiento y validación se solapan.")
    if set(training.codigo_estacion) != set(validation.codigo_estacion):
        raise ValueError("Las estaciones de entrenamiento y validación no coinciden.")
    return training, validation


def evaluate_models(training: pd.DataFrame, validation: pd.DataFrame,
                    models: dict[str, Regressor]) -> pd.DataFrame:
    predictions = []
    for name, model in models.items():
        model.fit(training[FEATURES], training.pm10_objetivo)
        prediction = model.predict(validation[FEATURES])
        output = validation[["codigo_estacion", "NOMBRE", "fecha_ultima_observacion", "fecha_objetivo", "pm10_objetivo"]].copy()
        output["modelo"] = name
        output["prediccion_sin_restriccion"] = prediction
        # Restricción física fijada para todos los candidatos, antes de calcular errores.
        output["prediccion"] = np.maximum(0, prediction)
        output["prediccion_negativa_corregida"] = prediction < 0
        predictions.append(output)
    for name, field in [("persistencia", "pm10_t"), ("media_movil_7d", "media_7_dias"), ("referencia_semanal", "pm10_t_menos_6")]:
        output = validation[["codigo_estacion", "NOMBRE", "fecha_ultima_observacion", "fecha_objetivo", "pm10_objetivo"]].copy()
        output["modelo"] = name
        output["prediccion_sin_restriccion"] = validation[field]
        output["prediccion"] = validation[field].clip(lower=0)
        output["prediccion_negativa_corregida"] = validation[field].lt(0)
        predictions.append(output)
    result = pd.concat(predictions, ignore_index=True)
    result["error"] = result.prediccion - result.pm10_objetivo
    result["error_absoluto"] = result.error.abs()
    result["error_cuadrado"] = result.error ** 2
    return result


def calculate_metrics(predictions: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    result = predictions.groupby(groups, as_index=False).agg(
        n=("error", "size"), mae=("error_absoluto", "mean"), mse=("error_cuadrado", "mean"),
        sesgo=("error", "mean"), negativas_corregidas=("prediccion_negativa_corregida", "sum"))
    result["rmse"] = np.sqrt(result.mse)
    return result.drop(columns="mse")

