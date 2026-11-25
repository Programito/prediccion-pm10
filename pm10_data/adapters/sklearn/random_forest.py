"""scikit-learn Random Forest behind the project's regression interface."""

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from .base import SklearnRegressorAdapter


DEFAULT_PARAMETERS = {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 5,
                      "max_features": 1.0, "bootstrap": True, "random_state": 42, "n_jobs": 2}


class RandomForestAdapter(SklearnRegressorAdapter):
    def __init__(self, numeric_features: list[str], categorical_features: list[str], **parameters):
        settings = {**DEFAULT_PARAMETERS, **parameters}
        super().__init__(RandomForestRegressor(**settings), numeric_features, categorical_features,
                         scale_numeric=False, parameters=settings)

    def feature_details(self) -> pd.DataFrame:
        return pd.DataFrame({"variable_transformada": self._feature_names(),
                             "importancia_impureza": self.pipeline.named_steps["regressor"].feature_importances_}).sort_values(
                                 "importancia_impureza", ascending=False)
