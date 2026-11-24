"""Primer ejercicio: leer el original y preparar tres diagnósticos respiratorios.

Ejecutar desde cualquier directorio: python scripts/01_explore_health.py
Requiere pandas. No modifica el archivo original.
"""

from pathlib import Path

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "data/raw/health_air_feasibility/ine_morbilidad_residencia_2024_79536.csv"
DESTINO = RAIZ / "data/interim/health_respiratory_2024.csv"

# Leemos como texto para conservar los códigos y el formato numérico original.
# El separador es punto y coma; el archivo lleva una marca UTF-8 (BOM).
original = pd.read_csv(ORIGEN, sep=";", encoding="utf-8-sig", dtype="string")
print("Filas y columnas del original:", original.shape)
print("Columnas:", original.columns.tolist())
print("\nPrimeras cinco filas:")
print(original.head().to_string(index=False))

table = original.rename(columns={
    "Diagnóstico principal (CIE10MC)": "diagnostico_original",
    "Provincia, Comunidad y Ciudad autónoma de residencia": "territorio_original",
    "Total": "tasa_original",
}).copy()
table["codigo_diagnostico"] = table["diagnostico_original"].str.split().str[0]

# Son categorías alternativas: no sumar el total respiratorio con sus subgrupos.
codigos = ["1000", "1006", "1007"]  # Respiratorias, EPOC/bronquiectasias, asma.
table = table.loc[table["codigo_diagnostico"].isin(codigos)].copy()

# El año se obtiene de la ficha oficial de la tabla 79536, no del contenido CSV.
table["anio"] = 2024
table["fuente_tabla"] = "INE 79536"

# En este archivo 1.234 significa 1234, no 1,234. '..' es un valor ausente.
numeros = table["tasa_original"].str.strip().replace("..", pd.NA)
numeros = numeros.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
table["tasa_altas_por_100000"] = pd.to_numeric(numeros, errors="raise").astype("Float64")

# Conservamos nación, comunidades y provincias, identificadas como pendientes.
# Clasificaremos y codificaremos los territorios antes de unir fuentes.
table["nivel_geografico"] = "pendiente_clasificar"
table = table[[
    "anio", "territorio_original", "nivel_geografico", "codigo_diagnostico",
    "diagnostico_original", "tasa_original", "tasa_altas_por_100000", "fuente_tabla",
]]
if table.duplicated(["anio", "territorio_original", "codigo_diagnostico"]).any():
    raise ValueError("Hay claves repetidas: revisar antes de exportar.")
if table.empty:
    raise ValueError("No se encontraron los diagnósticos esperados.")

DESTINO.parent.mkdir(parents=True, exist_ok=True)
table.to_csv(DESTINO, index=False, encoding="utf-8-sig")
print("\nEjemplo del resultado (total nacional):")
print(table.loc[table["territorio_original"].eq("TOTAL NACIONAL")].to_string(index=False))
print("\nFilas exportadas:", len(table))
print("Tasas ausentes:", table["tasa_altas_por_100000"].isna().sum())
print("Guardado en:", DESTINO)
