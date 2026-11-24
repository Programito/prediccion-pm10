"""API isolation and calendar checks for the two chart territories (no ML runtime)."""

import csv
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from explorer import server


class ChartTerritoriesTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.root_patch = patch('explorer.server.ROOT', self.root)
        self.root_patch.start()
        self.client = server.app.test_client()
        for territory, codes, value in [('madrid', server.PM10_STATIONS, 12), ('barcelona', server.BARCELONA_STATIONS, 44)]:
            daily, predictions = server.EXPERIMENT_FILES[territory]
            self.csv(daily, [dict(codigo_estacion=code, fecha='2024-02-01', pm10_valido=value) for code in codes] +
                     [dict(codigo_estacion=codes[0], fecha='2024-02-02', pm10_valido='')])
            self.csv(predictions, [dict(codigo_estacion=code, fecha_objetivo='2024-02-01', pm10_objetivo=value,
                                       modelo=model, prediccion=value-1) for code in codes for model in ['ridge', 'persistencia']])
            metadata = ('data/interim/experiments/barcelona/estaciones.csv' if territory == 'barcelona' else
                        'data/interim/provincial_feasibility/history/seleccion_estaciones_pm10_2024.csv')
            lat, lon = ('latitud', 'longitud') if territory == 'barcelona' else ('LATITUD_G', 'LONGITUD_G')
            self.csv(metadata, [dict(codigo_estacion=code, NOMBRE=territory, **{lat:41 if territory=='barcelona' else 40, lon:2 if territory=='barcelona' else -3}) for code in codes])
            metric = ('output/experiments/barcelona/prueba_2024/metricas.csv' if territory=='barcelona' else
                      'output/pm10_final_2024/metricas_regresion.csv')
            self.csv(metric, [dict(tramo='todos', modelo='ridge', mae=value, n=3)])
        self.csv('output/pm10_weather_test_2025/metricas_por_contexto.csv',
                 [dict(contexto='hoy_no_elevado', modelo='persistencia', vp=0, fp=0, positivos=2, n=10)])
        self.csv('output/experiments/barcelona/prueba_2024/errores.csv',
                 [dict(station='08184006', name='Barcelona', month=0, level='todos', n=1, mae_ridge=44, delta_mae=-1)])
        self.write_json('output/pm10_error_analysis/analisis.json', dict(threshold=27, groups=[dict(station='28079060')], sensitivity=[]))
        for path, code in [('output/pm10_bootstrap/analisis.json','28079060'),
                           ('output/experiments/barcelona/prueba_2024/bootstrap.json','08184006')]:
            self.write_json(path,dict(primaryBlockDays=14,rows=[dict(station=code)]))
        self.clear_caches()

    def tearDown(self):
        self.clear_caches()
        self.root_patch.stop()
        self.directory.cleanup()

    def clear_caches(self):
        for fn in [server.chart_daily_values, server.chart_test_predictions, server.chart_model_metrics,
                   server.error_analysis, server.bootstrap_analysis]:
            fn.cache_clear()

    def csv(self, relative, rows):
        path=self.root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)

    def write_json(self, relative, value):
        path=self.root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value),encoding='utf-8')

    def test_maps_use_own_stations_coordinates_and_observations(self):
        for territory, codes, expected in [('madrid',server.PM10_STATIONS,12),('barcelona',server.BARCELONA_STATIONS,44)]:
            response=self.client.get(f'/api/charts/map?territory={territory}&date=2024-02-01')
            self.assertEqual(response.status_code,200)
            data=response.get_json()
            self.assertEqual([s['code'] for s in data['stations']],list(codes))
            self.assertEqual(data['stations'][0]['value'],expected)
            self.assertEqual(data['stations'][0]['longitude'],2 if territory=='barcelona' else -3)
        # The legacy URL still means Madrid.
        self.assertEqual(self.client.get('/api/charts/map?date=2024-02-01').get_json()['territory'],'madrid')

    def test_observations_keep_leap_calendar_missing_values_and_zero(self):
        response=self.client.get('/api/charts/pm10?territory=barcelona&station=08184006&month=2024-02')
        rows=response.get_json()['days']
        self.assertEqual(len(rows),29)
        self.assertEqual(rows[0]['value'],44)
        self.assertIsNone(rows[1]['value'])
        self.assertIsNone(rows[-1]['value'])
        server.chart_daily_values.cache_clear()
        self.csv(server.EXPERIMENT_FILES['barcelona'][0],[dict(codigo_estacion='08184006',fecha='2024-02-01',pm10_valido=0)])
        self.assertEqual(self.client.get('/api/charts/pm10?territory=barcelona&month=2024-02').get_json()['days'][0]['value'],0)

    def test_predictions_preserve_own_frozen_values_and_calendar_gaps(self):
        for territory, expected in [('madrid',12),('barcelona',44)]:
            response=self.client.get('/api/charts/predictions?territory='+territory)
            data=response.get_json()
            self.assertEqual(len(data['days']),366)
            focal=next(d for d in data['days'] if d['date']=='2024-02-01')
            self.assertEqual(focal['observed'],expected)
            self.assertEqual(focal['ridge'],expected-1)
            self.assertEqual(data['days'][0],{'date':'2024-01-01'})
            self.assertEqual(len(data['episodes']),1 if territory=='barcelona' else 0)

    def test_metrics_errors_and_intervals_do_not_mix_territories(self):
        for territory, expected, station in [('madrid',12,'28079060'),('barcelona',44,'08184006')]:
            metrics=self.client.get('/api/charts/metrics?territory='+territory).get_json()
            self.assertEqual(metrics['regression'][0]['mae'],expected)
            self.assertEqual(len(metrics['onsets']),1 if territory=='madrid' else 0)
            errors=self.client.get('/api/charts/errors?territory='+territory).get_json()
            self.assertEqual(errors['groups'][0]['station'],station)
            intervals=self.client.get('/api/charts/uncertainty?territory='+territory).get_json()
            self.assertEqual(intervals['rows'][0]['station'],station)

    def test_unknown_regions_cross_region_stations_and_unavailable_periods_are_rejected(self):
        for view in ['map','pm10','predictions','metrics','errors','uncertainty','explanations']:
            self.assertEqual(self.client.get('/api/charts/'+view+'?territory=unknown').status_code,400)
        for view in ['pm10','predictions']:
            self.assertEqual(self.client.get('/api/charts/'+view+'?territory=barcelona&station=28079060').status_code,400)
        self.assertEqual(self.client.get('/api/charts/map?territory=barcelona&date=2025-01-01').status_code,400)
        self.assertEqual(self.client.get('/api/charts/pm10?territory=barcelona&month=2025-01').status_code,400)
        self.assertEqual(self.client.get('/api/charts/explanations?territory=barcelona').status_code,400)
