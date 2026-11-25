import unittest

import pandas as pd

from pm10_data.mappers.air import AirContext, AirQualityMapper
from pm10_data.evaluation.air_coverage import AirCoverageAuditor


class TestAuditoriaCobertura(unittest.TestCase):
    def table(self):
        row = {"PROVINCIA": "1", "MUNICIPIO": "22", "ESTACION": "1", "MAGNITUD": "10",
                "PUNTO_MUESTREO": "01022001_10_47", "ANNO": "2024", "MES": "2"}
        row.update({f"D{i:02d}": None for i in range(1, 32)})
        row.update({"D01": "0", "D02": "-1"})
        context = AirContext(2024, "10", "PM10", "µg/m3", "original.zip", "PM10.csv")
        table = AirQualityMapper().transform(pd.DataFrame([row], dtype="string"), context, "diaria")
        table["origen_diario"] = "diario_oficial"
        return table

    def test_incluye_meses_sin_filas_y_febrero_bisiesto(self):
        monthly = AirCoverageAuditor().audit(self.table(), 2024)
        self.assertEqual(len(monthly), 12)
        febrero = monthly.loc[monthly.mes.eq(2)].iloc[0]
        enero = monthly.loc[monthly.mes.eq(1)].iloc[0]
        self.assertEqual(febrero.dias_del_mes, 29)
        self.assertEqual(febrero.dias_validos, 1)  # El cero es una medida válida.
        self.assertEqual(febrero.dias_negativos, 1)
        self.assertEqual(febrero.dias_ausentes, 27)
        self.assertEqual(enero.dias_sin_registro, 31)
        self.assertEqual(enero.dias_ausentes, 0)
        self.assertTrue(enero.mes_sin_mediciones_validas)
        self.assertTrue(pd.isna(enero.media_dias_validos))
        self.assertEqual(monthly.dias_del_mes.sum(), 366)

    def test_distingue_horas_insuficientes_de_ausentes(self):
        table = self.table()
        table.loc[2, "estado"] = "cobertura_horaria_insuficiente"
        result = AirCoverageAuditor().audit(table, 2024)
        febrero = result.loc[result.mes.eq(2)].iloc[0]
        self.assertEqual(febrero.dias_horas_insuficientes, 1)
        self.assertEqual(febrero.dias_ausentes, 26)

    def test_rechaza_duplicados_y_anios_incorrectos(self):
        table = self.table()
        with self.assertRaisesRegex(ValueError, "repetidas"):
            AirCoverageAuditor().audit(pd.concat([table, table]), 2024)
        with self.assertRaisesRegex(ValueError, "único año"):
            AirCoverageAuditor().audit(table, 2023)


if __name__ == "__main__":
    unittest.main()
