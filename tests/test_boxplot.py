import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from explorer.descriptive_statistics import summarize_numeric_columns, summarize_boxplot_groups
from explorer.server import app


class BoxPlotTest(unittest.TestCase):
    def test_whiskers_use_observations_inside_fences_and_preserve_maximum(self):
        row = summarize_numeric_columns([{'x': x} for x in [0, 1, 2, 3, 4, 100]], ['x'], include_boxplot=True)['columns'][0]
        self.assertEqual((row['p25'], row['median'], row['p75']), (1.25, 2.5, 3.75))
        self.assertEqual(row['maximum'], 100)
        self.assertEqual(row['boxplot'], dict(lower_fence=-2.5, upper_fence=7.5, whisker_low=0, whisker_high=4, outliers=[100]))

    def test_empty_singleton_constant_and_repeated_fliers(self):
        for values in [[], [7], [7, 7]]:
            row = summarize_numeric_columns([{'x': x} for x in values], ['x'], include_boxplot=True)['columns'][0]
            self.assertEqual(row['boxplot']['outliers'], [])
            self.assertEqual(row['boxplot']['whisker_low'], 7 if values else None)
            json.dumps(row, allow_nan=False)
        row = summarize_numeric_columns([{'x': x} for x in [*range(20), 100, 100]], ['x'], include_boxplot=True)['columns'][0]
        self.assertEqual(row['boxplot']['outliers'], [100, 100])

    def test_groups_preserve_zero_missing_counts_and_codes(self):
        rows = [{'station':'01','name':'First','x':0}, {'station':'01','name':'First','x':None}, {'station':'02','name':'Second','x':100}]
        groups = summarize_boxplot_groups(iter(rows), 'x', group_by='station', label_by='name')
        self.assertEqual([row['group'] for row in groups], ['01','02'])
        self.assertEqual((groups[0]['row_count'],groups[0]['valid_count'],groups[0]['missing_count']), (2,1,1))
        self.assertEqual(groups[0]['median'],0)
        self.assertEqual(groups[1]['median'],100)
        self.assertEqual(summarize_boxplot_groups([{'station':0,'x':1}], 'x', group_by='station')[0]['group'], '0')

    def test_api_filters_all_rows_before_grouping_and_rejects_identifiers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'values.csv'
            path.write_text('codigo_estacion,NOMBRE,x\n'+''.join('01,First,'+str(x)+'\n' for x in range(20))+'02,Second,999\n',encoding='utf-8')
            table = dict(id='treated-test',local='values.csv',reader='csv',delimiter=',',columns=[
                dict(name='codigo_estacion',type='Código',isKey=True),dict(name='NOMBRE',type='Texto'),dict(name='x',type='Decimal')])
            with patch('explorer.server.find_table',return_value=table),patch('explorer.server.get_treated_tables',return_value={'treated-test':table}),patch('explorer.server.path_for',return_value=path):
                client=app.test_client()
                response=client.get('/api/tables/treated-test/boxplot?field=x&group_by=codigo_estacion&column=codigo_estacion&op=equals&value=01&page=2')
                self.assertEqual(response.status_code,200)
                result=response.get_json()
                self.assertEqual(result['row_count'],20)
                self.assertEqual(len(result['groups']),1)
                self.assertEqual(result['groups'][0]['median'],9.5)
                self.assertEqual(result['groups'][0]['maximum'],19)
                self.assertEqual(client.get('/api/tables/treated-test/boxplot?field=codigo_estacion').status_code,400)
                self.assertEqual(client.get('/api/tables/treated-test/boxplot?field=x&group_by=NOMBRE').status_code,400)
