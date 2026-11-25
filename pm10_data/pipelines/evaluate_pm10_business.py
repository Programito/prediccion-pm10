"""Translate fixed 2025 onset predictions into explicitly hypothetical costs."""

import csv
from datetime import datetime, timezone
import hashlib
import json

from pm10_data.config import PROJECT_ROOT


MODELS = ("persistencia", "logistica_sin_meteo", "logistica_con_meteo")
SCENARIOS = (
    ("costes_iguales", 1, 1),
    ("omision_doble", 1, 2),
    ("omision_quintuple", 1, 5),
)


def onset_counts(rows):
    """Require matched model samples and count station-day onset decisions."""
    samples = {model: {} for model in MODELS}
    for row in rows:
        model = row["modelo"]
        if model not in samples:
            raise ValueError(f"Modelo inesperado: {model}")
        key = (row["codigo_estacion"], row["fecha_objetivo"])
        if key in samples[model]:
            raise ValueError(f"Predicción repetida: {model}, {key}")
        if row["observado"] not in {"0", "1"} or row["aviso"] not in {"0", "1"}:
            raise ValueError(f"Etiqueta o aviso inválido: {model}, {key}")
        if row["contexto"] not in {"hoy_no_elevado", "hoy_elevado"}:
            raise ValueError(f"Contexto desconocido: {key}")
        samples[model][key] = row
    baseline = samples["persistencia"]
    if not baseline:
        raise ValueError("No hay predicciones para evaluar.")
    for model, predictions in samples.items():
        if predictions.keys() != baseline.keys():
            raise ValueError(f"Fechas y estaciones incompatibles: {model}")
        for key, row in predictions.items():
            reference = baseline[key]
            if (row["contexto"], row["observado"]) != (reference["contexto"], reference["observado"]):
                raise ValueError(f"Contexto o etiqueta incompatible: {model}, {key}")

    counts = []
    for model, predictions in samples.items():
        eligible = [row for row in predictions.values() if row["contexto"] == "hoy_no_elevado"]
        if not eligible:
            raise ValueError("No hay casos evaluables de inicio.")
        counts.append({
            "modelo": model,
            "casos": len(eligible),
            "inicios_reales": sum(row["observado"] == "1" for row in eligible),
            "inicios_detectados": sum(row["observado"] == row["aviso"] == "1" for row in eligible),
            "inicios_omitidos": sum(row["observado"] == "1" and row["aviso"] == "0" for row in eligible),
            "falsas_alarmas": sum(row["observado"] == "0" and row["aviso"] == "1" for row in eligible),
            "avisos": sum(row["aviso"] == "1" for row in eligible),
        })
    return counts


def scenario_costs(counts):
    results = []
    baseline = next(row for row in counts if row["modelo"] == "persistencia")
    for scenario, false_alarm_cost, missed_onset_cost in SCENARIOS:
        reference_cost = baseline["falsas_alarmas"] * false_alarm_cost + baseline["inicios_omitidos"] * missed_onset_cost
        for row in counts:
            cost = row["falsas_alarmas"] * false_alarm_cost + row["inicios_omitidos"] * missed_onset_cost
            results.append({
                "escenario": scenario,
                **row,
                "coste_falsa_alarma_unidades": false_alarm_cost,
                "coste_inicio_omitido_unidades": missed_onset_cost,
                "coste_simulado_unidades": cost,
                "diferencia_vs_persistencia_unidades": cost - reference_cost,
            })
    return results


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    source = PROJECT_ROOT / "output/pm10_weather_test_2025/predicciones_2025.csv"
    with source.open(encoding="utf-8-sig", newline="") as stream:
        counts = onset_counts(list(csv.DictReader(stream)))
    output = PROJECT_ROOT / "output/pm10_business_2025"
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "resumen_avisos.csv", counts)
    write_csv(output / "escenarios_coste.csv", scenario_costs(counts))
    configuration = {
        "generado_utc": datetime.now(timezone.utc).isoformat(),
        "fuente": source.relative_to(PROJECT_ROOT).as_posix(),
        "sha256_fuente": hashlib.sha256(source.read_bytes()).hexdigest(),
        "contexto": "hoy_no_elevado",
        "unidad": "estacion_fecha_objetivo",
        "unidad_coste": "coste_de_una_falsa_alarma",
        "naturaleza": "escenarios_hipoteticos_sin_costes_empresariales_observados",
        "formula": "falsas_alarmas * coste_falsa_alarma + inicios_omitidos * coste_inicio_omitido",
        "coste_acierto_unidades": 0,
        "escenarios": [
            {"id": name, "coste_falsa_alarma_unidades": false_alarm, "coste_inicio_omitido_unidades": missed}
            for name, false_alarm, missed in SCENARIOS
        ],
        "modelos_y_cortes": "conservados_de_la_prueba_2025",
    }
    (output / "configuracion.json").write_text(json.dumps(configuration, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Escenarios guardados en {output}")


if __name__ == "__main__":
    main()
