"""Join archived GFS predictors to the 2021–2024 supervised PM10 calendar."""

import json

import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT
from tfm_data.mappers.pm10_forecast import NUMERIC_FEATURES


KEY = ["codigo_estacion", "fecha_objetivo"]
WEATHER_FEATURES = ["viento_10m_mediodia_ms", "precipitacion_diaria_mm"]
STATIONS = ["28079060", "28080003", "28133002"]
START, END = "2021-01-01", "2024-12-31"


def join_weather(pm10, weather, threshold):
    pm10 = pm10.loc[pm10.fecha_objetivo.between(START, END)].copy()
    weather = weather.loc[weather.fecha_objetivo.between(START, END)].copy()
    expected = pd.MultiIndex.from_product([STATIONS, pd.date_range(START, END)], names=KEY)
    pm10_keys = pd.MultiIndex.from_frame(pm10[KEY])
    weather_keys = pd.MultiIndex.from_frame(weather[KEY])
    if pm10_keys.has_duplicates or not expected.difference(pm10_keys).empty or not pm10_keys.difference(expected).empty:
        raise ValueError("El calendario de PM10 debe tener una fila por fecha y estación.")
    if weather_keys.has_duplicates or not weather_keys.difference(expected).empty:
        raise ValueError("La tabla GFS tiene claves duplicadas o ajenas al calendario.")

    target_utc = pm10.fecha_objetivo.dt.tz_localize("UTC")
    if (not pm10.emision_simulada_utc.eq(target_utc).all()
            or not (pm10.fecha_objetivo - pm10.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all()):
        raise ValueError("Las fechas de PM10 deben corresponder a un pronóstico diario de t+1.")
    expected_cycle = weather.fecha_objetivo.dt.tz_localize("UTC") - pd.Timedelta(hours=12)
    if not weather.inicio_ciclo_utc.eq(expected_cycle).all():
        raise ValueError("El ciclo GFS debe empezar a las 12 UTC del día anterior.")
    for feature, status, accepted in [
        (WEATHER_FEATURES[0], "estado_viento", {"valido"}),
        (WEATHER_FEATURES[1], "estado_precipitacion", {"valido", "ajuste_tolerancia"}),
    ]:
        values = weather[feature].dropna()
        if (not np.isfinite(values).all() or values.lt(0).any()
                or not weather[feature].notna().eq(weather[status].isin(accepted)).all()):
            raise ValueError(f"Valores o estados de calidad incoherentes en {feature}.")

    joined = pm10.merge(weather, on=KEY, how="left", validate="one_to_one", indicator=True)
    joined["fila_gfs_presente"] = joined.pop("_merge").eq("both")
    joined["predictores_meteo_completos"] = joined[WEATHER_FEATURES].notna().all(axis=1)
    joined["fila_comun_utilizable"] = joined.fila_utilizable & joined.predictores_meteo_completos
    joined["anio_objetivo"] = joined.fecha_objetivo.dt.year
    joined["particion_meteo"] = joined.anio_objetivo.map({2021: "entrenamiento", 2022: "entrenamiento",
                                                        2023: "validacion", 2024: "diagnostico"})
    elevated = joined.pm10_objetivo.gt(threshold)
    has_target = joined.pm10_objetivo.notna()
    has_today_and_target = joined.pm10_t.notna() & has_target
    if (not joined.pm10_elevado_objetivo.notna().eq(has_target).all()
            or not joined.loc[has_target, "pm10_elevado_objetivo"].eq(elevated[has_target]).all()):
        raise ValueError("La etiqueta de PM10 elevado debe coincidir con el protocolo original.")
    joined["comienzo_pm10_elevado"] = (elevated & joined.pm10_t.le(threshold)).astype("boolean").where(has_today_and_target)
    return joined.sort_values(KEY).reset_index(drop=True)


def summarize_coverage(table, keys):
    available = table.assign(
        perdida_por_meteo=table.fila_utilizable & ~table.predictores_meteo_completos,
        elevados_en_base=table.fila_utilizable & table.pm10_elevado_objetivo.eq(1).fillna(False),
        elevados_en_comun=table.fila_comun_utilizable & table.pm10_elevado_objetivo.eq(1).fillna(False),
        comienzos_en_base=table.fila_utilizable & table.comienzo_pm10_elevado.fillna(False),
        comienzos_en_comun=table.fila_comun_utilizable & table.comienzo_pm10_elevado.fillna(False),
    )
    coverage = available.groupby(keys, as_index=False).agg(
        filas_calendario=("fecha_objetivo", "size"), filas_gfs_presentes=("fila_gfs_presente", "sum"),
        filas_meteo_completas=("predictores_meteo_completos", "sum"), filas_pm10_utilizables=("fila_utilizable", "sum"),
        filas_comunes=("fila_comun_utilizable", "sum"), perdidas_por_meteo=("perdida_por_meteo", "sum"),
        episodios_elevados_base=("elevados_en_base", "sum"), episodios_elevados_comunes=("elevados_en_comun", "sum"),
        comienzos_base=("comienzos_en_base", "sum"), comienzos_comunes=("comienzos_en_comun", "sum"),
    )
    coverage["proporcion_comun"] = coverage.filas_comunes / coverage.filas_calendario
    return coverage


def main():
    pm10_folder = PROJECT_ROOT / "data/interim/pm10_prediction"
    weather_folder = PROJECT_ROOT / "data/interim/weather_forecasts/gfs_2021_2025"
    pm10 = pd.read_csv(pm10_folder / "tabla_supervisada_pm10.csv",
                      dtype={"codigo_estacion": "string", "codigo_provincia": "string", "pm10_elevado_objetivo": "Int64"})
    weather = pd.read_csv(weather_folder / "previsiones_gfs_diarias.csv", dtype={"codigo_estacion": "string"})
    for column in ["fecha_objetivo", "fecha_ultima_observacion"]:
        pm10[column] = pd.to_datetime(pm10[column], format="%Y-%m-%d")
    weather["fecha_objetivo"] = pd.to_datetime(weather.fecha_objetivo, format="%Y-%m-%d")
    pm10["emision_simulada_utc"] = pd.to_datetime(pm10.emision_simulada_utc, utc=True)
    weather["inicio_ciclo_utc"] = pd.to_datetime(weather.inicio_ciclo_utc, utc=True)
    threshold = json.loads((pm10_folder / "protocolo.json").read_text(encoding="utf-8"))["umbral_clasificacion"]
    joined = join_weather(pm10, weather, threshold)
    coverage = summarize_coverage(joined, ["anio_objetivo", "codigo_estacion", "NOMBRE"])
    annual = summarize_coverage(joined, ["anio_objetivo", "particion_meteo"])

    output = PROJECT_ROOT / "data/interim/pm10_weather"
    output.mkdir(parents=True, exist_ok=True)
    for column in ["emision_simulada_utc", "inicio_ciclo_utc"]:
        joined[column] = joined[column].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    for name, table in [("tabla_pm10_meteo", joined), ("cobertura_por_estacion_anio", coverage), ("cobertura_por_anio", annual)]:
        table.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    schema = {"clave": KEY, "predictores_base": NUMERIC_FEATURES + ["codigo_estacion"],
              "predictores_meteorologicos": WEATHER_FEATURES, "umbral_pm10_elevado_ug_m3": threshold,
              "criterio_cohorte": "fila_comun_utilizable", "periodo_objetivo": [START, END]}
    (output / "esquema_comparacion.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(annual.to_string(index=False))


if __name__ == "__main__":
    main()
