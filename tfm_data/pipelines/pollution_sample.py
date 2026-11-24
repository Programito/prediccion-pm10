"""Selecciona y prepara tres series diarias de PM10 en Madrid, 2017-2024.

Ejecutar: python -m tfm_data.pipelines.pollution_sample
"""

from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import hashlib
import json
import zipfile

import pandas as pd

from tfm_data.mappers.air import AirContext, AirQualityReader, AirQualityMapper, AirQualityValidator, combine_daily_measurements, summarize_hours


def select_sample(points: pd.DataFrame, alerts: pd.DataFrame) -> pd.DataFrame:
    excluded = set(alerts.loc[alerts.revisar_diferencia_mayor_100m | alerts.tipo_area_cambia, "punto_muestreo"])
    madrid = points.loc[points.codigo_provincia.eq("28") & ~points.punto_muestreo.isin(excluded)].copy()
    summary = madrid.groupby(["punto_muestreo", "codigo_estacion", "NOMBRE", "TIPO_AREA"], as_index=False).agg(
        anios=("anio", "nunique"), cobertura_minima=("cobertura_anual", "min"), cobertura_media=("cobertura_anual", "mean"))
    summary = summary.loc[summary.anios.eq(8)]
    selected = []
    for tipo in ["URBANA", "SUBURBANA", "RURAL"]:
        candidates = summary.loc[summary.TIPO_AREA.eq(tipo)].sort_values(
            ["cobertura_minima", "cobertura_media", "codigo_estacion"], ascending=[False, False, True])
        if candidates.empty:
            raise ValueError(f"No hay una serie continua de área {tipo}.")
        selected.append(candidates.iloc[[0]])
    return pd.concat(selected, ignore_index=True)


def main():
    root = PROJECT_ROOT
    historico = root / "data/interim/provincial_feasibility/history"
    raw = root / "data/raw/health_air_history"
    destination = root / "data/interim/daily_pollution"
    tipos = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica"]}
    points = pd.read_csv(historico / "puntos_red_constante.csv", dtype=tipos)
    alerts = pd.read_csv(historico / "revision_coordenadas_red_constante.csv", dtype=tipos)
    muestra = select_sample(points, alerts)
    selected_points = set(muestra.punto_muestreo)
    sources = json.loads((raw / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    reader, mapper, validator = AirQualityReader(), AirQualityMapper(), AirQualityValidator()
    series = []
    for anio in range(2017, 2025):
        selected = {f["kind"]: f for f in sources if f["year"] == anio and f["status"] == "downloaded" and f["kind"] in {"miteco_diarios", "miteco_horarios"}}
        if len(selected) != 2:
            raise ValueError(f"Faltan fuentes en {anio}.")
        tables = {}
        for frequency, tipo in [("diaria", "miteco_diarios"), ("horaria", "miteco_horarios")]:
            source_info = selected[tipo]
            path = raw / source_info["file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != source_info["sha256"]:
                raise ValueError(f"Original alterado: {path.name}")
            with zipfile.ZipFile(path) as z:
                names = [n for n in z.namelist() if Path(n).name.startswith("PM10_") and n.endswith(".csv")]
            if len(names) != 1:
                raise ValueError("No se pudo identificar el CSV PM10.")
            original = reader.read(path, names[0])
            original = original.loc[original.PUNTO_MUESTREO.isin(selected_points)].copy()
            if original.empty:
                if frequency == "horaria":
                    raise ValueError(f"Faltan datos horarios en {anio}.")
                tables[frequency] = None
                continue
            context = AirContext(anio, "10", "PM10", "µg/m3", path.name, names[0])
            normalizada = mapper.transform(original, context, frequency)
            validator.validate(normalizada, frequency)
            tables[frequency] = normalizada
        derived = summarize_hours(tables["horaria"])
        daily = tables["diaria"] if tables["diaria"] is not None else derived.iloc[:0].copy()
        combined, _ = combine_daily_measurements(daily, derived)
        validator.validate(combined, "diaria")
        calendar_grid = pd.DataFrame({"fecha": pd.date_range(f"{anio}-01-01", f"{anio}-12-31")})
        rejilla = muestra[["punto_muestreo", "codigo_estacion", "NOMBRE", "TIPO_AREA"]].merge(calendar_grid, how="cross")
        columns = ["punto_muestreo", "fecha", "concentracion", "estado", "origen_diario", "n_horas_validas", "archivo_origen", "miembro_zip"]
        table = rejilla.merge(combined[columns], on=["punto_muestreo", "fecha"], how="left", validate="one_to_one", indicator=True)
        table.loc[table._merge.eq("left_only"), "estado"] = "sin_registro"
        table["pm10_valido"] = table.concentracion.where(table.estado.eq("valida"))
        table["anio"] = anio
        table["codigo_provincia"] = "28"
        table["unidad"] = "µg/m3"
        series.append(table.drop(columns="_merge"))
        print(f"{anio}: {table.estado.eq('valida').sum()} días-punto válidos de {len(table)}.", flush=True)
    completa = pd.concat(series, ignore_index=True).sort_values(["codigo_estacion", "fecha"])
    if completa.duplicated(["codigo_estacion", "fecha"]).any():
        raise ValueError("Fechas repetidas por estación.")
    for _, group in completa.groupby("codigo_estacion"):
        if not group.fecha.diff().dropna().eq(pd.Timedelta(days=1)).all():
            raise ValueError("El calendario diario tiene saltos.")
    completa["es_valido"] = completa.estado.eq("valida")
    cobertura = completa.groupby(["codigo_estacion", "NOMBRE", "TIPO_AREA", "anio"], as_index=False).agg(
        dias_naturales=("fecha", "size"), dias_validos=("es_valido", "sum"))
    cobertura["cobertura"] = cobertura.dias_validos / cobertura.dias_naturales
    destination.mkdir(parents=True, exist_ok=True)
    muestra.to_csv(destination / "estaciones_muestra_madrid.csv", index=False, encoding="utf-8-sig")
    completa.to_csv(destination / "pm10_madrid_diario_2017_2024.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    cobertura.to_csv(destination / "cobertura_muestra_por_anio.csv", index=False, encoding="utf-8-sig")
    summary = {"filas": len(completa), "dias_validos": int(completa.es_valido.sum()), "dias_no_validos": int((~completa.es_valido).sum()),
               "estaciones": muestra[["codigo_estacion", "NOMBRE", "TIPO_AREA", "cobertura_minima"]].to_dict("records"),
               "nota": "Muestra exploratoria elegida por cobertura histórica; no hay imputación, variables predictivas ni entrenamiento todavía. No representa toda la exposición provincial."}
    (destination / "resumen_muestra.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
