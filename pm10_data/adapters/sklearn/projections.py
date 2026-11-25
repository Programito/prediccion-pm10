"""Train-only PCA and regularized LDA, keeping vendor imports in adapters."""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .base import make_preprocessor


class PCAAdapter:
    def __init__(self):
        self.pipeline = Pipeline([('scale', StandardScaler()), ('pca', PCA(svd_solver='full'))])

    def fit(self, features):
        self.pipeline.fit(features)
        return self

    def transform(self, features):
        return self.pipeline.transform(features)

    def details(self):
        scale, pca = self.pipeline.named_steps['scale'], self.pipeline.named_steps['pca']
        return dict(means=scale.mean_.tolist(), scales=scale.scale_.tolist(),
                    components=pca.components_.tolist(), ratios=pca.explained_variance_ratio_.tolist())


class LDAAdapter:
    def __init__(self, numeric_features, categorical_features):
        self.pipeline = Pipeline([
            ('preprocessor', make_preprocessor(numeric_features, categorical_features, scale_numeric=True)),
            ('classifier', LinearDiscriminantAnalysis(solver='eigen', shrinkage='auto', n_components=1)),
        ])

    def fit(self, features, target):
        self.pipeline.fit(features, target)
        return self

    def predict_positive_probability(self, features):
        classifier = self.pipeline.named_steps['classifier']
        positive, = np.flatnonzero(classifier.classes_ == 1)
        return self.pipeline.predict_proba(features)[:, positive]

    def transform(self, features):
        return self.pipeline.transform(features)


def ranking_metrics(observed, probability):
    return dict(rocAuc=float(roc_auc_score(observed, probability)),
                averagePrecision=float(average_precision_score(observed, probability)))
