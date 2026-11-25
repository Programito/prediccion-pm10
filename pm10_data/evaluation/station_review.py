"""Evidencia y propuestas para puntos con cobertura baja. No elimina mediciones.

Ejecutar: python -m pm10_data.evaluation.station_review
"""

from pathlib import Path
from pm10_data.config import PROJECT_ROOT
import hashlib
import json

import pandas as pd


def propose_treatment(tecnica: str, meses_vacios: int, intervalo_parcial: bool) -> tuple[str, str]:
    """Reglas explícitas de revisión, sin atribuir causas a la falta de datos."""
    if tecnica == "M":
        return ("revisar_plan_muestreo_manual",
                "Conservar. Verificar calendario manual y representatividad temporal antes de aplicar un umbral diario o usar la media anual.")
    if intervalo_parcial:
        return ("revisar_intervalo_declarado_estacion",
                "Conservar como serie parcial. Contrastar las fechas de estación con las del punto; no tratar el periodo observado como un año completo.")
    if meses_vacios:
        return ("revisar_meses_sin_medidas",
                "Conservar. Revisar huecos y el historial del equipo con la red; mantener pendiente su media anual principal.")
    return ("revisar_cobertura_discontinua",
            "Conservar. Examinar frecuencia, distribución de días y disponibilidad del equipo; mantener pendiente su media anual principal.")


def review_sampling_points(low_coverage: pd.DataFrame, monthly: pd.DataFrame,
                   daily: pd.DataFrame, stations: pd.DataFrame, anio: int) -> pd.DataFrame:
    """Une evidencia existente y metadatos sin transformar las mediciones."""
    if low_coverage.empty or low_coverage.punto_muestreo.duplicated().any():
        raise ValueError("Se necesita una fila por punto con baja cobertura.")
    if not low_coverage.anio.eq(anio).all() or not monthly.anio.eq(anio).all():
        raise ValueError("Los años no coinciden.")
    meta = stations.copy()
    meta["codigo_estacion"] = meta.COD_LOCAL.astype("string").str.zfill(8)
    if meta.codigo_estacion.duplicated().any():
        raise ValueError("Metadatos de estación duplicados.")
    for field in ["FECHA_INI", "FECHA_FIN"]:
        text = meta[field].astype("string").str.strip().replace("", pd.NA)
        meta[field + "_parseada"] = pd.to_datetime(text, format="mixed", errors="raise").dt.normalize()
    if (meta.FECHA_FIN_parseada.notna() & meta.FECHA_INI_parseada.notna()
            & meta.FECHA_FIN_parseada.lt(meta.FECHA_INI_parseada)).any():
        raise ValueError("Hay una baja anterior al alta de la estación.")
    fields = ["codigo_estacion", "FECHA_INI", "FECHA_FIN", "FECHA_INI_parseada", "FECHA_FIN_parseada", "N_RED", "N_PROVINCIA", "N_MUNICIPIO"]
    revision = low_coverage.merge(meta[fields], on="codigo_estacion", how="left", validate="many_to_one", indicator="correspondencia_metadatos")
    if not revision.correspondencia_metadatos.eq("both").all():
        raise ValueError("Faltan estaciones en los metadatos de revisión.")
    inicio, fin = pd.Timestamp(f"{anio}-01-01"), pd.Timestamp(f"{anio}-12-31")
    revision["alta_estacion_durante_anio"] = revision.FECHA_INI_parseada.between(inicio, fin)
    revision["baja_estacion_durante_anio"] = revision.FECHA_FIN_parseada.between(inicio, fin)
    revision["intervalo_estacion_recorta_anio"] = revision.FECHA_INI_parseada.gt(inicio) | revision.FECHA_FIN_parseada.lt(fin)
    revision["fecha_inicio_estacion"] = revision.FECHA_INI_parseada.dt.strftime("%Y-%m-%d")
    revision["fecha_fin_estacion"] = revision.FECHA_FIN_parseada.dt.strftime("%Y-%m-%d")
    revision["alcance_fechas"] = "Alta/baja declarada de estación; no son fechas de actividad del punto de muestreo."
    selection = monthly.loc[monthly.punto_muestreo.isin(revision.punto_muestreo)]
    if selection.duplicated(["punto_muestreo", "mes"]).any() or not selection.groupby("punto_muestreo").size().reindex(revision.punto_muestreo, fill_value=0).eq(12).all():
        raise ValueError("La revisión necesita los doce meses de cada punto.")
    evidencia = []
    for point in revision.punto_muestreo:
        meses = selection.loc[selection.punto_muestreo.eq(point)].sort_values("mes")
        dias = daily.loc[daily.punto_muestreo.eq(point)]
        if dias.duplicated("fecha").any() or not dias.fecha.dt.year.eq(anio).all():
            raise ValueError("Fechas duplicadas o de otro año en la revisión.")
        validos = dias.loc[dias.estado.eq("valida"), "fecha"].sort_values()
        if len(validos) != meses.dias_validos.sum():
            raise ValueError("El detalle diario no coincide con la auditoría mensual.")
        saltos = validos.diff().dt.days.dropna()
        # Los extremos del año permiten contar también huecos iniciales y finales.
        bordes = pd.DatetimeIndex([inicio - pd.Timedelta(days=1)] + validos.tolist() + [fin + pd.Timedelta(days=1)])
        racha = int(max((bordes[1:] - bordes[:-1]).days - 1))
        evidencia.append({
            "punto_muestreo": point,
            "meses_sin_validos_detalle": " | ".join(meses.loc[meses.dias_validos.eq(0), "periodo"]),
            "primera_fecha_valida": validos.min().strftime("%Y-%m-%d") if len(validos) else None,
            "ultima_fecha_valida": validos.max().strftime("%Y-%m-%d") if len(validos) else None,
            "mediana_dias_entre_medidas": float(saltos.median()) if len(saltos) else None,
            "racha_max_dias_sin_medida_valida": racha,
            "archivos_mediciones": " | ".join(sorted(dias.archivo_origen.dropna().unique())),
            "miembros_mediciones_zip": " | ".join(sorted(dias.miembro_zip.dropna().unique())),
        })
    revision = revision.merge(pd.DataFrame(evidencia), on="punto_muestreo", validate="one_to_one")
    propuestas = [propose_treatment(str(f.tecnica), int(f.meses_sin_mediciones_validas), bool(f.intervalo_estacion_recorta_anio))
                  for f in revision.itertuples()]
    revision["motivo_revision"] = [p[0] for p in propuestas]
    revision["tratamiento_propuesto"] = [p[1] for p in propuestas]
    revision["causa_ausencias_confirmada"] = False
    revision["excluir_automaticamente"] = False
    revision["media_anual_principal_pendiente"] = True
    revision["fuente_metadatos"] = "miteco_estaciones_2024.xlsx; hoja Estaciones_2024"
    revision["fuente_tecnica"] = "miteco_estaciones_2024.xlsx; hoja Técnicas (M: manual gravimétrica)"
    return revision.drop(columns=["FECHA_INI_parseada", "FECHA_FIN_parseada", "correspondencia_metadatos"]).sort_values(["motivo_revision", "cobertura_anual"])


def main():
    root = PROJECT_ROOT
    folder = root / "data/interim/air/pm10_2024"
    raw = root / "data/raw/health_air_history"
    sources = json.loads((raw / "sources.json").read_text(encoding="utf-8-sig"))["sources"]
    source_info = next(f for f in sources if f["year"] == 2024 and f["kind"] == "miteco_estaciones" and f["status"] == "downloaded")
    path = raw / source_info["file"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != source_info["sha256"]:
        raise ValueError("Los metadatos no coinciden con su huella original.")
    tipos = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica"]}
    low_coverage = pd.read_csv(folder / "auditoria_resumen_puntos_baja_cobertura.csv", dtype=tipos)
    monthly = pd.read_csv(folder / "auditoria_cobertura_mensual.csv", dtype=tipos)
    daily = pd.read_csv(folder / "diarias_combinadas.csv.gz", dtype=tipos, parse_dates=["fecha"])
    stations = pd.read_excel(path, sheet_name="Estaciones_2024")
    tecnicas = pd.read_excel(path, sheet_name="Técnicas")
    manual = tecnicas.loc[tecnicas["OTROS CÓDIGOS"].astype("string").eq("M")]
    if len(manual) != 1 or "MANUAL" not in str(manual.iloc[0]["Unnamed: 6"]).upper():
        raise ValueError("No se ha podido confirmar el significado de la técnica M.")
    revision = review_sampling_points(low_coverage, monthly, daily, stations, 2024)
    revision.to_csv(folder / "revision_puntos_baja_cobertura.csv", index=False, encoding="utf-8-sig")
    summary = {
        "puntos_revisados": len(revision), "por_tipo_estacion": revision.TIPO_ESTACION.value_counts().to_dict(),
        "por_tecnica": revision.tecnica.value_counts().to_dict(),
        "por_motivo_revision": revision.motivo_revision.value_counts().to_dict(),
        "altas_estacion_durante_2024": int(revision.alta_estacion_durante_anio.sum()),
        "bajas_estacion_durante_2024": int(revision.baja_estacion_durante_anio.sum()),
        "intervalos_declarados_que_recortan_anio": int(revision.intervalo_estacion_recorta_anio.sum()),
        "manuales_con_datos_todos_los_meses": int((revision.tecnica.eq("M") & revision.meses_sin_mediciones_validas.eq(0)).sum()),
        "exclusiones_automaticas": int(revision.excluir_automaticamente.sum()),
        "nota": "El 75 % es un filtro exploratorio, no una regla universal para muestreo manual. Las fechas de estación no demuestran la actividad del equipo ni la causa de los huecos.",
    }
    (folder / "revision_puntos_baja_cobertura_resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
