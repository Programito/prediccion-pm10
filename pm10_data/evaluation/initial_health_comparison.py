"""Comparación temporal retrospectiva, sin atribución causal ni despliegue."""

from pathlib import Path
from pm10_data.config import PROJECT_ROOT
import json

import numpy as np
import pandas as pd

from pm10_data.evaluation.provincial_prototype import aggregate_provinces


DEMOGRAPHIC_FEATURES = ["log_poblacion_previa", "proporcion_65_mas_previa", "proporcion_80_mas_previa", "proporcion_0_14_previa"]
FEATURES = ["tasa_previa"] + DEMOGRAPHIC_FEATURES


class HistoricalHealthRidge:
    """Ridge con variables estandarizadas solo con entrenamiento, sin penalizar intercepto."""

    def __init__(self, alpha: float = 10.0):
        if alpha <= 0:
            raise ValueError("alpha debe ser positivo.")
        self.alpha = alpha

    def fit(self, x: np.ndarray, y: np.ndarray):
        x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("Hay valores ausentes o no finitos en entrenamiento.")
        self.media = x.mean(axis=0)
        self.escala = x.std(axis=0)
        self.escala[self.escala == 0] = 1
        z = (x - self.media) / self.escala
        self.intercepto = float(y.mean())
        self.coeficientes = np.linalg.solve(z.T @ z + self.alpha * np.eye(z.shape[1]), z.T @ (y - self.intercepto))
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.intercepto + ((np.asarray(x, dtype=float) - self.media) / self.escala) @ self.coeficientes


def create_lagged_features(panel: pd.DataFrame) -> pd.DataFrame:
    """y(t) se compara con salud, demografía y aire de t-1, nunca de t."""
    if panel.duplicated(["codigo_provincia", "anio"]).any():
        raise ValueError("Claves provinciales duplicadas antes de crear retardos.")
    df = panel.sort_values(["codigo_provincia", "anio"]).copy()
    if df.poblacion_total.le(0).any():
        raise ValueError("La población debe ser positiva.")
    groups = df.groupby("codigo_provincia")
    df["anio_variables"] = groups.anio.shift(1)
    df["tasa_previa"] = groups.tasa_altas_por_100000.shift(1)
    df["pm10_previo"] = groups.media_pm10_estaciones_fondo.shift(1)
    df["log_poblacion_previa"] = np.log(groups.poblacion_total.shift(1).astype(float))
    for field in ["proporcion_65_mas", "proporcion_80_mas", "proporcion_0_14"]:
        df[f"{field}_previa"] = groups[field].shift(1)
    # Si hay un salto, el último registro no es el año anterior.
    consecutivos = df.anio_variables.eq(df.anio - 1)
    df = df.loc[consecutivos].copy()
    df["variacion_tasa"] = df.tasa_altas_por_100000 - df.tasa_previa
    return df


def evaluate(lagged: pd.DataFrame, scenario: str, anios_prueba=(2023, 2024)) -> tuple[pd.DataFrame, pd.DataFrame]:
    predictions, coefficients = [], []
    for anio in anios_prueba:
        training = lagged.loc[lagged.anio.lt(anio)].copy()
        test = lagged.loc[lagged.anio.eq(anio)].copy()
        columns = FEATURES + ["pm10_previo", "variacion_tasa", "tasa_altas_por_100000"]
        if training.empty or test.empty or training[columns].isna().any().any() or test[columns].isna().any().any():
            raise ValueError("Entrenamiento o prueba incompletos; no imputar resultados sanitarios.")
        if training.anio.max() >= test.anio.min():
            raise ValueError("La prueba debe ser posterior a todo el entrenamiento.")
        base = test.tasa_previa.to_numpy(dtype=float)
        models = {"persistencia": base}
        for name, fields in [("ridge_demografia", FEATURES), ("ridge_demografia_pm10", FEATURES + ["pm10_previo"])]:
            # Predecimos la variación sobre la referencia; alpha=10 fijado antes de evaluar.
            model = HistoricalHealthRidge(alpha=10).fit(training[fields].to_numpy(dtype=float), training.variacion_tasa.to_numpy(dtype=float))
            models[name] = base + model.predict(test[fields].to_numpy(dtype=float))
            for field, valor in zip(fields, model.coeficientes):
                coefficients.append({"escenario": scenario, "anio_prueba": anio, "modelo": name,
                                     "variable": field, "coeficiente_estandarizado": float(valor), "intercepto_variacion": model.intercepto})
        for name, values in models.items():
            output = test[["codigo_provincia", "territorio", "anio", "anio_variables", "tasa_altas_por_100000", "tasa_previa"]].copy()
            output["escenario"] = scenario
            output["modelo"] = name
            output["prediccion"] = values
            output["n_filas_entrenamiento"] = len(training)
            output["ultimo_anio_entrenamiento"] = int(training.anio.max())
            output["error_absoluto"] = (output.prediccion - output.tasa_altas_por_100000).abs()
            output["error_cuadrado"] = (output.prediccion - output.tasa_altas_por_100000) ** 2
            predictions.append(output)
    return pd.concat(predictions, ignore_index=True), pd.DataFrame(coefficients)


def main():
    root = PROJECT_ROOT
    historico = root / "data/interim/provincial_feasibility/history"
    destination = root / "data/interim/initial_comparison"
    destination.mkdir(parents=True, exist_ok=True)
    tipos = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "tecnica"]}
    panel = pd.read_csv(historico / "panel_red_constante.csv", dtype=tipos)
    demo = pd.read_csv(root / "data/interim/demographics/demografia_provincial_2017_2024.csv", dtype=tipos)
    panel = panel.merge(demo, on=["codigo_provincia", "anio"], how="left", validate="one_to_one")
    if panel.poblacion_total.isna().any():
        raise ValueError("Falta demografía en el panel.")
    candidatos = pd.read_csv(historico / "puntos_red_constante.csv", dtype=tipos)
    alerts = pd.read_csv(historico / "revision_coordenadas_red_constante.csv", dtype=tipos)
    excluded = set(alerts.loc[alerts.revisar_diferencia_mayor_100m | alerts.tipo_area_cambia, "punto_muestreo"])
    sin_alertas = candidatos.loc[~candidatos.punto_muestreo.isin(excluded)].copy()
    aggregated = aggregate_provinces(sin_alertas)
    limpia = panel.drop(columns=[c for c in aggregated.columns if c not in ["codigo_provincia", "anio"]]).merge(
        aggregated, on=["codigo_provincia", "anio"], how="left", validate="one_to_one")
    # Recalcular indicadores del cruce para no conservar banderas de la red anterior.
    limpia["hay_indicador_pm10"] = limpia.media_pm10_estaciones_fondo.notna()
    limpia["cruce_ambiental"] = np.where(limpia.hay_indicador_pm10, "both", "left_only")
    predictions, coefficients = [], []
    for scenario, table in [("red_constante", panel), ("sin_alertas_ubicacion_area", limpia)]:
        table = table.loc[table.media_pm10_estaciones_fondo.notna()].copy()
        lagged = create_lagged_features(table)
        lagged.to_csv(destination / f"tabla_retardos_{scenario}.csv", index=False, encoding="utf-8-sig")
        pred, coef = evaluate(lagged, scenario)
        predictions.append(pred)
        coefficients.append(coef)
    pred = pd.concat(predictions, ignore_index=True)
    metrics = pred.groupby(["escenario", "modelo"], as_index=False).agg(n=("error_absoluto", "size"),
        mae=("error_absoluto", "mean"), mse=("error_cuadrado", "mean"))
    metrics["rmse"] = np.sqrt(metrics.mse)
    anual = pred.groupby(["escenario", "anio", "modelo"], as_index=False).agg(n=("error_absoluto", "size"),
        mae=("error_absoluto", "mean"), mse=("error_cuadrado", "mean"))
    anual["rmse"] = np.sqrt(anual.mse)
    for name, df in [("predicciones", pred), ("metricas", metrics), ("metricas_por_anio", anual),
                       ("coeficientes", pd.concat(coefficients, ignore_index=True)), ("panel_con_demografia", panel)]:
        df.to_csv(destination / f"{name}.csv", index=False, encoding="utf-8-sig")
    summary = {"anios_evaluados": [2023, 2024], "alpha_fijado": 10,
               "puntos_excluidos_solo_en_sensibilidad": len(excluded),
               "metricas": metrics.drop(columns="mse").to_dict("records"),
               "advertencia": "Comparación retrospectiva con datos revisados y selección de red en todo el periodo. No reproduce disponibilidad histórica de publicaciones ni demuestra causalidad o funcionamiento operativo.",
               "regla_evaluacion": "Cada año se ajusta con años anteriores; datos de t-1 para predecir t. Para 2024 se incluye 2023 en el entrenamiento como evaluación de origen móvil, sin ajustar hiperparámetros."}
    (destination / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(metrics.to_string(index=False))
    print(anual.to_string(index=False))
    print(f"Puntos con alertas excluidos solo en sensibilidad: {len(excluded)}")


if __name__ == "__main__":
    main()
