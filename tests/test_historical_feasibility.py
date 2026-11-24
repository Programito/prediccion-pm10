import unittest

import pandas as pd

from tfm_data.evaluation.historical_feasibility import audit_coordinates, summarize_territorial_continuity, select_constant_points
from tfm_data.mappers.air import combine_daily_measurements


class TestViabilidadHistorica(unittest.TestCase):
    def test_coordenadas_marca_diferencia_sin_confirmar_traslado(self):
        data = pd.DataFrame({"punto_muestreo": ["p1", "p1"], "LATITUD_G": [0., 1.],
                              "LONGITUD_G": [0., 0.], "TIPO_AREA": ["RURAL", "RURAL"]})
        result = audit_coordinates(data).iloc[0]
        self.assertAlmostEqual(result.distancia_maxima_coordenadas_m, 111194.93, places=1)
        self.assertTrue(result.revisar_diferencia_mayor_100m)
        self.assertFalse(result.tipo_area_cambia)

    def test_diario_oficial_vacio_conserva_derivados_horarios(self):
        derived = pd.DataFrame({"codigo_provincia": ["01"], "codigo_estacion": ["01001001"],
                                 "punto_muestreo": ["01001001_10_49"], "magnitud": ["10"],
                                 "fecha": [pd.Timestamp("2024-01-01")], "concentracion": [10.],
                                 "estado": ["valida"], "n_horas_validas": [24]})
        result, comparison = combine_daily_measurements(derived.iloc[:0].copy(), derived)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.origen_diario.iloc[0], "derivado_horario")
        self.assertEqual(len(comparison), 0)

    def test_constante_exige_mismo_punto_todos_anios(self):
        data = pd.DataFrame({"anio": [2023, 2024, 2023, 2024], "punto_muestreo": ["p1", "p1", "p2", "p3"]})
        result = select_constant_points(data, (2023, 2024))
        self.assertEqual(set(result.punto_muestreo), {"p1"})
        with self.assertRaisesRegex(ValueError, "repetidos"):
            select_constant_points(pd.concat([data, data.iloc[:1]]), (2023, 2024))

    def test_continuidad_no_rellena_ausencias_con_cero(self):
        data = pd.DataFrame({"codigo_provincia": ["01", "01"], "territorio": ["Álava"] * 2,
                              "anio": [2023, 2024], "media_pm10_estaciones_fondo": [0., None], "n_estaciones": [1, 0]})
        result = summarize_territorial_continuity(data, (2023, 2024)).iloc[0]
        self.assertEqual(result.anios_con_indicador, 1)
        self.assertFalse(result.todos_los_anios)
        self.assertEqual(result.anios_sin_indicador, "2024")


if __name__ == "__main__":
    unittest.main()
