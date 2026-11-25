import unittest

import pandas as pd

from pm10_data.evaluation.provincial_prototype import aggregate_provinces, select_sampling_points


class TestPrototipoProvincial(unittest.TestCase):
    def base(self):
        return pd.DataFrame({"anio": [2024, 2024, 2024], "codigo_provincia": ["01"] * 3,
                             "codigo_estacion": ["01001001", "01001002", "01001003"],
                             "punto_muestreo": ["p1", "p2", "p3"], "tecnica": ["49", "49", "M"],
                             "TIPO_ESTACION": ["FONDO"] * 3, "TIPO_AREA": ["URBANA", "RURAL", "SUBURBANA"],
                             "cumple_criterio_exploratorio": [True] * 3,
                             "media_anual_analisis": [10., 20., 100.], "cobertura_anual": [.8, .9, .95]})

    def test_manual_no_entra_y_peso_igual_por_estacion(self):
        selection = select_sampling_points(self.base(), {"p1", "p2", "p3"})
        result = aggregate_provinces(selection)
        self.assertEqual(result.n_estaciones.iloc[0], 2)
        self.assertEqual(result.media_pm10_estaciones_fondo.iloc[0], 15)
        self.assertEqual(result.n_urbanas.iloc[0], 1)
        self.assertEqual(result.n_rurales.iloc[0], 1)

    def test_no_duplicar_peso_de_una_estacion(self):
        selection = select_sampling_points(self.base(), {"p1", "p2"})
        selection.loc[1, "codigo_estacion"] = "01001001"
        with self.assertRaisesRegex(ValueError, "varios puntos"):
            aggregate_provinces(selection)

    def test_exige_horas_fondo_y_cobertura(self):
        base = self.base()
        base.loc[0, "TIPO_ESTACION"] = "TRAFICO"
        base.loc[1, "cumple_criterio_exploratorio"] = False
        selection = select_sampling_points(base, {"p1", "p2"})
        self.assertFalse(selection.seleccion_provisional.any())


if __name__ == "__main__":
    unittest.main()
