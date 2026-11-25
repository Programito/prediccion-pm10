import unittest

import pandas as pd

from pm10_data.mappers.air import (AirContext, AirQualityMapper, AirQualityValidator,
                           combine_daily_measurements, summarize_year, summarize_hours)


class TestCalidadAire(unittest.TestCase):
    def setUp(self):
        self.contexto = AirContext(2024, "10", "PM10", "µg/m3", "original.zip", "PM10.csv")
        self.mapeador = AirQualityMapper()

    def original(self, frequency="diaria", mes=2, dia=29):
        row = {"PROVINCIA": "1", "MUNICIPIO": "22", "ESTACION": "1", "MAGNITUD": "10",
                "PUNTO_MUESTREO": "01022001_10_47", "ANNO": "2024", "MES": str(mes)}
        prefix, n = ("D", 31) if frequency == "diaria" else ("H", 24)
        row.update({f"{prefix}{i:02d}": None for i in range(1, n + 1)})
        if frequency == "horaria":
            row["DIA"] = str(dia)
        return pd.DataFrame([row], dtype="string")

    def test_bisiesto_y_ausentes_no_son_cero(self):
        original = self.original()
        original.loc[0, "D29"] = "0"
        result = self.mapeador.transform(original, self.contexto, "diaria")
        self.assertEqual(len(result), 29)
        self.assertEqual(result.estado.eq("ausente").sum(), 28)
        self.assertEqual(result.concentracion.dropna().iloc[0], 0)
        self.assertEqual(result.codigo_estacion.iloc[0], "01022001")

    def test_fecha_imposible_con_valor_falla(self):
        original = self.original()
        original.loc[0, "D30"] = "2"
        with self.assertRaisesRegex(ValueError, "día imposible"):
            self.mapeador.transform(original, self.contexto, "diaria")

    def test_h24_cambia_de_anio_sin_cambiar_dia_muestreo(self):
        original = self.original("horaria", mes=12, dia=31)
        original.loc[0, "H24"] = "12.5"
        result = self.mapeador.transform(original, self.contexto, "horaria")
        ultimo = result.loc[result.hora_fin_original.eq(24)].iloc[0]
        self.assertEqual(ultimo.fecha, pd.Timestamp("2024-12-31"))
        self.assertEqual(ultimo.fin_periodo_utc, pd.Timestamp("2025-01-01", tz="UTC"))
        AirQualityValidator().validate(result, "horaria")

    def test_negativos_se_conservan_y_no_cuentan(self):
        original = self.original()
        original.loc[0, "D01"] = "-1"
        result = self.mapeador.transform(original, self.contexto, "diaria")
        self.assertEqual(result.concentracion.iloc[0], -1)
        self.assertEqual(result.estado.iloc[0], "negativa_pendiente_revision")
        self.assertEqual(summarize_year(result, 2024).dias_validos.iloc[0], 0)

    def test_umbral_horario_y_no_mutacion(self):
        original = self.original("horaria")
        for i in range(1, 19):
            original.loc[0, f"H{i:02d}"] = "10"
        copia = original.copy(deep=True)
        result = self.mapeador.transform(original, self.contexto, "horaria")
        pd.testing.assert_frame_equal(original, copia)
        self.assertEqual(summarize_hours(result).concentracion.iloc[0], 10)
        self.assertTrue(pd.isna(summarize_hours(result, 19).concentracion.iloc[0]))

    def test_prioridad_y_distintos_puntos_no_se_fusionan(self):
        diario = self.original(mes=1)
        diario.loc[0, "D01"] = "20"
        horario = self.original("horaria", mes=1, dia=1)
        for i in range(1, 25):
            horario.loc[0, f"H{i:02d}"] = "10"
        d = self.mapeador.transform(diario, self.contexto, "diaria")
        h = summarize_hours(self.mapeador.transform(horario, self.contexto, "horaria"))
        combined, comparison = combine_daily_measurements(d, h)
        primero = combined.loc[combined.fecha.eq(pd.Timestamp("2024-01-01"))]
        self.assertEqual(primero.concentracion.iloc[0], 20)
        self.assertEqual(comparison.diferencia_absoluta.iloc[0], 10)
        # Otro equipo de la misma estación debe conservar una serie separada.
        h["punto_muestreo"] = "01022001_10_M"
        h["tecnica"] = "M"
        combined, comparison = combine_daily_measurements(d, h)
        self.assertEqual(len(comparison), 0)
        self.assertEqual(combined.punto_muestreo.nunique(), 2)

    def test_rellena_diario_ausente_con_horario_valido(self):
        d = self.mapeador.transform(self.original(mes=1), self.contexto, "diaria")
        original = self.original("horaria", mes=1, dia=1)
        for i in range(1, 25):
            original.loc[0, f"H{i:02d}"] = "10"
        h = summarize_hours(self.mapeador.transform(original, self.contexto, "horaria"))
        result, _ = combine_daily_measurements(d, h)
        row = result.loc[result.fecha.eq(pd.Timestamp("2024-01-01"))].iloc[0]
        self.assertEqual(row.origen_diario, "derivado_horario")
        self.assertEqual(row.concentracion, 10)

    def test_duplicados_y_componentes_incorrectos_fallan(self):
        original = self.original()
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            self.mapeador.transform(pd.concat([original, original]), self.contexto, "diaria")
        original.loc[0, "MES"] = "13"
        with self.assertRaisesRegex(ValueError, "Mes imposible"):
            self.mapeador.transform(original, self.contexto, "diaria")

    def test_cobertura_anual_no_oculta_datos_insuficientes(self):
        original = self.original()
        original.loc[0, "D01"] = "10"
        dias = self.mapeador.transform(original, self.contexto, "diaria")
        anual = summarize_year(dias, 2024)
        self.assertEqual(anual.dias_del_anio.iloc[0], 366)
        self.assertAlmostEqual(anual.cobertura_anual.iloc[0], 1 / 366)
        self.assertEqual(anual.media_dias_disponibles.iloc[0], 10)
        self.assertTrue(pd.isna(anual.media_anual_analisis.iloc[0]))


if __name__ == "__main__":
    unittest.main()
