"""Audit missing values and high PM10 episodes through 2023."""

import json
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd

from pm10_data.adapters.sklearn.ridge import RidgeAdapter
from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.pm10_regression import calculate_metrics
from pm10_data.mappers.air import AirContext, AirQualityMapper, AirQualityReader, summarize_hours
from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES, PM10ForecastMapper, label_elevated_pm10
from pm10_data.pipelines.document_sources import file_hash


KEY = ["codigo_estacion", "fecha_objetivo"]
SHORT_FEATURES = [field for field in NUMERIC_FEATURES if field != "media_14_dias"]
DTYPES = {"codigo_estacion": "string", "punto_muestreo": "string"}


def audit_missing(table):
    table = table.assign(
        anio_objetivo=table.fecha_objetivo.dt.year,
        falta_objetivo=~table.objetivo_disponible,
        falta_predictores=~table.predictores_completos,
        predictores_7d=table[SHORT_FEATURES].notna().all(axis=1),
    )
    table["utilizable_7d"] = table.objetivo_disponible & table.predictores_7d
    table["solo_falta_objetivo"] = table.falta_objetivo & ~table.falta_predictores
    table["solo_faltan_predictores"] = ~table.falta_objetivo & table.falta_predictores
    table["faltan_ambos"] = table.falta_objetivo & table.falta_predictores
    table["recuperable_7d"] = table.utilizable_7d & ~table.fila_utilizable
    counts = table.groupby(["particion", "codigo_estacion", "NOMBRE", "anio_objetivo"], as_index=False).agg(
        filas=("fecha_objetivo", "size"), falta_objetivo=("falta_objetivo", "sum"),
        faltan_predictores=("falta_predictores", "sum"), solo_falta_objetivo=("solo_falta_objetivo", "sum"),
        solo_faltan_predictores=("solo_faltan_predictores", "sum"), faltan_ambos=("faltan_ambos", "sum"),
        utilizables_14d=("fila_utilizable", "sum"), utilizables_7d=("utilizable_7d", "sum"),
        recuperables_7d=("recuperable_7d", "sum"),
    )
    return table, counts


def compare_windows(table, previous):
    short = table.loc[table.utilizable_7d]
    train = short.loc[short.particion.eq("entrenamiento")]
    validation = short.loc[short.particion.eq("validacion")].copy()
    model = RidgeAdapter(SHORT_FEATURES, ["codigo_estacion"])
    features = SHORT_FEATURES + ["codigo_estacion"]
    model.fit(train[features], train.pm10_objetivo)
    validation["ridge_7d"] = np.maximum(0, model.predict(validation[features]))
    validation["persistencia"] = validation.pm10_t
    full = previous.loc[previous.modelo.eq("ridge"), KEY + ["prediccion", "pm10_objetivo"]].rename(
        columns={"prediccion": "ridge_14d", "pm10_objetivo": "objetivo_publicado"})
    validation = validation.merge(full, on=KEY, how="left", validate="one_to_one")
    common = validation.loc[validation.fila_utilizable]
    if (len(common) != len(full) or not validation.ridge_14d.notna().eq(validation.fila_utilizable).all()
            or not np.allclose(common.pm10_objetivo, common.objetivo_publicado, rtol=0, atol=1e-10)):
        raise ValueError("Las fechas o valores objetivo del modelo de referencia y de la tabla no coinciden.")
    samples = [
        ("fechas_comunes", common, ["ridge_14d", "ridge_7d", "persistencia"]),
        ("cobertura_7d", validation, ["ridge_7d", "persistencia"]),
        ("solo_recuperadas_7d", validation.loc[~validation.fila_utilizable], ["ridge_7d", "persistencia"]),
    ]
    results = []
    train_counts = {"ridge_7d": len(train), "ridge_14d": int(train.fila_utilizable.sum())}
    for sample, rows, models in samples:
        for name in models:
            if rows.empty:
                continue
            error = rows[name] - rows.pm10_objetivo
            results.append(dict(muestra=sample, modelo=name, filas_entrenamiento=train_counts.get(name),
                                n=len(error), mae=error.abs().mean(), rmse=np.sqrt(error.pow(2).mean()), sesgo=error.mean()))
    return pd.DataFrame(results), validation[KEY + ["pm10_objetivo", "ridge_14d", "ridge_7d", "persistencia", "fila_utilizable"]]


def inspect_peaks(daily, raw):
    series = daily.sort_values(["punto_muestreo", "fecha"]).copy()
    groups = series.groupby("punto_muestreo")
    series["pm10_dia_anterior"] = groups.pm10_valido.shift(1)
    series["pm10_dia_siguiente"] = groups.pm10_valido.shift(-1)
    series["periodo"] = np.where(series.fecha.dt.year.eq(2023), "validacion", "entrenamiento")
    peaks = (series.dropna(subset=["pm10_valido"])
             .sort_values(["pm10_valido", "fecha"], ascending=[False, True])
             .groupby(["codigo_estacion", "periodo"]).head(3).copy())
    peaks["anio"] = peaks.fecha.dt.year

    manifest = json.loads((raw / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    hourly_summaries = []
    for year, rows in peaks.groupby("anio"):
        source = next(s for s in manifest if s["year"] == year and s["kind"] == "miteco_horarios" and s["status"] == "downloaded")
        path = raw / source["file"]
        if file_hash(path) != source["sha256"]:
            raise ValueError(f"Original alterado: {path.name}")
        with zipfile.ZipFile(path) as archive:
            member, = [name for name in archive.namelist() if Path(name).name.startswith("PM10_") and name.endswith(".csv")]
        original = AirQualityReader().read(path, member)
        original = original.loc[original.PUNTO_MUESTREO.isin(rows.punto_muestreo)]
        dates = pd.to_datetime(dict(year=original.ANNO.astype(int), month=original.MES.astype(int), day=original.DIA.astype(int)))
        links = pd.MultiIndex.from_arrays([original.PUNTO_MUESTREO, dates])
        wanted = pd.MultiIndex.from_frame(rows[["punto_muestreo", "fecha"]])
        original = original.loc[links.isin(wanted)]
        if original.empty:
            continue
        context = AirContext(int(year), "10", "PM10", "µg/m3", path.name, member)
        hourly = AirQualityMapper().transform(original, context, "horaria")
        summaries = summarize_hours(hourly)
        hourly_summaries.append(summaries[["punto_muestreo", "fecha", "n_horas_validas", "media_horas_disponibles",
                                          "concentracion", "archivo_origen"]].rename(columns={
                                              "n_horas_validas": "horas_validas_contraste", "concentracion": "pm10_derivado",
                                              "archivo_origen": "archivo_horario"}))
    fields = ["codigo_estacion", "NOMBRE", "punto_muestreo", "fecha", "periodo", "pm10_valido",
              "pm10_dia_anterior", "pm10_dia_siguiente", "origen_diario", "archivo_origen"]
    result = peaks[fields]
    if hourly_summaries:
        result = result.merge(pd.concat(hourly_summaries), on=["punto_muestreo", "fecha"], how="left", validate="one_to_one")
        result["diferencia_con_derivado"] = (result.pm10_valido - result.pm10_derivado).abs()
    return result.sort_values(["codigo_estacion", "periodo", "pm10_valido"], ascending=[True, True, False])


def main():
    root = PROJECT_ROOT
    daily = pd.read_csv(root / "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv", dtype=DTYPES, parse_dates=["fecha"])
    daily = daily.loc[daily.fecha.lt("2024-01-01")].copy()
    forecast, threshold = label_elevated_pm10(PM10ForecastMapper().transform(daily))
    forecast = forecast.loc[forecast.fecha_objetivo.lt("2024-01-01")]
    forecast, missing = audit_missing(forecast)
    previous = pd.read_csv(root / "output/pm10_regression_validation/predicciones_validacion_2023.csv",
                           dtype=DTYPES, parse_dates=["fecha_objetivo"])
    if not previous.fecha_objetivo.dt.year.eq(2023).all():
        raise ValueError("Se esperaban únicamente predicciones de validación de 2023.")
    comparison, predictions = compare_windows(forecast, previous)
    peaks = inspect_peaks(daily, root / "data/raw/health_air_history")

    errors = previous.loc[previous.modelo.isin(["ridge", "persistencia"])].copy()
    errors["tramo"] = np.where(errors.pm10_objetivo.gt(threshold), "elevado", "resto")
    peak_metrics = calculate_metrics(errors, ["tramo", "modelo"])
    peak_metrics_by_station = calculate_metrics(errors, ["tramo", "modelo", "codigo_estacion", "NOMBRE"])
    out = root / "output/pm10_quality_audit"
    out.mkdir(parents=True, exist_ok=True)
    for name, table in [("huecos_por_estacion_anio", missing), ("comparacion_ventanas", comparison),
                        ("predicciones_ventanas_2023", predictions), ("revision_picos", peaks),
                        ("metricas_por_tramo_pm10", peak_metrics), ("metricas_por_tramo_y_estacion", peak_metrics_by_station)]:
        table.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    print(f"Umbral de entrenamiento: {threshold:g} µg/m³. Picos examinados: {len(peaks)}.")
    print(missing.groupby("particion").sum(numeric_only=True).drop(columns="anio_objetivo").to_string())
    print(comparison.to_string(index=False))
    print(peak_metrics.to_string(index=False))


if __name__ == "__main__":
    main()
