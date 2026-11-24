"""Inspect original table headers and document logical types separately from samples."""

from io import BytesIO
from pathlib import Path
import re
import zipfile

import pandas as pd

from tfm_data.config import PROJECT_ROOT


def column_definition(column: str, family: str) -> tuple[str, str]:
    """Logical interpretation for documentation, not an inferred provider contract."""
    if family == "health":
        if column == "Total":
            return "decimal o ausente", "Tasa de altas por 100.000; formato español; '..' o blanco = ausente."
        return "texto", "Diagnóstico o territorio original; puede incluir código y nombre."
    if family == "demographics":
        if column == "Total":
            return "entero o ausente", "Población; formato español. La selección utilizada exige recuentos completos."
        if column == "Periodo":
            return "texto de fecha de referencia", "Etiqueta del INE; se convierte a año y fecha de referencia tras filtrar."
        return "texto", "Categoría original; Provincias incluye código y nombre."
    if re.fullmatch(r"D\d{2}|H\d{2}", column):
        return "decimal o ausente", "Concentración; unidad según MAGNITUD. D = día del mes; H = fin horario UTC. Blanco no equivale a cero."
    if column in {"ANNO", "MES", "DIA"}:
        return "entero", "Componente de fecha; no es una fecha completa por sí solo."
    if column in {"PROVINCIA", "MUNICIPIO", "ESTACION", "COD_LOCAL", "MAGNITUD", "TECNICA"}:
        widths = {"PROVINCIA": 2, "MUNICIPIO": 3, "ESTACION": 3, "COD_LOCAL": 8}
        note = f" Conservar como texto con {widths[column]} posiciones en el esquema normalizado." if column in widths else " Identificador, no cantidad."
        return "código (texto recomendado)", "Puede aparecer como número en Excel." + note
    if column in {"FECHA_INI", "FECHA_FIN"}:
        return "fecha o ausente", "Inicio/fin registrado de estación; conservar ausencia de fin. Revisar celdas originales antes de convertir."
    if column in {"LATITUD_G", "LONGITUD_G", "ALTITUD"}:
        return "decimal o ausente", "Coordenada en grados o altitud en metros, según columna; no confundir con exposición poblacional."
    if column.startswith("Unnamed:"):
        return "sin interpretación asignada", "Encabezado vacío en el Excel: nombre asignado por pandas. No utilizado por los mapeadores."
    if column in {"PUNTO_MUESTREO", "COD_ESTACION_DEM"}:
        return "texto identificador", "Conservar exactamente; no convertir a número."
    if column in {"NOMBRE", "NOMBRE_I", "ABREVIATURA", "UNIDAD", "GRUPO", "N_RED", "N_CCAA", "N_PROVINCIA", "N_MUNICIPIO", "TIPO_ESTACION", "TIPO_AREA", "TIPO_SUBAREA_RURAL", "EST", "ZONA", "DIRECCION", "OTROS CÓDIGOS"}:
        return "texto o ausente", "Etiqueta o categoría del catálogo original."
    return "sin interpretación asignada", "Columna conservada en el inventario; revisar significado antes de utilizarla."


def inspect_source_tables(path):
    """Yield member, sheet, format and a small sample; inspect every table header."""
    def read(payload, suffix, member=""):
        if suffix == ".csv":
            yield member, "", "csv", pd.read_csv(payload, sep=";", encoding="utf-8-sig", dtype="string", nrows=30)
        else:
            with pd.ExcelFile(payload) as workbook:
                for sheet in workbook.sheet_names:
                    yield member, sheet, suffix.lstrip("."), pd.read_excel(workbook, sheet_name=sheet, nrows=30)

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                suffix = Path(member).suffix.lower()
                if suffix not in {".csv", ".xls", ".xlsx"}:
                    continue
                # Stream CSV: the complete multi-year payload is not loaded into memory.
                with archive.open(member) as stream:
                    payload = stream if suffix == ".csv" else BytesIO(stream.read())
                    yield from read(payload, suffix, member)
    else:
        yield from read(path, path.suffix.lower())


def write_source_schemas(sources: pd.DataFrame, destination) -> tuple[int, int]:
    tables, columns, schemas = [], [], {}
    for source in sources.itertuples():
        if source.scope == "demographics":
            family = "demographics"
        elif source.download_url.startswith("https://www.ine.es/"):
            family = "health"
        else:
            family = "air"
        for member, sheet, file_format, sample in inspect_source_tables(PROJECT_ROOT / source.local_file):
            names = [str(c) for c in sample.columns]
            signature = (family, file_format, tuple(names))
            if signature not in schemas:
                schemas[signature] = {"id": f"schema-{len(schemas) + 1:02d}", "family": family,
                                      "format": file_format, "names": names, "tables": []}
            schema = schemas[signature]
            table_id = f"source-table-{len(tables) + 1:03d}"
            table = dict(table_id=table_id, schema_id=schema["id"], download_url=source.download_url,
                         local_file=source.local_file, archive_member=member, sheet=sheet,
                         format=file_format, column_count=len(names), sample_rows=len(sample))
            tables.append(table)
            schema["tables"].append(table)
            for position, (name, dtype) in enumerate(zip(names, sample.dtypes), start=1):
                logical, note = column_definition(name, family)
                columns.append(dict(**table, column_position=position, column_name=name,
                                    logical_type=logical, read_type="string" if file_format == "csv" else "Excel: inferencia pandas en muestra",
                                    sample_pandas_dtype=str(dtype), notes=note))
    pd.DataFrame(tables).to_csv(destination / "source_tables.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(columns).to_csv(destination / "source_columns.csv", index=False, encoding="utf-8-sig")
    lines = ["# Tablas originales, columnas y tipos por endpoint", "",
             "Inventario generado inspeccionando las cabeceras de cada CSV y todas las hojas Excel de los originales descargados, incluidos los miembros de los ZIP. Incluye sanidad, contaminación, metadatos y demografía.", "",
             "Un CSV no declara tipos. **Tipo lógico** describe cómo interpretar el dato según su columna; no es un contrato publicado por el proveedor. Los CSV se inspeccionan como `string`, igual que los lectores del proyecto, para conservar códigos y formato numérico original. Excel contiene celdas tipadas y puede mezclar tipos en una columna.", "",
             "[Tablas por descarga](source_tables.csv) relaciona cada URL con archivo, miembro ZIP, hoja y esquema. [Diccionario completo de columnas](source_columns.csv) añade el tipo lógico, tipo de lectura y dtype de pandas observado en una muestra de hasta 30 filas por tabla. Ese dtype es orientativo: no certifica el tipo ni la ausencia de nulos del archivo completo. No se ha hecho una validación completa de todos los contaminantes ni se han añadido al modelado.", "",
             "Los esquemas repetidos se muestran una sola vez y se enlazan desde la documentación de endpoints. La lista exacta de tablas que usa cada esquema figura debajo. `Unnamed: n` identifica una cabecera vacía del Excel, no un nombre oficial.", ""]
    def escape(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    for schema in schemas.values():
        lines += [f"## {schema['id']}", "", f"Área: `{schema['family']}`. Formato: `{schema['format']}`. Tablas con esta estructura: {len(schema['tables'])}.", "",
                  "| Columna original | Tipo lógico | Tipo de lectura | Interpretación |", "| --- | --- | --- | --- |"]
        for name in schema["names"]:
            logical, note = column_definition(name, schema["family"])
            read_type = "string" if schema["format"] == "csv" else "Celdas Excel; dtype inferido por pandas"
            lines.append(f"| {escape(name)} | {logical} | {read_type} | {note} |")
        lines += ["", "Tablas originales que utilizan este esquema:", ""]
        for table in schema["tables"]:
            location = " → ".join(filter(None, [table["local_file"], table["archive_member"], table["sheet"]]))
            lines.append(f"- `{table['table_id']}`: `{location}` — [GET]({table['download_url']}).")
        lines.append("")
    (destination / "source_schemas.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(tables), len(schemas)
