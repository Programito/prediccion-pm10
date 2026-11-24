import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from tfm_data.mappers.pm10_forecast import PM10ForecastMapper
from tfm_data.evaluation.coverage_audit import audit_rows, build_audit
from explorer.server import app


class CoverageAuditTest(unittest.TestCase):
    def fixture(self):
        daily = pd.DataFrame(dict(fecha=pd.date_range("2023-12-01", "2024-12-31")))
        daily["codigo_estacion"], daily["NOMBRE"], daily["pm10_valido"] = "01", "Example", 10.0
        daily.loc[daily.fecha.eq("2024-01-04"), "pm10_valido"] = np.nan
        daily.loc[daily.fecha.between("2024-01-09", "2024-01-11"), "pm10_valido"] = 40.0
        return daily, PM10ForecastMapper().transform(daily)

    def test_one_missing_day_excludes_target_and_fourteen_later_predictions(self):
        daily, supervised = self.fixture()
        rows = audit_rows(supervised, daily)
        data = build_audit(rows)
        summary = data["groups"][0]
        self.assertEqual(summary["calendar"], 366)
        self.assertEqual(summary["unknownTarget"], 1)
        self.assertEqual(summary["observedExcluded"], 14)
        self.assertEqual(summary["evaluated"], 351)
        self.assertEqual(sum(summary["reasons"].values()), 366)
        self.assertEqual(summary["reasons"]["historial_14d"], 7)
        for row in rows.itertuples():
            for day in filter(None, row.fechas_historial_ausentes.split("|")):
                self.assertLess(pd.Timestamp(day), row.fecha_objetivo)
        feature = next(row for row in data["features"] if row["station"] == "todas" and row["month"] == 0 and row["feature"] == "media_14_dias")
        self.assertEqual(feature["missingWithTarget"], 14)
        self.assertEqual(feature["soleMissingWithTarget"], 7)

    def test_elevated_observations_are_counted_even_when_not_evaluated(self):
        daily, supervised = self.fixture()
        data = build_audit(audit_rows(supervised, daily))
        self.assertEqual(data["groups"][0]["elevatedObserved"], 3)
        self.assertEqual(data["groups"][0]["elevatedExcluded"], 3)
        episode = data["episodes"][0]
        self.assertEqual((episode["start"], episode["end"], episode["excludedDays"]), ("2024-01-09", "2024-01-11", 3))

    def test_rejects_mismatched_targets_or_evaluation_flags(self):
        daily, supervised = self.fixture()
        supervised.loc[supervised.fecha_objetivo.eq("2024-01-01"), "pm10_objetivo"] = 99
        with self.assertRaises(ValueError):
            audit_rows(supervised, daily)
        supervised = PM10ForecastMapper().transform(daily)
        supervised.loc[supervised.fecha_objetivo.eq("2024-01-01"), "fila_utilizable"] = False
        with self.assertRaises(ValueError):
            audit_rows(supervised, daily)

    def test_pagination_filters_before_slicing_and_rejects_invalid_parameters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "output/experiments/barcelona/coverage_audit/detalle.csv"
            path.parent.mkdir(parents=True)
            pd.DataFrame([dict(codigo_estacion="01", mes=2, evaluada=False, fecha_objetivo=f"2024-02-{day:02}") for day in range(1, 16)] +
                         [dict(codigo_estacion="02", mes=1, evaluada=True, fecha_objetivo="2024-01-01")]).to_csv(path, index=False)
            metadata = {"groups": [{"station": "todas"}, {"station": "01"}, {"station": "02"}]}
            with patch("explorer.server.ROOT", root), patch("explorer.server.regional_coverage", return_value=metadata):
                client = app.test_client()
                response = client.get("/api/experiments/barcelona/coverage/rows?station=01&month=2&page=2&size=10")
                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertEqual((data["total"], len(data["rows"]), data["hasNext"]), (15, 5, False))
                self.assertEqual(data["rows"][0]["fecha_objetivo"], "2024-02-11")
                for query in ["page=0", "month=13", "size=999", "page=a", "status=unknown", "station=03"]:
                    self.assertEqual(client.get("/api/experiments/barcelona/coverage/rows?" + query).status_code, 400)
