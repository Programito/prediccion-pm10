"""Ejecutar: python -m pm10_data.pipelines.prepare_demographics"""

from pathlib import Path
from pm10_data.config import PROJECT_ROOT
import hashlib
import json

import pandas as pd

from pm10_data.mappers.demographics import INEDemographicsMapper


def main():
    root = PROJECT_ROOT
    raw = root / "data/raw/demographics"
    source_info = json.loads((raw / "source.json").read_text(encoding="utf-8-sig"))
    file = raw / source_info["file"]
    if hashlib.sha256(file.read_bytes()).hexdigest() != source_info["sha256"].lower():
        raise ValueError("El original demográfico no coincide con su huella.")
    selection = []
    for bloque in pd.read_csv(file, sep=";", encoding="utf-8-sig", dtype="string", chunksize=200000):
        mask = (bloque.Periodo.str.strip().str.fullmatch(r"1 de enero de 20(?:17|18|19|20|21|22|23|24)")
                   & bloque.Sexo.eq("Total") & bloque.Provincias.str.match(r"^\d{2} "))
        selection.append(bloque.loc[mask].copy())
    original = pd.concat(selection, ignore_index=True)
    normalized = INEDemographicsMapper().transform(original)
    if len(normalized) != 52 * 8 or normalized.groupby("anio").codigo_provincia.nunique().ne(52).any():
        raise ValueError("El periodo no cubre 52 territorios por ocho años.")
    destination = root / "data/interim/demographics"
    destination.mkdir(parents=True, exist_ok=True)
    original.to_csv(destination / "seleccion_original_enero_2017_2024.csv", index=False, encoding="utf-8-sig")
    normalized.to_csv(destination / "demografia_provincial_2017_2024.csv", index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    print(f"Demografía normalizada: {len(normalized)} filas; edades suman el total en todos los territorios y años.")


if __name__ == "__main__":
    main()
