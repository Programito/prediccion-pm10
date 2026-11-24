"""Describe raw locations and the inputs used by processed columns."""

import csv
from datetime import date, timedelta
from functools import lru_cache
import json
from pathlib import Path

from openpyxl.utils.cell import get_column_letter

from explorer.treated_tables import BARCELONA_DAILY


DEMOGRAPHICS = "ine_poblacion_provincias_edad_56945.csv"
GFS_FIELDS = {"inicio_ciclo_utc", "latitud_gfs", "longitud_gfs", "viento_10m_mediodia_ms", "precipitacion_diaria_mm",
              "estado_viento", "estado_precipitacion", "fila_gfs_presente", "predictores_meteo_completos"}


@lru_cache(maxsize=2)
def daily_observations(root, daily_file):
    path = root / daily_file
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return {(row["codigo_estacion"], row["fecha"]): row for row in csv.DictReader(stream)}


@lru_cache(maxsize=2)
def messages_by_cycle(root):
    path = root / "data/interim/weather_forecasts/gfs_2021_2025/mensajes_gfs.json"
    if not path.is_file():
        return {}
    cycles = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        cycles.setdefault(item["inicio_ciclo_utc"], []).append(item)
    return cycles


def gfs_references(root, cycle, field, record):
    if field == "codigo_estacion":
        return "Código de estación del catálogo MITECO usado para seleccionar la celda GFS más próxima.", [
            dict(label="Estaciones de MITECO", format="Excel XLSX", file="miteco_estaciones_2024.xlsx", sheet="Estaciones_2024")]
    if field == "fecha_objetivo":
        return "Fecha del calendario para la que se solicitó una previsión. El ciclo de referencia se inicia a las 12 UTC del día anterior.", []
    if field in {"viento_10m_mediodia_ms", "estado_viento"}:
        rule = "Magnitud de UGRD y VGRD a 10 m en la celda seleccionada, en el plazo +24 h."
        labels = {"wind_u": "UGRD · viento este · +24 h", "wind_v": "VGRD · viento norte · +24 h"}
    elif field in {"precipitacion_diaria_mm", "estado_precipitacion"}:
        rule = "Se resta la precipitación acumulada a +12 h de la acumulada a +36 h para obtener la del día objetivo."
        labels = {"rain_start": "APCP · inicio del día · +12 h", "rain_end": "APCP · fin del día · +36 h"}
    else:
        rule = "Dato del ciclo y de la celda GFS más próxima a las coordenadas de la estación, o marca de calidad del cruce."
        labels = {"wind_u": "UGRD · +24 h", "wind_v": "VGRD · +24 h", "rain_start": "APCP · +12 h", "rain_end": "APCP · +36 h"}
    refs = []
    for item in messages_by_cycle(root).get(cycle, []):
        key = item["campo"]
        if key in labels:
            refs.append(dict(label=labels[key], format="GRIB2", file=item["url"].split("/")[-1],
                             url=item["url"], indexUrl=item["indice"], byteRange=item["rango"]))
    if field in {"latitud_gfs", "longitud_gfs"}:
        refs.append(dict(label="Coordenadas de la estación de partida", format="Excel XLSX",
                         file="miteco_estaciones_2024.xlsx", sheet="Estaciones_2024"))
    if not refs and not record.get(field):
        rule += " No consta ningún mensaje válido para esta celda y ciclo."
    return rule, refs


def reference(catalog, file, member=None, label=None):
    source = next((item for item in catalog if item.get("file") == file), None)
    if not file:
        return None
    suffix = Path(member or file).suffix.upper().lstrip(".")
    return dict(label=label, file=file, member=member, format=suffix, container="ZIP" if member else None,
                url=source["url"] if source else None)


def air_value_reference(catalog, record, with_input=True):
    stamp = record.get("fecha", "")
    if record.get("origen_diario") == "diario_oficial" and stamp:
        sample = f"{record.get('punto_muestreo')} · {stamp[:7]} · D{stamp[-2:]}"
    else:
        sample = f"{record.get('punto_muestreo')} · {stamp} · H01–H24"
    if with_input and record.get("pm10_valido") not in (None, ""):
        sample += f" → {record['pm10_valido']} µg/m³"
    return reference(catalog, record.get("archivo_origen"), record.get("miembro_zip"), sample)


def air_trace(root, catalog, record, field, daily_file):
    station = record.get("codigo_estacion")
    if field in {"NOMBRE", "TIPO_AREA", "unidad"}:
        return "Metadato de la estación o de la magnitud PM10 conservado en la serie diaria.", [
            dict(label="Hojas de estaciones y magnitudes de MITECO", format="Excel XLS o XLSX")]
    if field in {"pm10_objetivo", "pm10_elevado_objetivo", "comienzo_pm10_elevado", "objetivo_disponible",
                 "pm10_t"} or field.startswith(("pm10_t_menos_", "media_", "desviacion_")):
        target = record.get("fecha_objetivo")
        observed = record.get("fecha_ultima_observacion", record.get("fecha"))
        start = end = date.fromisoformat(observed)
        rule = "Concentración de PM10 aceptada para el último día observado."
        if field.startswith("pm10_t_menos_"):
            offset = int(field.rsplit("_", 1)[1])
            start = end = end - timedelta(days=offset)
            rule = f"Concentración observada {offset} días antes de la última observación."
        elif field.startswith(("media_", "desviacion_")):
            window = int(field.split("_")[1])
            start = end - timedelta(days=window - 1)
            rule = f"{'Media' if field.startswith('media_') else 'Desviación típica muestral'} de los últimos {window} días completos, incluido el último observado."
        elif field == "comienzo_pm10_elevado":
            end = date.fromisoformat(target)
            rule = "Compara dos días consecutivos para saber si el PM10 pasa de 27 µg/m³ o menos a más de 27 µg/m³."
        elif field in {"pm10_objetivo", "pm10_elevado_objetivo", "objetivo_disponible"}:
            start = end = date.fromisoformat(target)
            rule = {"pm10_objetivo": "PM10 observado en la fecha objetivo, un día después de la última observación.",
                    "pm10_elevado_objetivo": "Etiqueta de la fecha objetivo. Vale 1 si el PM10 observado supera 27 µg/m³.",
                    "objetivo_disponible": "Comprueba si hay una observación de PM10 para la fecha objetivo."}[field]
        refs = []
        daily = daily_observations(root, daily_file)
        for offset in range((end - start).days + 1):
            day = (start + timedelta(days=offset)).isoformat()
            source_row = daily.get((station, day), {})
            refs.append(air_value_reference(catalog, source_row) or {"label": f"{day} · no hay observación de origen registrada"})
        return rule, refs
    if field in {"pm10_valido", "concentracion", "estado", "origen_diario", "n_horas_validas", "es_valido",
                 "punto_muestreo", "codigo_estacion", "archivo_origen", "miembro_zip", "codigo_provincia"}:
        ref = air_value_reference(catalog, record)
        rule = "Se selecciona la medida diaria oficial cuando es válida. La media horaria alternativa requiere al menos 18 horas válidas del mismo punto y día."
        return rule, [ref] if ref else []
    rules = {
        "fecha": "Día de la medida del fichero MITECO o de la fila en el calendario diario completado.",
        "fecha_ultima_observacion": "Copia del día de observación de la serie diaria.",
        "fecha_objetivo": "Un día después de la fecha de la última observación de PM10.",
        "emision_simulada_utc": "Medianoche UTC de la fecha objetivo, usada como instante de emisión simulado.",
        "anio": "Año de la observación diaria.",
        "anio_objetivo": "Año de la fecha del pronóstico.",
        "particion": "Grupo de evaluación asignado según el año de la fecha objetivo en el experimento original.",
        "particion_meteo": "Grupo asignado según el año de la fecha objetivo para el experimento con GFS.",
        "predictores_completos": "Comprueba si están presentes todos los predictores de PM10 requeridos por el modelo.",
        "fila_utilizable": "Combina la disponibilidad del objetivo y de los predictores de PM10 con el periodo de evaluación.",
        "fila_comun_utilizable": "Exige una fila utilizable de PM10 y los dos predictores meteorológicos completos, en la misma estación y fecha objetivo.",
    }
    if field.startswith(("semana_", "mes_")) and field.endswith(("_sin", "_cos")):
        return "Transformación circular del calendario de la fecha objetivo usando seno o coseno.", []
    return rules.get(field, "Componente del calendario construido a partir de la fecha objetivo."), []


def treated_trace(root, catalog, table, record, field):
    table_id = table["id"]
    if table_id in {"treated-gfs-estacion", "gfs-daily"} or (table_id == "treated-pm10-meteo" and field in GFS_FIELDS):
        return gfs_references(root, record.get("inicio_ciclo_utc"), field, record)
    if table_id in {"treated-pm10-diario-barcelona", "treated-pm10-supervisado-barcelona"}:
        return air_trace(root, catalog, record, field, BARCELONA_DAILY)
    if table_id in {"treated-pm10-diario", "treated-pm10-supervisado", "treated-pm10-meteo"}:
        return air_trace(root, catalog, record, field, "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv")
    demographic = field.startswith(("poblacion_", "proporcion_")) or field in {"fecha_referencia_poblacion", "fuente_demografia"}
    if table_id == "treated-demografia-provincia" or (table_id == "treated-panel-sanitario" and demographic):
        label = f"Tabla 56945 · provincia {record.get('codigo_provincia')} · año {record.get('anio')}"
        rule = "El mapeador selecciona ambos sexos y el 1 de enero. Los grupos de edad se obtienen de las edades simples y las proporciones dividen cada grupo entre la población total."
        return rule, [reference(catalog, DEMOGRAPHICS, label=label)]
    if table_id == "treated-panel-sanitario" and (field.startswith(("media_pm10_", "minimo_medias_", "maximo_medias_", "n_", "cobertura_"))
                                                  or field in {"metodo_pm10", "hay_indicador_pm10", "cruce_ambiental", "unidad_pm10"}):
        year = record.get("anio")
        refs = [reference(catalog, f"miteco_{frequency}_{year}.zip", f"PM10_{code}_{year}.csv", "Medidas de la red de fondo")
                for frequency, code in [("diarios", "DD"), ("horarios", "HH")]]
        return "Indicador agregado a partir de los puntos de muestreo seleccionados. Se une al panel por provincia y año.", refs
    labels = {"anio": "El año se toma de la ficha anual del archivo.",
              "tasa_altas_por_100000": f"Se normaliza el campo Total del INE. El valor original es {record.get('tasa_original') or 'ausente'}.",
              "tasa_original": "Valor del campo Total tal como se publicó en el CSV.",
              "codigo_diagnostico": "Se extrae del código que abre la descripción del diagnóstico.",
              "codigo_provincia": "Se asigna la clave territorial a partir del territorio original y la referencia del INE."}
    return labels.get(field, "Dato de la tabla anual de altas hospitalarias o metadato asociado durante la normalización."), [
        reference(catalog, record.get("archivo_origen"), label=f"Provincia {record.get('codigo_provincia')} · diagnóstico {record.get('codigo_diagnostico')}")]


def explain_value(root, catalog, table, record, field, position, column_index):
    identifier = table["id"]
    owner = next((item for item in catalog if any(t["id"] == identifier for t in item["tables"])), None)
    container = (owner or {}).get("format") if table.get("member") else None
    stored = dict(file=table["local"], member=table.get("member"), sheet=table.get("sheet"), format=table["format"],
                  container=container, position=position)
    if table.get("sheet"):
        stored["cell"] = f"{get_column_letter(column_index + 1)}{position + 1}"
    if identifier.startswith("treated-") or identifier == "gfs-daily":
        rule, refs = treated_trace(root, catalog, table, record, field)
    elif identifier == "gfs-requests":
        rule = "Metadato del manifiesto local que registra el fragmento solicitado y su procedencia."
        refs = [dict(label=record.get("campo"), format="GRIB2", file=(record.get("url") or "").split("/")[-1],
                     url=record.get("url"), indexUrl=record.get("indice"), byteRange=record.get("rango"))]
    else:
        rule = "Valor leído de la columna original del archivo publicado."
        refs = [dict(label=(owner or {}).get("provider"), url=table.get("url") or (owner or {}).get("url"),
                     format=table["format"], container=container)]
    return dict(column=field, value=record.get(field), stored=stored, rule=rule, sources=[ref for ref in refs if ref],
                description=table["columns"][column_index])
