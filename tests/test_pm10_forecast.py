import unittest

import numpy as np
import pandas as pd

from pm10_data.mappers.pm10_forecast import PM10ForecastMapper, NUMERIC_FEATURES, label_elevated_pm10


class TestPrediccionPM10(unittest.TestCase):
    def serie(self, inicio="2022-12-01", periodos=40):
        return pd.DataFrame({"codigo_estacion": ["01"] * periodos,
                             "fecha": pd.date_range(inicio, periods=periodos),
                             "pm10_valido": np.arange(periodos, dtype=float)})

    def test_objetivo_es_manana_y_particion_sigue_objetivo(self):
        result = PM10ForecastMapper().transform(self.serie())
        row = result.loc[result.fecha.eq(pd.Timestamp("2022-12-31"))].iloc[0]
        self.assertEqual(row.particion, "validacion")
        self.assertEqual(row.pm10_t, 30)
        self.assertEqual(row.pm10_objetivo, 31)
        self.assertEqual(row.pm10_t_menos_6, 24)
        self.assertEqual(row.emision_simulada_utc, pd.Timestamp("2023-01-01", tz="UTC"))

    def test_futuro_no_cambia_predictores_pasados(self):
        original = self.serie()
        alterado = original.copy()
        alterado.loc[alterado.fecha.gt(pd.Timestamp("2022-12-31")), "pm10_valido"] = 99999
        a = PM10ForecastMapper().transform(original)
        b = PM10ForecastMapper().transform(alterado)
        np.testing.assert_allclose(a.loc[a.fecha.le("2022-12-31"), NUMERIC_FEATURES],
                                   b.loc[b.fecha.le("2022-12-31"), NUMERIC_FEATURES], equal_nan=True)

    def test_umbral_no_usa_validacion_y_ausente_no_es_negativo(self):
        original = self.serie()
        a = PM10ForecastMapper().transform(original)
        _, threshold = label_elevated_pm10(a)
        original.loc[original.fecha.ge("2023-01-01"), "pm10_valido"] = 99999
        b, nuevo = label_elevated_pm10(PM10ForecastMapper().transform(original))
        self.assertEqual(threshold, nuevo)
        self.assertTrue(pd.isna(b.pm10_elevado_objetivo.iloc[-1]))
        self.assertFalse(b.fila_utilizable.iloc[-1])

    def test_calentamiento_y_ausencias_no_se_rellenan(self):
        original = self.serie()
        result = PM10ForecastMapper().transform(original)
        self.assertFalse(result.predictores_completos.iloc[:13].any())
        self.assertTrue(result.predictores_completos.iloc[13])
        original.loc[20, "pm10_valido"] = np.nan
        result = PM10ForecastMapper().transform(original)
        self.assertTrue(pd.isna(result.pm10_objetivo.iloc[19]))
        self.assertTrue(pd.isna(result.media_14_dias.iloc[25]))

    def test_estaciones_no_se_mezclan_y_rechaza_saltos(self):
        una = self.serie()
        otra = una.assign(codigo_estacion="02", pm10_valido=1000.)
        result = PM10ForecastMapper().transform(pd.concat([una, otra], ignore_index=True))
        segunda = result.loc[result.codigo_estacion.eq("02")]
        self.assertTrue(pd.isna(segunda.pm10_t_menos_1.iloc[0]))
        self.assertEqual(segunda.media_7_dias.iloc[6], 1000)
        with self.assertRaisesRegex(ValueError, "saltos"):
            PM10ForecastMapper().transform(una.drop(index=10))


if __name__ == "__main__":
    unittest.main()
