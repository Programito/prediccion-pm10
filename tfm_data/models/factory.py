"""Select project adapters without exposing vendor estimators to pipelines."""

from tfm_data.adapters.sklearn.logistic import LogisticAdapter
from tfm_data.adapters.sklearn.ridge import RidgeAdapter
from tfm_data.adapters.sklearn.random_forest import RandomForestAdapter
from tfm_data.mappers.pm10_forecast import NUMERIC_FEATURES
from .base import Regressor


FEATURES = NUMERIC_FEATURES + ["codigo_estacion"]


def create_models() -> dict[str, Regressor]:
    return {"ridge": RidgeAdapter(NUMERIC_FEATURES, ["codigo_estacion"]),
            "random_forest": RandomForestAdapter(NUMERIC_FEATURES, ["codigo_estacion"])}


def create_classifier() -> LogisticAdapter:
    return LogisticAdapter(NUMERIC_FEATURES, ["codigo_estacion"])
