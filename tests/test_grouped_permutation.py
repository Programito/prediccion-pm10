import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from explorer.server import app
from tfm_data.mappers.pm10_forecast import NUMERIC_FEATURES
from tfm_data.evaluation.grouped_permutation import circular_orders, shift_columns, station_relabelings, grouped_permutation, FEATURES


class GroupedPermutationTest(unittest.TestCase):
    def fixture(self):
        rows=[]
        for station in ['01','02','03']:
            for day in range(10):
                row={field:0.0 for field in NUMERIC_FEATURES}
                row.update(codigo_estacion=station,fecha_objetivo=pd.Timestamp('2023-01-01')+pd.Timedelta(days=day),
                           fecha_ultima_observacion=pd.Timestamp('2022-12-31')+pd.Timedelta(days=day),
                           pm10_t=float(day+1),pm10_t_menos_1=float(day+101),pm10_objetivo=float(day+1))
                rows.append(row)
        return pd.DataFrame(rows)

    def test_circular_orders_are_reproducible_and_preserve_station_sequences(self):
        stations=self.fixture().codigo_estacion.to_numpy()
        orders,offsets=circular_orders(stations,4,2,42)
        again,_=circular_orders(stations,4,2,42)
        np.testing.assert_array_equal(orders,again)
        for order in orders:
            np.testing.assert_array_equal(np.sort(order),np.arange(len(stations)))
            np.testing.assert_array_equal(stations[order],stations)
            self.assertFalse((order==np.arange(len(stations))).any())
            for code in set(stations):
                values=order[np.flatnonzero(stations==code)]
                np.testing.assert_array_equal(np.diff(values)%10,np.ones(9))
        self.assertEqual(len(offsets),12)
        with self.assertRaises(ValueError):circular_orders(['01']*4,2,2,42)

    def test_group_columns_move_together_without_changing_other_inputs(self):
        features=self.fixture()[FEATURES]
        copy=features.copy(deep=True)
        order,_=circular_orders(features.codigo_estacion,2,2,42)
        changed=shift_columns(features,['pm10_t','pm10_t_menos_1'],order[0])
        np.testing.assert_allclose(changed.pm10_t_menos_1-changed.pm10_t,100)
        pd.testing.assert_frame_equal(features,copy)
        pd.testing.assert_series_equal(changed.codigo_estacion,features.codigo_estacion)
        with self.assertRaises(ValueError):shift_columns(features,['pm10_objetivo'],order[0])
        with self.assertRaises(ValueError):shift_columns(features,['pm10_t'],np.zeros(len(features),dtype=int))

    def test_station_mappings_are_stable_nonidentity_cycles(self):
        maps=station_relabelings(['01','01','02','03'])
        self.assertEqual(len(maps),2)
        for mapping in maps:
            self.assertEqual(set(mapping),set(mapping.values()))
            self.assertTrue(all(code!=value for code,value in mapping.items()))

    def test_importance_detects_used_group_and_keeps_baseline_cases(self):
        data=self.fixture()
        original=data.copy(deep=True)
        def predict(frame):
            self.assertEqual(list(frame.columns),FEATURES)
            return frame.pm10_t.to_numpy()
        result=grouped_permutation(predict,data,repeats=4,minimum_shift=2,seed=42)
        self.assertEqual((result['n'],result['baselineMae']),(30,0))
        rows={row['group']:row for row in result['rows']}
        self.assertGreater(rows['recent']['mean'],0)
        self.assertEqual(rows['windows']['mean'],0)
        self.assertEqual(rows['calendar']['mean'],0)
        self.assertEqual(rows['station']['mean'],0)
        self.assertEqual(rows['station']['repetitions'],2)
        pd.testing.assert_frame_equal(data,original)
        two_stations=grouped_permutation(predict,data.loc[data.codigo_estacion.ne('03')],repeats=2,minimum_shift=2,seed=42)
        station=next(row for row in two_stations['rows'] if row['group']=='station')
        self.assertIsNone(station['std'])
        json.dumps(two_stations['rows'],allow_nan=False)

    def test_future_or_duplicate_validation_rows_are_rejected(self):
        data=self.fixture()
        data.loc[0,'fecha_objetivo']=pd.Timestamp('2024-01-01')
        with self.assertRaises(ValueError):grouped_permutation(lambda frame:frame.pm10_t,data,repeats=2,minimum_shift=2)
        data=self.fixture()
        with self.assertRaises(ValueError):grouped_permutation(lambda frame:frame.pm10_t,pd.concat([data,data.head(1)]),repeats=2,minimum_shift=2)

    def test_api_serves_saved_diagnostic_without_loading_models(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('explorer.server.ROOT',root):
                client=app.test_client()
                self.assertEqual(client.get('/api/experiments/grouped-permutation').status_code,404)
                path=root/'output/experiments/grouped_permutation/resumen.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'year':2023,'originalArtifactsUnchanged':True}),encoding='utf-8')
                response=client.get('/api/experiments/grouped-permutation')
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.get_json()['year'],2023)
