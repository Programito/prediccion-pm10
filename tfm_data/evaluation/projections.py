"""Temporal guards for exploratory projections and binary comparisons."""

import numpy as np
import pandas as pd

KEYS = ['codigo_estacion', 'fecha_objetivo']


def validate_cohorts(training, validation, features, years, threshold):
    if 'pm10_objetivo' in features or 'pm10_elevado_objetivo' in features:
        raise ValueError('El objetivo no puede ser predictor.')
    for rows, allowed in [(training, years), (validation, [2023])]:
        if rows.empty or rows.duplicated(KEYS).any():
            raise ValueError('Cohorte vacía o con claves duplicadas.')
        dates = pd.to_datetime(rows.fecha_objetivo, errors='raise')
        if not dates.dt.year.isin(allowed).all():
            raise ValueError('Las fechas no respetan las particiones temporales.')
        numeric = rows[[f for f in features if f != 'codigo_estacion']].to_numpy(dtype=float)
        if not np.isfinite(numeric).all():
            raise ValueError('Se requieren entradas completas y finitas.')
        if (not np.isfinite(rows.pm10_objetivo.to_numpy(dtype=float)).all()
                or not rows.pm10_elevado_objetivo.eq(rows.pm10_objetivo.gt(threshold)).all()
                or set(rows.pm10_elevado_objetivo.unique()) != {0, 1}):
            raise ValueError('Las etiquetas deben coincidir con el umbral y contener ambas clases.')


def choose_cut(scores, elevated, today_high, budget):
    # Same pre-existing rule as the weather comparison, not a test-set choice.
    from tfm_data.pipelines.compare_pm10_weather import threshold_sweep
    if not np.isfinite(scores).all() or not ((scores >= 0) & (scores <= 1)).all():
        raise ValueError('Probabilidades inválidas.')
    sweep = threshold_sweep(scores, elevated, today_high)
    eligible = sweep.loc[sweep.falsas_alarmas.le(budget)]
    selected = eligible.sort_values(['comienzos_detectados', 'positivos_detectados', 'falsas_alarmas', 'umbral'],
                                   ascending=[False, False, True, False]).iloc[0]
    return float(selected.umbral), sweep
