"""Variables retrospectivas para PM10 de t+1 usando información hasta t."""

import numpy as np
import pandas as pd


NUMERIC_FEATURES = ["pm10_t", "pm10_t_menos_1", "pm10_t_menos_2", "pm10_t_menos_6",
                      "media_3_dias", "media_7_dias", "media_14_dias", "desviacion_7_dias",
                      "semana_sin", "semana_cos", "mes_sin", "mes_cos"]


class PM10ForecastMapper:
    def transform(self, original: pd.DataFrame) -> pd.DataFrame:
        required = {"codigo_estacion", "fecha", "pm10_valido"}
        if original.empty or not required.issubset(original.columns):
            raise ValueError("Faltan series diarias para preparar la predicción.")
        data = original.copy().sort_values(["codigo_estacion", "fecha"]).reset_index(drop=True)
        data["fecha"] = pd.to_datetime(data.fecha, errors="raise")
        if data.fecha.dt.tz is not None or not data.fecha.eq(data.fecha.dt.normalize()).all():
            raise ValueError("Las fechas de muestreo deben ser días sin hora ni zona.")
        if data[["codigo_estacion", "fecha"]].isna().any().any() or data.duplicated(["codigo_estacion", "fecha"]).any():
            raise ValueError("Claves diarias ausentes o duplicadas.")
        data["pm10_valido"] = pd.to_numeric(data.pm10_valido, errors="raise").astype(float)
        validos = data.pm10_valido.dropna()
        if not np.isfinite(validos).all() or validos.lt(0).any():
            raise ValueError("La concentración aceptada debe ser finita y no negativa.")
        groups = data.groupby("codigo_estacion", sort=False)
        if not groups.fecha.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError("El calendario tiene saltos; completarlo sin imputar valores.")
        data["fecha_ultima_observacion"] = data.fecha
        data["fecha_objetivo"] = data.fecha + pd.Timedelta(days=1)
        data["emision_simulada_utc"] = data.fecha_objetivo.dt.tz_localize("UTC")
        data["pm10_objetivo"] = groups.pm10_valido.shift(-1)
        data["pm10_t"] = data.pm10_valido
        for retraso in [1, 2, 6]:
            data[f"pm10_t_menos_{retraso}"] = groups.pm10_valido.shift(retraso)
        for ventana in [3, 7, 14]:
            data[f"media_{ventana}_dias"] = groups.pm10_valido.transform(lambda s: s.rolling(ventana, min_periods=ventana).mean())
        data["desviacion_7_dias"] = groups.pm10_valido.transform(lambda s: s.rolling(7, min_periods=7).std())
        data["dia_semana_objetivo"] = data.fecha_objetivo.dt.dayofweek
        data["mes_objetivo"] = data.fecha_objetivo.dt.month
        data["semana_sin"] = np.sin(2 * np.pi * data.dia_semana_objetivo / 7)
        data["semana_cos"] = np.cos(2 * np.pi * data.dia_semana_objetivo / 7)
        data["mes_sin"] = np.sin(2 * np.pi * (data.mes_objetivo - 1) / 12)
        data["mes_cos"] = np.cos(2 * np.pi * (data.mes_objetivo - 1) / 12)
        data["particion"] = "fuera_periodo"
        anio = data.fecha_objetivo.dt.year
        data.loc[anio.between(2017, 2022), "particion"] = "entrenamiento"
        data.loc[anio.eq(2023), "particion"] = "validacion"
        data.loc[anio.eq(2024), "particion"] = "prueba_reservada"
        data["objetivo_disponible"] = data.pm10_objetivo.notna()
        data["predictores_completos"] = data[NUMERIC_FEATURES].notna().all(axis=1)
        data["fila_utilizable"] = (data.objetivo_disponible & data.predictores_completos & data.particion.ne("fuera_periodo"))
        return data


def label_elevated_pm10(table: pd.DataFrame, quantile: float = .90) -> tuple[pd.DataFrame, float]:
    if not 0 < quantile < 1:
        raise ValueError("Cuantil fuera del intervalo (0,1).")
    result = table.copy()
    training = result.loc[result.particion.eq("entrenamiento") & result.objetivo_disponible, "pm10_objetivo"]
    if training.empty:
        raise ValueError("No hay objetivos de entrenamiento para definir el umbral.")
    threshold = float(training.quantile(quantile, interpolation="linear"))
    result["pm10_elevado_objetivo"] = pd.Series(pd.NA, index=result.index, dtype="Int64")
    disponibles = result.objetivo_disponible
    result.loc[disponibles, "pm10_elevado_objetivo"] = result.loc[disponibles, "pm10_objetivo"].gt(threshold).astype("Int64")
    return result, threshold
