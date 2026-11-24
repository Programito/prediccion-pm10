"""Independent Barcelona PM10 regression experiment and Madrid comparison.

Run stages in order: prepare, train, evaluate, compare (or all).
Existing Madrid inputs, models and results are only read.
"""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import zipfile

import joblib
import numpy as np
import pandas as pd

from tfm_data.config import PROJECT_ROOT as ROOT
from tfm_data.adapters.sklearn.base import backend_version
from tfm_data.mappers.air import AirContext, AirQualityReader, AirQualityMapper, AirQualityValidator, combine_daily_measurements, summarize_hours
from tfm_data.mappers.pm10_forecast import PM10ForecastMapper
from tfm_data.models.factory import FEATURES, create_models
from tfm_data.evaluation.pm10_regression import split_dataset, evaluate_models, calculate_metrics
from tfm_data.evaluation.pm10_errors import pair_predictions, summarize, grouped_errors
from tfm_data.evaluation.pm10_bootstrap import moving_block_indices, resampled_differences

DATA = ROOT / "data/interim/experiments/barcelona"
OUTPUT = ROOT / "output/experiments/barcelona"
MODELS = ROOT / "models/experiments/barcelona"
THRESHOLD, SEED, REPLICATES = 27, 20261119, 5000
BLOCKS = (7, 14, 28)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save_csv(path, table):
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")


def select_candidates(points, alerts):
    excluded = set(alerts.loc[alerts.revisar_diferencia_mayor_100m | alerts.tipo_area_cambia, "punto_muestreo"])
    candidates = points.loc[points.codigo_provincia.eq("08")].groupby(
        ["punto_muestreo", "codigo_estacion"], as_index=False).agg(
        NOMBRE=("NOMBRE", "last"), TIPO_AREA=("TIPO_AREA", "last"),
        anios=("anio", "nunique"), cobertura_minima=("cobertura_anual", "min"), cobertura_media=("cobertura_anual", "mean"),
        latitud=("LATITUD_G", "last"), longitud=("LONGITUD_G", "last"))
    candidates["coordenadas_o_area_inestables"] = candidates.punto_muestreo.isin(excluded)
    candidates["elegible"] = candidates.anios.eq(8) & ~candidates.coordenadas_o_area_inestables
    candidates = candidates.sort_values(["elegible", "cobertura_minima", "cobertura_media", "codigo_estacion"],
                                        ascending=[False, False, False, True]).reset_index(drop=True)
    eligible = candidates.loc[candidates.elegible]
    if len(eligible) < 3:
        raise ValueError("Se necesitan tres puntos estables con ocho años de cobertura.")
    # The rule is based on coverage, never on prediction errors or concentrations.
    candidates["seleccionada"] = candidates.punto_muestreo.isin(eligible.head(3).punto_muestreo)
    return candidates


def longest_missing(values):
    missing = pd.Series(values).isna()
    runs = missing.groupby(missing.ne(missing.shift()).cumsum()).sum()
    return int(runs.max()) if len(runs) else 0


def prepare():
    history = ROOT / "data/interim/provincial_feasibility/history"
    types = {key: str for key in ["codigo_provincia", "codigo_estacion", "punto_muestreo"]}
    candidates = select_candidates(pd.read_csv(history / "puntos_red_constante.csv", dtype=types),
                                   pd.read_csv(history / "revision_coordenadas_red_constante.csv", dtype=types))
    sample = candidates.loc[candidates.seleccionada].copy()
    save_csv(DATA / "candidatas.csv", candidates)
    save_csv(DATA / "estaciones.csv", sample)
    raw = ROOT / "data/raw/health_air_history"
    sources = json.loads((raw / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    points = set(sample.punto_muestreo)
    reader, mapper, validator = AirQualityReader(), AirQualityMapper(), AirQualityValidator()
    years, provenance = [], []
    for year in range(2017, 2025):
        tables = {}
        for frequency, kind in [("diaria", "miteco_diarios"), ("horaria", "miteco_horarios")]:
            source = next(item for item in sources if item["year"] == year and item["kind"] == kind and item["status"] == "downloaded")
            path = raw / source["file"]
            if digest(path) != source["sha256"]:
                raise ValueError("Original alterado: " + str(path))
            with zipfile.ZipFile(path) as archive:
                members = [name for name in archive.namelist() if Path(name).name.startswith("PM10_") and name.endswith(".csv")]
            if len(members) != 1:
                raise ValueError("CSV PM10 ambiguo.")
            original = reader.read_points(path, members[0], points)
            provenance.append({**source, "member": members[0], "selected_source_rows": len(original)})
            if original.empty:
                if frequency == "horaria":
                    raise ValueError("Falta la fuente horaria.")
                tables[frequency] = None
                continue
            context = AirContext(year, "10", "PM10", "µg/m3", path.name, members[0])
            tables[frequency] = mapper.transform(original, context, frequency)
            validator.validate(tables[frequency], frequency)
        derived = summarize_hours(tables["horaria"])
        daily = tables["diaria"] if tables["diaria"] is not None else derived.iloc[:0].copy()
        combined, _ = combine_daily_measurements(daily, derived)
        validator.validate(combined, "diaria")
        calendar = sample[["punto_muestreo", "codigo_estacion", "NOMBRE", "TIPO_AREA"]].merge(
            pd.DataFrame({"fecha": pd.date_range(f"{year}-01-01", f"{year}-12-31")}), how="cross")
        columns = ["punto_muestreo", "fecha", "concentracion", "estado", "origen_diario", "n_horas_validas", "archivo_origen", "miembro_zip"]
        table = calendar.merge(combined[columns], on=["punto_muestreo", "fecha"], how="left", validate="one_to_one")
        table["estado"] = table.estado.fillna("sin_registro")
        table["pm10_valido"] = table.concentracion.where(table.estado.eq("valida"))
        table["anio"], table["codigo_provincia"], table["unidad"] = year, "08", "µg/m3"
        years.append(table)
        print(f"Barcelona {year}: {table.pm10_valido.notna().sum()} días válidos de {len(table)}", flush=True)
    daily = pd.concat(years, ignore_index=True).sort_values(["codigo_estacion", "fecha"])
    save_csv(DATA / "diario_2017_2024.csv", daily)
    annual = daily.groupby(["codigo_estacion", "NOMBRE", "anio"], as_index=False).agg(
        dias_calendario=("fecha", "size"), dias_validos=("pm10_valido", "count"),
        mayor_ausencia_consecutiva=("pm10_valido", longest_missing))
    annual["cobertura"] = annual.dias_validos / annual.dias_calendario
    save_csv(DATA / "cobertura_anual.csv", annual)
    monthly = daily.assign(mes=daily.fecha.dt.strftime("%Y-%m")).groupby(["codigo_estacion", "mes"], as_index=False).agg(
        dias_calendario=("fecha", "size"), dias_validos=("pm10_valido", "count"))
    save_csv(DATA / "cobertura_mensual.csv", monthly)
    table = PM10ForecastMapper().transform(daily)
    save_csv(DATA / "tabla_supervisada.csv", table)
    complete = table.loc[table.fila_utilizable].copy()
    save_csv(DATA / "tabla_modelos_completa.csv", complete)
    coverage = table.groupby(["particion", "codigo_estacion", "NOMBRE"], as_index=False).agg(
        filas=("fecha_objetivo", "size"), objetivos_disponibles=("objetivo_disponible", "sum"), filas_utilizables=("fila_utilizable", "sum"))
    save_csv(DATA / "cobertura_particiones.csv", coverage)
    save_json(DATA / "fuentes.json", {"sources": provenance, "metadata": "MITECO; puntos_red_constante y revisión de coordenadas 2017–2024"})
    print(coverage.to_string(index=False), flush=True)


def train():
    table_path = DATA / "tabla_modelos_completa.csv"
    table = pd.read_csv(table_path, dtype={"codigo_estacion": str}, parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    training, validation = split_dataset(table)
    models = create_models()
    madrid_config = json.loads((ROOT / "output/pm10_regression_validation/configuracion.json").read_text(encoding="utf-8"))
    if FEATURES != madrid_config["variables"]:
        raise ValueError("Las variables difieren de Madrid.")
    for name in models:
        if models[name].get_parameters() != madrid_config["parametros_" + name]:
            raise ValueError("Los parámetros difieren de Madrid.")
    configuration = {
        "experiment": "barcelona", "scope": "Provincia; tres puntos de fondo, una estación urbana y dos suburbanas",
        "training": ["2017-01-01", "2022-12-31"], "validation": ["2023-01-01", "2023-12-31"],
        "test": ["2024-01-01", "2024-12-31"], "features": FEATURES,
        "training_rows": len(training), "validation_rows": len(validation),
        "source": table_path.relative_to(ROOT).as_posix(), "sha256_source": digest(table_path),
        "sha256_stations": digest(DATA / "estaciones.csv"),
        "parameters": {name: model.get_parameters() for name, model in models.items()},
        "test_models_fixed_before_fit": ["ridge", "persistencia"],
        "selection": "Ridge fijado para replicar la especificación de Madrid, incluso si el bosque mejora en validación de Barcelona",
        "retrain_after_validation": False, "hyperparameter_search": False,
        "non_negative_prediction": True, "common_high_level_threshold": THRESHOLD,
        "station_selection": "Tres mayores coberturas mínimas anuales 2017–2024; ocho años y sin cambios >100 m ni de área; desempate cobertura media y código",
        "limitations": ["Selección por disponibilidad histórica, incluida 2024", "Modelos ajustados por territorio; no prueba de transferencia del modelo de Madrid", "Emisión UTC simulada y datos revisados"],
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": backend_version()},
    }
    save_json(OUTPUT / "protocolo.json", configuration)
    predictions = evaluate_models(training, validation, models)
    save_csv(OUTPUT / "validacion/predicciones.csv", predictions)
    save_csv(OUTPUT / "validacion/metricas.csv", calculate_metrics(predictions, ["modelo"]))
    MODELS.mkdir(parents=True, exist_ok=True)
    for name, model in models.items():
        joblib.dump({"pipeline": model, "configuracion": configuration, "modelo": name}, MODELS / (name + ".joblib"), compress=3)
        save_csv(OUTPUT / "validacion" / ("variables_" + name + ".csv"), model.feature_details())
    save_json(OUTPUT / "modelos_congelados.json", {"sha256_protocolo": digest(OUTPUT / "protocolo.json"),
              "models": {name: digest(MODELS / (name + ".joblib")) for name in models}})
    print(calculate_metrics(predictions, ["modelo"]).to_string(index=False), flush=True)


def evaluate():
    config_path = OUTPUT / "protocolo.json"
    configuration = json.loads(config_path.read_text(encoding="utf-8"))
    lock = json.loads((OUTPUT / "modelos_congelados.json").read_text(encoding="utf-8"))
    if digest(config_path) != lock["sha256_protocolo"] or digest(DATA / "tabla_modelos_completa.csv") != configuration["sha256_source"]:
        raise ValueError("El protocolo o las entradas han cambiado tras el ajuste.")
    path = MODELS / "ridge.joblib"
    if digest(path) != lock["models"]["ridge"]:
        raise ValueError("El modelo congelado ha cambiado.")
    model = joblib.load(path)
    if model["configuracion"] != configuration:
        raise ValueError("El modelo no corresponde al protocolo.")
    table = pd.read_csv(DATA / "tabla_modelos_completa.csv", dtype={"codigo_estacion": str}, parse_dates=["fecha_objetivo", "fecha_ultima_observacion"])
    test = table.loc[table.fecha_objetivo.dt.year.eq(2024)].copy()
    if test.empty or not test.particion.eq("prueba_reservada").all() or not (test.fecha_objetivo - test.fecha_ultima_observacion).eq(pd.Timedelta(days=1)).all():
        raise ValueError("Prueba de 2024 incompatible.")
    raw = model["pipeline"].predict(test[FEATURES])
    if not np.isfinite(raw).all():
        raise ValueError("Predicciones no finitas.")
    base = test[["codigo_estacion", "NOMBRE", "fecha_objetivo", "fecha_ultima_observacion", "pm10_objetivo", "pm10_t"]]
    predictions = pd.concat([base.assign(modelo="ridge", prediccion=np.maximum(raw, 0), prediccion_negativa_corregida=raw < 0),
                             base.assign(modelo="persistencia", prediccion=base.pm10_t, prediccion_negativa_corregida=False)], ignore_index=True)
    predictions["error"] = predictions.prediccion - predictions.pm10_objetivo
    predictions["error_absoluto"] = predictions.error.abs()
    predictions["error_cuadrado"] = predictions.error.pow(2)
    predictions["tramo"] = np.where(predictions.pm10_objetivo.gt(THRESHOLD), "elevado", "resto")
    all_groups = pd.concat([predictions, predictions.assign(tramo="todos")], ignore_index=True)
    save_csv(OUTPUT / "prueba_2024/predicciones.csv", predictions)
    metrics = calculate_metrics(all_groups, ["tramo", "modelo"])
    save_csv(OUTPUT / "prueba_2024/metricas.csv", metrics)
    save_csv(OUTPUT / "prueba_2024/metricas_por_estacion.csv", calculate_metrics(all_groups, ["codigo_estacion", "NOMBRE", "tramo", "modelo"]))
    paired = pair_predictions(predictions)
    bootstrap = bootstrap_summary(paired)
    save_json(OUTPUT / "prueba_2024/bootstrap.json", bootstrap)
    save_csv(OUTPUT / "prueba_2024/intervalos.csv", pd.DataFrame(bootstrap["rows"]))
    save_csv(OUTPUT / "prueba_2024/errores.csv", grouped_errors(paired, THRESHOLD))
    save_json(OUTPUT / "prueba_2024/ejecucion.json", {"sha256_protocolo": digest(config_path), "sha256_modelo": digest(path),
              "sha256_predicciones": digest(OUTPUT / "prueba_2024/predicciones.csv"), "n": len(test), "reajuste": False})
    print(metrics.to_string(index=False), flush=True)


def bootstrap_summary(paired):
    calendar = pd.date_range("2024-01-01", "2024-12-31")
    rows = []
    for length in BLOCKS:
        indices = moving_block_indices(len(calendar), length, REPLICATES, SEED)
        groups = [("todas", "Todas las estaciones", paired), *[(code, group.nombre.iloc[0], group) for code, group in paired.groupby("codigo_estacion")]]
        for code, name, group in groups:
            daily = group.assign(delta=group.ae_ridge - group.ae_persistencia).groupby("fecha_objetivo").agg(total=("delta", "sum"), n=("delta", "size")).reindex(calendar, fill_value=0)
            values, counts = resampled_differences(daily.total.to_numpy(), daily.n.to_numpy(), indices)
            lo, hi = np.quantile(values, [.025, .975], method="linear")
            rows.append(dict(station=code, name=name, block_days=length, n=len(group), estimate=float((group.ae_ridge - group.ae_persistencia).mean()),
                             lower=float(lo), upper=float(hi), includes_zero=bool(lo <= 0 <= hi), minimum_resampled_cases=int(counts.min()), maximum_resampled_cases=int(counts.max())))
    return dict(primaryBlockDays=14, coverage=.95, replicates=REPLICATES, seed=SEED, rows=rows,
                method="overlapping_non_circular_moving_blocks", scope="Exploratorio y condicional a los modelos y muestras; estaciones sincronizadas por fecha")


def experiment_summary(key, paired, station_metadata, bootstrap, training_rows, validation_rows):
    groups = grouped_errors(paired, THRESHOLD)
    total = summarize(paired)
    total["improvement_pct"] = 100 * (total["mae_persistencia"] - total["mae_ridge"]) / total["mae_persistencia"]
    interval = next(row for row in bootstrap["rows"] if row["station"] == "todas" and row["block_days"] == 14)
    stations = []
    for code, group in paired.groupby("codigo_estacion"):
        metadata = station_metadata.loc[station_metadata.codigo_estacion.eq(code)].iloc[0]
        stations.append(dict(code=code, name=group.nombre.iloc[0].strip(), area=metadata.TIPO_AREA,
                             latitude=float(metadata.latitud), longitude=float(metadata.longitud), **summarize(group)))
    return dict(id=key, name="Madrid" if key == "madrid" else "Barcelona (provincia)", stations=stations,
                trainingRows=training_rows, validationRows=validation_rows,
                expectedStationDays=366 * len(stations), testCoverage=len(paired) / (366 * len(stations)),
                summary=total, interval=interval,
                observed=dict(mean=float(paired.observado.mean()), p95=float(paired.observado.quantile(.95)), maximum=float(paired.observado.max())),
                monthly=groups.loc[groups.station.eq("todas") & groups.month.gt(0) & groups.level.eq("todos")].to_dict("records"),
                levels=groups.loc[groups.station.eq("todas") & groups.month.eq(0)].to_dict("records"))


def compare():
    madrid = pair_predictions(pd.read_csv(ROOT / "output/pm10_final_2024/predicciones_regresion.csv", dtype={"codigo_estacion": str}))
    barcelona = pair_predictions(pd.read_csv(OUTPUT / "prueba_2024/predicciones.csv", dtype={"codigo_estacion": str}))
    metadata = pd.read_csv(ROOT / "data/interim/provincial_feasibility/history/seleccion_estaciones_pm10_2024.csv", dtype={"codigo_estacion": str}).rename(columns={"LATITUD_G": "latitud", "LONGITUD_G": "longitud"})
    madrid_config = json.loads((ROOT / "output/pm10_regression_validation/configuracion.json").read_text(encoding="utf-8"))
    bcn_config = json.loads((OUTPUT / "protocolo.json").read_text(encoding="utf-8"))
    experiments = [experiment_summary("madrid", madrid, metadata, json.loads((ROOT / "output/pm10_bootstrap/analisis.json").read_text()), madrid_config["filas_entrenamiento"], madrid_config["filas_validacion"]),
                   experiment_summary("barcelona", barcelona, pd.read_csv(DATA / "estaciones.csv", dtype={"codigo_estacion": str}), json.loads((OUTPUT / "prueba_2024/bootstrap.json").read_text(encoding="utf-8")), bcn_config["training_rows"], bcn_config["validation_rows"])]
    for experiment in experiments:
        key = experiment["id"]
        daily_path = (ROOT / "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv") if key == "madrid" else DATA / "diario_2017_2024.csv"
        daily = pd.read_csv(daily_path, dtype={"codigo_estacion": str}, parse_dates=["fecha"])
        daily = daily.loc[daily.fecha.dt.year.eq(2024)]
        for station in experiment["stations"]:
            values = daily.loc[daily.codigo_estacion.eq(station["code"]), "pm10_valido"]
            station["validObservedDays"] = int(values.notna().sum())
            station["longestMissingDays"] = longest_missing(values)
        validation_path = ROOT / "output/pm10_regression_validation/metricas_validacion_2023.csv" if key == "madrid" else OUTPUT / "validacion/metricas.csv"
        experiment["validationMetrics"] = pd.read_csv(validation_path).loc[lambda rows: rows.modelo.isin(["ridge", "random_forest", "persistencia"]), ["modelo", "n", "mae", "rmse"]].to_dict("records")
    complete_dates = []
    for paired in (madrid, barcelona):
        counts = paired.groupby("fecha_objetivo").codigo_estacion.nunique()
        complete_dates.append(set(counts.index[counts.eq(3)]))
    common = sorted(set.intersection(*complete_dates))
    if not common:
        raise ValueError("No hay fechas completas compartidas.")
    matched = []
    for key, paired in [("madrid", madrid), ("barcelona", barcelona)]:
        subset = paired.loc[paired.fecha_objetivo.isin(common)]
        metrics = summarize(subset)
        metrics["improvement_pct"] = 100 * (metrics["mae_persistencia"] - metrics["mae_ridge"]) / metrics["mae_persistencia"]
        matched.append(dict(experiment=key, **metrics))
    save_csv(ROOT / "output/experiments/comparacion/fechas_comunes.csv", pd.DataFrame({"fecha_objetivo": common}))
    source_paths = ["output/pm10_final_2024/predicciones_regresion.csv", "output/pm10_bootstrap/analisis.json", "output/experiments/barcelona/prueba_2024/predicciones.csv", "output/experiments/barcelona/prueba_2024/bootstrap.json"]
    save_json(ROOT / "output/experiments/comparacion/resumen.json", dict(
        testYear=2024, threshold=THRESHOLD, training="2017–2022", validation="2023", experiments=experiments,
        matchedDates=[day.strftime("%Y-%m-%d") for day in common], matched=matched,
        limitations=["Tres estaciones por territorio con composiciones de área diferentes", "Selección por cobertura histórica incluye el año de prueba", "La comparación principal usa las fechas evaluables de cada territorio; la sensibilidad utiliza fechas completas compartidas", "Cada territorio ajusta su propio modelo con la misma especificación; no se mide transferencia geográfica", "Un MAE absoluto distinto puede reflejar diferente variabilidad y nivel de PM10", "No se ha preparado meteorología ni clasificación de Barcelona en 2025"],
        sources=[dict(path=path, sha256=digest(ROOT / path)) for path in source_paths]))
    print(pd.DataFrame([dict(experiment=exp["id"], **exp["summary"]) for exp in experiments]).to_string(index=False), flush=True)
    print("Fechas completas comunes:", len(common), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["prepare", "train", "evaluate", "compare", "all"])
    stage = parser.parse_args().stage
    protected = [ROOT / path for path in ["output/pm10_final_2024/predicciones_regresion.csv", "output/pm10_bootstrap/analisis.json", "models/pm10/validation_2023/ridge.joblib"]]
    before = {str(path.relative_to(ROOT)): digest(path) for path in protected}
    for name, action in [("prepare", prepare), ("train", train), ("evaluate", evaluate), ("compare", compare)]:
        if stage in (name, "all"):
            print("Etapa:", name, flush=True)
            action()
    if any(digest(ROOT / path) != sha for path, sha in before.items()):
        raise ValueError("Cambió un artefacto protegido de Madrid.")
    save_json(OUTPUT / "integridad_madrid.json", before)


if __name__ == "__main__":
    main()
