import unittest

import numpy as np
import pandas as pd

from tfm_data.evaluation.initial_health_comparison import HistoricalHealthRidge, create_lagged_features, evaluate


class TestComparacionInicial(unittest.TestCase):
    def base(self):
        return pd.DataFrame([{
            "codigo_provincia": f"{p:02d}", "territorio": str(p), "anio": a,
            "tasa_altas_por_100000": 1000 + p * 50 + (a - 2017) * 10,
            "media_pm10_estaciones_fondo": 10 + p + (a - 2017),
            "poblacion_total": 100000 + p * 1000, "proporcion_65_mas": .2,
            "proporcion_80_mas": .05, "proporcion_0_14": .15,
        } for p in [1, 2, 3] for a in range(2017, 2025)])

    def test_retardos_no_saltan_un_anio_ausente(self):
        base = self.base()
        base = base.loc[~(base.codigo_provincia.eq("01") & base.anio.eq(2020))]
        lagged = create_lagged_features(base)
        self.assertFalse((lagged.codigo_provincia.eq("01") & lagged.anio.eq(2021)).any())
        self.assertTrue(lagged.anio_variables.eq(lagged.anio - 1).all())

    def test_cambiar_objetivo_prueba_no_cambia_sus_predicciones(self):
        original = self.base()
        alterado = original.copy()
        alterado.loc[alterado.anio.eq(2023), "tasa_altas_por_100000"] = 99999
        antes, _ = evaluate(create_lagged_features(original), "prueba", (2023,))
        despues, _ = evaluate(create_lagged_features(alterado), "prueba", (2023,))
        np.testing.assert_allclose(antes.prediccion, despues.prediccion)
        self.assertTrue(antes.ultimo_anio_entrenamiento.eq(2022).all())

    def test_intercepto_no_se_penaliza_y_no_modifica_entrada(self):
        x = np.zeros((3, 2))
        copia = x.copy()
        model = HistoricalHealthRidge(alpha=100).fit(x, np.array([10., 10., 10.]))
        np.testing.assert_allclose(model.predict(np.zeros((1, 2))), [10.])
        np.testing.assert_array_equal(x, copia)
