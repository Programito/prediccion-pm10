"""Audit fixed 2024 errors by station, month, level and influential dates."""

import hashlib
import json

import pandas as pd

from tfm_data.config import PROJECT_ROOT
from tfm_data.evaluation.pm10_errors import pair_predictions, grouped_errors, date_sensitivity


def main():
    source = PROJECT_ROOT / "output/pm10_final_2024/predicciones_regresion.csv"
    protocol = PROJECT_ROOT / "docs/reference/pm10_final_protocol.json"
    threshold = json.loads(protocol.read_text(encoding="utf-8"))["umbral_pm10_ug_m3"]
    paired = pair_predictions(pd.read_csv(source, dtype={"codigo_estacion": str}))
    groups = grouped_errors(paired, threshold)
    daily, sensitivity = date_sensitivity(paired)
    worst = paired.sort_values("ae_ridge", ascending=False, kind="stable").head(10)
    output = PROJECT_ROOT / "output/pm10_error_analysis"
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in [
        ("grupos", groups), ("contribucion_por_fecha", daily), ("sensibilidad_fechas", sensitivity),
        ("mayores_errores_ridge", worst),
    ]:
        frame.to_csv(output / f"{name}.csv", index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
    metadata = {
        "year": 2024, "threshold": threshold, "paired_cases": len(paired),
        "dates_removed_per_scenario": 5,
        "scope": "descriptive_posthoc_fixed_models_and_predictions",
        "delta_definition": "MAE Ridge - MAE persistencia",
        "refit": False,
        "sources": {path.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (source, protocol)},
    }
    chart_data = {"threshold": threshold, "groups": groups.to_dict("records"), "sensitivity": sensitivity.to_dict("records")}
    (output / "analisis.json").write_text(json.dumps(chart_data, allow_nan=False, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "configuracion.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(groups.loc[groups.month.eq(0)].to_string(index=False))
    print(sensitivity.to_string(index=False))


if __name__ == "__main__":
    main()
