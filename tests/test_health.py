"""Casos donde un error silencioso cambiaría la interpretación de los datos."""

import unittest

import pandas as pd

from tfm_data.mappers.health import (
    HealthContext, DIAGNOSIS_COLUMN, TERRITORY_COLUMN, INEHealthMapper,
    INEHealthValidator, parse_spanish_rate,
)


class TestMapeadorSanidad(unittest.TestCase):
    def setUp(self):
        self.mapeador = INEHealthMapper()
        self.contexto = HealthContext(2024, "INE ejemplo", "original.csv")

    def flat(self, name="MADRID, COMUNIDAD DE", tasa="1.268"):
        return pd.DataFrame({DIAGNOSIS_COLUMN: ["1007 Asma J45"], TERRITORY_COLUMN: [name], "Total": [tasa]}, dtype="string")

    def transform(self, df):
        return self.mapeador.transform(df, self.contexto, ("1007",))

    def test_miles_decimales_y_ausentes(self):
        result = parse_spanish_rate(pd.Series(["1.268", "1.234,5", "0", "..", None, " "]))
        self.assertEqual(result.iloc[:3].tolist(), [1268, 1234.5, 0])
        self.assertTrue(result.iloc[3:].isna().all())

    def test_rechaza_numero_ambiguo(self):
        with self.assertRaisesRegex(ValueError, "Formato de tasa"):
            parse_spanish_rate(pd.Series(["1.2"]))

    def test_madrid_es_territorio_provincial_sin_inventar_fecha(self):
        result = self.transform(self.flat())
        self.assertEqual(result.codigo_provincia.iloc[0], "28")
        self.assertEqual(result.nivel_geografico_original.iloc[0], "comunidad_autonoma")
        self.assertEqual(result.nivel_geografico.iloc[0], "provincia")
        self.assertEqual(result.anio.iloc[0], 2024)
        self.assertNotIn("fecha", result)

    def test_jerarquia_elige_provincia_y_no_ccaa(self):
        original = pd.DataFrame({DIAGNOSIS_COLUMN: ["1007 Asma J45"], "Total Nacional": ["Total Nacional"],
                                 "Comunidades y Ciudades Autónomas": ["01 Andalucía"],
                                 "Provincias": ["04 Almería"], "Total": ["39"]}, dtype="string")
        result = self.transform(original)
        self.assertEqual(result.codigo_provincia.iloc[0], "04")
        self.assertEqual(result.codigo_ccaa.iloc[0], "01")
        original.loc[0, "Provincias"] = "05 Almería"
        with self.assertRaisesRegex(ValueError, "códigos originales"):
            self.transform(original)

    def test_desconocido_no_se_convierte_en_dato_ausente(self):
        with self.assertRaisesRegex(ValueError, "sin correspondencia"):
            self.transform(self.flat(name="Provincia desconocida"))

    def test_no_modifica_original_y_mantiene_procedencia(self):
        original = self.flat()
        antes = original.copy(deep=True)
        result = self.transform(original)
        pd.testing.assert_frame_equal(original, antes)
        self.assertEqual(result.tasa_original.iloc[0], "1.268")
        self.assertEqual(result.archivo_origen.iloc[0], "original.csv")

    def test_no_fabrica_codigos_provinciales_para_agregados(self):
        for name in ["TOTAL NACIONAL", "ANDALUCÍA"]:
            result = self.transform(self.flat(name=name))
            self.assertTrue(result.codigo_provincia.isna().all())
            self.assertNotEqual(result.nivel_geografico.iloc[0], "provincia")

    def test_ceuta_melilla_y_codigos_con_cero(self):
        for name, codigo in [("Ceuta", "51"), ("Melilla", "52"), ("Araba/Álava", "01")]:
            self.assertEqual(self.transform(self.flat(name)).codigo_provincia.iloc[0], codigo)

    def test_rechaza_diagnostico_ausente_y_esquema_desconocido(self):
        with self.assertRaisesRegex(ValueError, "Faltan diagnósticos"):
            self.mapeador.transform(self.flat(), self.contexto)
        with self.assertRaisesRegex(ValueError, "Estructura geográfica"):
            self.transform(self.flat().drop(columns=[TERRITORY_COLUMN]))

    def test_validador_rechaza_duplicados(self):
        result = self.transform(self.flat())
        INEHealthValidator().validate(result)
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            INEHealthValidator().validate(pd.concat([result, result], ignore_index=True))


if __name__ == "__main__":
    unittest.main()
