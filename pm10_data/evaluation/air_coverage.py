"""Auditoría mensual del calendario completo, sin imputar mediciones."""

import pandas as pd

from pm10_data.mappers.air import DAILY_KEY, AirQualityValidator


class AirCoverageAuditor:
    def audit(self, daily: pd.DataFrame, anio: int) -> pd.DataFrame:
        AirQualityValidator().validate(daily, "diaria")
        if not daily.fecha.dt.year.eq(anio).all():
            raise ValueError("La auditoría debe recibir un único año coincidente.")
        if not daily.fecha.eq(daily.fecha.dt.normalize()).all():
            raise ValueError("Se esperaban fechas diarias sin horas.")
        estados = {"valida", "ausente", "negativa_pendiente_revision", "cobertura_horaria_insuficiente"}
        if not daily.estado.isin(estados).all():
            raise ValueError("Hay estados sin clasificar para la auditoría.")
        columns = ["codigo_provincia", "codigo_estacion", "punto_muestreo", "magnitud", "tecnica", "unidad", "contaminante"]
        points = daily[columns].drop_duplicates()
        if points.punto_muestreo.duplicated().any():
            raise ValueError("Los metadatos de un punto cambian dentro del año.")
        # El calendario hace visibles también meses que no tienen ninguna fila.
        calendar_grid = pd.DataFrame({"fecha": pd.date_range(f"{anio}-01-01", f"{anio}-12-31")})
        rejilla = points.merge(calendar_grid, how="cross")
        data = daily[DAILY_KEY + ["estado", "concentracion", "origen_diario", "archivo_origen", "miembro_zip"]]
        rejilla = rejilla.merge(data, on=DAILY_KEY, how="left", validate="one_to_one", indicator="presencia")
        rejilla["mes"] = rejilla.fecha.dt.month
        rejilla["con_registro"] = rejilla.presencia.eq("both").astype(int)
        rejilla["valido"] = rejilla.estado.eq("valida").astype(int)
        rejilla["ausente"] = rejilla.estado.eq("ausente").astype(int)
        rejilla["negativo"] = rejilla.estado.eq("negativa_pendiente_revision").astype(int)
        rejilla["horas_insuficientes"] = rejilla.estado.eq("cobertura_horaria_insuficiente").astype(int)
        rejilla["valido_oficial"] = (rejilla.estado.eq("valida") & rejilla.origen_diario.eq("diario_oficial")).astype(int)
        rejilla["valido_derivado"] = (rejilla.estado.eq("valida") & rejilla.origen_diario.eq("derivado_horario")).astype(int)
        if not (rejilla.valido_oficial + rejilla.valido_derivado).eq(rejilla.valido).all():
            raise ValueError("Hay medidas válidas con origen diario desconocido.")
        rejilla["valor_valido"] = rejilla.concentracion.where(rejilla.valido.eq(1))
        monthly = rejilla.groupby(columns + ["mes"], as_index=False, observed=True).agg(
            dias_del_mes=("fecha", "size"), dias_con_registro=("con_registro", "sum"),
            dias_validos=("valido", "sum"), dias_ausentes=("ausente", "sum"),
            dias_negativos=("negativo", "sum"), dias_horas_insuficientes=("horas_insuficientes", "sum"),
            dias_validos_oficiales=("valido_oficial", "sum"), dias_validos_derivados=("valido_derivado", "sum"),
            media_dias_validos=("valor_valido", "mean"))
        monthly["anio"] = anio
        monthly["periodo"] = pd.to_datetime(dict(year=monthly.anio, month=monthly.mes, day=1)).dt.strftime("%Y-%m")
        monthly["dias_sin_registro"] = monthly.dias_del_mes - monthly.dias_con_registro
        monthly["dias_no_validos_con_registro"] = monthly.dias_con_registro - monthly.dias_validos
        monthly["cobertura_mensual"] = monthly.dias_validos / monthly.dias_del_mes
        monthly["mes_sin_mediciones_validas"] = monthly.dias_validos.eq(0)
        monthly["mes_con_alguna_ausencia"] = monthly.dias_validos.lt(monthly.dias_del_mes)
        total = monthly.dias_validos + monthly.dias_ausentes + monthly.dias_negativos + monthly.dias_horas_insuficientes + monthly.dias_sin_registro
        if not total.eq(monthly.dias_del_mes).all():
            raise ValueError("Las categorías no cuadran con los días naturales.")
        # Estas columnas enlazan con los archivos originales, incluso en meses sin fila.
        procedencia = daily.groupby("punto_muestreo", as_index=False).agg(
            archivos_origen=("archivo_origen", lambda s: " | ".join(sorted(s.dropna().unique()))),
            miembros_zip=("miembro_zip", lambda s: " | ".join(sorted(s.dropna().unique()))))
        return monthly.merge(procedencia, on="punto_muestreo", validate="many_to_one").sort_values(["punto_muestreo", "mes"]).reset_index(drop=True)
