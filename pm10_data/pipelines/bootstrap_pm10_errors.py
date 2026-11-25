"""Estimate exploratory intervals for fixed 2024 paired MAE differences."""

import hashlib
import json

import numpy as np
import pandas as pd

from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.pm10_errors import pair_predictions
from pm10_data.evaluation.pm10_bootstrap import moving_block_indices, resampled_differences


BLOCKS = (7, 14, 28)
REPLICATES = 5000
SEED = 20261119


def main():
    source = PROJECT_ROOT / "output/pm10_final_2024/predicciones_regresion.csv"
    paired = pair_predictions(pd.read_csv(source, dtype={"codigo_estacion": str}))
    paired["difference"] = paired.ae_ridge - paired.ae_persistencia
    calendar = pd.date_range("2024-01-01", "2024-12-31")
    groups = [("todas", "Todas las estaciones", paired)]
    groups += [(str(code), group.nombre.iloc[0], group) for code, group in paired.groupby("codigo_estacion")]
    rows, samples = [], []
    for length in BLOCKS:
        indices = moving_block_indices(len(calendar), length, REPLICATES, SEED)
        for station, name, group in groups:
            daily = group.groupby("fecha_objetivo").agg(total=("difference", "sum"), n=("difference", "size"))
            daily = daily.reindex(calendar, fill_value=0)
            differences, counts = resampled_differences(daily.total.to_numpy(), daily.n.to_numpy(), indices)
            lower, upper = np.quantile(differences, [.025, .975], method="linear")
            rows.append({
                "station": station, "name": name, "block_days": length,
                "n": len(group), "replicates": REPLICATES,
                "estimate": float(group.difference.mean()),
                "lower": float(lower), "upper": float(upper),
                "includes_zero": bool(lower <= 0 <= upper),
                "minimum_resampled_cases": int(counts.min()),
                "maximum_resampled_cases": int(counts.max()),
            })
            samples.append(pd.DataFrame({
                "station": station, "block_days": length, "replica": np.arange(1, REPLICATES + 1),
                "delta_mae": differences, "n": counts.astype(int),
            }))
    summary = pd.DataFrame(rows)
    output = PROJECT_ROOT / "output/pm10_bootstrap"
    output.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output / "intervalos.csv", index=False, encoding="utf-8-sig")
    pd.concat(samples, ignore_index=True).to_csv(output / "replicas.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    configuration = {
        "source": source.relative_to(PROJECT_ROOT).as_posix(),
        "sha256_source": hashlib.sha256(source.read_bytes()).hexdigest(),
        "calendar": ["2024-01-01", "2024-12-31"], "calendar_days": len(calendar),
        "method": "overlapping_non_circular_moving_blocks",
        "replicates": REPLICATES, "seed": SEED, "block_days": list(BLOCKS), "primary_block_days": 14,
        "interval": "percentile", "nominal_coverage": .95,
        "quantiles": [.025, .975], "quantile_method": "linear",
        "statistic": "sum(AE Ridge - AE persistence) / resampled evaluated station-days",
        "stations_resampled_together": True,
        "missing_calendar_dates": "zero count and zero sum; no imputed observations",
        "selection": "posthoc diagnostic conditional on fixed models and evaluated 2024 sample",
        "refit": False, "numpy": np.__version__, "pandas": pd.__version__,
    }
    (output / "configuracion.json").write_text(json.dumps(configuration, indent=2) + "\n", encoding="utf-8")
    (output / "analisis.json").write_text(json.dumps({
        "primaryBlockDays": 14, "coverage": .95, "replicates": REPLICATES,
        "seed": SEED, "rows": summary.to_dict("records"),
    }, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
