"""Transformación explícita de las dos estructuras sanitarias del INE."""

from dataclasses import dataclass
from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import re
import unicodedata

import pandas as pd


DIAGNOSIS_COLUMN = "Diagnóstico principal (CIE10MC)"
TERRITORY_COLUMN = "Provincia, Comunidad y Ciudad autónoma de residencia"
HIERARCHICAL_GEOGRAPHY_COLUMNS = {"Total Nacional", "Comunidades y Ciudades Autónomas", "Provincias"}
REFERENCE_CSV = PROJECT_ROOT / "data/reference/territorios_ine.csv"


def normalize_name(text: str) -> str:
    """Ignora mayúsculas, acentos y espacios, conservando el original aparte."""
    text = re.sub(r"^\d{2}\s+", "", text.strip())
    text = unicodedata.normalize("NFKD", text)
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).upper().split())


def parse_spanish_rate(values: pd.Series) -> pd.Series:
    """Interpreta el formato español y conserva '..' y blancos como ausentes."""
    text = values.astype("string").str.strip()
    missing = text.isna() | text.isin(["", ".."])
    # Detectar formatos desconocidos evita convertir, por ejemplo, '1.2' en 12.
    patron = r"(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?"
    invalid = ~missing & ~text.str.fullmatch(patron, na=False)
    if invalid.any():
        raise ValueError(f"Formato de tasa desconocido: {text[invalid].unique().tolist()}")
    text = text.mask(missing).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(text, errors="raise").astype("Float64")


@dataclass(frozen=True)
class HealthContext:
    """El año procede del catálogo oficial: estos CSV no traen fecha completa."""

    anio: int
    fuente_tabla: str
    archivo_origen: str

    def __post_init__(self):
        if type(self.anio) is not int or not 1900 <= self.anio <= 9999:
            raise ValueError("El año debe ser un entero de cuatro cifras.")
        if not self.fuente_tabla.strip() or not self.archivo_origen.strip():
            raise ValueError("Se necesita la procedencia de los datos.")


class INEHealthReader:
    def read(self, path: Path | str) -> pd.DataFrame:
        return pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype="string")


class INEHealthMapper:
    """Devuelve una tabla nueva. No lee ni escribe los archivos sanitarios."""

    def __init__(self, reference: pd.DataFrame | None = None):
        reference = (pd.read_csv(REFERENCE_CSV, dtype="string", encoding="utf-8-sig")
                      if reference is None else reference.copy())
        reference["clave"] = reference["nombre_fuente"].map(normalize_name)
        if reference["clave"].duplicated().any():
            raise ValueError("Hay nombres ambiguos en la referencia territorial.")
        self.territorios = reference.set_index("clave")

    def transform(self, original: pd.DataFrame, context: HealthContext,
                    codigos: tuple[str, ...] = ("1000", "1006", "1007")) -> pd.DataFrame:
        columns = set(original.columns)
        if not {DIAGNOSIS_COLUMN, "Total"}.issubset(columns):
            raise ValueError("Faltan las columnas de diagnóstico o tasa.")
        flat = TERRITORY_COLUMN in columns
        hierarchical = HIERARCHICAL_GEOGRAPHY_COLUMNS.issubset(columns)
        if flat == hierarchical:
            raise ValueError("Estructura geográfica desconocida o ambigua.")
        if not codigos or len(set(codigos)) != len(codigos):
            raise ValueError("Los códigos seleccionados deben ser únicos y no vacíos.")

        # Primero seleccionamos por código, nunca por nombre de la enfermedad.
        codigo = original[DIAGNOSIS_COLUMN].astype("string").str.extract(r"^(\d{4})\s", expand=False)
        missing_codes = set(codigos) - set(codigo.dropna())
        if missing_codes:
            raise ValueError(f"Faltan diagnósticos seleccionados: {sorted(missing_codes)}")
        rows = original.loc[codigo.isin(codigos)].copy().reset_index(drop=True)
        table = pd.DataFrame(index=rows.index)
        table["anio"] = pd.Series(context.anio, index=rows.index, dtype="Int64")
        table["codigo_diagnostico"] = rows[DIAGNOSIS_COLUMN].str.extract(r"^(\d{4})\s", expand=False)
        table["diagnostico_original"] = rows[DIAGNOSIS_COLUMN]

        if flat:
            territory = rows[TERRITORY_COLUMN].astype("string").str.strip()
        else:
            # Las columnas superiores se repiten: escogemos la más específica.
            geo = rows[list(HIERARCHICAL_GEOGRAPHY_COLUMNS)].astype("string").replace(r"^\s*$", pd.NA, regex=True)
            territory = geo["Provincias"].combine_first(geo["Comunidades y Ciudades Autónomas"]).combine_first(geo["Total Nacional"])
        if territory.isna().any():
            raise ValueError("Hay filas sin territorio.")
        table["territorio_original"] = territory
        clave = territory.map(normalize_name)
        unknown = territory[~clave.isin(self.territorios.index)]
        if not unknown.empty:
            raise ValueError(f"Territorios sin correspondencia: {unknown.unique().tolist()}")
        for destination, source_info in [("territorio", "nombre_fuente"),
                                ("nivel_geografico_original", "nivel_original"),
                                ("codigo_ccaa", "codigo_ccaa"),
                                ("codigo_provincia", "codigo_provincia")]:
            table[destination] = clave.map(self.territorios[source_info]).astype("string")

        if hierarchical:
            # Si el original aporta código provincial, debe coincidir con el nombre.
            prov = rows["Provincias"].astype("string").str.extract(r"^(\d{2})\s", expand=False)
            ccaa = rows["Comunidades y Ciudades Autónomas"].astype("string").str.extract(r"^(\d{2})\s", expand=False)
            if (prov.notna() & prov.ne(table.codigo_provincia)).any() or (ccaa.notna() & ccaa.ne(table.codigo_ccaa)).any():
                raise ValueError("Los códigos originales no coinciden con la referencia territorial.")

        table["nivel_geografico"] = table["nivel_geografico_original"].copy()
        table.loc[table.codigo_provincia.notna(), "nivel_geografico"] = "provincia"
        table["tasa_original"] = rows["Total"].astype("string")
        table["tasa_altas_por_100000"] = parse_spanish_rate(table["tasa_original"])
        table["fuente_tabla"] = context.fuente_tabla
        table["archivo_origen"] = context.archivo_origen
        return table


class INEHealthValidator:
    def validate(self, table: pd.DataFrame) -> None:
        required = {"anio", "codigo_diagnostico", "territorio", "nivel_geografico",
                      "codigo_provincia", "tasa_altas_por_100000", "fuente_tabla", "archivo_origen"}
        if not required.issubset(table.columns) or table.empty:
            raise ValueError("La tabla está vacía o faltan columnas normalizadas.")
        if table[["anio", "codigo_diagnostico", "territorio", "fuente_tabla", "archivo_origen"]].isna().any().any():
            raise ValueError("Faltan claves o datos de procedencia.")
        if table.duplicated(["anio", "codigo_diagnostico", "territorio", "nivel_geografico"]).any():
            raise ValueError("Hay claves geográficas duplicadas.")
        if (table.tasa_altas_por_100000.dropna() < 0).any():
            raise ValueError("Las tasas no pueden ser negativas.")
        provincias = table.loc[table.nivel_geografico.eq("provincia")]
        if not provincias.codigo_provincia.str.fullmatch(r"\d{2}", na=False).all():
            raise ValueError("Faltan códigos provinciales de dos cifras.")
        if provincias.duplicated(["anio", "codigo_diagnostico", "codigo_provincia"]).any():
            raise ValueError("Hay provincias repetidas para el mismo diagnóstico y año.")
