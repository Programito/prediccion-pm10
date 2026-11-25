"""Small backend-independent contract used by training and evaluation."""

from typing import Any, Protocol, Self

import numpy as np
import pandas as pd


class Regressor(Protocol):
    def fit(self, features: pd.DataFrame, target: pd.Series) -> Self: ...

    def predict(self, features: pd.DataFrame) -> np.ndarray: ...

    def get_parameters(self) -> dict[str, Any]: ...

    def feature_details(self) -> pd.DataFrame: ...
