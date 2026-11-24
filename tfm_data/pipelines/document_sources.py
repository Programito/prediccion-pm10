"""Build source and transformation inventories from local manifests and tables.

Run: python -m tfm_data.pipelines.document_sources
This reads existing files; it does not download data or retrain models.
"""

from pathlib import Path
import hashlib
import json
import zipfile

import pandas as pd

from tfm_data.config import PROJECT_ROOT
from tfm_data.pipelines.source_schemas import write_source_schemas


MANIFESTS = [
    ("health_air_history", "data/raw/health_air_history/sources.json"),
    ("demographics", "data/raw/demographics/source.json"),
    ("initial_feasibility_sample", "data/raw/health_air_feasibility/sources.json"),
]

TABLES = [
    ("health/tasas_respiratorias_todos_niveles.csv", "INEHealthMapper", "mapped", "Territorio, año y diagnóstico; incluye agregados"),
    ("health/tasas_respiratorias_provincias.csv", "INEHealthMapper + provincial selection", "mapped", "Provincia/territorio provincial, año y diagnóstico"),
    ("demographics/seleccion_original_enero_2017_2024.csv", "prepare_demographics", "filtered_source", "Provincia, edad y fecha de referencia; incluye subtotales"),
    ("demographics/demografia_provincial_2017_2024.csv", "INEDemographicsMapper", "mapped", "Provincia y año, población a 1 de enero"),
    ("air/pm10_2024/mediciones_diarias.csv.gz", "AirQualityMapper", "mapped", "Punto de muestreo y día; conserva ausencias"),
    ("air/pm10_2024/mediciones_horarias.csv.gz", "AirQualityMapper", "mapped", "Punto de muestreo y hora de fin UTC"),
    ("air/pm10_2024/diarias_derivadas_horarias.csv.gz", "summarize_hours", "aggregated", "Punto de muestreo y día, derivado de horas"),
    ("air/pm10_2024/diarias_combinadas.csv.gz", "combine_daily_measurements", "combined", "Punto de muestreo y día, sin duplicar fuentes"),
    ("air/pm10_2024/resumen_anual_punto_muestreo.csv", "summarize_year + station metadata", "aggregated", "Punto de muestreo y año"),
    ("air/pm10_2024/solapamientos.csv.gz", "combine_daily_measurements", "audit", "Punto y día presente en ambas fuentes"),
    ("air/pm10_2024/incidencias_diarias.csv", "daily measurement selection", "audit", "Medición diaria negativa pendiente de revisión"),
    ("air/pm10_2024/auditoria_cobertura_mensual.csv", "AirCoverageAuditor", "audit", "Punto de muestreo y mes, calendario completo"),
    ("air/pm10_2024/auditoria_mensual_puntos_baja_cobertura.csv", "AirCoverageAuditor + low coverage selection", "audit", "Punto con baja cobertura anual y mes"),
    ("air/pm10_2024/revision_puntos_baja_cobertura.csv", "review_sampling_points", "audit", "Punto con baja cobertura anual y evidencia de revisión"),
    ("provincial_feasibility/history/panel_red_variable.csv", "aggregate_provinces + join_health_data", "joined", "Provincia y año, selección de estaciones variable"),
    ("provincial_feasibility/history/panel_red_constante.csv", "select_constant_points + aggregate_provinces", "joined", "Provincia y año, mismos puntos en el periodo"),
    ("daily_pollution/estaciones_muestra_madrid.csv", "select_sample", "selection", "Estación seleccionada y criterio de cobertura"),
    ("daily_pollution/pm10_madrid_diario_2017_2024.csv", "AirQualityMapper + daily aggregation + sample selection", "combined", "Estación y día, calendario completo de la muestra"),
    ("daily_pollution/cobertura_muestra_por_anio.csv", "pollution_sample", "audit", "Estación seleccionada y año"),
    ("pm10_prediction/tabla_supervisada_pm10.csv", "PM10ForecastMapper + label_elevated_pm10", "features", "Estación, día observado t y objetivo t+1; incluye filas no utilizables"),
    ("pm10_prediction/tabla_modelos_completa.csv", "PM10ForecastMapper + complete row selection", "features", "Estación y fecha objetivo con variables y objetivo completos"),
    ("initial_comparison/panel_con_demografia.csv", "initial_health_comparison", "joined", "Provincia y año, cruce sanitario-ambiental-demográfico"),
]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_inventory() -> pd.DataFrame:
    rows = []
    for scope, name in MANIFESTS:
        manifest_path = PROJECT_ROOT / name
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        entries = manifest.get("sources", manifest.get("files", [manifest]))
        for entry in entries:
            if entry.get("status", "downloaded") != "downloaded":
                continue
            path = manifest_path.parent / entry["file"]
            digest = file_hash(path)
            if digest != entry["sha256"].lower():
                raise ValueError(f"Original does not match its manifest: {path.name}")
            members, payloads = [], []
            if path.suffix.lower() == ".zip":
                with zipfile.ZipFile(path) as archive:
                    members = [m.filename for m in archive.infolist() if not m.is_dir()]
                    payloads = sorted({Path(m).suffix.lower().lstrip(".") for m in members})
            source_url = entry.get("source_url", "")
            year = entry.get("year")
            if year is None and scope == "initial_feasibility_sample":
                year = 2024
            is_csv = path.suffix.lower() == ".csv"
            with path.open("rb") as stream:
                bom = stream.read(3) == b"\xef\xbb\xbf" if is_csv else False
            rows.append({
                "scope": scope, "source_kind": entry.get("kind", "population_age" if scope == "demographics" else path.stem),
                "year": year, "method": "GET", "download_url": source_url,
                "catalog_url": entry.get("catalog_url", ""),
                "format": path.suffix.lower().lstrip("."), "payload_formats": " | ".join(payloads),
                "csv_delimiter": ";" if is_csv or "csv" in payloads else "",
                "direct_csv_encoding": ("UTF-8 with BOM" if bom else "UTF-8, no BOM observed") if is_csv else "",
                "archive_members": " | ".join(members),
                "local_file": path.relative_to(PROJECT_ROOT).as_posix(),
                "downloaded_on": manifest.get("retrieved_on", manifest.get("download_date", "")),
                "size_bytes": path.stat().st_size, "sha256": digest,
                "manifest_file": name, "local_integrity_verified": True,
            })
    return pd.DataFrame(rows)


def table_inventory() -> pd.DataFrame:
    rows = []
    for name, producer, stage, grain in TABLES:
        path = PROJECT_ROOT / "data/interim" / name
        if not path.exists():
            raise FileNotFoundError(path)
        header = pd.read_csv(path, nrows=0).columns.tolist()
        count = sum(len(block) for block in pd.read_csv(path, usecols=[0], chunksize=200000))
        rows.append({"table_file": path.relative_to(PROJECT_ROOT).as_posix(), "producer": producer,
                     "stage": stage, "row_grain": grain, "rows": count,
                     "column_count": len(header), "columns": " | ".join(header),
                     "format": "csv.gz" if path.name.endswith(".csv.gz") else "csv",
                     "delimiter": ",", "size_bytes": path.stat().st_size})
    return pd.DataFrame(rows)


def main():
    destination = PROJECT_ROOT / "docs/reference"
    destination.mkdir(parents=True, exist_ok=True)
    sources = source_inventory()
    tables = table_inventory()
    source_table_count, schema_count = write_source_schemas(sources, destination)
    source_tables = pd.read_csv(destination / "source_tables.csv")
    sources.to_csv(destination / "source_catalog.csv", index=False, encoding="utf-8-sig")
    tables.to_csv(destination / "table_catalog.csv", index=False, encoding="utf-8-sig")
    lines = ["# URLs exactas de las descargas registradas", "",
             "Generado desde los manifiestos locales. Las URLs se registran como descargas HTTP GET públicas; no son endpoints propios de una aplicación.", "",
             "Se incluyen las 37 fuentes principales y las tres copias de la muestra inicial de 2024. No es un log completo de solicitudes HTTP exploratorias, errores o redirecciones.", "",
             "Cada enlace de la última columna lleva a las columnas y tipos de las tablas originales contenidas en esa descarga. El [inventario de tablas](source_tables.csv) identifica los miembros de ZIP y las hojas de Excel; el [diccionario de columnas](source_columns.csv) conserva el detalle por tabla.", "",
             "| Ámbito / tipo | Año | Formato y contenido | Descarga registrada | Archivo original | Tablas y esquemas de columnas |",
             "| --- | --- | --- | --- | --- | --- |"]
    for row in sources.itertuples():
        year = str(int(row.year)) if pd.notna(row.year) else "Serie histórica"
        file_format = row.format.upper() + (f" ({row.payload_formats.upper()})" if row.payload_formats else "")
        selected = source_tables.loc[source_tables.local_file.eq(row.local_file)]
        links = ", ".join(f"[{schema}](source_schemas.md#{schema})" for schema in selected.schema_id.unique())
        lines.append(f"| {row.scope} / {row.source_kind} | {year} | {file_format} | [GET]({row.download_url}) | [{Path(row.local_file).name}](../../{row.local_file}) | {len(selected)} tablas: {links} |")
    lines += ["", "El catálogo CSV adjunto conserva además páginas de catálogo, fecha de descarga registrada, miembros de cada ZIP, tamaño, SHA-256 y ruta del manifiesto.", "",
              "Las fechas registradas en los manifiestos son de descarga. No se han reconstruido fechas de publicación ni códigos de respuesta HTTP que no se guardaron."]
    lines += ["", "## Piloto de previsiones meteorológicas", "",
              "El archivo NOAA GFS en Amazon S3 se consultó mediante índices `.idx` y rangos de bytes GRIB2. El manifiesto del piloto registra las URLs y rangos de sus 16 mensajes. [Peticiones del piloto](../../output/pm10_weather_feasibility/mensajes_gfs.json) · [Campos, tipos y mapeo](../22_viabilidad_meteorologia_pm10.md)"]
    (destination / "source_endpoints.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Inventario verificado: {len(sources)} originales registrados y {len(tables)} tablas principales.")
    print(f"Cabeceras inspeccionadas: {source_table_count} tablas originales, {schema_count} esquemas de columnas.")


if __name__ == "__main__":
    main()
