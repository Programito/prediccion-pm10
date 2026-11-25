"""scikit-learn Ridge behind the project's regression interface."""

import pandas as pd
from sklearn.linear_model import Ridge

from .base import SklearnRegressorAdapter


DEFAULT_PARAMETERS = {"alpha": 10.0, "solver": "svd"}


class RidgeAdapter(SklearnRegressorAdapter):
    def __init__(self, numeric_features: list[str], categorical_features: list[str], **parameters):
        settings = {**DEFAULT_PARAMETERS, **parameters}
        super().__init__(Ridge(**settings), numeric_features, categorical_features,
                         scale_numeric=True, parameters=settings)

    def feature_details(self) -> pd.DataFrame:
        return pd.DataFrame({"variable_transformada": self._feature_names(),
                             "coeficiente": self.pipeline.named_steps["regressor"].coef_})

    def explain_predictions(self, features: pd.DataFrame) -> dict:
        regressor = self.pipeline.named_steps["regressor"]
        transformed = self.pipeline.named_steps["preprocessor"].transform(features)
        return {
            "names": self._feature_names().tolist(),
            "transformed": transformed,
            "coefficients": regressor.coef_,
            "contributions": transformed * regressor.coef_,
            "intercept": float(regressor.intercept_),
            "predictions": self.predict(features),
        }
