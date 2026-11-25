"""Muestra PM10 2024. Ejecutar: python -m pm10_data.pipelines.prepare_air"""

from pathlib import Path
from pm10_data.config import PROJECT_ROOT
import gzip
import hashlib
import json
import zipfile

import pandas as pd

from pm10_data.mappers.air import (AirContext, AirQualityReader, AirQualityMapper,
                   AirQualityValidator, combine_daily_measurements, summarize_year, summarize_hours)


def main():
    root = PROJECT_ROOT
    source = root / "data/raw/health_air_history"
    output = root / "data/interim/air/pm10_2024"
    sources = json.loads((source / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    selected = {f["kind"]: f for f in sources if f["year"] == 2024 and f["status"] == "downloaded" and f["kind"].startswith("miteco_")}
    for source_info in selected.values():
        if hashlib.sha256((source / source_info["file"]).read_bytes()).hexdigest() != source_info["sha256"]:
            raise ValueError("Un original no coincide con su huella guardada.")
    magnitudes = pd.read_excel(source / selected["miteco_estaciones"]["file"], sheet_name="Magnitudes")
    pm10 = magnitudes.loc[magnitudes.MAGNITUD.eq(10)]
    if len(pm10) != 1 or pm10.iloc[0].ABREVIATURA != "PM10":
        raise ValueError("No se ha podido verificar la magnitud PM10.")
    unidad = str(pm10.iloc[0].UNIDAD).strip()
    if unidad != "µg/m3":
        raise ValueError(f"Unidad inesperada: {unidad}")

    reader, mapper, validator = AirQualityReader(), AirQualityMapper(), AirQualityValidator()
    original_tables = {}
    contextos = {}
    for frequency, tipo in [("diaria", "miteco_diarios"), ("horaria", "miteco_horarios")]:
        source_info = selected[tipo]
        path = source / source_info["file"]
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if Path(n).name.startswith("PM10_") and n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError("Se esperaba un único CSV de PM10.")
        context = AirContext(2024, "10", "PM10", unidad, path.name, members[0])
        original_tables[frequency] = reader.read(path, members[0])
        contextos[frequency] = context

    daily = mapper.transform(original_tables["diaria"], contextos["diaria"], "diaria")
    validator.validate(daily, "diaria")
    output.mkdir(parents=True, exist_ok=True)
    daily.to_csv(output / "mediciones_diarias.csv.gz", index=False, date_format="%Y-%m-%d", compression={"method": "gzip", "compresslevel": 1})

    # Procesamos las horas por bloques para no mantener millones de filas en memoria.
    original_horas = original_tables["horaria"]
    if original_horas.duplicated([c for c in original_horas.columns if not c.startswith("H")]).any():
        raise ValueError("Hay días horarios duplicados entre bloques.")
    derivados = []
    estados_hora = {}
    filas_hora = 0
    with gzip.open(output / "mediciones_horarias.csv.gz", "wt", encoding="utf-8", newline="", compresslevel=1) as file:
        for inicio in range(0, len(original_horas), 5000):
            bloque = original_horas.iloc[inicio:inicio + 5000]
            hourly = mapper.transform(bloque, contextos["horaria"], "horaria")
            validator.validate(hourly, "horaria")
            # ISO 8601 explícito solo al exportar; los cálculos conservan datetime UTC.
            exportable = hourly.assign(fin_periodo_utc=hourly.fin_periodo_utc.dt.strftime("%Y-%m-%dT%H:%M:%SZ"))
            exportable.to_csv(file, index=False, header=inicio == 0)
            derivados.append(summarize_hours(hourly, minimum_hours=18))
            filas_hora += len(hourly)
            for estado, count in hourly.estado.value_counts().items():
                estados_hora[estado] = estados_hora.get(estado, 0) + int(count)
    derived = pd.concat(derivados, ignore_index=True)
    combined, overlaps = combine_daily_measurements(daily, derived)
    validator.validate(combined, "diaria")
    anual = summarize_year(combined, 2024, minimum_coverage=0.75)

    stations = pd.read_excel(source / selected["miteco_estaciones"]["file"], sheet_name="Estaciones_2024")
    stations["codigo_estacion"] = stations.COD_LOCAL.astype("string").str.zfill(8)
    if stations.codigo_estacion.duplicated().any():
        raise ValueError("Metadatos de estación duplicados.")
    anual = anual.merge(stations[["codigo_estacion", "NOMBRE", "TIPO_ESTACION", "TIPO_AREA"]],
                        on="codigo_estacion", how="left", validate="many_to_one", indicator="estado_metadatos")
    for name, table in [("diarias_derivadas_horarias", derived), ("diarias_combinadas", combined), ("solapamientos", overlaps)]:
        table.to_csv(output / f"{name}.csv.gz", index=False, date_format="%Y-%m-%d", compression={"method": "gzip", "compresslevel": 1})
    anual.to_csv(output / "resumen_anual_punto_muestreo.csv", index=False, encoding="utf-8-sig")
    incidencias = daily.loc[daily.estado.eq("negativa_pendiente_revision")]
    incidencias.to_csv(output / "incidencias_diarias.csv", index=False, encoding="utf-8-sig")
    summary = {
        "anio": 2024, "contaminante": "PM10", "unidad": unidad,
        "filas_diarias_normalizadas": len(daily), "estados_diarios": daily.estado.value_counts().to_dict(),
        "filas_horarias_normalizadas": filas_hora, "estados_horarios": estados_hora,
        "dias_punto_combinados": len(combined), "puntos_muestreo": len(anual),
        "estaciones": int(anual.codigo_estacion.nunique()),
        "codigos_provinciales": int(anual.codigo_provincia.nunique()),
        "puntos_con_cobertura_75": int(anual.cumple_criterio_exploratorio.sum()),
        "filas_solapadas_mismo_punto_dia": len(overlaps),
        "solapamientos_con_ambas_medidas_validas": int(overlaps.diferencia_absoluta.notna().sum()),
        "diferencia_maxima_solapamientos": float(overlaps.diferencia_absoluta.max()) if overlaps.diferencia_absoluta.notna().any() else None,
        "puntos_sin_metadatos_estacion": int(anual.estado_metadatos.eq("left_only").sum()),
        "minimo_horas_diarias": 18, "minimo_cobertura_anual": 0.75,
        "advertencia": "Criterios exploratorios, sin evaluación normativa ni exposición provincial. No se han unido datos sanitarios.",
    }
    (output / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
