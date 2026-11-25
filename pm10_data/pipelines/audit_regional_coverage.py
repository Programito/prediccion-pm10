"""Audit 2024 complete-case exclusions for both fixed regional experiments."""

import json

import pandas as pd

from pm10_data.config import PROJECT_ROOT as ROOT
from pm10_data.evaluation.coverage_audit import audit_rows, build_audit
from pm10_data.pipelines.barcelona_experiment import digest, save_csv, save_json

SOURCES = {
    "madrid": ("data/interim/pm10_prediction/tabla_supervisada_pm10.csv", "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv", "output/pm10_final_2024/predicciones_regresion.csv"),
    "barcelona": ("data/interim/experiments/barcelona/tabla_supervisada.csv", "data/interim/experiments/barcelona/diario_2017_2024.csv", "output/experiments/barcelona/prueba_2024/predicciones.csv"),
}


def main():
    for experiment, paths in SOURCES.items():
        before = {path: digest(ROOT / path) for path in paths}
        supervised, daily, predictions = [pd.read_csv(ROOT / path, dtype={"codigo_estacion": str}) for path in paths]
        rows = audit_rows(supervised, daily)
        keys = set(zip(rows.loc[rows.evaluada, "codigo_estacion"], rows.loc[rows.evaluada, "fecha_objetivo"].dt.strftime("%Y-%m-%d")))
        for model, group in predictions.groupby("modelo"):
            if keys != set(zip(group.codigo_estacion, group.fecha_objetivo)) or group.duplicated(["codigo_estacion", "fecha_objetivo"]).any():
                raise ValueError("Los casos calculados difieren de las predicciones guardadas: " + model)
        result = build_audit(rows)
        result["experiment"] = experiment
        result["sources"] = [dict(path=path, sha256=sha) for path, sha in before.items()]
        output = ROOT / "output/experiments" / experiment / "coverage_audit"
        save_csv(output / "detalle.csv", rows)
        save_csv(output / "variables.csv", pd.DataFrame(result["features"]))
        save_csv(output / "episodios.csv", pd.DataFrame(result["episodes"]))
        save_csv(output / "cobertura.csv", pd.DataFrame([{**{key: value for key, value in group.items() if key != "reasons"}, **group["reasons"]} for group in result["groups"]]))
        save_json(output / "resumen.json", result)
        if any(digest(ROOT / path) != sha for path, sha in before.items()):
            raise ValueError("Cambió una entrada durante la auditoría.")
        print(experiment, json.dumps(result["groups"][0], ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
