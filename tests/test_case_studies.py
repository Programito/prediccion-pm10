import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from explorer.server import app
from tfm_data.evaluation.case_studies import reconstruct, select_typical, validate_alerts


class CaseStudiesTests(unittest.TestCase):
    def test_typical_ignores_errors_and_has_stable_ties(self):
        data = pd.DataFrame({"codigo_estacion": ["02", "01", "01", "01"],
                             "fecha_objetivo": ["2024-01-01", "2024-01-03", "2024-01-02", "2024-01-04"],
                             "observado": [10., 10., 10., 80.], "ae_ridge": [0., 2., 999., 0.]})
        selected, meta = select_typical(data.sample(frac=1, random_state=4))
        self.assertEqual((selected.codigo_estacion, selected.fecha_objetivo), ("01", "2024-01-02"))
        self.assertEqual((meta['candidates'], meta['median']), (3, 10))
        data.ae_ridge = [1000, 0, 0, 0]
        self.assertEqual(select_typical(data)[0].fecha_objetivo, selected.fecha_objetivo)
        with self.assertRaises(ValueError):
            select_typical(data.loc[data.observado.gt(27)])

    def fixture(self):
        return pd.DataFrame([dict(modelo=model, codigo_estacion='01', fecha_objetivo='2025-08-05',
                                  pm10_t=24., pm10_objetivo=42., observado=1, aviso=alert,
                                  probabilidad_elevado=prob)
                             for model, alert, prob in [('persistencia', 0, float('nan')),
                                                       ('logistica_sin_meteo', 0, .19),
                                                       ('logistica_con_meteo', 1, .20)]])

    def test_alerts_use_individual_cuts_and_persistence_rule(self):
        cuts = {'logistica_sin_meteo': .21, 'logistica_con_meteo': .20}
        validate_alerts(self.fixture(), cuts)
        for column, index, value in [('aviso', 2, 0), ('observado', 0, 0), ('pm10_objetivo', 1, 5),
                                     ('probabilidad_elevado', 2, float('nan')), ('aviso', 0, 1)]:
            with self.subTest(column=column, index=index):
                changed = self.fixture()
                changed.loc[index, column] = value
                with self.assertRaises(ValueError):
                    validate_alerts(changed, cuts)
        with self.assertRaises(ValueError):
            validate_alerts(pd.concat([self.fixture(), self.fixture().head(1)]), cuts)

    def test_additive_reconstruction_respects_nonnegative_output(self):
        self.assertEqual(reconstruct(2, [3, -1], 4), 4)
        self.assertEqual(reconstruct(2, [-3], 0), -1)
        with self.assertRaises(ValueError):
            reconstruct(2, [3, -1], 5)

    def test_api_download_whitelist_and_attachment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('explorer.server.ROOT', root):
                client = app.test_client()
                self.assertEqual(client.get('/api/case-studies').status_code, 404)
                folder = root / 'output/case_studies'
                folder.mkdir(parents=True)
                (folder / 'resumen.json').write_text(json.dumps({'cases': []}), encoding='utf-8')
                self.assertEqual(client.get('/api/case-studies').get_json(), {'cases': []})
                (folder / 'onset').mkdir()
                (folder / 'onset/avisos.csv').write_text('modelo,aviso\nlogistica,1\n', encoding='utf-8')
                with client.get('/api/case-studies/onset/evidence/avisos.csv') as response:
                    self.assertEqual(response.status_code, 200)
                    self.assertIn('attachment;', response.headers['Content-Disposition'])
                for url in ['/api/case-studies/onset/evidence/resumen.json',
                            '/api/case-studies/unknown/evidence/avisos.csv',
                            '/api/case-studies/onset/evidence/entradas.csv',
                            '/api/case-studies/onset/evidence/%2e%2e%2fresumen.json']:
                    self.assertEqual(client.get(url).status_code, 404)
