import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from explorer.descriptive_statistics import summarize_numeric_columns, numeric_measurement_columns
from explorer.server import app


class DescriptiveStatisticsTest(unittest.TestCase):
    def test_exact_linear_quartiles_and_sample_deviation(self):
        result = summarize_numeric_columns(({'value': value} for value in [0, 10]), ['value'])
        row = result['columns'][0]
        self.assertEqual((result['row_count'], row['valid_count']), (2, 2))
        self.assertEqual((row['minimum'], row['p25'], row['median'], row['mean'], row['p75'], row['maximum']), (0, 2.5, 5, 5, 7.5, 10))
        self.assertAlmostEqual(row['std_dev'], 50 ** .5)

    def test_counts_missing_invalid_and_zero_without_clipping_extremes(self):
        values = [None, '', '  .. ', float('nan'), '1,5', float('inf'), True, 0, '-5', '1e3']
        row = summarize_numeric_columns([{'x': value} for value in values], ['x'])['columns'][0]
        self.assertEqual((row['valid_count'], row['missing_count'], row['invalid_count']), (3, 4, 3))
        self.assertEqual((row['missing_pct'], row['minimum'], row['maximum']), (40, -5, 1000))
        self.assertEqual(summarize_numeric_columns([{'x':'1_000'}], ['x'])['columns'][0]['invalid_count'], 1)

    def test_empty_single_and_constant_samples_have_explicit_undefined_statistics(self):
        empty = summarize_numeric_columns([], ['x'])['columns'][0]
        self.assertIsNone(empty['mean'])
        self.assertIsNone(empty['missing_pct'])
        single = summarize_numeric_columns([{'x': 7}], ['x'])['columns'][0]
        self.assertIsNone(single['std_dev'])
        constant = summarize_numeric_columns([{'x': 0}, {'x': 0}], ['x'])['columns'][0]
        self.assertEqual(constant['std_dev'], 0)
        json.dumps(empty, allow_nan=False)
        with self.assertRaises(ValueError):
            summarize_numeric_columns([], ['x', 'x'])

    def test_logical_types_exclude_identifiers_booleans_and_keys(self):
        columns = [dict(name='codigo_estacion', type='Entero'), dict(name='year', type='Entero', isKey=True),
                   dict(name='valid', type='Booleano'), dict(name='value', type='Decimal o nulo'),
                   dict(name='count', type='Entero'), dict(name='proportion', type='Proporción o nulo')]
        self.assertEqual(numeric_measurement_columns(columns), ['value', 'count', 'proportion'])

    def test_api_applies_filters_to_entire_table_before_statistics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'values.csv'
            path.write_text('codigo_estacion,value\n' + ''.join('01,'+str(value)+'\n' for value in range(20)) + '02,999\n', encoding='utf-8')
            table = dict(id='treated-test', local='values.csv', reader='csv', delimiter=',', columns=[
                dict(name='codigo_estacion', type='Código', isKey=True, notes='Identifier'),
                dict(name='value', type='Decimal o nulo', isKey=False, notes='Measurement')])
            with patch('explorer.server.find_table', return_value=table), patch('explorer.server.get_treated_tables', return_value={'treated-test':table}), patch('explorer.server.path_for', return_value=path):
                client = app.test_client()
                response = client.get('/api/tables/treated-test/statistics?column=codigo_estacion&op=equals&value=01&page=2&size=10')
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual(data['row_count'], 20)
                self.assertEqual(data['columns'][0]['mean'], 9.5)
                self.assertEqual(data['columns'][0]['maximum'], 19)
                self.assertEqual(data['excluded_columns'], ['codigo_estacion'])
                self.assertEqual(client.get('/api/tables/treated-test/statistics?q=absent').get_json()['row_count'], 0)
                self.assertEqual(client.get('/api/tables/treated-test/statistics?column=unknown').status_code, 400)
