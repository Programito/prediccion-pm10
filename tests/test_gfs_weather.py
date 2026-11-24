import unittest

from tfm_data.mappers.gfs_weather import GridValue, map_daily_weather


class GFSWeatherTest(unittest.TestCase):
    def daily(self, u=3.0, v=-4.0, start=0.0, end=0.0):
        values = {"wind_u": u, "wind_v": v, "rain_start": start, "rain_end": end}
        return map_daily_weather({field: GridValue(40.5, 356.25, value) for field, value in values.items()})

    def test_missing_accumulation_stays_null_and_valid_zero_stays_zero(self):
        missing = self.daily(end=None)
        self.assertIsNone(missing["precipitacion_diaria_mm"])
        self.assertEqual(missing["estado_precipitacion"], "ausente_grib")
        self.assertEqual(missing["viento_10m_mediodia_ms"], 5.0)
        self.assertEqual(self.daily()["precipitacion_diaria_mm"], 0.0)

    def test_inconsistent_and_non_finite_values_stay_null(self):
        row = self.daily(u=float("inf"), start=3.0, end=1.0)
        self.assertIsNone(row["viento_10m_mediodia_ms"])
        self.assertEqual(row["estado_viento"], "no_finito")
        self.assertIsNone(row["precipitacion_diaria_mm"])
        self.assertEqual(row["estado_precipitacion"], "acumulado_incoherente")

    def test_small_negative_is_flagged_and_large_finite_values_are_kept(self):
        row = self.daily(u=-100.0, start=1.0, end=0.995)
        self.assertGreater(row["viento_10m_mediodia_ms"], 100.0)
        self.assertEqual(row["precipitacion_diaria_mm"], 0.0)
        self.assertEqual(row["estado_precipitacion"], "ajuste_tolerancia")
        self.assertEqual(self.daily(end=300.0)["precipitacion_diaria_mm"], 300.0)
