"""Primer mapeador ambiental: CSV diarios y horarios de MITECO, PM10 2024."""

from dataclasses import dataclass
from pathlib import Path
import calendar
import zipfile

import numpy as np
import pandas as pd


IDENTIFIER_COLUMNS = ["PROVINCIA", "MUNICIPIO", "ESTACION", "MAGNITUD", "PUNTO_MUESTREO", "ANNO", "MES"]
DAILY_KEY = ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "fecha"]


@dataclass(frozen=True)
class AirContext:
    anio: int
    magnitud: str
    contaminante: str
    unidad: str
    archivo_origen: str
    miembro_zip: str

    def __post_init__(self):
        if type(self.anio) is not int or not 1900 <= self.anio <= 9999:
            raise ValueError("Año ambiental inválido.")
        if not all([self.magnitud, self.contaminante, self.unidad, self.archivo_origen, self.miembro_zip]):
            raise ValueError("Falta contexto o procedencia ambiental.")


class AirQualityReader:
    def read_points(self, ruta_zip: Path | str, member: str, points: set[str]) -> pd.DataFrame:
        """Filter source rows in chunks before expanding daily/hourly columns."""
        chunks = []
        columns = None
        with zipfile.ZipFile(ruta_zip) as archive:
            with archive.open(member) as content:
                for chunk in pd.read_csv(content, sep=";", encoding="utf-8-sig", dtype="string", chunksize=50000):
                    columns = chunk.columns
                    selected = chunk.loc[chunk.PUNTO_MUESTREO.isin(points)]
                    if not selected.empty:
                        chunks.append(selected)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=columns)

    def read(self, ruta_zip: Path | str, member: str) -> pd.DataFrame:
        with zipfile.ZipFile(ruta_zip) as file:
            with file.open(member) as content:
                return pd.read_csv(content, sep=";", encoding="utf-8-sig", dtype="string")


class AirQualityMapper:
    def transform(self, original: pd.DataFrame, context: AirContext,
                    frequency: str) -> pd.DataFrame:
        if frequency not in {"diaria", "horaria"}:
            raise ValueError("Frecuencia desconocida.")
        prefix, count = ("D", 31) if frequency == "diaria" else ("H", 24)
        values = [f"{prefix}{i:02d}" for i in range(1, count + 1)]
        ids = IDENTIFIER_COLUMNS + (["DIA"] if frequency == "horaria" else [])
        if set(original.columns) != set(ids + values):
            raise ValueError("Esquema ambiental inesperado; revisar columnas.")
        df = original.astype("string").copy()
        for name in ids:
            df[name] = df[name].str.strip()
        if df[ids].isna().any().any():
            raise ValueError("Faltan identificadores ambientales.")
        if df.duplicated(ids).any():
            raise ValueError("Hay filas ambientales duplicadas en el original.")

        for column in ["ANNO", "MES"] + (["DIA"] if frequency == "horaria" else []):
            if not df[column].str.fullmatch(r"\d+", na=False).all():
                raise ValueError(f"Componente de fecha inválido: {column}")
        if not df.ANNO.astype(int).eq(context.anio).all():
            raise ValueError("El año del archivo no coincide con el contexto.")
        if not df.MES.astype(int).between(1, 12).all():
            raise ValueError("Mes imposible.")
        for column, ancho in [("PROVINCIA", 2), ("MUNICIPIO", 3), ("ESTACION", 3)]:
            if not df[column].str.fullmatch(r"\d{1," + str(ancho) + r"}", na=False).all():
                raise ValueError(f"Código geográfico inválido: {column}")
            df[column] = df[column].str.zfill(ancho)
        if not df.MAGNITUD.eq(context.magnitud).all():
            raise ValueError("La magnitud no coincide con el contexto.")
        station = df.PROVINCIA + df.MUNICIPIO + df.ESTACION
        if not df.PUNTO_MUESTREO.str.match(r"\d{8}_\d+_[A-Za-z0-9]+$", na=False).all():
            raise ValueError("Punto de muestreo desconocido.")
        parts = df.PUNTO_MUESTREO.str.split("_", expand=True)
        if not parts[0].eq(station).all() or not parts[1].eq(context.magnitud).all():
            raise ValueError("El punto de muestreo no coincide con estación o magnitud.")
        df["codigo_estacion"] = station
        df["tecnica"] = parts[2]

        # melt convierte D01…D31 o H01…H24 en filas, conservando los identificadores.
        long_table = df.melt(id_vars=ids + ["codigo_estacion", "tecnica"], value_vars=values,
                        var_name="columna_original", value_name="valor_original")
        text = long_table.valor_original.str.strip()
        missing = text.isna() | text.eq("")
        patron = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
        if (~missing & ~text.str.fullmatch(patron, na=False)).any():
            raise ValueError("Concentración con formato desconocido; MITECO usa punto decimal.")
        long_table["concentracion"] = pd.to_numeric(text.mask(missing), errors="raise").astype("Float64")
        if not np.isfinite(long_table.concentracion.dropna().astype(float)).all():
            raise ValueError("Concentración no finita.")

        dia = (long_table.columna_original.str[1:].astype(int) if frequency == "diaria"
               else long_table.DIA.astype(int))
        dates = pd.to_datetime(pd.DataFrame({"year": long_table.ANNO.astype(int),
                                              "month": long_table.MES.astype(int), "day": dia}), errors="coerce")
        if frequency == "diaria":
            # D30 de febrero vacío es relleno estructural. Con valor sería un error.
            if (dates.isna() & long_table.concentracion.notna()).any():
                raise ValueError("Hay una medición en un día imposible.")
            keep = dates.notna()
            long_table = long_table.loc[keep].copy()
            dates = dates.loc[keep]
        elif dates.isna().any():
            raise ValueError("Día horario imposible, incluso si sus medidas están vacías.")
        long_table["fecha"] = dates  # Día de muestreo, sin inventar una hora.
        if frequency == "horaria":
            long_table["hora_fin_original"] = long_table.columna_original.str[1:].astype("Int64")
            long_table["fin_periodo_utc"] = (dates.dt.tz_localize("UTC")
                                        + pd.to_timedelta(long_table.hora_fin_original.astype(int), unit="h"))
        long_table["estado"] = "valida"
        long_table.loc[long_table.concentracion.isna(), "estado"] = "ausente"
        long_table.loc[long_table.concentracion.lt(0).fillna(False), "estado"] = "negativa_pendiente_revision"
        long_table["codigo_provincia"] = long_table.PROVINCIA
        long_table["punto_muestreo"] = long_table.PUNTO_MUESTREO
        long_table["magnitud"] = context.magnitud
        long_table["contaminante"] = context.contaminante
        long_table["unidad"] = context.unidad
        long_table["archivo_origen"] = context.archivo_origen
        long_table["miembro_zip"] = context.miembro_zip
        columns = DAILY_KEY + ["tecnica", "columna_original", "valor_original", "concentracion", "estado",
                               "contaminante", "unidad", "archivo_origen", "miembro_zip"]
        if frequency == "horaria":
            columns += ["hora_fin_original", "fin_periodo_utc"]
        return long_table[columns].reset_index(drop=True)


class AirQualityValidator:
    def validate(self, table: pd.DataFrame, frequency: str) -> None:
        clave = DAILY_KEY + (["hora_fin_original"] if frequency == "horaria" else [])
        if table.empty or table[clave].isna().any().any():
            raise ValueError("Tabla ambiental vacía o claves ausentes.")
        if table.duplicated(clave).any():
            raise ValueError("Mediciones repetidas para el mismo punto y periodo.")
        if (table.loc[table.estado.eq("valida"), "concentracion"].isna().any()
                or table.loc[table.estado.eq("valida"), "concentracion"].lt(0).any()):
            raise ValueError("Mediciones inválidas marcadas como válidas.")
        if frequency == "horaria":
            esperado = table.fecha.dt.tz_localize("UTC") + pd.to_timedelta(table.hora_fin_original.astype(int), unit="h")
            if not table.fin_periodo_utc.eq(esperado).all():
                raise ValueError("La hora de fin no respeta la convención UTC de MITECO.")


def summarize_hours(hourly: pd.DataFrame, minimum_hours: int = 18) -> pd.DataFrame:
    """Criterio exploratorio configurable; no equivale a una evaluación normativa."""
    if not 1 <= minimum_hours <= 24:
        raise ValueError("El mínimo de horas debe estar entre 1 y 24.")
    df = hourly.copy()
    df["valor_valido"] = df.concentracion.where(df.estado.eq("valida"))
    groups = DAILY_KEY + ["tecnica", "unidad", "contaminante", "archivo_origen", "miembro_zip"]
    diario = df.groupby(groups, as_index=False, observed=True).agg(
        n_horas_validas=("valor_valido", "count"), media_horas_disponibles=("valor_valido", "mean"))
    diario["concentracion"] = diario.media_horas_disponibles.where(diario.n_horas_validas.ge(minimum_hours))
    diario["estado"] = "cobertura_horaria_insuficiente"
    diario.loc[diario.concentracion.notna(), "estado"] = "valida"
    return diario


def combine_daily_measurements(daily: pd.DataFrame, derived: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prioriza el dato diario válido, solo dentro del MISMO punto de muestreo."""
    for table in (daily, derived):
        if table.duplicated(DAILY_KEY).any():
            raise ValueError("Duplicados diarios: resolver antes de combinar.")
    comparison = daily[DAILY_KEY + ["concentracion", "estado"]].merge(
        derived[DAILY_KEY + ["concentracion", "estado", "n_horas_validas"]],
        on=DAILY_KEY, how="inner", suffixes=("_oficial", "_horaria"), validate="one_to_one")
    ambas = comparison.estado_oficial.eq("valida") & comparison.estado_horaria.eq("valida")
    comparison["diferencia_absoluta"] = (comparison.concentracion_oficial - comparison.concentracion_horaria).abs().where(ambas)
    d = daily.copy()
    h = derived.copy()
    d["origen_diario"] = "diario_oficial"
    h["origen_diario"] = "derivado_horario"
    d["prioridad"] = d.estado.eq("valida").map({True: 0, False: 2})
    h["prioridad"] = h.estado.eq("valida").map({True: 1, False: 3})
    combined = pd.concat([d, h], ignore_index=True).sort_values("prioridad", kind="stable")
    combined = combined.drop_duplicates(DAILY_KEY, keep="first").drop(columns="prioridad")
    return combined.sort_values(DAILY_KEY).reset_index(drop=True), comparison


def summarize_year(daily: pd.DataFrame, anio: int, minimum_coverage: float = 0.75) -> pd.DataFrame:
    if not 0 < minimum_coverage <= 1 or not daily.fecha.dt.year.eq(anio).all():
        raise ValueError("Año o cobertura anual inválidos.")
    if daily.duplicated(DAILY_KEY).any():
        raise ValueError("No se puede resumir un año con días duplicados.")
    df = daily.copy()
    df["valor_valido"] = df.concentracion.where(df.estado.eq("valida"))
    claves = ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica", "unidad", "contaminante"]
    summary = df.groupby(claves, as_index=False, observed=True).agg(
        dias_validos=("valor_valido", "count"), media_dias_disponibles=("valor_valido", "mean"))
    summary["anio"] = anio
    summary["dias_del_anio"] = 366 if calendar.isleap(anio) else 365
    summary["cobertura_anual"] = summary.dias_validos / summary.dias_del_anio
    summary["cumple_criterio_exploratorio"] = summary.cobertura_anual.ge(minimum_coverage)
    summary["media_anual_analisis"] = summary.media_dias_disponibles.where(summary.cumple_criterio_exploratorio)
    return summary
