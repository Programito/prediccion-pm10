"""Ejecutar desde la raíz: python -m tfm_data.pipelines.audit_air_coverage"""

from pathlib import Path
from tfm_data.config import PROJECT_ROOT
import json

import numpy as np
import pandas as pd

from tfm_data.evaluation.air_coverage import AirCoverageAuditor


def main():
    folder = PROJECT_ROOT / "data/interim/air/pm10_2024"
    tipos = {c: "string" for c in ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica"]}
    daily = pd.read_csv(folder / "diarias_combinadas.csv.gz", dtype=tipos, parse_dates=["fecha"])
    anual = pd.read_csv(folder / "resumen_anual_punto_muestreo.csv", dtype=tipos)
    monthly = AirCoverageAuditor().audit(daily, 2024)
    summary = monthly.groupby("punto_muestreo", as_index=False).agg(
        dias_validos_mensuales=("dias_validos", "sum"), dias_naturales=("dias_del_mes", "sum"),
        meses_sin_mediciones_validas=("mes_sin_mediciones_validas", "sum"),
        meses_con_alguna_ausencia=("mes_con_alguna_ausencia", "sum"),
        dias_sin_registro=("dias_sin_registro", "sum"),
        dias_ausentes=("dias_ausentes", "sum"), dias_negativos=("dias_negativos", "sum"),
        dias_horas_insuficientes=("dias_horas_insuficientes", "sum"))
    comparison = anual.merge(summary, on="punto_muestreo", how="outer", validate="one_to_one", indicator=True)
    if (not comparison._merge.eq("both").all()
            or not comparison.dias_validos.eq(comparison.dias_validos_mensuales).all()
            or not comparison.dias_del_anio.eq(comparison.dias_naturales).all()
            or not np.allclose(comparison.cobertura_anual, comparison.dias_validos_mensuales / comparison.dias_naturales)):
        raise ValueError("La auditoría mensual no cuadra con el resumen anual.")
    meta = anual[["punto_muestreo", "NOMBRE", "TIPO_ESTACION", "TIPO_AREA", "cobertura_anual", "cumple_criterio_exploratorio"]]
    monthly = monthly.merge(meta, on="punto_muestreo", validate="many_to_one")
    low_coverage = comparison.loc[~comparison.cumple_criterio_exploratorio].drop(columns="_merge")
    low_coverage = low_coverage.sort_values(["meses_sin_mediciones_validas", "cobertura_anual"], ascending=[False, True])
    monthly.to_csv(folder / "auditoria_cobertura_mensual.csv", index=False, encoding="utf-8-sig")
    monthly.loc[~monthly.cumple_criterio_exploratorio].to_csv(folder / "auditoria_mensual_puntos_baja_cobertura.csv", index=False, encoding="utf-8-sig")
    low_coverage.to_csv(folder / "auditoria_resumen_puntos_baja_cobertura.csv", index=False, encoding="utf-8-sig")
    result = {
        "anio": 2024, "contaminante": "PM10", "filas_punto_mes": len(monthly),
        "puntos_auditados": int(monthly.punto_muestreo.nunique()),
        "puntos_baja_cobertura_anual": len(low_coverage),
        "baja_cobertura_con_algun_mes_sin_validos": int(low_coverage.meses_sin_mediciones_validas.gt(0).sum()),
        "baja_cobertura_sin_meses_totalmente_vacios": int(low_coverage.meses_sin_mediciones_validas.eq(0).sum()),
        "dias_sin_registro_total": int(monthly.dias_sin_registro.sum()),
        "meses_sin_validos_total": int(monthly.mes_sin_mediciones_validas.sum()),
        "cuadre_con_resumen_anual": True,
        "nota": "Sin mediciones válidas no significa que la estación estuviera activa, averiada o cerrada. No se infiere la causa de las ausencias ni se certifica la exactitud física de los sensores.",
    }
    (folder / "auditoria_cobertura_resumen.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
