"""Revisa originales descargados. Genera inventarios; no crea la tabla de modelos."""

from pathlib import Path
import io
import json
import zipfile

import pandas as pd


RAIZ = Path(__file__).resolve().parents[1]
ORIGEN = RAIZ / "data/raw/health_air_history"
SALIDA = RAIZ / "data/interim/history_audit"
SALIDA.mkdir(parents=True, exist_ok=True)

sanidad = []
aire = []
horarios = []
for anio in range(2016, 2025):
    file = ORIGEN / f"ine_tasas_residencia_{anio}.csv"
    df = pd.read_csv(file, sep=";", encoding="utf-8-sig", dtype="string")
    if not df.columns[0].startswith("Diagnóstico") or "Total" not in df.columns:
        raise ValueError(f"Formato sanitario inesperado: {file}")
    diagnosticos = df.iloc[:, 0].str.split().str[0]
    selection = df.loc[diagnosticos.isin(["1000", "1006", "1007"])]
    if set(diagnosticos[diagnosticos.isin(["1000", "1006", "1007"])]) != {"1000", "1006", "1007"}:
        raise ValueError(f"Falta un diagnóstico en {anio}")
    # Solo identificamos las dimensiones: no normalizamos territorios todavía.
    geografia = [c for c in df.columns if c not in [df.columns[0], "Total"]]
    sanidad.append({
        "anio": anio, "filas_originales": len(df), "columnas": len(df.columns),
        "filas_tres_grupos_respiratorios": len(selection),
        "tasas_respiratorias_ausentes": int(selection.Total.isna().sum() + selection.Total.eq("..").sum()),
        "columnas_geograficas": " | ".join(geografia),
        "archivo": file.name,
    })

    with zipfile.ZipFile(ORIGEN / f"miteco_diarios_{anio}.zip") as z:
        corrupto = z.testzip()
        if corrupto:
            raise ValueError(f"Miembro ZIP corrupto: {corrupto}")
        for contaminante, prefijos in [("PM10", ("PM10_",)), ("PM2.5", ("PM2.5_", "PM25_"))]:
            members = [n for n in z.namelist() if Path(n).name.startswith(prefijos)]
            if len(members) != 1:
                raise ValueError(f"Se esperaba un fichero para {contaminante} en {anio}")
            member = members[0]
            content = io.BytesIO(z.read(member))
            if member.endswith(".xlsx"):
                data = pd.read_excel(content)
            else:
                data = pd.read_csv(content, sep=";", encoding="utf-8-sig")
            data.columns = [str(c).strip().upper() for c in data.columns]
            if set(pd.to_numeric(data["ANNO"], errors="raise").dropna().astype(int)) != {anio}:
                raise ValueError(f"Año ambiental incorrecto en {member}")
            dias = data.filter(regex=r"^D\d{2}$")
            if len(dias.columns) != 31:
                raise ValueError(f"Formato diario inesperado: {member}")
            con_valores = dias.notna().any(axis=1)
            aire.append({
                "anio": anio, "contaminante": contaminante,
                "filas_estacion_mes": len(data),
                "codigos_provinciales_con_valores": data.loc[con_valores, "PROVINCIA"].nunique(),
                "estaciones_con_valores": len(data.loc[con_valores, ["PROVINCIA", "MUNICIPIO", "ESTACION"]].drop_duplicates()),
                "celdas_diarias_no_vacias": int(dias.notna().sum().sum()),
                "formato_original": Path(member).suffix,
                "miembro_zip": member,
            })

    with zipfile.ZipFile(ORIGEN / f"miteco_horarios_{anio}.zip") as z:
        if z.testzip():
            raise ValueError(f"ZIP horario corrupto en {anio}")
        for contaminante, prefijos in [("PM10", ("PM10_",)), ("PM2.5", ("PM2.5_", "PM25_")), ("NO2", ("NO2_",))]:
            members = [n for n in z.namelist() if Path(n).name.startswith(prefijos)]
            if len(members) != 1:
                raise ValueError(f"Fichero horario inesperado para {contaminante} en {anio}")
            member = members[0]
            if member.endswith(".xlsx"):
                # El Excel de 2016 se valida como archivo, pero aún no se perfila.
                horarios.append({"anio": anio, "contaminante": contaminante,
                                 "estado": "xlsx_descargado_pendiente_perfil", "miembro_zip": member})
                continue
            provincias = set()
            stations = set()
            rows = celdas = 0
            with z.open(member) as f:
                for chunk in pd.read_csv(f, sep=";", encoding="utf-8-sig", chunksize=20000):
                    if set(chunk.ANNO.dropna().astype(int)) != {anio}:
                        raise ValueError(f"Año horario incorrecto: {member}")
                    horas = chunk.filter(regex=r"^H\d{2}$")
                    if len(horas.columns) != 24:
                        raise ValueError(f"Columnas horarias inesperadas: {member}")
                    presentes = horas.notna().any(axis=1)
                    provincias.update(chunk.loc[presentes, "PROVINCIA"].astype(int))
                    stations.update(chunk.loc[presentes, ["PROVINCIA", "MUNICIPIO", "ESTACION"]].itertuples(index=False, name=None))
                    rows += len(chunk)
                    celdas += int(horas.notna().sum().sum())
            horarios.append({"anio": anio, "contaminante": contaminante, "estado": "csv_perfilado",
                             "codigos_provinciales_con_valores": len(provincias),
                             "estaciones_con_valores": len(stations), "filas_estacion_dia": rows,
                             "celdas_horarias_no_vacias": celdas, "miembro_zip": member})

health = pd.DataFrame(sanidad)
ambiental = pd.DataFrame(aire)
horario = pd.DataFrame(horarios)
health.to_csv(SALIDA / "cobertura_sanidad.csv", index=False, encoding="utf-8-sig")
ambiental.to_csv(SALIDA / "cobertura_aire.csv", index=False, encoding="utf-8-sig")
horario.to_csv(SALIDA / "cobertura_aire_horario.csv", index=False, encoding="utf-8-sig")
manifest = json.loads((ORIGEN / "sources.json").read_text(encoding="utf-8-sig"))
fallos = [s for s in manifest["sources"] if s["status"] != "downloaded"]
summary = {
    "anios_ambas_fuentes": sorted(set(health.anio) & set(ambiental.anio)),
    "archivos_descargados": sum(s["status"] == "downloaded" for s in manifest["sources"]),
    "bytes_descargados": sum(s.get("bytes", 0) for s in manifest["sources"]),
    "errores_descarga": fallos,
    "celdas_diarias_no_vacias_pm": int(ambiental.celdas_diarias_no_vacias.sum()),
    "celdas_horarias_no_vacias_pm_no2_csv": int(horario.celdas_horarias_no_vacias.sum()),
    "horarios_xlsx_pendientes_perfil": horario.loc[horario.estado.ne("csv_perfilado"), ["anio", "contaminante"]].to_dict("records"),
    "advertencia": "Presencia de datos no garantiza cobertura anual suficiente ni representatividad provincial. No se han unido fuentes, ajustado por edad ni validado comparabilidad de tasas entre años.",
}
(SALIDA / "resumen.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(health[["anio", "filas_originales", "filas_tres_grupos_respiratorios", "tasas_respiratorias_ausentes"]].to_string(index=False))
print(ambiental[["anio", "contaminante", "codigos_provinciales_con_valores", "celdas_diarias_no_vacias"]].to_string(index=False))
print(horario[["anio", "contaminante", "estado", "codigos_provinciales_con_valores"]].to_string(index=False))
print(json.dumps(summary, ensure_ascii=True, indent=2))
