import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from explorer.server import app
from pm10_data.adapters.sklearn.projections import LDAAdapter, PCAAdapter
from pm10_data.evaluation.projections import choose_cut, validate_cohorts


class ProjectionTests(unittest.TestCase):
    def test_pca_uses_training_scaling_and_full_variance(self):
        train = pd.DataFrame({'a': [1., 2., 3., 4.], 'b': [2., 4., 6., 8.]})
        model = PCAAdapter().fit(train)
        before = model.details()
        np.testing.assert_allclose(before['means'], [2.5, 5.])
        np.testing.assert_allclose(sum(before['ratios']), 1.)
        self.assertAlmostEqual(before['ratios'][0], 1.)
        transformed = model.transform(pd.DataFrame({'a': [1000.], 'b': [2000.]}))
        self.assertEqual(transformed.shape, (1, 2))
        self.assertEqual(model.details(), before)
        # All components reconstruct the standardized training inputs.
        standardized = (train.to_numpy() - before['means']) / before['scales']
        np.testing.assert_allclose(model.transform(train) @ np.array(before['components']), standardized, atol=1e-12)

    def test_lda_handles_correlated_features_and_has_one_axis(self):
        rng = np.random.default_rng(17)
        target = pd.Series([0] * 30 + [1] * 30)
        signal = rng.normal(size=60) + 3 * target
        data = pd.DataFrame({'a': signal, 'b': signal, 'codigo_estacion': ['01', '02', '03'] * 20})
        model = LDAAdapter(['a', 'b'], ['codigo_estacion']).fit(data, target)
        before = model.pipeline.named_steps['preprocessor'].named_transformers_['numeric'].mean_.copy()
        self.assertEqual(model.transform(data).shape, (60, 1))
        scores = model.predict_positive_probability(data)
        self.assertTrue(np.isfinite(scores).all())
        self.assertTrue(((scores >= 0) & (scores <= 1)).all())
        self.assertGreater(scores[30:].mean(), scores[:30].mean())
        model.transform(data.assign(a=10000, b=10000))
        np.testing.assert_array_equal(model.pipeline.named_steps['preprocessor'].named_transformers_['numeric'].mean_, before)

    def fixture(self, year):
        return pd.DataFrame({'codigo_estacion': ['01', '01'], 'fecha_objetivo': [f'{year}-01-01', f'{year}-01-02'],
                             'a': [1., 2.], 'pm10_objetivo': [5., 40.], 'pm10_elevado_objetivo': [0, 1]})

    def test_temporal_guard_rejects_future_targets_missing_values_and_duplicates(self):
        train, valid = self.fixture(2022), self.fixture(2023)
        validate_cohorts(train, valid, ['a'], [2021, 2022], 27)
        invalid = [self.fixture(2024), pd.concat([valid, valid.head(1)]), valid.assign(a=np.nan),
                   valid.assign(pm10_elevado_objetivo=[1, 1])]
        for rows in invalid:
            with self.assertRaises(ValueError):
                validate_cohorts(train, rows, ['a'], [2021, 2022], 27)
        with self.assertRaises(ValueError):
            validate_cohorts(train, valid, ['a', 'pm10_objetivo'], [2021, 2022], 27)

    def test_cut_selection_respects_tied_scores_and_false_alarm_budget(self):
        probability = np.array([.8, .8, .6, .2])
        positive = pd.Series([True, False, True, False])
        today = pd.Series([False] * 4)
        cut, sweep = choose_cut(probability, positive, today, 0)
        self.assertGreater(cut, .8)
        cut, sweep = choose_cut(probability, positive, today, 1)
        self.assertEqual(cut, .6)
        self.assertEqual(int(((probability >= cut) & ~positive).sum()), 1)
        self.assertEqual(int(((probability >= cut) & positive).sum()), 2)

    def test_api_serves_saved_report_and_whitelists_downloads(self):
        with tempfile.TemporaryDirectory() as directory, patch('explorer.server.ROOT', Path(directory)):
            client = app.test_client()
            self.assertEqual(client.get('/api/experiments/projections').status_code, 404)
            folder = Path(directory) / 'output/experiments/projections'
            folder.mkdir(parents=True)
            (folder / 'resumen.json').write_text(json.dumps({'validation': 2023}), encoding='utf-8')
            (folder / 'pca_pesos.csv').write_text('feature,PC1\na,1\n', encoding='utf-8')
            self.assertEqual(client.get('/api/experiments/projections').get_json(), {'validation': 2023})
            with client.get('/api/experiments/projections/files/pca_pesos.csv') as response:
                self.assertEqual(response.status_code, 200)
                self.assertIn('attachment;', response.headers['Content-Disposition'])
            for file in ['artefactos.joblib', 'resumen.json', '%2e%2e%2fprotocolo.json']:
                self.assertEqual(client.get('/api/experiments/projections/files/' + file).status_code, 404)
