"""Grouped permutation diagnostics on fixed 2023 complete validation cases."""

import numpy as np
import pandas as pd

from pm10_data.mappers.pm10_forecast import NUMERIC_FEATURES

FEATURES = NUMERIC_FEATURES + ["codigo_estacion"]
GROUPS = {
    "recent": ("PM10 reciente y retardos", ["pm10_t", "pm10_t_menos_1", "pm10_t_menos_2", "pm10_t_menos_6"]),
    "windows": ("Medias y variabilidad", ["media_3_dias", "media_7_dias", "media_14_dias", "desviacion_7_dias"]),
    "calendar": ("Calendario", ["semana_sin", "semana_cos", "mes_sin", "mes_cos"]),
    "station": ("Estación", ["codigo_estacion"]),
}
JOINT_HISTORY = GROUPS["recent"][1] + GROUPS["windows"][1]


def circular_orders(stations, repeats=50, minimum_shift=14, seed=20261120):
    if repeats < 2 or minimum_shift < 1:
        raise ValueError("Se requieren al menos dos repeticiones y separación positiva.")
    stations = np.asarray(stations)
    rng = np.random.default_rng(seed)
    orders, offsets = [], []
    for repetition in range(1, repeats + 1):
        order = np.arange(len(stations))
        for station in sorted(set(stations)):
            positions = np.flatnonzero(stations == station)
            if len(positions) < 2 * minimum_shift + 1:
                raise ValueError("Una estación no admite la separación circular solicitada.")
            offset = int(rng.integers(minimum_shift, len(positions) - minimum_shift + 1))
            order[positions] = np.roll(positions, offset)
            offsets.append(dict(repetition=repetition, station=str(station), evaluated_rows=len(positions), shift_rows=offset))
        orders.append(order)
    return orders, offsets


def shift_columns(features, columns, order):
    if not columns or not set(columns).issubset(FEATURES) or not set(columns).issubset(features.columns):
        raise ValueError("Grupo de variables desconocido.")
    order = np.asarray(order)
    if not np.issubdtype(order.dtype, np.integer) or not np.array_equal(np.sort(order), np.arange(len(features))):
        raise ValueError("Se requiere una permutación completa de las filas.")
    changed = features.copy()
    changed.loc[:, columns] = features.iloc[order][columns].to_numpy()
    return changed


def station_relabelings(stations):
    codes = sorted(set(stations))
    if len(codes) < 2:
        raise ValueError("Se necesitan al menos dos estaciones para alterar sus identidades.")
    return [dict(zip(codes, np.roll(codes, shift).tolist())) for shift in range(1, len(codes))]


def grouped_permutation(predict, original, *, repeats=50, minimum_shift=14, seed=20261120):
    if sorted(field for _, fields in GROUPS.values() for field in fields) != sorted(FEATURES):
        raise ValueError("Los grupos principales deben cubrir las variables una sola vez.")
    data = original.copy()
    data["fecha_objetivo"] = pd.to_datetime(data.fecha_objetivo)
    data["fecha_ultima_observacion"] = pd.to_datetime(data.fecha_ultima_observacion)
    if data.empty or not data.fecha_objetivo.dt.year.eq(2023).all() or data.duplicated(["codigo_estacion", "fecha_objetivo"]).any():
        raise ValueError("Se requieren filas únicas de la validación de 2023.")
    if not (data.fecha_objetivo - data.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all():
        raise ValueError("El horizonte debe ser un día.")
    if data[FEATURES + ["pm10_objetivo"]].isna().any().any() or not np.isfinite(data[NUMERIC_FEATURES + ["pm10_objetivo"]].to_numpy(dtype=float)).all():
        raise ValueError("La cohorte debe tener entradas y objetivos completos y finitos.")
    data = data.sort_values(["codigo_estacion", "fecha_objetivo"]).reset_index(drop=True)
    features = data[FEATURES].copy()
    observed = data.pm10_objetivo.to_numpy(dtype=float)

    def mae(frame):
        prediction = np.asarray(predict(frame), dtype=float)
        if prediction.shape != observed.shape or not np.isfinite(prediction).all():
            raise ValueError("El predictor produjo una salida incompatible.")
        return float(np.abs(np.maximum(0, prediction) - observed).mean())

    baseline = mae(features)
    orders, offsets = circular_orders(features.codigo_estacion.to_numpy(), repeats, minimum_shift, seed)
    definitions = {**GROUPS, "joint_history": ("Historial completo · sensibilidad conjunta", JOINT_HISTORY)}
    samples, label_maps = [], []
    for group, (label, columns) in definitions.items():
        if group == "station":
            maps = station_relabelings(features.codigo_estacion)
            for repetition, mapping in enumerate(maps, 1):
                changed = features.copy()
                changed["codigo_estacion"] = changed.codigo_estacion.map(mapping)
                error = mae(changed)
                samples.append(dict(group=group, label=label, repetition=repetition, mae=error, delta_mae=error - baseline, method="station_cyclic_relabel"))
                label_maps.append(dict(repetition=repetition, mapping=mapping))
        else:
            for repetition, order in enumerate(orders, 1):
                error = mae(shift_columns(features, columns, order))
                samples.append(dict(group=group, label=label, repetition=repetition, mae=error, delta_mae=error - baseline, method="within_station_circular_shift"))
    samples = pd.DataFrame(samples)
    summary = []
    for group, rows in samples.groupby("group", sort=False):
        summary.append(dict(group=group, label=definitions[group][0], features=definitions[group][1],
                            kind="sensitivity" if group == "joint_history" else "primary", method=rows.method.iloc[0],
                            repetitions=len(rows), mean=float(rows.delta_mae.mean()), median=float(rows.delta_mae.median()),
                            std=float(rows.delta_mae.std(ddof=1)) if len(rows) > 1 else None, minimum=float(rows.delta_mae.min()), maximum=float(rows.delta_mae.max()),
                            meanPermutedMae=float(rows.mae.mean())))
    return dict(n=len(data), baselineMae=baseline, rows=summary, samples=samples, offsets=offsets, stationMappings=label_maps)
