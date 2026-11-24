"""Explain the two frozen Ridge models through grouped validation permutations."""

import json
import platform

import joblib
import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT as ROOT
from tfm_data.adapters.sklearn.base import backend_version
from tfm_data.models.factory import FEATURES
from tfm_data.evaluation.window_ablation import make_window_cohorts
from tfm_data.evaluation.grouped_permutation import GROUPS, JOINT_HISTORY, grouped_permutation
from tfm_data.pipelines.compare_pm10_windows import SOURCES
from tfm_data.pipelines.barcelona_experiment import digest, save_csv, save_json

SEED, REPEATS, MINIMUM_SHIFT = 20261120, 50, 14
REFERENCES = {
    "madrid": ("output/pm10_regression_validation/coeficientes_ridge.csv", "output/pm10_regression_validation/importancias_random_forest.csv"),
    "barcelona": ("output/experiments/barcelona/validacion/variables_ridge.csv", "output/experiments/barcelona/validacion/variables_random_forest.csv"),
}


def main():
    reports = []
    protected_paths = list((ROOT / "models").rglob("*.joblib")) + [ROOT / source["test"] for source in SOURCES.values()]
    protected = {path.relative_to(ROOT).as_posix(): digest(path) for path in protected_paths}
    for index, (experiment, source) in enumerate(SOURCES.items()):
        paths = [*source.values(), *REFERENCES[experiment]]
        hashes = {path: digest(ROOT / path) for path in paths}
        table = pd.read_csv(ROOT / source["table"], dtype={"codigo_estacion": str})
        validation = make_window_cohorts(table)["validation_common"].sort_values(["codigo_estacion", "fecha_objetivo"]).reset_index(drop=True)
        model = joblib.load(ROOT / source["model"])["pipeline"]
        if model.numeric_features + model.categorical_features != FEATURES:
            raise ValueError("Las variables del modelo original no coinciden.")
        output = ROOT / "output/experiments/grouped_permutation" / experiment
        configuration = dict(experiment=experiment, year=2023, n=len(validation), seed=SEED + index,
                             repeats=REPEATS, minimumShiftEvaluatedRows=MINIMUM_SHIFT,
                             groups={group: dict(label=label, features=fields) for group, (label, fields) in GROUPS.items()},
                             sensitivityFeatures=JOINT_HISTORY, sourceHashes=hashes, refit=False, newTestEvaluation=False,
                             metric="MAE", predictionRule="max(0, prediction)",
                             versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, sklearn=backend_version(), joblib=joblib.__version__),
                             temporalMethod="Circular shifts in chronologically ordered complete-case rows, independently within station; same shifts for all numeric groups",
                             categoricalMethod="Enumerate the non-identity cyclic relabelings of station codes; with three stations, two mappings",
                             interpretation="Monte Carlo variation is not a confidence interval; validation already used, exploratory diagnostic")
        save_json(output / "protocolo.json", configuration)
        prediction = np.maximum(0, model.predict(validation[FEATURES]))
        saved = pd.read_csv(ROOT / source["validation"], dtype={"codigo_estacion": str}, parse_dates=["fecha_objetivo"])
        saved = saved.loc[saved.modelo.eq("ridge")].sort_values(["codigo_estacion", "fecha_objetivo"]).reset_index(drop=True)
        if (not validation[["codigo_estacion", "fecha_objetivo"]].equals(saved[["codigo_estacion", "fecha_objetivo"]])
                or not np.allclose(validation.pm10_objetivo, saved.pm10_objetivo, rtol=0, atol=1e-12)
                or not np.allclose(prediction, saved.prediccion, rtol=0, atol=1e-10)):
            raise ValueError("La cohorte o las predicciones difieren de la validación congelada.")
        result = grouped_permutation(model.predict, validation, repeats=REPEATS, minimum_shift=MINIMUM_SHIFT, seed=SEED + index)
        save_csv(output / "repeticiones.csv", result.pop("samples"))
        save_csv(output / "desplazamientos.csv", pd.DataFrame(result.pop("offsets")))
        save_csv(output / "resumen.csv", pd.DataFrame(result["rows"]).assign(features=lambda rows: rows.features.map("|".join)))
        references = {}
        for kind, path in zip(["ridge", "forest"], REFERENCES[experiment]):
            references[kind] = pd.read_csv(ROOT / path).to_dict("records")
        report = dict(id=experiment, name="Madrid" if experiment == "madrid" else "Barcelona (provincia)", **result,
                      seed=SEED + index, minimumShiftRows=MINIMUM_SHIFT, referenceFeatures=references,
                      sourceHashes=hashes, originalValidationMatches=True,
                      stations=[dict(code=code, name=rows.NOMBRE.iloc[0].strip(), n=len(rows)) for code, rows in validation.groupby("codigo_estacion")])
        save_json(output / "resumen.json", report)
        if any(digest(ROOT / path) != sha for path, sha in hashes.items()):
            raise ValueError("Cambió una entrada protegida.")
        reports.append(report)
        print(experiment, "MAE original", report["baselineMae"], flush=True)
        print(pd.DataFrame(report["rows"])[["label", "mean", "minimum", "maximum", "repetitions"]].to_string(index=False), flush=True)
    if any(digest(ROOT / path) != sha for path, sha in protected.items()):
        raise ValueError("Cambió un modelo o una prueba original.")
    save_json(ROOT / "output/experiments/grouped_permutation/resumen.json", dict(
        year=2023, repeats=REPEATS, minimumShiftRows=MINIMUM_SHIFT, experiments=reports, originalArtifactsUnchanged=True,
        protectedHashes=protected,
        limitations=["La importancia mide dependencia del modelo ante perturbaciones; no es causal ni una proporción de contribución",
                     "Las filas evaluables pueden tener saltos: 14 posiciones no equivalen necesariamente a 14 días naturales",
                     "El desplazamiento preserva el orden circular del grupo, pero cambia su alineación con objetivos y otras variables; puede romper relaciones estacionales y físicas",
                     "Una perturbación puede usar valores de fechas posteriores al objetivo; es un diagnóstico artificial, no una predicción operativa ni una entrada de entrenamiento",
                     "Las medias y los retardos comparten información; sus importancias no se suman. El grupo conjunto es una sensibilidad que se solapa",
                     "La variación entre perturbaciones no es un intervalo de confianza y no cuantifica incertidumbre de muestreo",
                     "La estación usa solo dos rotaciones de etiquetas en cada territorio; no resume todas las perturbaciones posibles",
                     "La rotación conserva una etiqueta por serie, pero puede cambiar sus frecuencias cuando las estaciones tienen distintos números de casos",
                     "Se reutiliza una validación conocida de 2023 con modelos congelados; no se evalúa de nuevo 2024 ni 2025"]
    ))


if __name__ == "__main__":
    main()
