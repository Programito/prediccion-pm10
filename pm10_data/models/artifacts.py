"""Read and write model artifacts using their original serialization names."""

from functools import cache
from pathlib import Path
import sys

import joblib

import pm10_data
from pm10_data import adapters
from pm10_data.adapters import sklearn as sklearn_adapters
from pm10_data.adapters.sklearn import logistic, random_forest, ridge


@cache
def _register_artifact_modules() -> None:
    # Frozen protocols check file hashes. Keep the original pickle identifiers
    # resolvable and continue writing them when reproducing a frozen model.
    legacy_package = "tfm_data"
    legacy_adapters = f"{legacy_package}.adapters"
    legacy_sklearn = f"{legacy_adapters}.sklearn"
    sys.modules.setdefault(legacy_package, pm10_data)
    sys.modules.setdefault(legacy_adapters, adapters)
    sys.modules.setdefault(legacy_sklearn, sklearn_adapters)
    for module, adapter in (
        (logistic, logistic.LogisticAdapter),
        (random_forest, random_forest.RandomForestAdapter),
        (ridge, ridge.RidgeAdapter),
    ):
        module_name = f"{legacy_sklearn}.{module.__name__.rsplit('.', 1)[-1]}"
        sys.modules.setdefault(module_name, module)
        adapter.__module__ = module_name


def load_model(path: Path) -> dict:
    """Load a trusted project artifact from disk."""
    _register_artifact_modules()
    return joblib.load(path)


def save_model(artifact: dict, path: Path) -> None:
    """Save a model in the format recorded by the evaluation protocols."""
    _register_artifact_modules()
    joblib.dump(artifact, path, compress=3)
