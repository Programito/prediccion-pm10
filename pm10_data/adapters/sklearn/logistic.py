"""Binary logistic regression with the same preprocessing as Ridge."""

from typing import Self

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from .base import make_preprocessor


class LogisticAdapter:
    def __init__(self, numeric_features: list[str], categorical_features: list[str]):
        self.parameters = {"C": 1.0, "solver": "lbfgs", "max_iter": 1000, "class_weight": None}
        self.pipeline = Pipeline([
            ("preprocessor", make_preprocessor(numeric_features, categorical_features, scale_numeric=True)),
            ("classifier", LogisticRegression(**self.parameters)),
        ])

    def fit(self, features: pd.DataFrame, target: pd.Series) -> Self:
        self.pipeline.fit(features, target)
        return self

    def predict_positive_probability(self, features: pd.DataFrame) -> np.ndarray:
        classes = self.pipeline.named_steps["classifier"].classes_
        positive_index, = np.flatnonzero(classes == 1)
        return self.pipeline.predict_proba(features)[:, positive_index]

    def get_parameters(self) -> dict:
        return dict(self.parameters)
