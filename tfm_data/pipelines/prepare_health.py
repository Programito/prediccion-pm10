"""Ejecutar desde la raíz: python -m tfm_data.pipelines.prepare_health"""

from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import hashlib
import json
import re

import pandas as pd

from tfm_data.mappers.health import HealthContext, INEHealthReader, INEHealthMapper, INEHealthValidator


def main():
    root = PROJECT_ROOT
    source = root / "data/raw/health_air_history"
    destination = root / "data/interim/health"
    manifiesto = json.loads((source / "sources.json").read_text(encoding="utf-8-sig"))
    reader = INEHealthReader()
    mapper = INEHealthMapper()
    validator = INEHealthValidator()
    tables = []
    for source_info in manifiesto["sources"]:
        if source_info["kind"] != "ine_tasas_residencia" or source_info["status"] != "downloaded":
            continue
        path = source / source_info["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source_info["sha256"]:
            raise ValueError(f"El original cambió respecto al manifiesto: {path.name}")
        tabla_id = re.search(r"tpx=(\d+)", source_info["catalog_url"])
        if tabla_id is None:
            raise ValueError("No se puede identificar la tabla oficial.")
        context = HealthContext(source_info["year"], f"INE {tabla_id[1]}", path.name)
        normalized = mapper.transform(reader.read(path), context)
        validator.validate(normalized)
        tables.append(normalized)
    if not tables:
        raise ValueError("No hay fuentes sanitarias descargadas.")
    all_rows = pd.concat(tables, ignore_index=True).sort_values(["anio", "codigo_diagnostico", "territorio"])
    validator.validate(all_rows)
    provincias = all_rows.loc[all_rows.nivel_geografico.eq("provincia")].copy()
    # Validamos el conjunto completo antes de escribir resultados.
    destination.mkdir(parents=True, exist_ok=True)
    all_rows.to_csv(destination / "tasas_respiratorias_todos_niveles.csv", index=False, encoding="utf-8-sig")
    provincias.to_csv(destination / "tasas_respiratorias_provincias.csv", index=False, encoding="utf-8-sig")
    summary = provincias.groupby("anio").agg(filas=("codigo_provincia", "size"), territorios=("codigo_provincia", "nunique"), diagnosticos=("codigo_diagnostico", "nunique"))
    print(summary.to_string())
    print(f"Total: {len(all_rows)} filas; selección provincial: {len(provincias)} filas.")
    print(f"Resultados: {destination}")


if __name__ == "__main__":
    main()
