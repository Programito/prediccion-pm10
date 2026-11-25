"""Explain complete-case exclusions without changing samples or fitting models."""

import pandas as pd

from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES

REASONS = {
    "evaluada": "Fila evaluable",
    "sin_objetivo": "Falta la observación objetivo",
    "sin_ultimo_dia": "Falta el último día observado",
    "historial_3d": "Falla el bloque de 3 días",
    "historial_7d": "Falla el bloque de 7 días",
    "historial_14d": "Falla la media de 14 días",
    "otras_variables": "Faltan otras variables",
}


def audit_rows(supervised, daily, year=2024, threshold=27):
    data = supervised.copy()
    data["fecha_objetivo"] = pd.to_datetime(data.fecha_objetivo)
    data = data.loc[data.fecha_objetivo.dt.year.eq(year)].sort_values(["codigo_estacion", "fecha_objetivo"]).copy()
    observations = daily.copy()
    observations["fecha"] = pd.to_datetime(observations.fecha)
    key = ["codigo_estacion", "fecha_objetivo"]
    if data.duplicated(key).any() or observations.duplicated(["codigo_estacion", "fecha"]).any():
        raise ValueError("Claves diarias repetidas.")
    expected = pd.MultiIndex.from_product([sorted(data.codigo_estacion.unique()), pd.date_range(f"{year}-01-01", f"{year}-12-31")], names=key)
    if data.empty or not pd.MultiIndex.from_frame(data[key]).sort_values().equals(expected):
        raise ValueError("La auditoría requiere el calendario completo del año objetivo.")
    lookup = observations.set_index(["codigo_estacion", "fecha"]).pm10_valido
    targets = lookup.reindex(pd.MultiIndex.from_frame(data[key].rename(columns={"fecha_objetivo": "fecha"}))).to_numpy()
    if not ((data.pm10_objetivo.to_numpy() == targets) | (data.pm10_objetivo.isna().to_numpy() & pd.isna(targets))).all():
        raise ValueError("Los objetivos supervisados no coinciden con los diarios.")
    available = data.pm10_objetivo.notna()
    complete = data[NUMERIC_FEATURES].notna().all(axis=1)
    evaluated = available & complete
    if not evaluated.eq(data.fila_utilizable).all():
        raise ValueError("La exclusión calculada difiere de la tabla supervisada.")
    reason = pd.Series("evaluada", index=data.index)
    reason.loc[~available] = "sin_objetivo"
    pending = available & ~complete
    for label, fields in [
        ("sin_ultimo_dia", ["pm10_t"]),
        ("historial_3d", ["pm10_t_menos_1", "pm10_t_menos_2", "media_3_dias"]),
        ("historial_7d", ["pm10_t_menos_6", "media_7_dias", "desviacion_7_dias"]),
        ("historial_14d", ["media_14_dias"]),
    ]:
        affected = pending & data[fields].isna().any(axis=1)
        reason.loc[affected] = label
        pending &= ~affected
    reason.loc[pending] = "otras_variables"
    result = data[key + ["NOMBRE", "pm10_objetivo"]].copy()
    result["evaluada"], result["motivo"] = evaluated, reason
    result["mes"] = result.fecha_objetivo.dt.month
    result["objetivo_disponible"] = available
    result["elevado_observado"] = available & data.pm10_objetivo.gt(threshold)
    result["variables_ausentes"] = data[NUMERIC_FEATURES].isna().apply(lambda row: "|".join(row.index[row]), axis=1)
    traces = []
    for row in result.itertuples():
        dates = pd.date_range(row.fecha_objetivo - pd.Timedelta(days=14), row.fecha_objetivo - pd.Timedelta(days=1))
        traces.append("|".join(day.strftime("%Y-%m-%d") for day in dates if pd.isna(lookup.get((row.codigo_estacion, day)))))
    result["fechas_historial_ausentes"] = traces
    for feature in NUMERIC_FEATURES:
        result["ausente__" + feature] = data[feature].isna()
    return result.reset_index(drop=True)


def summarize_rows(rows):
    known = rows.objetivo_disponible
    elevated = rows.elevado_observado
    excluded = ~rows.evaluada
    return dict(calendar=len(rows), evaluated=int(rows.evaluada.sum()), excluded=int(excluded.sum()),
                unknownTarget=int((~known).sum()), observedExcluded=int((known & excluded).sum()),
                elevatedObserved=int(elevated.sum()), elevatedExcluded=int((elevated & excluded).sum()),
                otherObserved=int((known & ~elevated).sum()), otherExcluded=int((known & ~elevated & excluded).sum()),
                reasons={key: int(rows.motivo.eq(key).sum()) for key in REASONS})


def build_audit(rows, threshold=27):
    years = rows.fecha_objetivo.dt.year.unique()
    if len(years) != 1:
        raise ValueError("La auditoría agregada requiere un único año.")
    groups, features = [], []
    for station in ["todas", *sorted(rows.codigo_estacion.unique())]:
        station_rows = rows if station == "todas" else rows.loc[rows.codigo_estacion.eq(station)]
        for month in range(13):
            subset = station_rows if month == 0 else station_rows.loc[station_rows.mes.eq(month)]
            groups.append(dict(station=station, month=month, **summarize_rows(subset)))
            known = subset.objetivo_disponible
            flags = subset[["ausente__" + field for field in NUMERIC_FEATURES]]
            for field in NUMERIC_FEATURES:
                missing = flags["ausente__" + field]
                features.append(dict(station=station, month=month, feature=field,
                                     missing=int(missing.sum()), missingWithTarget=int((missing & known).sum()),
                                     soleMissingWithTarget=int((missing & known & flags.sum(axis=1).eq(1)).sum())))
    episodes = []
    for station, group in rows.groupby("codigo_estacion", sort=True):
        group = group.sort_values("fecha_objetivo").copy()
        run = (~group.elevado_observado).cumsum()
        for _, elevated in group.loc[group.elevado_observado].groupby(run):
            peak = elevated.loc[elevated.pm10_objetivo.idxmax()]
            episodes.append(dict(station=station, name=peak.NOMBRE,
                                 start=elevated.fecha_objetivo.min().strftime("%Y-%m-%d"),
                                 end=elevated.fecha_objetivo.max().strftime("%Y-%m-%d"),
                                 peakDate=peak.fecha_objetivo.strftime("%Y-%m-%d"), peak=float(peak.pm10_objetivo),
                                 observedDays=len(elevated), evaluatedDays=int(elevated.evaluada.sum()),
                                 excludedDays=int((~elevated.evaluada).sum())))
    episodes.sort(key=lambda episode: (-episode["excludedDays"], -episode["peak"], episode["station"], episode["start"]))
    return dict(year=int(years[0]), threshold=threshold, reasonLabels=REASONS, groups=groups, features=features, episodes=episodes)
