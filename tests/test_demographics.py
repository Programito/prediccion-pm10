import unittest

import pandas as pd

from tfm_data.mappers.demographics import INEDemographicsMapper


class TestDemografia(unittest.TestCase):
    def base(self):
        edades = [f"{i} año" if i == 1 else f"{i} años" for i in range(100)] + ["100 y más años"]
        # 101 edades disjuntas con una persona en cada una; el subtotal 85+ se solapa.
        return pd.DataFrame({"Edad simple": ["Todas las edades", "85 y más años"] + edades,
                             "Provincias": ["01 Araba/Álava"] * 103, "Sexo": ["Total"] * 103,
                             "Periodo": ["1 de enero de 2024"] * 103, "Total": ["101", "16"] + ["1"] * 101}, dtype="string")

    def test_no_suma_subtotal_y_conserva_fecha_y_codigo(self):
        original = self.base()
        antes = original.copy(deep=True)
        result = INEDemographicsMapper().transform(original).iloc[0]
        self.assertEqual(result.poblacion_total, 101)
        self.assertEqual(result.poblacion_65_mas, 36)
        self.assertEqual(result.poblacion_80_mas, 21)
        self.assertEqual(result.codigo_provincia, "01")
        self.assertEqual(result.fecha_referencia_poblacion, pd.Timestamp("2024-01-01"))
        pd.testing.assert_frame_equal(original, antes)

    def test_rechaza_edades_incompletas_y_total_incoherente(self):
        with self.assertRaisesRegex(ValueError, "Faltan edades"):
            INEDemographicsMapper().transform(self.base().iloc[:-1])
        original = self.base()
        original.loc[0, "Total"] = "102"
        with self.assertRaisesRegex(ValueError, "suma de edades"):
            INEDemographicsMapper().transform(original)

