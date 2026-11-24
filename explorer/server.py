"""Serve the React explorer and page through the local TFM source files."""

import csv
from calendar import monthrange
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from functools import lru_cache
from io import BytesIO, TextIOWrapper
from itertools import groupby, islice
import json
import os
from pathlib import Path
import re
import unicodedata
from zipfile import ZipFile

from flask import Flask, abort, jsonify, request, send_from_directory

from explorer.treated_tables import treated_catalog
from explorer.provenance import explain_value
from explorer.column_dictionary import enrich_columns
from explorer.descriptive_statistics import summarize_numeric_columns, numeric_measurement_columns, summarize_boxplot_groups


HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("TFM_DATA_ROOT", HERE.parent)).resolve()
REFERENCE = ROOT / "docs/reference"
DIST = HERE / "dist"
app = Flask(__name__, static_folder=None)
ARTICLES = {
    "fuentes": ("Fuentes, endpoints y formatos", "15_fuentes_endpoints_formatos.md"),
    "descargas": ("Inventario de descargas", "reference/source_endpoints.md"),
    "esquemas": ("Esquemas de los originales", "reference/source_schemas.md"),
    "transformaciones": ("Mapeadores y tablas", "16_trazabilidad_mappers_tablas.md"),
    "noaa": ("Previsiones NOAA GFS", "22_viabilidad_meteorologia_pm10.md"),
    "cruce": ("Cruce de PM10 y GFS", "23_cruce_pm10_meteorologia.md"),
    "eea": ("PM10 verificado de la EEA", "25_prueba_meteorologia_2025.md"),
    "explorador": ("Guía del explorador", "28_explorador_react.md"),
    "explicabilidad": ("Explicabilidad de los modelos", "31_explicabilidad_pm10.md"),
    "produccion": ("Propuesta conceptual de producción", "32_propuesta_produccion_pm10.md"),
    "errores": ("Errores por estación, mes y nivel", "35_analisis_errores_pm10.md"),
    "incertidumbre": ("Incertidumbre de la diferencia de MAE", "36_incertidumbre_pm10.md"),
    "siguientes_mejoras": ("Trabajo pendiente y preparación de la defensa", "37_siguientes_mejoras.md"),
    "experimentos": ("Experimentos de Madrid y Barcelona", "38_experimentos_madrid_barcelona.md"),
    "cobertura_territorial": ("Auditoría de días excluidos", "39_auditoria_cobertura_territorial.md"),
    "estadisticas": ("Estadísticas descriptivas de tablas", "40_estadisticas_descriptivas.md"),
    "ventanas": ("Comparación de ventanas en 2023", "41_comparacion_ventanas_pm10.md"),
    "permutacion": ("Importancia por permutación agrupada", "42_importancia_agrupada_pm10.md"),
    "casos": ("Casos de estudio para la defensa", "43_casos_de_estudio_defensa.md"),
    "proyecciones": ("PCA y LDA en validación", "44_pca_lda_pm10.md"),
    "graficos_territoriales": ("Gráficos por territorio", "45_graficos_territoriales.md"),
}

PM10_STATIONS = ("28079060", "28080003", "28133002")
BARCELONA_STATIONS = ("08184006", "08202001", "08263001")
PM10_THRESHOLD = 27


def chart_territory():
    territory = request.args.get("territory", "madrid")
    if territory not in {"madrid", "barcelona"}:
        abort(400, "Selecciona Madrid o Barcelona provincia.")
    return territory


def chart_stations(territory):
    return BARCELONA_STATIONS if territory == "barcelona" else PM10_STATIONS


@app.get("/api/experiments/projections")
def projection_experiments():
    path = ROOT / "output/experiments/projections/resumen.json"
    if not path.is_file():
        abort(404, "Genera el análisis con python -m tfm_data.pipelines.analyze_pm10_projections.")
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/experiments/projections/files/<filename>")
def projection_evidence(filename):
    allowed = {"pca_componentes.csv", "pca_pesos.csv", "pca_proyecciones.csv",
               "lda_sin_meteo_proyecciones.csv", "lda_con_meteo_proyecciones.csv",
               "lda_sin_meteo_barrido.csv", "lda_con_meteo_barrido.csv",
               "predicciones_validacion_2023.csv", "metricas.csv", "metricas_contexto.csv", "ranking.csv", "protocolo.json"}
    if filename not in allowed:
        abort(404)
    return send_from_directory(ROOT / "output/experiments/projections", filename, as_attachment=True)


@app.get("/api/case-studies")
def case_studies():
    path = ROOT / "output/case_studies/resumen.json"
    if not path.is_file():
        abort(404, "Genera los casos con python -m tfm_data.pipelines.prepare_case_studies.")
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/case-studies/<case_id>/evidence/<filename>")
def case_evidence(case_id, filename):
    allowed = {
        "typical": {"predicciones.csv", "aportes.csv", "entradas.csv", "contexto.csv"},
        "peak": {"predicciones.csv", "aportes.csv", "entradas.csv", "contexto.csv"},
        "onset": {"avisos.csv", "meteorologia.csv", "contexto.csv"},
        "false_alarm": {"avisos.csv", "meteorologia.csv", "contexto.csv"},
    }
    if filename not in allowed.get(case_id, set()):
        abort(404)
    return send_from_directory(ROOT / "output/case_studies" / case_id, filename, as_attachment=True)

PROFILES = {
    "aire-diario": ("MITECO", "Mediciones diarias", "Calidad del aire", "Concentraciones por punto de muestreo y día. Es la fuente preferente para la serie diaria de PM10."),
    "aire-horario": ("MITECO", "Mediciones horarias", "Calidad del aire", "Concentraciones por punto de muestreo y hora. Permite calcular medias diarias y contrastar picos de PM10."),
    "estaciones": ("MITECO", "Metadatos de estaciones", "Calidad del aire", "Describe estaciones, magnitudes y técnicas. Sirve para identificar puntos, interpretar unidades y localizar las estaciones."),
    "sanidad": ("INE", "Altas hospitalarias", "Sanidad", "Tasas anuales de altas por residencia y diagnóstico. Se usan en el análisis respiratorio exploratorio por provincia."),
    "demografia": ("INE", "Población por edad", "Demografía", "Recuentos de población por provincia, sexo, edad y fecha. Aportan el tamaño y la estructura de edad del territorio."),
    "noaa": ("NOAA", "Previsiones GFS", "Meteorología", "Cada ciclo archivado aporta viento y precipitación para el día objetivo. El CSV conserva las celdas elegidas y el manifiesto conserva los rangos GRIB2 solicitados."),
    "eea": ("EEA", "PM10 horario verificado", "Calidad del aire", "Series horarias de los tres puntos de muestreo. Se contrastaron con MITECO en 2024 y aportan el PM10 observado de 2025."),
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


@lru_cache(maxsize=4)
def chart_daily_values(year, territory="madrid"):
    path = (
        "output/pm10_weather_test_2025/pm10_diario_2025.csv"
        if year == 2025
        else "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv"
    )
    if territory == "barcelona":
        path = "data/interim/experiments/barcelona/diario_2017_2024.csv"
    return {
        (row["codigo_estacion"], row["fecha"]): float(row["pm10_valido"]) if row["pm10_valido"] else None
        for row in read_csv(ROOT / path)
    }


@app.get("/api/charts/map")
def chart_station_map():
    territory = chart_territory()
    last_year = 2024 if territory == "barcelona" else 2025
    selected_date = request.args.get("date", "2024-10-31")
    try:
        parsed = date.fromisoformat(selected_date)
    except ValueError:
        abort(400, "Selecciona una fecha válida con formato AAAA-MM-DD.")
    if parsed.isoformat() != selected_date or not 2017 <= parsed.year <= last_year:
        abort(400, f"Selecciona una fecha entre 2017 y {last_year} para este territorio.")
    metadata_path = "data/interim/provincial_feasibility/history/seleccion_estaciones_pm10_2024.csv"
    latitude, longitude = "LATITUD_G", "LONGITUD_G"
    stations = chart_stations(territory)
    if territory == "barcelona":
        metadata_path = "data/interim/experiments/barcelona/estaciones.csv"
        latitude, longitude = "latitud", "longitud"
    metadata = {row["codigo_estacion"]: row for row in read_csv(ROOT / metadata_path)
                if row["codigo_estacion"] in stations}
    values = chart_daily_values(2025 if parsed.year == 2025 else 2024, territory)
    return jsonify(
        territory=territory, date=selected_date, threshold=PM10_THRESHOLD,
        source="EEA" if parsed.year == 2025 else "MITECO",
        coordinateSource=metadata_path, coordinateYear=2024, coordinateColumns=[latitude, longitude],
        stations=[dict(code=code, name=metadata[code]["NOMBRE"].strip(),
                       latitude=float(metadata[code][latitude]),
                       longitude=float(metadata[code][longitude]),
                       value=values.get((code, selected_date))) for code in stations],
    )


@app.get("/api/charts/pm10")
def chart_pm10():
    territory = chart_territory()
    station = request.args.get("station", chart_stations(territory)[0])
    month = request.args.get("month", "2024-10" if territory == "barcelona" else "2025-08")
    if station not in chart_stations(territory):
        abort(400, "La estación no pertenece al territorio seleccionado.")
    if not re.fullmatch(r"20(?:1[7-9]|2[0-5])-(?:0[1-9]|1[0-2])", month):
        abort(400, "Selecciona un mes entre enero de 2017 y diciembre de 2025.")
    year, month_number = map(int, month.split("-"))
    if territory == "barcelona" and year > 2024:
        abort(400, "Barcelona dispone de observaciones entre 2017 y 2024.")
    period = 2025 if year == 2025 else 2024
    measurements = chart_daily_values(period, territory)
    dates = [f"{month}-{day:02}" for day in range(1, monthrange(year, month_number)[1] + 1)]
    return jsonify(
        territory=territory,
        source="EEA" if year == 2025 else "MITECO",
        threshold=PM10_THRESHOLD,
        days=[{"date": day, "value": measurements.get((station, day))} for day in dates],
    )


@lru_cache(maxsize=2)
def chart_test_predictions(territory="madrid"):
    predictions = {}
    for row in read_csv(ROOT / EXPERIMENT_FILES[territory][1]):
        key = (row["codigo_estacion"], row["fecha_objetivo"])
        day = predictions.setdefault(key, {"observed": float(row["pm10_objetivo"])})
        day[row["modelo"]] = float(row["prediccion"])
    return predictions


@app.get("/api/charts/predictions")
def chart_predictions():
    territory = chart_territory()
    station = request.args.get("station", chart_stations(territory)[0])
    if station not in chart_stations(territory):
        abort(400, "La estación no pertenece al territorio seleccionado.")

    predictions = chart_test_predictions(territory)
    start = date(2024, 1, 1)
    dates = [(start + timedelta(days=offset)).isoformat() for offset in range(366)]
    days = [
        {"date": day, **predictions.get((station, day), {})}
        for day in dates
    ]
    episodes = []
    for elevated, group in groupby(days, key=lambda day: day.get("observed", 0) > PM10_THRESHOLD):
        if elevated:
            sequence = list(group)
            peak = max(sequence, key=lambda day: day["observed"])
            episodes.append({"start": sequence[0]["date"], "end": sequence[-1]["date"], "peak": peak["date"]})
    episodes.sort(key=lambda episode: -predictions[(station, episode["peak"])]["observed"])
    return jsonify(territory=territory, days=days, episodes=episodes, threshold=PM10_THRESHOLD)


@lru_cache(maxsize=2)
def chart_model_metrics(territory="madrid"):
    regression_path = ("output/experiments/barcelona/prueba_2024/metricas.csv" if territory == "barcelona"
                       else "output/pm10_final_2024/metricas_regresion.csv")
    regression = read_csv(ROOT / regression_path)
    classification = [] if territory == "barcelona" else read_csv(ROOT / "output/pm10_weather_test_2025/metricas_por_contexto.csv")
    return {
        "territory": territory,
        "threshold": PM10_THRESHOLD,
        "regression": [
            {"group": row["tramo"], "model": row["modelo"], "mae": float(row["mae"]), "n": int(row["n"])}
            for row in regression if row["tramo"] in {"todos", "elevado"}
        ],
        "onsets": [
            {
                "model": row["modelo"], "detected": int(row["vp"]), "falseAlarms": int(row["fp"]),
                "positives": int(row["positivos"]), "n": int(row["n"]),
            }
            for row in classification if row["contexto"] == "hoy_no_elevado"
        ],
    }


@app.get("/api/charts/metrics")
def chart_metrics():
    return jsonify(chart_model_metrics(chart_territory()))


EXPERIMENT_FILES = {
    "madrid": ("data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv", "output/pm10_final_2024/predicciones_regresion.csv"),
    "barcelona": ("data/interim/experiments/barcelona/diario_2017_2024.csv", "output/experiments/barcelona/prueba_2024/predicciones.csv"),
}


def experiment_comparison():
    path = ROOT / "output/experiments/comparacion/resumen.json"
    if not path.is_file():
        abort(404, "Falta la comparación. Ejecuta python -m tfm_data.pipelines.barcelona_experiment all.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/experiments")
def experiments():
    return jsonify(experiment_comparison())


@app.get("/api/experiments/window-ablation")
def experiment_window_ablation():
    path = ROOT / "output/experiments/window_ablation/resumen.json"
    if not path.is_file():
        abort(404, "Falta la comparación de ventanas. Ejecuta python -m tfm_data.pipelines.compare_pm10_windows.")
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@app.get("/api/experiments/grouped-permutation")
def experiment_grouped_permutation():
    path = ROOT / "output/experiments/grouped_permutation/resumen.json"
    if not path.is_file():
        abort(404, "Falta la importancia agrupada. Ejecuta python -m tfm_data.pipelines.interpret_pm10_permutation.")
    return jsonify(json.loads(path.read_text(encoding="utf-8")))


@lru_cache(maxsize=2)
def experiment_series_values(experiment):
    daily_path, predictions_path = EXPERIMENT_FILES[experiment]
    observed = {(row["codigo_estacion"], row["fecha"]): float(row["pm10_valido"]) if row["pm10_valido"] else None
                for row in read_csv(ROOT / daily_path)}
    predictions = {}
    for row in read_csv(ROOT / predictions_path):
        predictions.setdefault((row["codigo_estacion"], row["fecha_objetivo"]), {})[row["modelo"]] = float(row["prediccion"])
    return observed, predictions


def regional_coverage(experiment):
    if experiment not in EXPERIMENT_FILES:
        abort(404, "Experimento desconocido.")
    path = ROOT / "output/experiments" / experiment / "coverage_audit/resumen.json"
    if not path.is_file():
        abort(404, "Falta la auditoría. Ejecuta python -m tfm_data.pipelines.audit_regional_coverage.")
    return json.loads(path.read_text(encoding="utf-8"))


def coverage_station(data):
    station = request.args.get("station", "todas")
    if station not in {group["station"] for group in data["groups"]}:
        abort(400, "La estación no pertenece a esta auditoría.")
    return station


@app.get("/api/experiments/<experiment>/coverage")
def experiment_coverage(experiment):
    data = regional_coverage(experiment)
    station = coverage_station(data)
    return jsonify(year=data["year"], threshold=data["threshold"], reasonLabels=data["reasonLabels"],
                   summary=next(group for group in data["groups"] if group["station"] == station and group["month"] == 0),
                   monthly=[group for group in data["groups"] if group["station"] == station and group["month"] > 0],
                   features=[row for row in data["features"] if row["station"] == station and row["month"] == 0],
                   episodes=[row for row in data["episodes"] if row["excludedDays"] > 0 and (station == "todas" or row["station"] == station)],
                   sources=data["sources"])


@app.get("/api/experiments/<experiment>/coverage/rows")
def experiment_coverage_rows(experiment):
    data = regional_coverage(experiment)
    station = coverage_station(data)
    try:
        page, size, month = (int(request.args.get(key, default)) for key, default in [("page", "1"), ("size", "10"), ("month", "0")])
    except ValueError:
        abort(400, "Página, tamaño y mes deben ser enteros.")
    if page < 1 or size not in {10, 25, 50} or not 0 <= month <= 12:
        abort(400, "Página, tamaño o mes fuera del intervalo permitido.")
    status = request.args.get("status", "excluded")
    if status not in {"all", "excluded", "evaluated"}:
        abort(400, "Estado de auditoría desconocido.")
    path = ROOT / "output/experiments" / experiment / "coverage_audit/detalle.csv"
    rows = read_csv(path)
    filtered = [row for row in rows if (station == "todas" or row["codigo_estacion"] == station)
                and (month == 0 or int(row["mes"]) == month)
                and (status == "all" or (row["evaluada"] == "True") == (status == "evaluated"))]
    start = (page - 1) * size
    return jsonify(rows=filtered[start:start + size], total=len(filtered), page=page, size=size,
                   hasNext=start + size < len(filtered), source=path.relative_to(ROOT).as_posix())


@app.get("/api/experiments/<experiment>/series")
def experiment_series(experiment):
    if experiment not in EXPERIMENT_FILES:
        abort(404, "Experimento desconocido.")
    summary = next(item for item in experiment_comparison()["experiments"] if item["id"] == experiment)
    station = request.args.get("station", summary["stations"][0]["code"])
    if station not in {item["code"] for item in summary["stations"]}:
        abort(400, "La estación no pertenece al experimento seleccionado.")
    month = request.args.get("month", "2024-10")
    if not re.fullmatch(r"20(?:1[7-9]|2[0-4])-(?:0[1-9]|1[0-2])", month):
        abort(400, "Selecciona un mes entre 2017 y 2024.")
    year, number = map(int, month.split("-"))
    observed, predictions = experiment_series_values(experiment)
    days = []
    for day in range(1, monthrange(year, number)[1] + 1):
        target = f"{month}-{day:02}"
        key = (station, target)
        values = dict(date=target, evaluated=key in predictions, **predictions.get(key, {}))
        if observed.get(key) is not None:
            values["observed"] = observed[key]
        days.append(values)
    return jsonify(experiment=experiment, station=station, month=month, source="MITECO", threshold=27,
                   observedSource=EXPERIMENT_FILES[experiment][0], predictionsSource=EXPERIMENT_FILES[experiment][1], days=days)


@lru_cache(maxsize=1)
def error_analysis():
    path = ROOT / "output/pm10_error_analysis/analisis.json"
    if not path.is_file():
        abort(404, "Falta la auditoría de errores. Ejecuta el pipeline audit_pm10_errors.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/charts/errors")
def chart_errors():
    if chart_territory() == "barcelona":
        rows = read_csv(ROOT / "output/experiments/barcelona/prueba_2024/errores.csv")
        integers = {"month", "n"}
        groups = [{key: int(value) if key in integers else value if key in {"station", "name", "level"} else float(value)
                   for key, value in row.items()} for row in rows]
        return jsonify(territory="barcelona", threshold=PM10_THRESHOLD, groups=groups, sensitivity=[])
    return jsonify(error_analysis())


@lru_cache(maxsize=1)
def bootstrap_analysis():
    path = ROOT / "output/pm10_bootstrap/analisis.json"
    if not path.is_file():
        abort(404, "Falta el bootstrap. Ejecuta el pipeline bootstrap_pm10_errors.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/charts/uncertainty")
def chart_uncertainty():
    if chart_territory() == "barcelona":
        path = ROOT / "output/experiments/barcelona/prueba_2024/bootstrap.json"
        return jsonify(json.loads(path.read_text(encoding="utf-8")))
    return jsonify(bootstrap_analysis())


@lru_cache(maxsize=1)
def model_explanations():
    path = ROOT / "output/pm10_explanations/explicaciones.json"
    if not path.is_file():
        abort(404, "Faltan las explicaciones. Ejecuta el pipeline explain_pm10_models.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/charts/explanations")
def chart_explanations():
    if chart_territory() != "madrid":
        abort(400, "La explicación individual de Ridge solo está preparada para Madrid.")
    station = request.args.get("station", "28079060")
    if station not in PM10_STATIONS:
        abort(400, "Selecciona una de las tres estaciones del estudio.")
    data = model_explanations()
    cases = [case for case in data["cases"] if case["station"] == station]
    selected = request.args.get("date")
    if selected is None:
        current = max(cases, key=lambda case: case["observed"])
    else:
        current = next((case for case in cases if case["date"] == selected), None)
        if current is None:
            abort(404, "La fecha seleccionada está fuera de la prueba de esta estación.")
    return jsonify(
        trainingEnd=data["trainingEnd"], testYear=data["testYear"],
        features=data["features"], forest=data["forest"], intercept=data["intercept"],
        dates=sorted(case["date"] for case in cases), case=current,
    )


def profile(kind):
    if "ine_tasas" in kind or "ine_morbilidad" in kind:
        return "sanidad"
    if "diarios" in kind:
        return "aire-diario"
    if "horarios" in kind:
        return "aire-horario"
    if "estaciones" in kind or "metainformacion" in kind:
        return "estaciones"
    if kind == "population_age":
        return "demografia"
    raise ValueError(f"Fuente sin perfil en el catálogo: {kind}")


def column(name, data_type, notes):
    return {"name": name, "type": data_type, "notes": notes}


def extra_sources():
    gfs = "data/interim/weather_forecasts/gfs_2021_2025"
    weather_columns = [
        column("codigo_estacion", "Código", "Identificador de la estación MITECO."),
        column("fecha_objetivo", "Fecha ISO", "Día para el que se prevé el tiempo."),
        column("inicio_ciclo_utc", "Fecha y hora UTC", "Ciclo del día anterior a las 12:00 UTC."),
        column("latitud_gfs", "Decimal o nulo", "Latitud de la celda seleccionada, en grados."),
        column("longitud_gfs", "Decimal o nulo", "Longitud de la celda seleccionada, en grados."),
        column("viento_10m_mediodia_ms", "Decimal o nulo", "Velocidad del viento prevista a mediodía, en m/s."),
        column("precipitacion_diaria_mm", "Decimal o nulo", "Precipitación prevista para el día UTC, en mm."),
        column("estado_viento", "Texto", "Control de calidad del viento."),
        column("estado_precipitacion", "Texto", "Control de calidad de la precipitación."),
    ]
    manifest_columns = [column(name, data_type, notes) for name, data_type, notes in [
        ("campo", "Texto", "Identificador del campo meteorológico descargado."),
        ("url", "URL", "Archivo GRIB2 del que se pidió el rango."),
        ("indice", "URL", "Archivo de texto con los desplazamientos de cada mensaje."),
        ("rango", "Dos enteros", "Primer y último byte solicitado, ambos incluidos."),
        ("bytes", "Entero", "Número de bytes conservados para el cálculo."),
        ("sha256", "Texto", "Huella del fragmento recibido."),
        ("inicio_ciclo_utc", "Fecha y hora UTC", "Inicio del ciclo del modelo meteorológico."),
        ("validez_utc", "Fecha y hora UTC", "Instante para el que se hizo la previsión."),
    ]]
    noaa_example = "https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20251230/12/atmos/gfs.t12z.pgrb2.0p25.f036.idx"
    noaa = {"id": "noaa", "profile": "noaa", "year": "2021–2025", "format": "GRIB2 + índice",
            "method": "GET", "url": noaa_example, "catalog": "https://registry.opendata.aws/noaa-gfs-bdp-pds/",
            "requestNote": "Ejemplo de descarga del índice .idx. El pipeline pide después rangos de bytes del GRIB2. Cada URL exacta figura en el manifiesto.",
            "tables": [
                {"id": "gfs-daily", "name": "Previsiones diarias por estación", "format": "CSV derivado",
                 "reader": "csv", "delimiter": ",", "local": f"{gfs}/previsiones_gfs_diarias.csv", "columns": weather_columns},
                {"id": "gfs-requests", "name": "Peticiones de fragmentos GRIB2", "format": "JSON de procedencia",
                 "reader": "json", "local": f"{gfs}/mensajes_gfs.json", "columns": manifest_columns},
            ]}
    manifest = json.loads((ROOT / "data/raw/eea_pm10/sources.json").read_text(encoding="utf-8"))
    eea_columns = [column(name, data_type, note) for name, data_type, note in [
        ("Samplingpoint", "Texto", "Identificador del punto de muestreo."), ("Pollutant", "Entero", "Código EEA del contaminante. 5 corresponde a PM10."),
        ("Start", "Fecha y hora", "Inicio del intervalo en UTC+1 fijo."), ("End", "Fecha y hora", "Fin del intervalo en UTC+1 fijo."),
        ("Value", "Decimal", "Concentración observada."), ("Unit", "Texto", "Unidad publicada en el archivo."),
        ("AggType", "Texto", "Tipo de intervalo de la observación."), ("Validity", "Entero", "Código de validez del dato."),
        ("Verification", "Entero", "Código de verificación del dato."), ("ResultTime", "Fecha y hora", "Marca temporal del resultado."),
        ("DataCapture", "Decimal", "Captura de datos declarada en el registro."), ("FkObservationLog", "Texto", "Identificador de procedencia de la observación."),
    ]]
    eea = {"id": "eea", "profile": "eea", "year": "Series históricas", "format": "Parquet", "method": "POST",
           "url": manifest["catalog_url"], "payload": manifest["catalog_query"],
           "catalog": "https://www.eea.europa.eu/en/datahub/datahubitem-view/778ef9f5-6293-4846-badd-56a29c70880d",
           "requestNote": "El POST devuelve las URLs de los archivos. El archivo original de cada punto se descargó por GET.",
           "tables": [{"id": f"eea-{point}", "name": point, "format": "Parquet", "reader": "parquet",
                       "local": f"data/raw/eea_pm10/{item['file']}", "url": item["url"], "columns": eea_columns}
                      for point, item in manifest["sources"].items()]}
    return [noaa, eea]


@lru_cache(maxsize=1)
def get_catalog():
    columns = {}
    for row in read_csv(REFERENCE / "source_columns.csv"):
        columns.setdefault(row["table_id"], []).append(column(row["column_name"], row["logical_type"], row["notes"]))
    by_file = {}
    for row in read_csv(REFERENCE / "source_tables.csv"):
        member, sheet, local = row["archive_member"], row["sheet"], row["local_file"]
        name = " · ".join(filter(None, [member, sheet])) or Path(local).name
        table = {"id": row["table_id"], "name": name, "format": row["format"].upper(), "reader": row["format"],
                 "local": local, "member": member, "sheet": sheet, "delimiter": ";", "columns": columns[row["table_id"]]}
        by_file.setdefault(local, []).append(table)
    sources = []
    for index, row in enumerate(read_csv(REFERENCE / "source_catalog.csv"), 1):
        local = row["local_file"]
        sources.append({"id": f"source-{index:02}", "profile": profile(row["source_kind"]),
                        "year": row["year"].removesuffix(".0") or "Serie histórica", "format": row["format"].upper(),
                        "scope": row["scope"], "file": Path(local).name, "method": row["method"], "url": row["download_url"],
                        "catalog": row["catalog_url"], "tables": by_file[local]})
    sources.extend(extra_sources())
    for source in sources:
        source["provider"], source["title"], source["domain"], source["purpose"] = PROFILES[source["profile"]]
        for table in source["tables"]:
            enrich_columns(table, source["profile"])
    return sources, {table["id"]: table for source in sources for table in source["tables"]}


def path_for(table):
    path = (ROOT / table["local"]).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        abort(404, description="El archivo registrado no está disponible en esta copia del proyecto.")
    return path


def serializable(cell):
    if isinstance(cell, (date, datetime, time)):
        return cell.isoformat()
    if isinstance(cell, (Decimal, timedelta)):
        return str(cell)
    return None if cell == "" else cell


def normalized_text(value):
    value = serializable(value)
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        value = " – ".join(map(str, value))
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value).strip().casefold()
    if text.isascii():
        return text
    return "".join(char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char))


def requested_filter(table, args):
    query = args.get("q", "").strip()
    field = args.get("column", "")
    operator = args.get("op", "contains")
    value = args.get("value", "").strip()
    names = [column["name"] for column in table["columns"]]
    if len(query) > 200 or len(value) > 200:
        abort(400, description="La búsqueda admite hasta 200 caracteres por campo.")
    if operator not in {"contains", "equals", "missing"} or field and field not in names:
        abort(400, description="La columna o el operador de filtro no son válidos.")
    if not field and (value or operator != "contains"):
        abort(400, description="Selecciona una columna para aplicar esta condición.")
    if field and operator != "missing" and not value:
        abort(400, description="Introduce el valor que deseas buscar en la columna.")
    if not query and not field:
        return None

    term = normalized_text(query)
    condition = normalized_text(value)
    position = names.index(field) if field else None
    ine_source = Path(table["local"]).name.startswith("ine_")

    def is_missing(cell):
        return cell is None or isinstance(cell, str) and (not cell.strip() or ine_source and cell.strip() == "..")

    def matches(row):
        if position is not None:
            cell = row[position] if position < len(row) else None
            absent = is_missing(cell)
            if operator == "missing":
                if not absent:
                    return False
            elif absent:
                return False
            else:
                text = normalized_text(cell)
                if (operator == "equals" and condition != text) or (operator == "contains" and condition not in text):
                    return False
        return not term or any(not is_missing(cell) and term in normalized_text(cell) for cell in row)

    return matches


def page_of(rows, start, size, matches=None, first=1):
    numbered = enumerate(rows, first)
    if matches:
        numbered = ((position, row) for position, row in numbered if matches(row))
    return list(islice(numbered, start, start + size + 1))


def page_csv(stream, table, start, size, matches):
    rows = csv.reader(stream, delimiter=table["delimiter"])
    header = list(next(rows))
    expected = [field["name"] for field in table["columns"]]
    if header != expected:
        raise ValueError("La cabecera CSV difiere del esquema catalogado.")
    return page_of((row for row in rows if row), start, size, matches)


def page_xlsx(stream, sheet, start, size, matches):
    from openpyxl import load_workbook
    workbook = load_workbook(stream, read_only=True, data_only=True)
    try:
        worksheet = workbook[sheet]
        if matches:
            return page_of(worksheet.iter_rows(min_row=2, values_only=True), start, size, matches)
        end = min(start + size + 2, worksheet.max_row or start + size + 2)
        if start + 2 > end:
            return []
        return page_of(worksheet.iter_rows(min_row=start + 2, max_row=end, values_only=True), 0, size, first=start + 1)
    finally:
        workbook.close()


@lru_cache(maxsize=1)
def read_gfs_manifest(path, modified):
    return json.loads(path.read_text(encoding="utf-8"))


def load_page(table, start, size, matches=None):
    path = path_for(table)
    reader = table["reader"]
    sheet = table.get("sheet")
    member = table.get("member")
    names = [field["name"] for field in table["columns"]]
    if member:
        with ZipFile(path) as archive, archive.open(member) as raw:
            if reader == "csv":
                with TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                    return page_csv(text, table, start, size, matches)
            return page_xlsx(BytesIO(raw.read()), sheet, start, size, matches)
    if reader == "csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return page_csv(stream, table, start, size, matches)
    if reader == "xlsx":
        return page_xlsx(path, sheet, start, size, matches)
    if reader == "xls":
        import xlrd
        with xlrd.open_workbook(str(path), on_demand=True) as workbook:
            worksheet = workbook.sheet_by_name(sheet)
            rows = ([xlrd.xldate_as_datetime(cell.value, workbook.datemode) if cell.ctype == xlrd.XL_CELL_DATE else cell.value
                     for cell in worksheet.row(index)] for index in range(1 if matches else start + 1, worksheet.nrows))
            return page_of(rows, start if matches else 0, size, matches, first=1 if matches else start + 1)
    if reader == "parquet":
        from pyarrow.parquet import ParquetFile
        with ParquetFile(path) as parquet:
            rows = (row for batch in parquet.iter_batches(batch_size=1024, columns=names) for row in batch.to_pylist())
            return page_of(([row[name] for name in names] for row in rows), start, size, matches)
    if reader == "json":
        rows = read_gfs_manifest(path, path.stat().st_mtime_ns)
        return page_of(([row[name] for name in names] for row in rows), start, size, matches)
    raise ValueError(f"Formato sin lector: {reader}")


@app.get("/api/sources")
def sources():
    catalog, _ = get_catalog()
    return jsonify([{**source, "tables": [{key: value for key, value in table.items() if key not in {"columns", "reader", "delimiter"}}
                                        for table in source["tables"]]} for source in catalog])


@lru_cache(maxsize=1)
def get_treated_tables():
    tables = treated_catalog(ROOT)
    for table in tables.values():
        enrich_columns(table)
    return tables


@app.get("/api/treated-tables")
def treated_tables():
    tables = get_treated_tables().values()
    return jsonify([{key: value for key, value in table.items() if key not in {"columns", "reader", "delimiter"}}
                    for table in tables])


def find_table(table_id):
    _, tables = get_catalog()
    table = tables.get(table_id) or get_treated_tables().get(table_id)
    if table is None:
        abort(404, description="La tabla no existe en el catálogo.")
    return table


@app.get("/api/tables/<table_id>")
def table_page(table_id):
    table = find_table(table_id)
    page = request.args.get("page", "1")
    size = request.args.get("size", "10")
    if not page.isascii() or not page.isdecimal() or len(page) > 7 or not 1 <= int(page):
        abort(400, description="La página debe ser un entero positivo.")
    if size not in {"10", "25", "50"}:
        abort(400, description="El tamaño de página debe ser 10, 25 o 50.")
    page, size = int(page), int(size)
    start = (page - 1) * size
    width = len(table["columns"])
    matches = requested_filter(table, request.args)
    rows = load_page(table, start, size, matches)
    serialized = [[serializable(cell) for cell in (list(row) + [None] * width)[:width]] for _, row in rows[:size]]
    return jsonify(columns=table["columns"], rows=serialized, page=page, size=size, start=start,
                   positions=[position for position, _ in rows[:size]], hasNext=len(rows) > size)


def statistics_table(table_id):
    table = find_table(table_id)
    if table_id not in get_treated_tables():
        abort(400, "Las estadísticas están disponibles para las tablas tratadas con esquema numérico declarado.")
    return table


def iter_treated_records(table, matches):
    path = path_for(table)
    fields = [field["name"] for field in table["columns"]]
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, delimiter=table["delimiter"])
        if next(rows) != fields:
            raise ValueError("La cabecera CSV difiere del esquema catalogado.")
        for row in rows:
            if row and (matches is None or matches(row)):
                yield dict(zip(fields, row))


@app.get("/api/tables/<table_id>/statistics")
def table_statistics(table_id):
    table = statistics_table(table_id)
    matches = requested_filter(table, request.args)
    fields = [field["name"] for field in table["columns"]]
    selected = numeric_measurement_columns(table["columns"])
    result = summarize_numeric_columns(iter_treated_records(table, matches), selected)
    descriptions = {field["name"]: field for field in table["columns"]}
    for column in result["columns"]:
        column.update(type=descriptions[column["name"]]["type"], description=descriptions[column["name"]]["notes"])
    return jsonify(**result, table=table_id, source=table["local"], scope="all_filtered_rows",
                   excluded_columns=[field for field in fields if field not in selected],
                   filters={key: request.args.get(key, "") for key in ["q", "column", "op", "value"]})


@app.get("/api/tables/<table_id>/boxplot")
def table_boxplot(table_id):
    table = statistics_table(table_id)
    matches = requested_filter(table, request.args)
    selected = numeric_measurement_columns(table["columns"])
    field = request.args.get("field", "pm10_valido" if "pm10_valido" in selected else next(iter(selected), ""))
    group = request.args.get("group_by", "none")
    fields = [column["name"] for column in table["columns"]]
    if field not in selected:
        abort(400, "Selecciona una columna numérica de medida.")
    if group not in {"none", "codigo_estacion"} or group == "codigo_estacion" and group not in fields:
        abort(400, "La agrupación solicitada no está disponible en esta tabla.")
    groups = summarize_boxplot_groups(iter_treated_records(table, matches), field,
                                      group_by=None if group == "none" else group,
                                      label_by="NOMBRE" if "NOMBRE" in fields else None)
    return jsonify(column=field, group_by=group, groups=groups, row_count=sum(row["row_count"] for row in groups),
                   source=table["local"], scope="all_filtered_rows", quantile_method="linear (n-1)*p", whisker_iqr_multiplier=1.5)


@app.get("/api/tables/<table_id>/provenance")
def provenance(table_id):
    table = find_table(table_id)
    path_for(table)
    names = [field["name"] for field in table["columns"]]
    field = request.args.get("column", "")
    row = request.args.get("row", "")
    if field not in names or not row.isascii() or not row.isdecimal() or len(row) > 7 or int(row) < 1:
        abort(400, description="Selecciona una columna y un número de registro válido.")
    numbered = load_page(table, int(row) - 1, 1)
    if not numbered:
        abort(404, description="El registro no existe en el archivo.")
    position, values = numbered[0]
    record = dict(zip(names, map(serializable, values)))
    catalog, _ = get_catalog()
    return jsonify(explain_value(ROOT, catalog, table, record, field, position, names.index(field)))


@app.get("/api/documentation")
def documentation():
    return jsonify([dict(id=key, title=title, path=path) for key, (title, path) in ARTICLES.items()])


@app.get("/api/documentation/<article_id>")
def article(article_id):
    if article_id not in ARTICLES:
        abort(404, description="El documento no está incluido en el explorador.")
    title, filename = ARTICLES[article_id]
    path = ROOT / "docs" / filename
    if not path.is_file():
        abort(404, description="No se encuentra el documento en esta copia del proyecto.")
    return jsonify(title=title, path=filename, markdown=path.read_text(encoding="utf-8-sig"))


@app.errorhandler(400)
@app.errorhandler(404)
def bad_request(error):
    return jsonify(error=error.description), error.code


@app.get("/")
def index():
    return send_from_directory(DIST, "index.html")


@app.get("/assets/<path:asset>")
def assets(asset):
    return send_from_directory(DIST / "assets", asset)


@app.get("/figures/<path:filename>")
def documentation_figure(filename):
    return send_from_directory(ROOT / "docs/figures", filename)


if __name__ == "__main__":
    app.run(host=os.environ.get("TFM_HOST", "127.0.0.1"), port=int(os.environ.get("TFM_PORT", "8066")))
