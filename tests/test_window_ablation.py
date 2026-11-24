import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from tfm_data.mappers.pm10_forecast import PM10ForecastMapper
from tfm_data.evaluation.window_ablation import make_window_cohorts, score_prediction_cases, KEYS
from explorer.server import app


class WindowAblationTest(unittest.TestCase):
    def fixture(self):
        daily = pd.DataFrame({'fecha': pd.date_range('2021-01-01', '2024-02-01')})
        daily['codigo_estacion'], daily['NOMBRE'], daily['pm10_valido'] = '01', 'Example', 10.0
        daily.loc[daily.fecha.isin(pd.to_datetime(['2022-05-10','2023-01-04'])), 'pm10_valido'] = np.nan
        return PM10ForecastMapper().transform(daily)

    def test_one_gap_recovers_seven_cases_and_preserves_disjoint_validation_cohorts(self):
        cohorts = make_window_cohorts(self.fixture())
        self.assertEqual(len(cohorts['validation_additional']), 7)
        common = set(map(tuple,cohorts['validation_common'][KEYS].to_numpy()))
        additional = set(map(tuple,cohorts['validation_additional'][KEYS].to_numpy()))
        expanded = set(map(tuple,cohorts['validation_expanded'][KEYS].to_numpy()))
        self.assertFalse(common & additional)
        self.assertEqual(common | additional,expanded)
        self.assertEqual(len(cohorts['calendar_validation']),365)
        self.assertGreater(len(cohorts['train_expanded']),len(cohorts['train_common']))

    def test_future_values_and_duplicates_cannot_change_training_or_validation(self):
        source = self.fixture()
        expected = make_window_cohorts(source)
        future = source.fecha_objetivo.dt.year.eq(2024)
        source.loc[future, 'pm10_t'] = np.inf
        source.loc[future, 'pm10_objetivo'] = -9999
        source = pd.concat([source,source.loc[future].head(1)],ignore_index=True)
        result = make_window_cohorts(source)
        for key in expected:
            pd.testing.assert_frame_equal(expected[key].reset_index(drop=True),result[key].reset_index(drop=True))
        self.assertLessEqual(result['train_expanded'].fecha_objetivo.max(),pd.Timestamp('2022-12-31'))

    def test_inconsistent_horizon_and_original_cohort_are_rejected(self):
        source = self.fixture()
        source.loc[source.fecha_objetivo.eq('2023-01-01'),'fecha_ultima_observacion'] = pd.Timestamp('2022-12-30')
        with self.assertRaises(ValueError):make_window_cohorts(source)
        source = self.fixture()
        source.loc[source.fecha_objetivo.eq('2023-01-01'),'fila_utilizable'] = False
        with self.assertRaises(ValueError):make_window_cohorts(source)
        source = self.fixture()
        source.loc[source.fecha_objetivo.eq('2023-01-01'),'media_14_dias'] = np.inf
        with self.assertRaises(ValueError):make_window_cohorts(source)

    def test_non_negative_prediction_rule_and_nonfinite_rejection(self):
        rows=make_window_cohorts(self.fixture())['validation_common'].head(2)
        result=score_prediction_cases(rows,np.array([-1,5]),'candidate')
        self.assertEqual(result.prediccion.tolist(),[0,5])
        self.assertEqual(result.prediccion_negativa_corregida.tolist(),[True,False])
        with self.assertRaises(ValueError):score_prediction_cases(rows,np.array([np.nan,5]),'candidate')

    def test_report_endpoint_reads_only_saved_results(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('explorer.server.ROOT',root):
                client=app.test_client()
                self.assertEqual(client.get('/api/experiments/window-ablation').status_code,404)
                path=root/'output/experiments/window_ablation/resumen.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'validation':'2023','originalArtifactsUnchanged':True}),encoding='utf-8')
                result=client.get('/api/experiments/window-ablation')
                self.assertEqual(result.status_code,200)
                self.assertEqual(result.get_json()['validation'],'2023')
