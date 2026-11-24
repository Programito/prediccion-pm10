"""Export the evaluated station-days as a static data file for the demo."""

import csv
from datetime import date, timedelta
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIONS = {"28079060": "Tres Olivos", "28080003": "Majadahonda", "28133002": "San Martín de Valdeiglesias"}


def read_csv(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def build_cases(rows, year):
    cases = {}
    for row in rows:
        key = (row["codigo_estacion"], row["fecha_objetivo"])
        if key[0] not in STATIONS or date.fromisoformat(key[1]).year != year:
            raise ValueError(f"Fecha o estación inesperada: {key}")
        today, observed = float(row["pm10_t"]), float(row["pm10_objetivo"])
        case = cases.setdefault(key, dict(station=key[0], date=key[1], previous=today, observed=observed, results={}))
        model = row["modelo"]
        if (case["previous"], case["observed"]) != (today, observed) or model in case["results"]:
            raise ValueError(f"Predicciones incongruentes o repetidas en {key}")
        if year == 2024:
            case["results"][model] = float(row["prediccion"])
        else:
            probability = row["probabilidad_elevado"]
            case["results"][model] = {"alert": row["aviso"] == "1", "probability": float(probability) if probability else None}
    expected = {"ridge", "persistencia"} if year == 2024 else {"logistica_con_meteo", "logistica_sin_meteo", "persistencia"}
    if not cases or any(set(case["results"]) != expected for case in cases.values()):
        raise ValueError(f"Faltan resultados de los modelos de {year}.")
    return cases


def main():
    historical = build_cases(read_csv("output/pm10_final_2024/predicciones_regresion.csv"), 2024)
    recent = build_cases(read_csv("output/pm10_weather_test_2025/predicciones_2025.csv"), 2025)
    weather = {(row["codigo_estacion"], row["fecha_objetivo"]): row for row in read_csv(
        "data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv")}
    protocol = json.loads((ROOT / "docs/reference/pm10_weather_test_2025.json").read_text(encoding="utf-8"))
    for key, case in recent.items():
        row = weather[key]
        previous_day = date.fromisoformat(key[1]) - timedelta(days=1)
        if row["inicio_ciclo_utc"] != f"{previous_day.isoformat()}T12:00:00Z":
            raise ValueError(f"Ciclo GFS inesperado en {key}")
        case["weather"] = dict(wind=float(row["viento_10m_mediodia_ms"]), rain=float(row["precipitacion_diaria_mm"]),
                               cycle=row["inicio_ciclo_utc"])
    data = {"stations": STATIONS, "eventThreshold": protocol["umbral_pm10_ug_m3"], "probabilityCuts": protocol["cortes"],
            "regression": [historical[key] for key in sorted(historical)], "classification": [recent[key] for key in sorted(recent)]}
    target = ROOT / "demo/data.js"
    target.write_text("globalThis.PM10_DEMO = " + json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + ";\n",
                      encoding="utf-8")
    print(f"Preparadas {len(historical)} fechas de regresión y {len(recent)} de clasificación.")


if __name__ == "__main__":
    main()
