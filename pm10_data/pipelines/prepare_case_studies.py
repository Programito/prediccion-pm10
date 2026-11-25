"""Export compact, auditable defense cases from frozen predictions; no training."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from pm10_data.config import PROJECT_ROOT
from pm10_data.evaluation.case_studies import reconstruct, select_typical, validate_alerts
from pm10_data.evaluation.pm10_errors import pair_predictions


SOURCES = {
    "regression": "output/pm10_final_2024/predicciones_regresion.csv",
    "explanations": "output/pm10_explanations/explicaciones.json",
    "inputs": "data/interim/pm10_prediction/tabla_modelos_completa.csv",
    "daily2024": "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv",
    "daily2025": "output/pm10_weather_test_2025/pm10_diario_2025.csv",
    "alerts": "output/pm10_weather_test_2025/predicciones_2025.csv",
    "weather": "data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv",
    "protocol": "docs/reference/pm10_weather_test_2025.json",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = PROJECT_ROOT
    output = root / "output/case_studies"
    output.mkdir(parents=True, exist_ok=True)
    hashes = {path: digest(root / path) for path in SOURCES.values()}
    # Include all model files in the preservation check, without deserializing them.
    protected = {p.relative_to(root).as_posix(): digest(p) for p in (root / "models").rglob("*.joblib")}
    protected.update(hashes)
    tables = {key: pd.read_csv(root / path, dtype={"codigo_estacion": str})
              for key, path in SOURCES.items() if path.endswith(".csv")}
    explanations = json.loads((root / SOURCES["explanations"]).read_text(encoding="utf-8"))
    protocol = json.loads((root / SOURCES["protocol"]).read_text(encoding="utf-8"))
    paired = pair_predictions(tables["regression"])
    typical, selection = select_typical(paired)
    specs = [
        ("typical", "Una predicción habitual", str(typical.codigo_estacion), typical.fecha_objetivo.strftime("%Y-%m-%d")),
        ("peak", "El pico subestimado", "28079060", "2024-10-31"),
        ("onset", "Un comienzo detectado", "28079060", "2025-08-05"),
        ("false_alarm", "La falsa alarma de contraste", "28079060", "2025-02-22"),
    ]
    cases = []
    for case_id, title, station, day in specs:
        folder = output / case_id
        folder.mkdir(exist_ok=True)
        evidence = []

        def export(name, frame):
            path = folder / name
            frame.to_csv(path, index=False, encoding="utf-8-sig", date_format="%Y-%m-%d")
            evidence.append({"file": name, "format": "CSV UTF-8", "rows": len(frame),
                             "sha256": digest(path), "url": f"/api/case-studies/{case_id}/evidence/{name}"})

        focal = pd.Timestamp(day)
        regression = focal.year == 2024
        case = {"id": case_id, "title": title, "station": station, "name": "Tres Olivos",
                "date": day, "kind": "regression" if regression else "classification",
                "emission": f"{day}T00:00:00Z",
                "lastObservation": (focal - pd.Timedelta(days=1)).strftime("%Y-%m-%d")}
        if regression:
            rows = tables["regression"].loc[lambda t: t.codigo_estacion.eq(station) & t.fecha_objetivo.eq(day)]
            if len(rows) != 2:
                raise ValueError("Falta la pareja de regresión.")
            export("predicciones.csv", rows)
            observed = float(rows.pm10_objetivo.iloc[0])
            case["predictions"] = [{"model": row.modelo, "value": float(row.prediccion),
                                    "absoluteError": abs(float(row.prediccion) - observed)} for row in rows.itertuples()]
            explanation = next(c for c in explanations["cases"] if c["station"] == station and c["date"] == day)
            prediction = next(c["value"] for c in case["predictions"] if c["model"] == "ridge")
            case["rawPrediction"] = reconstruct(explanations["intercept"], explanation["contributions"], prediction)
            case["intercept"] = explanations["intercept"]
            case["contributions"] = [{"feature": f["name"], "coefficient": f["coefficient"],
                                       "transformed": value, "contribution": contribution}
                                      for f, value, contribution in zip(explanations["features"], explanation["transformed"], explanation["contributions"], strict=True)]
            export("aportes.csv", pd.DataFrame(case["contributions"]))
            inputs = tables["inputs"].loc[lambda t: t.codigo_estacion.eq(station) & t.fecha_objetivo.eq(day)]
            if len(inputs) != 1 or inputs.fecha_ultima_observacion.iloc[0] != case["lastObservation"]:
                raise ValueError("Los datos de entrada no son del día anterior.")
            export("entradas.csv", inputs)
            case["prior"] = float(inputs.pm10_t.iloc[0])
            case["inputs"] = explanation["inputs"]
        else:
            rows = tables["alerts"].loc[lambda t: t.codigo_estacion.eq(station) & t.fecha_objetivo.eq(day)]
            validate_alerts(rows, protocol["cortes"])
            export("avisos.csv", rows)
            observed = float(rows.pm10_objetivo.iloc[0])
            case["prior"] = float(rows.pm10_t.iloc[0])
            case["alerts"] = [{"model": row.modelo, "alert": bool(row.aviso),
                              "probability": None if pd.isna(row.probabilidad_elevado) else float(row.probabilidad_elevado),
                              "cut": protocol["cortes"].get(row.modelo)} for row in rows.itertuples()]
            weather = tables["weather"].loc[lambda t: t.codigo_estacion.eq(station) & t.fecha_objetivo.eq(day)]
            expected_cycle = (focal - pd.Timedelta(days=1)).strftime("%Y-%m-%dT12:00:00Z")
            if (len(weather) != 1 or weather.inicio_ciclo_utc.iloc[0] != expected_cycle
                    or weather.estado_viento.iloc[0] != "valido" or weather.estado_precipitacion.iloc[0] != "valido"):
                raise ValueError("El ciclo meteorológico no respeta el protocolo.")
            export("meteorologia.csv", weather)
            case["weather"] = weather.iloc[0].to_dict()
        case["observed"] = observed
        daily = tables["daily2024" if regression else "daily2025"]
        values = daily.loc[daily.codigo_estacion.eq(station)].set_index("fecha").pm10_valido
        days = []
        for date in pd.date_range(focal - pd.Timedelta(days=3), focal + pd.Timedelta(days=3)):
            date_string = date.strftime("%Y-%m-%d")
            value = values.get(date_string)
            item = {"date": date_string}
            if pd.notna(value):
                item["observed"] = float(value)
            if regression:
                matching = paired.loc[paired.codigo_estacion.eq(station) & paired.fecha_objetivo.eq(date)]
                if len(matching):
                    item.update(ridge=float(matching.prediccion_ridge.iloc[0]), persistencia=float(matching.prediccion_persistencia.iloc[0]))
            days.append(item)
        if next(d.get("observed") for d in days if d["date"] == day) != observed:
            if not abs(next(d.get("observed") for d in days if d["date"] == day) - observed) < 1e-9:
                raise ValueError("La observación diaria no coincide.")
        case["days"] = days
        export("contexto.csv", pd.DataFrame(days))
        case["evidence"] = evidence
        cases.append(case)
    for path, expected in protected.items():
        if digest(root / path) != expected:
            raise ValueError(f"Ha cambiado un original: {path}")
    onset_rows = tables["alerts"].loc[lambda t: t.pm10_t.le(27)]
    onset_summary = []
    for model, rows in onset_rows.groupby("modelo", sort=True):
        onset_summary.append({"model": model, "n": len(rows), "onsets": int(rows.observado.sum()),
                              "detected": int((rows.observado.eq(1) & rows.aviso.eq(1)).sum()),
                              "falseAlarms": int((rows.observado.eq(0) & rows.aviso.eq(1)).sum())})
    result = {"threshold": 27, "scope": "Madrid · ejemplos retrospectivos de pruebas ya conocidas",
              "selection": selection, "cases": cases,
              "onsets": onset_summary,
              "sources": [{"path": path, "format": Path(path).suffix[1:].upper(), "sha256": sha} for path, sha in hashes.items()],
              "originalArtifactsUnchanged": True,
              "protectedArtifacts": protected}
    (output / "resumen.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Exportados {len(cases)} casos sin entrenar ni modificar modelos.")


if __name__ == "__main__":
    main()
