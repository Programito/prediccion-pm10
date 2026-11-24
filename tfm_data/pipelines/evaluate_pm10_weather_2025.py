"""Verify EEA PM10 against MITECO in 2024, then evaluate fixed models in 2025."""

from datetime import datetime
import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT
from tfm_data.mappers.air import AirContext, AirQualityMapper, AirQualityReader
from tfm_data.mappers.pm10_forecast import PM10ForecastMapper
from tfm_data.pipelines.train_pm10_classification import classification_metrics


KEY = ["codigo_estacion", "fecha_objetivo"]
WEATHER_FEATURES = ["viento_10m_mediodia_ms", "precipitacion_diaria_mm"]
UTC_OFFSET = pd.Timedelta(hours=1)


def checked_path(path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError(f"El archivo no coincide con su huella registrada: {path.name}")
    return path


def read_eea_hours(folder, stations, year):
    manifest = json.loads((folder / "sources.json").read_text(encoding="utf-8"))["sources"]
    lower = datetime(year, 1, 1, 1)
    upper = datetime(year + 1, 1, 1, 1)
    hours = []
    for station in stations.itertuples(index=False):
        point = station.punto_muestreo
        source = manifest[point]
        path = checked_path(folder / source["file"], source["sha256"])
        raw = pd.read_parquet(path, engine="pyarrow", filters=[("Start", ">=", lower), ("Start", "<", upper)])
        if (raw.empty or not raw.Samplingpoint.eq(f"ES/SP_{point}").all()
                or not raw.Pollutant.eq(5).all() or not raw.Unit.eq("ug.m-3").all()
                or not raw.AggType.eq("hour").all()
                or not (raw.End - raw.Start).eq(pd.Timedelta(hours=1)).all()
                or not raw.Start.eq(raw.Start.dt.floor("h")).all()):
            raise ValueError(f"Serie horaria EEA incompatible en {point}, {year}.")
        concentration = pd.to_numeric(raw.Value, errors="raise").astype(float)
        accepted = raw.Verification.eq(1) & raw.Validity.isin([1, 2, 3])
        usable = accepted & np.isfinite(concentration) & concentration.ge(0)
        utc_start = (raw.Start - UTC_OFFSET).dt.tz_localize("UTC")
        utc_end = (raw.End - UTC_OFFSET).dt.tz_localize("UTC")
        if utc_end.duplicated().any():
            raise ValueError(f"Intervalos horarios repetidos para {point}.")
        hours.append(pd.DataFrame({"punto_muestreo": point, "codigo_estacion": station.codigo_estacion,
                                   "fin_periodo_utc": utc_end, "fecha": utc_start.dt.tz_localize(None).dt.normalize(),
                                   "pm10_horario": concentration.where(usable)}))
    return pd.concat(hours, ignore_index=True)


def check_overlap(root, eea, stations):
    raw = root / "data/raw/health_air_history/miteco_horarios_2024.zip"
    member = "PM10_HH_2024.csv"
    original = AirQualityReader().read(raw, member)
    original = original.loc[original.PUNTO_MUESTREO.isin(stations.punto_muestreo)]
    national = AirQualityMapper().transform(original, AirContext(2024, "10", "PM10", "µg/m3", raw.name, member), "horaria")
    keys = ["punto_muestreo", "fin_periodo_utc"]
    valid_national = national.loc[national.estado.eq("valida"), keys + ["concentracion"]]
    valid_eea = eea.loc[eea.pm10_horario.notna(), keys + ["pm10_horario"]]
    comparison = valid_national.merge(valid_eea, on=keys, how="outer", validate="one_to_one", indicator=True)
    if not comparison._merge.eq("both").all() or not comparison.concentracion.eq(comparison.pm10_horario).all():
        raise ValueError("Las horas válidas EEA y MITECO no coinciden exactamente en 2024.")
    return comparison.groupby("punto_muestreo", as_index=False).agg(horas_validas_iguales=("fin_periodo_utc", "size"))


def build_test(root, hours, stations):
    daily = hours.groupby(["codigo_estacion", "fecha"], as_index=False).agg(
        horas_validas=("pm10_horario", "count"), pm10_valido=("pm10_horario", "mean"),
    )
    daily["pm10_valido"] = daily.pm10_valido.where(daily.horas_validas.ge(18))
    calendar = stations[["codigo_estacion", "punto_muestreo", "NOMBRE"]].merge(
        pd.DataFrame({"fecha": pd.date_range("2025-01-01", "2025-12-31")}), how="cross")
    daily = calendar.merge(daily, on=["codigo_estacion", "fecha"], how="left", validate="one_to_one")
    daily["horas_validas"] = daily.horas_validas.fillna(0).astype(int)
    history = pd.read_csv(root / "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv",
                          usecols=["codigo_estacion", "fecha", "pm10_valido"], parse_dates=["fecha"],
                          dtype={"codigo_estacion": "string"})
    previous_days = history.loc[history.fecha.between("2024-12-18", "2024-12-31")].merge(
        stations[["codigo_estacion", "punto_muestreo", "NOMBRE"]], on="codigo_estacion", validate="many_to_one")
    forecast = PM10ForecastMapper().transform(pd.concat([previous_days, daily], ignore_index=True))
    return daily, forecast.loc[forecast.fecha_objetivo.dt.year.eq(2025)].copy()


def main():
    root = PROJECT_ROOT
    protocol_path = root / "docs/reference/pm10_weather_test_2025.json"
    protocol_bytes = protocol_path.read_bytes()
    protocol = json.loads(protocol_bytes)
    bundle = joblib.load(checked_path(root / protocol["modelo_archivo"], protocol["modelo_sha256"]))
    config = bundle["configuracion"]
    if (config["cortes_probabilidad"] != protocol["cortes"] or config["entrenamiento"] != protocol["entrenamiento"]
            or config["validacion_y_seleccion_umbral"] != protocol["seleccion_de_cortes"]
            or config["umbral_pm10_ug_m3"] != protocol["umbral_pm10_ug_m3"]):
        raise ValueError("El modelo no corresponde al protocolo fijado.")
    stations = pd.read_csv(root / "data/interim/daily_pollution/estaciones_muestra_madrid.csv",
                           dtype={"codigo_estacion": "string"})
    eea = root / "data/raw/eea_pm10"
    overlap = check_overlap(root, read_eea_hours(eea, stations, 2024), stations)
    year = protocol["anio_objetivo"]
    daily, test = build_test(root, read_eea_hours(eea, stations, year), stations)
    weather_path = root / "data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv"
    weather = pd.read_csv(checked_path(weather_path, protocol["gfs_sha256"]), parse_dates=["fecha_objetivo"],
                          dtype={"codigo_estacion": "string"})
    weather = weather.loc[weather.fecha_objetivo.dt.year.eq(year), KEY + ["inicio_ciclo_utc", *WEATHER_FEATURES]]
    test = test.merge(weather, on=KEY, how="left", validate="one_to_one")
    lead = test.emision_simulada_utc - pd.to_datetime(test.inicio_ciclo_utc, utc=True)
    if len(test) != len(daily) or not lead.eq(pd.Timedelta(hours=12)).all():
        raise ValueError("Calendario de prueba o ciclos meteorológicos incompletos.")
    test["utilizable"] = test.objetivo_disponible & test.predictores_completos & test[WEATHER_FEATURES].notna().all(axis=1)
    coverage = test.groupby(["codigo_estacion", "NOMBRE"], as_index=False).agg(
        dias_calendario=("fecha_objetivo", "size"), objetivos_disponibles=("objetivo_disponible", "sum"),
        predictores_pm10_completos=("predictores_completos", "sum"), filas_evaluadas=("utilizable", "sum"),
    )
    sample = test.loc[test.utilizable]
    if set(sample.codigo_estacion) != set(stations.codigo_estacion):
        raise ValueError("Se necesitan filas completas en las tres estaciones.")
    threshold = protocol["umbral_pm10_ug_m3"]
    base = sample[KEY + ["NOMBRE", "pm10_t", "pm10_objetivo"]].copy()
    today_high = base.pm10_t.gt(threshold)
    base["observado"] = base.pm10_objetivo.gt(threshold).astype(int)
    base["contexto"] = np.where(today_high, "hoy_elevado", "hoy_no_elevado")
    predictions = [base.assign(modelo="persistencia", aviso=today_high.astype(int), probabilidad_elevado=np.nan)]
    for name, model in bundle["modelos"].items():
        features = config["predictores"][name]
        probabilities = model.predict_positive_probability(sample[features])
        if not pd.Series(probabilities).between(0, 1).all():
            raise ValueError(f"Probabilidades inválidas en {name}.")
        predictions.append(base.assign(modelo=name, aviso=(probabilities >= protocol["cortes"][name]).astype(int),
                                       probabilidad_elevado=probabilities))
    predictions = pd.concat(predictions, ignore_index=True)
    overall = classification_metrics(predictions, ["modelo"])
    context = classification_metrics(predictions, ["contexto", "modelo"])
    by_station = classification_metrics(predictions, ["codigo_estacion", "NOMBRE", "modelo"])
    out = root / "output/pm10_weather_test_2025"
    out.mkdir(parents=True, exist_ok=True)
    for name, table in [("contraste_horario_2024", overlap), ("pm10_diario_2025", daily), ("cobertura_2025", coverage),
                        ("predicciones_2025", predictions), ("metricas_2025", overall), ("metricas_por_contexto", context),
                        ("metricas_por_estacion", by_station)]:
        table.to_csv(out / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    (out / "ejecucion.json").write_text(json.dumps({"sha256_protocolo": hashlib.sha256(protocol_bytes).hexdigest(),
                                                   "filas_evaluadas": len(sample), "reajuste": False}, indent=2) + "\n", encoding="utf-8")
    for table in (overlap, coverage, overall, context):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
