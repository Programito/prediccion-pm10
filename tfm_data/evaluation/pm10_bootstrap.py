"""Paired moving-block bootstrap over calendar dates and synchronized stations."""

import numpy as np


def moving_block_indices(days, length, replicates, seed):
    if not 1 <= length <= days or replicates < 2:
        raise ValueError("Bloque incompatible con el calendario o réplicas insuficientes.")
    rng = np.random.default_rng(np.random.SeedSequence([seed, length]))
    blocks = (days + length - 1) // length
    starts = rng.integers(0, days - length + 1, size=(replicates, blocks))
    return (starts[:, :, None] + np.arange(length)).reshape(replicates, -1)[:, :days]


def resampled_differences(totals, counts, indices):
    totals = np.asarray(totals, dtype=float)
    counts = np.asarray(counts, dtype=float)
    if totals.ndim != 1 or totals.shape != counts.shape:
        raise ValueError("Se requieren sumas y recuentos diarios alineados.")
    if (not np.isfinite(totals).all() or not np.isfinite(counts).all()
            or (counts < 0).any() or not np.equal(counts, np.floor(counts)).all()
            or np.any((counts == 0) & (totals != 0))):
        raise ValueError("Sumas o recuentos diarios inválidos.")
    denominator = counts[indices].sum(axis=1)
    if (denominator == 0).any():
        raise ValueError("Una réplica carece de observaciones evaluables.")
    return totals[indices].sum(axis=1) / denominator, denominator
