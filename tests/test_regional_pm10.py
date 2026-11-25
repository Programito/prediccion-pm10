import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch

import pandas as pd

from pm10_data.mappers.air import AirQualityReader
from pm10_data.pipelines.barcelona_experiment import select_candidates, longest_missing
from explorer.server import app


class RegionalPM10Test(unittest.TestCase):
    def test_selection_uses_coverage_and_excludes_unstable_points(self):
        rows = []
        for i, coverage in enumerate([.99, .98, .97, .96, .95]):
            for year in range(2017, 2025):
                rows.append(dict(codigo_provincia="08", codigo_estacion=str(i), punto_muestreo=str(i), anio=year,
                                 NOMBRE="Station", TIPO_AREA="URBANA", cobertura_anual=coverage, LATITUD_G=41, LONGITUD_G=2))
        alerts = pd.DataFrame([dict(punto_muestreo="0", revisar_diferencia_mayor_100m=True, tipo_area_cambia=False)])
        result = select_candidates(pd.DataFrame(rows), alerts)
        self.assertEqual(set(result.loc[result.seleccionada, "codigo_estacion"]), {"1", "2", "3"})
        shuffled = select_candidates(pd.DataFrame(rows).sample(frac=1, random_state=1), alerts)
        self.assertEqual(set(shuffled.loc[shuffled.seleccionada, "codigo_estacion"]), {"1", "2", "3"})

    def test_chunk_reader_preserves_codes_and_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.zip"
            with ZipFile(path, "w") as archive:
                archive.writestr("PM10.csv", "PUNTO_MUESTREO;D01\n08184006_10_47;0\n28079060_10_47;99\n08184006_10_47;\n")
            selected = AirQualityReader().read_points(path, "PM10.csv", {"08184006_10_47"})
            self.assertEqual(len(selected), 2)
            self.assertEqual(selected.iloc[0].D01, "0")
            self.assertTrue(pd.isna(selected.iloc[1].D01))
            self.assertTrue(AirQualityReader().read_points(path, "PM10.csv", {"absent"}).empty)

    def test_missing_runs_do_not_replace_missing_with_zero(self):
        self.assertEqual(longest_missing([None, None, 0, None, 4]), 2)
        self.assertEqual(longest_missing([0, 1]), 0)

    def test_series_keeps_observation_when_prediction_is_unavailable(self):
        summary = {"experiments": [{"id": "barcelona", "stations": [{"code": "08184006"}]}]}
        observed = {("08184006", "2024-02-01"): 42.0, ("08184006", "2024-02-02"): None}
        with patch("explorer.server.experiment_comparison", return_value=summary), patch("explorer.server.experiment_series_values", return_value=(observed, {})):
            client = app.test_client()
            response = client.get("/api/experiments/barcelona/series?station=08184006&month=2024-02")
            self.assertEqual(response.status_code, 200)
            rows = response.get_json()["days"]
            self.assertEqual(len(rows), 29)
            self.assertEqual(rows[0]["observed"], 42)
            self.assertFalse(rows[0]["evaluated"])
            self.assertNotIn("ridge", rows[0])
            self.assertNotIn("observed", rows[1])
            self.assertEqual(client.get("/api/experiments/barcelona/series?station=28079060").status_code, 400)
            self.assertEqual(client.get("/api/experiments/barcelona/series?month=2025-01").status_code, 400)
            self.assertEqual(client.get("/api/experiments/unknown/series").status_code, 404)
