"""Prueba provincial PM10 2017-2024 con red variable y red constante.

Ejecutar: python -m pm10_data.evaluation.historical_feasibility
No modifica originales ni exporta millones de filas horarias intermedias.
"""

from pathlib import Path
from pm10_data.config import PROJECT_ROOT
import hashlib
import json
import math
import zipfile

import pandas as pd

from pm10_data.mappers.air import (AirContext, AirQualityReader, AirQualityMapper,
                   AirQualityValidator, combine_daily_measurements, summarize_year, summarize_hours)
from pm10_data.evaluation.provincial_prototype import aggregate_provinces, select_sampling_points


YEARS = tuple(range(2017, 2025))
DTYPES = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica"]}


def select_constant_points(stations: pd.DataFrame, anios: tuple[int, ...]) -> pd.DataFrame:
    """Mismo punto (incluida técnica), elegible en todos los años solicitados."""
    if stations.duplicated(["anio", "punto_muestreo"]).any():
        raise ValueError("Hay puntos repetidos dentro de un año.")
    if not set(stations.anio).issubset(anios):
        raise ValueError("Hay años ajenos al periodo de análisis.")
    conteo = stations.groupby("punto_muestreo").anio.nunique()
    constant_points = set(conteo[conteo.eq(len(anios))].index)
    return stations.loc[stations.punto_muestreo.isin(constant_points)].copy()


def summarize_territorial_continuity(panel: pd.DataFrame, anios: tuple[int, ...]) -> pd.DataFrame:
    if panel.duplicated(["codigo_provincia", "anio"]).any():
        raise ValueError("Provincia y año repetidos.")
    registros = []
    for codigo, group in panel.groupby("codigo_provincia"):
        disponibles = group.loc[group.media_pm10_estaciones_fondo.notna(), "anio"].astype(int)
        registros.append({
            "codigo_provincia": codigo, "territorio": group.territorio.iloc[0],
            "anios_con_indicador": len(disponibles),
            "todos_los_anios": set(disponibles) == set(anios),
            "anios_sin_indicador": " | ".join(str(a) for a in anios if a not in set(disponibles)),
            "minimo_estaciones_en_periodo": int(group.n_estaciones.min()),
            "maximo_estaciones_en_periodo": int(group.n_estaciones.max()),
            "anios_con_dos_o_mas_estaciones": int(group.n_estaciones.ge(2).sum()),
        })
    return pd.DataFrame(registros)


def audit_coordinates(constant_points: pd.DataFrame) -> pd.DataFrame:
    """Distancia esférica entre coordenadas declaradas; no confirma un traslado."""
    registros = []
    for point, group in constant_points.groupby("punto_muestreo"):
        pares = [(float(a), float(b)) for a, b in zip(group.LATITUD_G, group.LONGITUD_G)]
        if not all(math.isfinite(a) and math.isfinite(b) and -90 <= a <= 90 and -180 <= b <= 180 for a, b in pares):
            raise ValueError("Coordenadas inválidas o ausentes en la red constante.")
        maxima = 0.0
        for a, b in pares:
            for c, d in pares:
                h = (math.sin(math.radians(c - a) / 2) ** 2
                     + math.cos(math.radians(a)) * math.cos(math.radians(c)) * math.sin(math.radians(d - b) / 2) ** 2)
                maxima = max(maxima, 2 * 6371000 * math.asin(min(1, math.sqrt(h))))
        registros.append({
            "punto_muestreo": point, "latitud_min": min(a for a, b in pares), "latitud_max": max(a for a, b in pares),
            "longitud_min": min(b for a, b in pares), "longitud_max": max(b for a, b in pares),
            "coordenadas_declaradas_cambian": len(set(pares)) > 1,
            "distancia_maxima_coordenadas_m": maxima,
            "revisar_diferencia_mayor_100m": maxima > 100,
            "tipo_area_cambia": group.TIPO_AREA.nunique(dropna=False) > 1,
        })
    return pd.DataFrame(registros, columns=["punto_muestreo", "latitud_min", "latitud_max", "longitud_min", "longitud_max",
                                            "coordenadas_declaradas_cambian", "distancia_maxima_coordenadas_m",
                                            "revisar_diferencia_mayor_100m", "tipo_area_cambia"])


def process_year(anio: int, raw: Path, sources: dict[str, dict]) -> tuple[pd.DataFrame, dict]:
    for f in sources.values():
        if hashlib.sha256((raw / f["file"]).read_bytes()).hexdigest() != f["sha256"]:
            raise ValueError(f"Original alterado: {f['file']}")
    excel = pd.ExcelFile(raw / sources["miteco_estaciones"]["file"])
    stations_sheet = [s for s in excel.sheet_names if "estacion" in s.lower()]
    magnitudes_sheet = [s for s in excel.sheet_names if s.lower() == "magnitudes"]
    if len(stations_sheet) != 1 or len(magnitudes_sheet) != 1:
        raise ValueError(f"Metadatos inesperados en {anio}.")
    meta = pd.read_excel(excel, sheet_name=stations_sheet[0])
    magnitudes = pd.read_excel(excel, sheet_name=magnitudes_sheet[0])
    pm10 = magnitudes.loc[magnitudes.MAGNITUD.eq(10)]
    if len(pm10) != 1 or str(pm10.iloc[0].UNIDAD).strip() != "µg/m3" or pm10.iloc[0].ABREVIATURA != "PM10":
        raise ValueError(f"No se puede confirmar PM10/unidad en {anio}.")
    meta["codigo_estacion"] = meta.COD_LOCAL.astype("string").str.zfill(8)
    if meta.codigo_estacion.duplicated().any():
        raise ValueError(f"Estación duplicada en los metadatos de {anio}.")
    fondos = set(meta.loc[meta.TIPO_ESTACION.eq("FONDO"), "codigo_estacion"])
    reader, mapper, validator = AirQualityReader(), AirQualityMapper(), AirQualityValidator()
    original_tables, contextos = {}, {}
    for frequency, tipo in [("diaria", "miteco_diarios"), ("horaria", "miteco_horarios")]:
        path = raw / sources[tipo]["file"]
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if Path(n).name.startswith("PM10_") and n.endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"CSV PM10 no identificado en {path.name}.")
        original_tables[frequency] = reader.read(path, members[0])
        contextos[frequency] = AirContext(anio, "10", "PM10", "µg/m3", path.name, members[0])
    horas = original_tables["horaria"]
    hourly_points = set(horas.PUNTO_MUESTREO)
    candidatos = {p for p in hourly_points if str(p).split("_")[0] in fondos and not str(p).endswith("_M")}
    if not candidatos:
        raise ValueError(f"No hay puntos horarios de fondo en {anio}.")
    horas = horas.loc[horas.PUNTO_MUESTREO.isin(candidatos)].copy()
    if horas.duplicated([c for c in horas.columns if not c.startswith("H")]).any():
        raise ValueError("Hay días horarios duplicados antes de procesar por bloques.")
    original_tables["diaria"] = original_tables["diaria"].loc[original_tables["diaria"].PUNTO_MUESTREO.isin(candidatos)].copy()
    # En algunos años los diarios solo contienen puntos manuales. No inventar
    # registros oficiales para los automáticos: sus días se derivan de horas.
    daily = None
    if not original_tables["diaria"].empty:
        daily = mapper.transform(original_tables["diaria"], contextos["diaria"], "diaria")
        validator.validate(daily, "diaria")
    derivados = []
    for inicio in range(0, len(horas), 5000):
        hourly = mapper.transform(horas.iloc[inicio:inicio + 5000], contextos["horaria"], "horaria")
        validator.validate(hourly, "horaria")
        derivados.append(summarize_hours(hourly, minimum_hours=18))
    derived = pd.concat(derivados, ignore_index=True)
    if daily is None:
        daily = derived.iloc[:0].copy()
    combined, overlaps = combine_daily_measurements(daily, derived)
    validator.validate(combined, "diaria")
    anual = summarize_year(combined, anio, minimum_coverage=0.75)
    anual = anual.merge(meta[["codigo_estacion", "NOMBRE", "TIPO_ESTACION", "TIPO_AREA", "LATITUD_G", "LONGITUD_G"]],
                        on="codigo_estacion", validate="many_to_one", how="left")
    anual = select_sampling_points(anual, hourly_points)
    audit_info = {
        "anio": anio, "puntos_candidatos_fondo_con_horas": len(anual),
        "puntos_seleccionados": int(anual.seleccion_provisional.sum()),
        "dias_punto_combinados": len(combined),
        "dias_validos": int(combined.estado.eq("valida").sum()),
        "negativos_seleccionados_para_revision": int(combined.estado.eq("negativa_pendiente_revision").sum()),
        "maxima_diferencia_diario_horario": float(overlaps.diferencia_absoluta.max()) if overlaps.diferencia_absoluta.notna().any() else None,
        "archivo_diario": sources["miteco_diarios"]["file"],
        "archivo_horario": sources["miteco_horarios"]["file"],
        "archivo_metadatos": sources["miteco_estaciones"]["file"],
        "hoja_estaciones": stations_sheet[0],
    }
    return anual, audit_info


def join_health_data(sanidad: pd.DataFrame, aggregated: pd.DataFrame) -> pd.DataFrame:
    panel = sanidad.merge(aggregated, on=["codigo_provincia", "anio"], how="left", validate="one_to_one", indicator="cruce_ambiental")
    panel["hay_indicador_pm10"] = panel.cruce_ambiental.eq("both")
    for c in ["n_estaciones", "n_urbanas", "n_suburbanas", "n_rurales", "n_area_no_clasificada"]:
        panel[c] = panel[c].fillna(0).astype("Int64")
    return panel


def main():
    root = PROJECT_ROOT
    raw = root / "data/raw/health_air_history"
    destination = root / "data/interim/provincial_feasibility/history"
    destination.mkdir(parents=True, exist_ok=True)
    sources = json.loads((raw / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    tables, audits = [], []
    for anio in YEARS:
        annual_sources = {f["kind"]: f for f in sources if f["year"] == anio and f["status"] == "downloaded" and f["kind"] in {"miteco_diarios", "miteco_horarios", "miteco_estaciones"}}
        if len(annual_sources) != 3:
            raise ValueError(f"Faltan fuentes de {anio}.")
        anual, audit_info = process_year(anio, raw, annual_sources)
        anual.to_csv(destination / f"seleccion_estaciones_pm10_{anio}.csv", index=False, encoding="utf-8-sig")
        (destination / f"auditoria_{anio}.json").write_text(json.dumps(audit_info, ensure_ascii=False, indent=2), encoding="utf-8")
        tables.append(anual)
        audits.append(audit_info)
        print(f"{anio}: {audit_info['puntos_seleccionados']} puntos seleccionados de {len(anual)} candidatos.", flush=True)
    all_rows = pd.concat(tables, ignore_index=True)
    selected = all_rows.loc[all_rows.seleccion_provisional].copy()
    constant_points = select_constant_points(selected, YEARS)
    aggregated = aggregate_provinces(all_rows)
    # Red constante vacía sería un resultado de inviabilidad, no un promedio cero.
    if constant_points.empty:
        agregado_constante = aggregated.iloc[:0].copy()
    else:
        agregado_constante = aggregate_provinces(constant_points)
    health = pd.read_csv(root / "data/interim/health/tasas_respiratorias_provincias.csv",
                       dtype={"codigo_provincia": "string", "codigo_diagnostico": "string"})
    health = health.loc[health.anio.isin(YEARS) & health.codigo_diagnostico.eq("1000")].copy()
    if len(health) != 52 * len(YEARS):
        raise ValueError("El panel sanitario no tiene las 52 provincias/territorios por año.")
    variable = join_health_data(health, aggregated)
    constante = join_health_data(health, agregado_constante)
    continuity = summarize_territorial_continuity(variable, YEARS)
    continuidad_constante = summarize_territorial_continuity(constante, YEARS)
    cobertura = variable.groupby("anio", as_index=False).agg(
        territorios_con_pm10=("hay_indicador_pm10", "sum"), estaciones_seleccionadas=("n_estaciones", "sum"))
    cobertura["territorios_red_constante"] = constante.groupby("anio").hay_indicador_pm10.sum().reindex(cobertura.anio).to_numpy()
    # Detecta cambios en los puntos usados, sin confundirlos con aperturas o averías.
    cambios = []
    for provincia in sorted(health.codigo_provincia.unique()):
        anterior = None
        for anio in YEARS:
            actuales = set(selected.loc[selected.codigo_provincia.eq(provincia) & selected.anio.eq(anio), "punto_muestreo"])
            cambios.append({"codigo_provincia": provincia, "anio": anio,
                            "puntos_que_entran_en_seleccion": len(actuales - anterior) if anterior is not None else None,
                            "puntos_que_salen_de_seleccion": len(anterior - actuales) if anterior is not None else None,
                            "cambia_seleccion_respecto_anio_anterior": actuales != anterior if anterior is not None else None})
            anterior = actuales
    coordinates = audit_coordinates(constant_points)
    resultados = {
        "panel_red_variable": variable, "panel_red_constante": constante,
        "continuidad_provincial_red_variable": continuity, "continuidad_provincial_red_constante": continuidad_constante,
        "cobertura_por_anio": cobertura, "cambios_seleccion_por_provincia": pd.DataFrame(cambios),
        "puntos_red_constante": constant_points, "revision_coordenadas_red_constante": coordinates,
        "auditoria_anios": pd.DataFrame(audits),
    }
    for name, table in resultados.items():
        table.to_csv(destination / f"{name}.csv", index=False, encoding="utf-8-sig")
    summary = {
        "anios": list(YEARS), "filas_provincia_anio_por_panel": len(variable),
        "filas_con_pm10_red_variable": int(variable.hay_indicador_pm10.sum()),
        "territorios_con_pm10_todos_anios_red_variable": int(continuity.todos_los_anios.sum()),
        "puntos_elegibles_todos_anios": int(constant_points.punto_muestreo.nunique()),
        "territorios_red_constante": int(continuidad_constante.todos_los_anios.sum()),
        "filas_con_pm10_red_constante": int(constante.hay_indicador_pm10.sum()),
        "territorios_red_constante_con_dos_o_mas_estaciones_todos_anios": int(continuidad_constante.minimo_estaciones_en_periodo.ge(2).sum()),
        "puntos_constantes_con_coordenadas_declaradas_distintas": int(coordinates.coordenadas_declaradas_cambian.sum()),
        "puntos_constantes_con_diferencia_coordenadas_mayor_100m": int(coordinates.revisar_diferencia_mayor_100m.sum()),
        "puntos_constantes_con_tipo_area_distinto": int(coordinates.tipo_area_cambia.sum()),
        "pendiente": "2016 sigue fuera de esta prueba por formato Excel horario. Faltan demografía, revisión de comparabilidad sanitaria y representatividad, y validación predictiva temporal.",
        "advertencia": "Red constante significa mismo punto elegible, no prueba de idéntica ubicación o equipo. Cruces descriptivos del mismo año; no son aún tablas predictivas.",
    }
    (destination / "resumen_historico.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(cobertura.to_string(index=False), flush=True)
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == "__main__":
    main()
