import unittest

import numpy as np
import pandas as pd

from tfm_data.models.factory import create_models
from tfm_data.evaluation.pm10_regression import evaluate_models, split_dataset
from tfm_data.mappers.pm10_forecast import NUMERIC_FEATURES


class TestEntrenamientoRegresionPM10(unittest.TestCase):
    def test_aportaciones_ridge_reconstruyen_prediccion_y_escalado(self):
        training, validation = split_dataset(self.table())
        model = create_models()["ridge"].fit(training, training.pm10_objetivo)
        explanation = model.explain_predictions(validation)
        expected = model.predict(validation)
        np.testing.assert_allclose(explanation["intercept"] + explanation["contributions"].sum(axis=1), expected)
        np.testing.assert_allclose(explanation["predictions"], expected)
        preprocessor = model.pipeline.named_steps["preprocessor"]
        scaler = preprocessor.named_transformers_["numeric"]
        index = explanation["names"].index("numeric__pm10_t")
        expected_scaled = (validation.pm10_t.to_numpy() - scaler.mean_[index]) / scaler.scale_[index]
        np.testing.assert_allclose(explanation["transformed"][:, index], expected_scaled)
        np.testing.assert_allclose(explanation["contributions"], explanation["transformed"] * explanation["coefficients"])

    def table(self):
        rows = []
        for station in ["01", "02"]:
            for i, (fecha, particion) in enumerate([
                ("2022-12-27", "entrenamiento"), ("2022-12-28", "entrenamiento"),
                ("2023-01-01", "validacion"), ("2024-01-01", "prueba_reservada"),
            ]):
                row = {c: float(i + 10) for c in NUMERIC_FEATURES}
                row.update(codigo_estacion=station, NOMBRE=station, particion=particion,
                            fecha_objetivo=pd.Timestamp(fecha), fecha_ultima_observacion=pd.Timestamp(fecha) - pd.Timedelta(days=1),
                            pm10_objetivo=float(i + 11))
                rows.append(row)
        return pd.DataFrame(rows)

    def test_prueba_reservada_no_entra_en_ajuste_ni_validacion(self):
        table = self.table()
        table.loc[table.particion.eq("prueba_reservada"), NUMERIC_FEATURES + ["pm10_objetivo"]] = np.nan
        training, validation = split_dataset(table)
        self.assertEqual(len(training), 4)
        self.assertEqual(len(validation), 2)
        self.assertTrue(training.fecha_objetivo.dt.year.eq(2022).all())
        self.assertTrue(validation.fecha_objetivo.dt.year.eq(2023).all())

    def test_cambiar_objetivo_validacion_no_modifica_predicciones(self):
        training, validation = split_dataset(self.table())
        a = evaluate_models(training, validation, {"ridge": create_models()["ridge"]})
        alterada = validation.copy()
        alterada["pm10_objetivo"] = 99999.
        b = evaluate_models(training, alterada, {"ridge": create_models()["ridge"]})
        np.testing.assert_allclose(a.prediccion, b.prediccion)

    def test_escalado_solo_con_entrenamiento_y_fechas_coherentes(self):
        training, validation = split_dataset(self.table())
        validation["pm10_t"] = 10000.
        model = create_models()["ridge"]
        evaluate_models(training, validation, {"ridge": model})
        escalador = model.pipeline.named_steps["preprocessor"].named_transformers_["numeric"]
        np.testing.assert_allclose(escalador.mean_, training[NUMERIC_FEATURES].mean().to_numpy())
        table = self.table()
        table.loc[table.particion.eq("validacion"), "fecha_objetivo"] = pd.Timestamp("2024-01-02")
        with self.assertRaisesRegex(ValueError, "partición"):
            split_dataset(table)


if __name__ == "__main__":
    unittest.main()
