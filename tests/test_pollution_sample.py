import unittest

import pandas as pd

from tfm_data.pipelines.pollution_sample import select_sample


class TestMuestraContaminacion(unittest.TestCase):
    def test_elige_cobertura_minima_y_aparta_alertas(self):
        rows = []
        for point, tipo, cobertura in [("u1", "URBANA", .9), ("u2", "URBANA", .95),
                                        ("s", "SUBURBANA", .9), ("r", "RURAL", .9)]:
            rows.extend({"codigo_provincia": "28", "punto_muestreo": point, "codigo_estacion": point,
                          "NOMBRE": point, "TIPO_AREA": tipo, "anio": a, "cobertura_anual": cobertura}
                         for a in range(2017, 2025))
        data = pd.DataFrame(rows)
        alerts = pd.DataFrame({"punto_muestreo": ["u2"], "revisar_diferencia_mayor_100m": [True], "tipo_area_cambia": [False]})
        muestra = select_sample(data, alerts)
        self.assertEqual(set(muestra.punto_muestreo), {"u1", "s", "r"})
