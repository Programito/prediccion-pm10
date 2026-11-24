"""Export exact additive Ridge explanations for the frozen 2024 predictions."""

import hashlib
import json
import platform

import joblib
import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT
from tfm_data.adapters.sklearn.base import backend_version


def main():
    protocol_path = PROJECT_ROOT / "docs/reference/pm10_final_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    paths = {}
    for name in ("ridge", "tabla"):
        entry = protocol["entradas"][name]
        path = PROJECT_ROOT / entry["ruta"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"El archivo difiere del protocolo: {name}")
        paths[name] = path

    artifact = joblib.load(paths["ridge"])
    if artifact["modelo"] != "ridge" or artifact["configuracion"]["fecha_maxima_entrenamiento"] != "2022-12-31":
        raise ValueError("El modelo no coincide con el Ridge congelado.")
    features = artifact["configuracion"]["variables"]
    table = pd.read_csv(paths["tabla"], dtype={"codigo_estacion": str})
    test = table.loc[table.fecha_objetivo.str.startswith("2024-")].copy()
    keys = ["codigo_estacion", "fecha_objetivo"]
    reference_path = PROJECT_ROOT / "output/pm10_final_2024/predicciones_regresion.csv"
    reference = pd.read_csv(reference_path, dtype={"codigo_estacion": str})
    reference = reference.loc[reference.modelo.eq("ridge"), keys + ["prediccion", "pm10_objetivo"]]
    matched = test.merge(reference, on=keys, how="outer", validate="one_to_one", indicator=True, suffixes=("", "_guardado"))
    if not matched._merge.eq("both").all() or not matched.pm10_objetivo.eq(matched.pm10_objetivo_guardado).all():
        raise ValueError("La muestra no coincide con las predicciones guardadas.")

    explanation = artifact["pipeline"].explain_predictions(matched[features])
    reconstructed = explanation["intercept"] + explanation["contributions"].sum(axis=1)
    np.testing.assert_allclose(reconstructed, explanation["predictions"], atol=1e-10, rtol=1e-12)
    np.testing.assert_allclose(np.maximum(0, reconstructed), matched.prediccion, atol=1e-10, rtol=1e-12)
    coefficients_path = PROJECT_ROOT / "output/pm10_regression_validation/coeficientes_ridge.csv"
    coefficients = pd.read_csv(coefficients_path)
    if coefficients.variable_transformada.tolist() != explanation["names"]:
        raise ValueError("Las variables del CSV de coeficientes difieren del modelo.")
    np.testing.assert_allclose(coefficients.coeficiente, explanation["coefficients"], atol=1e-12)
    importances_path = PROJECT_ROOT / "output/pm10_regression_validation/importancias_random_forest.csv"
    importances = pd.read_csv(importances_path)
    forest_path = PROJECT_ROOT / "models/pm10/validation_2023/random_forest.joblib"
    forest = joblib.load(forest_path)
    if forest["modelo"] != "random_forest" or forest["configuracion"]["fecha_maxima_entrenamiento"] != "2022-12-31":
        raise ValueError("La versión de Random Forest es incompatible.")
    forest_details = forest["pipeline"].feature_details()
    pd.testing.assert_frame_equal(importances.reset_index(drop=True), forest_details.reset_index(drop=True), check_exact=False, atol=1e-12, rtol=1e-12)
    if not importances.importancia_impureza.ge(0).all() or not np.isclose(importances.importancia_impureza.sum(), 1):
        raise ValueError("Importancias de Random Forest inválidas.")

    payload = {
        "model": "ridge",
        "trainingEnd": "2022-12-31",
        "testYear": 2024,
        "intercept": explanation["intercept"],
        "features": [
            {"name": name, "coefficient": float(coefficient)}
            for name, coefficient in zip(explanation["names"], explanation["coefficients"], strict=True)
        ],
        "forest": [
            {"name": row.variable_transformada, "importance": float(row.importancia_impureza)}
            for row in importances.itertuples(index=False)
        ],
        "cases": [
            {
                "station": row.codigo_estacion, "date": row.fecha_objetivo,
                "observed": float(row.pm10_objetivo), "prediction": float(row.prediccion),
                "rawPrediction": float(explanation["predictions"][index]),
                "inputs": {name: float(row[name]) for name in artifact["pipeline"].numeric_features},
                "transformed": explanation["transformed"][index].tolist(),
                "contributions": explanation["contributions"][index].tolist(),
            }
            for index, (_, row) in enumerate(matched.iterrows())
        ],
    }
    output = PROJECT_ROOT / "output/pm10_explanations"
    output.mkdir(parents=True, exist_ok=True)
    (output / "explicaciones.json").write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n", encoding="utf-8")
    sources = [protocol_path, paths["ridge"], paths["tabla"], reference_path, coefficients_path, importances_path, forest_path]
    metadata = {
        "sources": {path.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "cases": len(matched),
        "maximum_reconstruction_error": float(np.max(np.abs(reconstructed - explanation["predictions"]))),
        "refit": False,
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": backend_version(), "joblib": joblib.__version__},
    }
    (output / "configuracion.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
