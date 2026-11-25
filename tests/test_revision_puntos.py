import unittest

import pandas as pd

from pm10_data.evaluation.station_review import propose_treatment, review_sampling_points


class TestRevisionPuntos(unittest.TestCase):
    def ejemplo(self, fin=None):
        point = "01022001_10_47"
        low_coverage = pd.DataFrame({"punto_muestreo": [point], "codigo_estacion": ["01022001"], "anio": [2024],
                              "tecnica": ["47"], "meses_sin_mediciones_validas": [11], "cobertura_anual": [1 / 366]})
        meses = pd.DataFrame({"punto_muestreo": [point] * 12, "anio": [2024] * 12, "mes": range(1, 13),
                              "periodo": [f"2024-{m:02d}" for m in range(1, 13)], "dias_validos": [1] + [0] * 11})
        dias = pd.DataFrame({"punto_muestreo": [point], "fecha": [pd.Timestamp("2024-01-01")], "estado": ["valida"],
                             "archivo_origen": ["original.zip"], "miembro_zip": ["PM10.csv"]})
        meta = pd.DataFrame({"COD_LOCAL": [1022001], "FECHA_INI": ["2000-01-01"], "FECHA_FIN": [fin],
                             "N_RED": ["Red"], "N_PROVINCIA": ["Álava"], "N_MUNICIPIO": ["Elciego"]})
        return low_coverage, meses, dias, meta

    def test_manual_requiere_plan_y_no_exclusion_por_porcentaje(self):
        motivo, tratamiento = propose_treatment("M", 3, False)
        self.assertEqual(motivo, "revisar_plan_muestreo_manual")
        self.assertIn("Conservar", tratamiento)

    def test_baja_ultimo_dia_no_recorta_anio(self):
        result = review_sampling_points(*self.ejemplo("2024-12-31"), 2024)
        self.assertTrue(result.baja_estacion_durante_anio.iloc[0])
        self.assertFalse(result.intervalo_estacion_recorta_anio.iloc[0])
        self.assertFalse(result.causa_ausencias_confirmada.iloc[0])
        self.assertEqual(result.racha_max_dias_sin_medida_valida.iloc[0], 365)
        self.assertFalse(result.excluir_automaticamente.iloc[0])

    def test_baja_intermedia_se_marca_sin_cambiar_cobertura(self):
        result = review_sampling_points(*self.ejemplo("2024-06-30"), 2024)
        self.assertTrue(result.intervalo_estacion_recorta_anio.iloc[0])
        self.assertEqual(result.motivo_revision.iloc[0], "revisar_intervalo_declarado_estacion")
        self.assertEqual(result.cobertura_anual.iloc[0], 1 / 366)

    def test_sin_baja_no_inventa_causa_y_rechaza_meses_incompletos(self):
        args = self.ejemplo()
        result = review_sampling_points(*args, 2024)
        self.assertTrue(pd.isna(result.fecha_fin_estacion.iloc[0]))
        with self.assertRaisesRegex(ValueError, "doce meses"):
            review_sampling_points(args[0], args[1].iloc[:11], args[2], args[3], 2024)


if __name__ == "__main__":
    unittest.main()
