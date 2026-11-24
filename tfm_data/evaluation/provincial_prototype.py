"""Prueba descriptiva de cruce provincial para 2024; no entrena modelos."""

from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import json

import pandas as pd


def select_sampling_points(anual: pd.DataFrame, hourly_points: set[str]) -> pd.DataFrame:
    table = anual.copy()
    table["es_fondo"] = table.TIPO_ESTACION.eq("FONDO")
    table["tiene_serie_horaria"] = table.punto_muestreo.isin(hourly_points)
    table["es_tecnica_no_manual"] = table.tecnica.ne("M")
    table["seleccion_provisional"] = (table.es_fondo & table.tiene_serie_horaria
                                       & table.es_tecnica_no_manual & table.cumple_criterio_exploratorio)
    # Estas banderas explican la selección; no borran los puntos originales.
    return table


def aggregate_provinces(selection: pd.DataFrame) -> pd.DataFrame:
    selected = selection.loc[selection.seleccion_provisional].copy()
    if selected.empty:
        raise ValueError("No hay estaciones seleccionadas.")
    if selected.duplicated(["anio", "codigo_estacion"]).any():
        raise ValueError("Una estación tiene varios puntos seleccionados: resolver su peso antes de agregar.")
    if selected.media_anual_analisis.isna().any():
        raise ValueError("Una serie seleccionada no tiene media anual aceptada.")
    selected["urbana"] = selected.TIPO_AREA.eq("URBANA").astype(int)
    selected["suburbana"] = selected.TIPO_AREA.eq("SUBURBANA").astype(int)
    selected["rural"] = selected.TIPO_AREA.fillna("").str.startswith("RURAL").astype(int)
    aggregated = selected.groupby(["codigo_provincia", "anio"], as_index=False).agg(
        media_pm10_estaciones_fondo=("media_anual_analisis", "mean"),
        minimo_medias_estacion=("media_anual_analisis", "min"),
        maximo_medias_estacion=("media_anual_analisis", "max"),
        n_estaciones=("codigo_estacion", "nunique"),
        cobertura_minima_estacion=("cobertura_anual", "min"),
        cobertura_media_estaciones=("cobertura_anual", "mean"),
        n_urbanas=("urbana", "sum"), n_suburbanas=("suburbana", "sum"), n_rurales=("rural", "sum"))
    aggregated["n_area_no_clasificada"] = aggregated.n_estaciones - aggregated.n_urbanas - aggregated.n_suburbanas - aggregated.n_rurales
    aggregated["unidad_pm10"] = "µg/m3"
    aggregated["metodo_pm10"] = "Media simple de medias anuales de estaciones seleccionadas; sin ponderar por población."
    return aggregated


def main():
    root = PROJECT_ROOT
    aire = root / "data/interim/air/pm10_2024"
    destination = root / "data/interim/provincial_feasibility"
    tipos = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "tecnica"]}
    anual = pd.read_csv(aire / "resumen_anual_punto_muestreo.csv", dtype=tipos)
    horarios = pd.read_csv(aire / "diarias_derivadas_horarias.csv.gz", usecols=["punto_muestreo"], dtype="string")
    selection = select_sampling_points(anual, set(horarios.punto_muestreo))
    provincias = aggregate_provinces(selection)
    sanidad = pd.read_csv(root / "data/interim/health/tasas_respiratorias_provincias.csv",
                         dtype={"codigo_provincia": "string", "codigo_diagnostico": "string"})
    sanidad = sanidad.loc[sanidad.anio.eq(2024) & sanidad.codigo_diagnostico.eq("1000"),
                         ["codigo_provincia", "anio", "territorio", "codigo_diagnostico", "tasa_altas_por_100000", "fuente_tabla", "archivo_origen"]]
    if len(sanidad) != 52 or sanidad.duplicated(["codigo_provincia", "anio"]).any():
        raise ValueError("La referencia sanitaria provincial de 2024 no tiene las 52 claves esperadas.")
    result = sanidad.merge(provincias, on=["codigo_provincia", "anio"], how="left", validate="one_to_one", indicator="cruce_ambiental")
    if set(provincias.codigo_provincia) - set(sanidad.codigo_provincia):
        raise ValueError("Hay códigos ambientales sin correspondencia sanitaria.")
    result["hay_indicador_pm10"] = result.cruce_ambiental.eq("both")
    result["solo_una_estacion"] = result.n_estaciones.eq(1)
    # Los recuentos sin estaciones son cero; las concentraciones ausentes siguen vacías.
    for column in ["n_estaciones", "n_urbanas", "n_suburbanas", "n_rurales", "n_area_no_clasificada"]:
        result[column] = result[column].fillna(0).astype("Int64")
    result["interpretacion"] = "Cruce descriptivo del mismo año; no es exposición poblacional ni previsión sanitaria."
    destination.mkdir(parents=True, exist_ok=True)
    selection.to_csv(destination / "seleccion_estaciones_pm10_2024.csv", index=False, encoding="utf-8-sig")
    result.to_csv(destination / "prototipo_pm10_sanidad_2024.csv", index=False, encoding="utf-8-sig")
    summary = {
        "anio": 2024, "puntos_revisados": len(selection),
        "estaciones_seleccionadas": int(selection.seleccion_provisional.sum()),
        "territorios_con_cruce": int(result.hay_indicador_pm10.sum()),
        "territorios_sin_indicador_pm10": result.loc[~result.hay_indicador_pm10, "territorio"].tolist(),
        "territorios_con_una_estacion": int(result.solo_una_estacion.sum()),
        "territorios_con_dos_o_mas_estaciones": int(result.n_estaciones.ge(2).sum()),
        "nota": "Prueba de un año; falta evaluar continuidad histórica, representatividad territorial y demografía. No se han entrenado modelos ni inferido causalidad.",
    }
    (destination / "resumen_2024.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
