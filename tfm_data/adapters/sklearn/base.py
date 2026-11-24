"""Shared preprocessing for scikit-learn adapters."""

from typing import Any, Self

import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def backend_version() -> str:
    return sklearn.__version__


def make_preprocessor(numeric_features: list[str], categorical_features: list[str], *, scale_numeric: bool) -> ColumnTransformer:
    return ColumnTransformer([
        ("numeric", StandardScaler() if scale_numeric else "passthrough", numeric_features),
        ("station", OneHotEncoder(handle_unknown="error", sparse_output=False), categorical_features),
    ], remainder="drop")


class SklearnRegressorAdapter:
    def __init__(self, estimator: Any, numeric_features: list[str], categorical_features: list[str],
                 *, scale_numeric: bool, parameters: dict[str, Any]):
        self.numeric_features = list(numeric_features)
        self.categorical_features = list(categorical_features)
        self.parameters = dict(parameters)
        preprocessor = make_preprocessor(self.numeric_features, self.categorical_features, scale_numeric=scale_numeric)
        self.pipeline = Pipeline([("preprocessor", preprocessor), ("regressor", estimator)])

    def fit(self, features: pd.DataFrame, target: pd.Series) -> Self:
        self.pipeline.fit(features, target)
        return self

    def predict(self, features: pd.DataFrame) -> np.ndarray:
        return self.pipeline.predict(features)

    def get_parameters(self) -> dict[str, Any]:
        return dict(self.parameters)

    def _feature_names(self) -> np.ndarray:
        return self.pipeline.named_steps["preprocessor"].get_feature_names_out()
