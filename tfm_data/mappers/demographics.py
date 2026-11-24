"""Mapeo de la tabla provincial de población por edad del INE (56945)."""

import pandas as pd

from tfm_data.mappers.health import parse_spanish_rate


class INEDemographicsMapper:
    def transform(self, original: pd.DataFrame) -> pd.DataFrame:
        if set(original.columns) != {"Edad simple", "Provincias", "Sexo", "Periodo", "Total"}:
            raise ValueError("Esquema demográfico inesperado.")
        data = original.astype("string").copy()
        if not data.Sexo.eq("Total").all():
            raise ValueError("Se esperaba exclusivamente el total de ambos sexos.")
        anios = data.Periodo.str.strip().str.extract(r"^1 de enero de (\d{4})$", expand=False)
        codigos = data.Provincias.str.extract(r"^(\d{2})\s", expand=False)
        if anios.isna().any() or codigos.isna().any():
            raise ValueError("Periodo o código provincial no reconocido.")
        data["anio"] = anios.astype(int)
        data["codigo_provincia"] = codigos
        if data.duplicated(["codigo_provincia", "anio", "Edad simple"]).any():
            raise ValueError("Edades duplicadas para una provincia y año.")
        data["poblacion"] = parse_spanish_rate(data.Total)
        if data.poblacion.isna().any() or data.poblacion.lt(0).any() or data.poblacion.mod(1).ne(0).any():
            raise ValueError("Los recuentos de población deben ser enteros no negativos.")
        data["poblacion"] = data.poblacion.astype("Int64")
        claves = ["codigo_provincia", "anio"]
        totales = data.loc[data["Edad simple"].eq("Todas las edades"), claves + ["poblacion"]].rename(columns={"poblacion": "poblacion_total"})
        edades = data.loc[~data["Edad simple"].isin(["Todas las edades", "85 y más años"])].copy()
        # 85 y más es un subtotal: sumarlo con 85, 86…100+ duplicaría personas.
        edades["edad"] = edades["Edad simple"].str.extract(r"^(\d+) (?:años?|y más años)$", expand=False).astype("Int64")
        if edades.edad.isna().any():
            raise ValueError("Etiqueta de edad no reconocida.")
        counts = edades.groupby(claves).edad.agg(["nunique", "min", "max"])
        if not (counts["nunique"].eq(101) & counts["min"].eq(0) & counts["max"].eq(100)).all():
            raise ValueError("Faltan edades simples 0-99 o el grupo 100 y más.")
        result = totales.set_index(claves)
        suma = edades.groupby(claves).poblacion.sum()
        if set(result.index) != set(suma.index) or not result.poblacion_total.eq(suma).all():
            raise ValueError("La suma de edades no coincide con el total oficial.")
        for name, mask in [("poblacion_0_14", edades.edad.lt(15)),
                                ("poblacion_65_mas", edades.edad.ge(65)),
                                ("poblacion_80_mas", edades.edad.ge(80))]:
            result[name] = edades.loc[mask].groupby(claves).poblacion.sum()
        if result.poblacion_total.le(0).any():
            raise ValueError("Población total nula.")
        for group in ["0_14", "65_mas", "80_mas"]:
            result[f"proporcion_{group}"] = result[f"poblacion_{group}"] / result.poblacion_total
        result = result.reset_index()
        result["fecha_referencia_poblacion"] = pd.to_datetime(dict(year=result.anio, month=1, day=1))
        result["fuente_demografia"] = "INE ECP 56945; serie revisada descargada en 2026"
        return result.sort_values(claves).reset_index(drop=True)
