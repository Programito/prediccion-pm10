import unittest

import numpy as np
import pandas as pd

from pm10_data.evaluation.pm10_errors import pair_predictions, grouped_errors, date_sensitivity


class TestPairedPm10Errors(unittest.TestCase):
    def predictions(self):
        rows = []
        for station in ("01", "02"):
            for day, ridge, baseline in ((1, 20, 25), (2, 20, 21), (3, 22, 20), (4, 22, 20)):
                for model, prediction in (("ridge", ridge), ("persistencia", baseline)):
                    rows.append({
                        "codigo_estacion": station, "NOMBRE": station,
                        "fecha_objetivo": f"2024-01-{day:02}", "pm10_objetivo": 20.,
                        "modelo": model, "prediccion": float(prediction),
                    })
        return pd.DataFrame(rows)

    def test_metricas_pareadas_y_particiones_conservan_los_casos(self):
        paired = pair_predictions(self.predictions())
        groups = grouped_errors(paired, 27)
        annual = groups.loc[groups.station.eq("todas") & groups.month.eq(0) & groups.level.eq("todos")].iloc[0]
        self.assertEqual(annual.n, 8)
        self.assertEqual(annual.mae_ridge, 1.)
        self.assertEqual(annual.mae_persistencia, 1.5)
        self.assertEqual(annual.delta_mae, -.5)
        self.assertEqual(groups.loc[groups.station.eq("todas") & groups.month.gt(0) & groups.level.eq("todos"), "n"].sum(), 8)
        self.assertFalse(groups.level.eq("elevado").any())

    def test_sensibilidad_retira_fecha_completa_en_ambas_estaciones(self):
        paired = pair_predictions(self.predictions())
        _, sensitivity = date_sensitivity(paired, count=1)
        favorable = sensitivity.loc[sensitivity.scenario.eq("sin_fechas_mas_favorables")].iloc[0]
        adverse = sensitivity.loc[sensitivity.scenario.eq("sin_fechas_mas_desfavorables")].iloc[0]
        self.assertEqual(favorable.excluded_dates, "2024-01-01")
        self.assertEqual(adverse.excluded_dates, "2024-01-03")
        self.assertEqual(favorable.n, 6)
        self.assertEqual(adverse.n, 6)
        self.assertAlmostEqual(favorable.delta_mae, 1.)

    def test_rechaza_filas_duplicadas_ausentes_y_observados_distintos(self):
        original = self.predictions()
        mismatch = original.copy()
        mismatch.loc[0, "pm10_objetivo"] = 21
        for invalid in (pd.concat([original, original.iloc[[0]]]), original.iloc[1:], mismatch):
            with self.subTest(rows=len(invalid)):
                with self.assertRaises(ValueError):
                    pair_predictions(invalid)

    def test_rechaza_prediccion_no_finita_y_otra_ventana_temporal(self):
        for field, value in (("prediccion", np.nan), ("fecha_objetivo", "2025-01-01")):
            invalid = self.predictions()
            invalid.loc[0, field] = value
            with self.assertRaises(ValueError):
                pair_predictions(invalid)


if __name__ == "__main__":
    unittest.main()
