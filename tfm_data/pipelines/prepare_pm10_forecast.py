"""Prepara tabla supervisada y referencias de VALIDACIÓN; no evalúa 2024.

Ejecutar: python -m tfm_data.pipelines.prepare_pm10_forecast
"""

from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import json

import numpy as np
import pandas as pd

from tfm_data.mappers.pm10_forecast import PM10ForecastMapper, NUMERIC_FEATURES, label_elevated_pm10


def main():
    root = PROJECT_ROOT
    source = root / "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv"
    destination = root / "data/interim/pm10_prediction"
    original = pd.read_csv(source, parse_dates=["fecha"], dtype={"codigo_estacion": "string", "punto_muestreo": "string", "codigo_provincia": "string"})
    table = PM10ForecastMapper().transform(original)
    table, threshold = label_elevated_pm10(table)
    cobertura = table.groupby(["particion", "codigo_estacion", "NOMBRE"], as_index=False).agg(
        filas=("fecha_objetivo", "size"), objetivos_disponibles=("objetivo_disponible", "sum"),
        predictores_completos=("predictores_completos", "sum"), filas_utilizables=("fila_utilizable", "sum"))
    balance = table.loc[table.fila_utilizable & table.particion.isin(["entrenamiento", "validacion"])].groupby(
        ["particion", "codigo_estacion", "NOMBRE"], as_index=False).agg(
        n=("pm10_elevado_objetivo", "size"), positivos=("pm10_elevado_objetivo", "sum"))
    balance["proporcion_positivos"] = balance.positivos / balance.n
    validation = table.loc[table.fila_utilizable & table.particion.eq("validacion")].copy()
    if validation.empty:
        raise ValueError("No hay validación completa.")
    predictions = []
    for name, column in [("persistencia", "pm10_t"), ("media_movil_7d", "media_7_dias"), ("referencia_semanal", "pm10_t_menos_6")]:
        output = validation[["codigo_estacion", "NOMBRE", "fecha_ultima_observacion", "fecha_objetivo", "pm10_objetivo"]].copy()
        output["referencia"] = name
        output["prediccion"] = validation[column]
        output["error"] = output.prediccion - output.pm10_objetivo
        output["error_absoluto"] = output.error.abs()
        output["error_cuadrado"] = output.error ** 2
        predictions.append(output)
    predictions = pd.concat(predictions, ignore_index=True)
    metrics = predictions.groupby("referencia", as_index=False).agg(
        n=("error", "size"), mae=("error_absoluto", "mean"), mse=("error_cuadrado", "mean"), sesgo=("error", "mean"))
    metrics["rmse"] = np.sqrt(metrics.mse)
    by_station = predictions.groupby(["referencia", "codigo_estacion", "NOMBRE"], as_index=False).agg(
        n=("error", "size"), mae=("error_absoluto", "mean"), mse=("error_cuadrado", "mean"), sesgo=("error", "mean"))
    by_station["rmse"] = np.sqrt(by_station.mse)
    destination.mkdir(parents=True, exist_ok=True)
    # Las tablas conservan fechas ISO; no se reemplazan los valores ausentes.
    exportable = table.copy()
    exportable["emision_simulada_utc"] = exportable.emision_simulada_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for column in ["fecha", "fecha_ultima_observacion", "fecha_objetivo"]:
        exportable[column] = exportable[column].dt.strftime("%Y-%m-%d")
    exportable.to_csv(destination / "tabla_supervisada_pm10.csv", index=False, encoding="utf-8-sig")
    exportable.loc[table.fila_utilizable].to_csv(destination / "tabla_modelos_completa.csv", index=False, encoding="utf-8-sig")
    for name, df in [("cobertura_particiones", cobertura), ("balance_clasificacion_entrenamiento_validacion", balance),
                       ("referencias_validacion_2023", metrics), ("referencias_validacion_por_estacion", by_station),
                       ("predicciones_referencias_validacion", predictions)]:
        df.to_csv(destination / f"{name}.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    protocolo = {
        "objetivo": "PM10 medio del día siguiente", "unidad": "µg/m3",
        "variables_numericas": NUMERIC_FEATURES, "variable_categorica": "codigo_estacion",
        "entrenamiento": "2017-2022 según fecha objetivo", "validacion": "2023 según fecha objetivo", "prueba_reservada": "2024 según fecha objetivo",
        "umbral_clasificacion": threshold, "cuantil": .9, "interpolacion_cuantil": "linear", "comparacion": "objetivo > umbral",
        "origen_umbral": "Objetivos válidos de entrenamiento; no usa validación ni prueba.",
        "metricas_2024_calculadas": False,
        "advertencia": "Evaluación retrospectiva; emisión UTC simulada supone disponibilidad inmediata del dato del día anterior. Fuentes revisadas y estaciones elegidas por cobertura histórica; clasificación relativa, no sanitaria ni legal.",
    }
    (destination / "protocolo.json").write_text(json.dumps(protocolo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(cobertura.to_string(index=False))
    print(f"Umbral de clasificación (solo entrenamiento): {threshold:.4f} µg/m3")
    print(balance.to_string(index=False))
    print(metrics.to_string(index=False))
    print("Prueba de 2024 reservada: no se han calculado métricas.")


if __name__ == "__main__":
    main()
