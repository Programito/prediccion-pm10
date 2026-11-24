"""Register the processed tables that connect the project's main analyses."""

import csv
from pathlib import Path


BARCELONA_DAILY = "data/interim/experiments/barcelona/diario_2017_2024.csv"

TABLES = [
    ("pm10-diario", "mapped", "madrid", "PM10 diario de Madrid", "PM10 y meteorología", "data/interim/daily_pollution/pm10_madrid_diario_2017_2024.csv",
     "AirQualityMapper + agregación diaria", ["codigo_estacion", "fecha"], "Una fila por estación y día.",
     "Reúne las mediciones diarias de PM10 de las tres estaciones de Madrid. Si un día no tiene una medición válida, se conserva la fila y el PM10 válido queda vacío. La serie permite usar las mediciones de días anteriores para predecir el PM10 del día siguiente."),
    ("pm10-supervisado", "supervised", "madrid", "Tabla supervisada de PM10 de Madrid", "PM10 y meteorología", "data/interim/pm10_prediction/tabla_supervisada_pm10.csv",
     "PM10ForecastMapper + etiqueta de PM10 elevado", ["codigo_estacion", "fecha_objetivo"], "Una fila por estación y día que se quiere predecir.",
     "Transforma la serie en observaciones de entrenamiento, validación y prueba, con retardos, calendario y la concentración del día siguiente."),
    ("pm10-diario-barcelona", "mapped", "barcelona", "PM10 diario de Barcelona provincia", "PM10", BARCELONA_DAILY,
     "AirQualityMapper + agregación diaria", ["codigo_estacion", "fecha"], "Una fila por estación y día.",
     "Reúne las observaciones de Rubí, Sant Celoni y Sant Vicenç dels Horts entre 2017 y 2024, incluidos los días sin medida."),
    ("pm10-supervisado-barcelona", "supervised", "barcelona", "Tabla supervisada de PM10 de Barcelona provincia", "PM10",
     "data/interim/experiments/barcelona/tabla_supervisada.csv",
     "PM10ForecastMapper", ["codigo_estacion", "fecha_objetivo"], "Una fila por estación y fecha objetivo.",
     "Contiene los retardos, las medias móviles, el calendario y el objetivo del día siguiente para la réplica de regresión."),
    ("gfs-estacion", "mapped", "madrid", "Previsión meteorológica diaria", "PM10 y meteorología", "data/interim/weather_forecasts/gfs_2021_2025/previsiones_gfs_diarias.csv",
     "map_daily_weather", ["codigo_estacion", "fecha_objetivo"], "Una fila por estación y fecha de validez de la previsión.",
     "GFS (Global Forecast System) es el modelo de previsión meteorológica de NOAA. Esta tabla recoge el viento previsto al mediodía y la precipitación acumulada prevista para el día objetivo."),
    ("pm10-meteo", "joined", "madrid", "PM10 con previsión meteorológica", "PM10 y meteorología", "data/interim/pm10_weather/tabla_pm10_meteo.csv",
     "prepare_pm10_weather", ["codigo_estacion", "fecha_objetivo"], "Una fila por estación y día objetivo, incluidas filas incompletas.",
     "Combina las mediciones de PM10 con el viento y la precipitación previstos por el modelo meteorológico GFS de NOAA. La marca fila_comun_utilizable indica qué filas sirven para comparar los dos modelos de avisos."),
    ("altas-provincia", "mapped", "provincial", "Altas respiratorias provinciales", "Sanidad y demografía", "data/interim/health/tasas_respiratorias_provincias.csv",
     "INEHealthMapper + selección provincial", ["codigo_provincia", "anio", "codigo_diagnostico"], "Una fila por provincia, año y diagnóstico.",
     "Normaliza la tasa de altas respiratorias por cada 100.000 habitantes y conserva el diagnóstico y la procedencia."),
    ("demografia-provincia", "mapped", "provincial", "Demografía provincial", "Sanidad y demografía", "data/interim/demographics/demografia_provincial_2017_2024.csv",
     "INEDemographicsMapper", ["codigo_provincia", "anio"], "Una fila por provincia y año, con población a 1 de enero.",
     "Resume población total y grupos de edad para describir la estructura demográfica de cada territorio."),
    ("panel-sanitario", "joined", "provincial", "Panel sanitario con demografía", "Sanidad y demografía", "data/interim/initial_comparison/panel_con_demografia.csv",
     "initial_health_comparison", ["codigo_provincia", "anio"], "Una fila por provincia y año en el análisis respiratorio.",
     "Une la tasa de altas, la demografía y el indicador provincial de PM10 cuando está disponible. La unidad de análisis es el territorio."),
]

PREPARATION = {
    "pm10-diario": "Se normalizan las mediciones y se obtiene un valor diario por estación. Se prioriza la medida diaria oficial y, si falta, se calcula la media cuando hay al menos 18 horas válidas.",
    "pm10-diario-barcelona": "Se normalizan las mediciones diarias y horarias. Se completa el calendario de cada estación y se dejan vacíos los días sin una medida válida.",
    "pm10-supervisado": "Para cada estación se calculan los valores de días anteriores y las medias móviles. La medición del día siguiente se guarda como objetivo.",
    "pm10-supervisado-barcelona": "Para cada estación se calculan los valores de días anteriores y las medias móviles. La medición del día siguiente se guarda como objetivo.",
    "gfs-estacion": "Se elige la celda de GFS más próxima a cada estación y se extraen el viento al mediodía y la precipitación prevista para el día.",
    "pm10-meteo": "Se une la tabla supervisada de PM10 a las previsiones de GFS por estación y fecha objetivo.",
    "altas-provincia": "Se normalizan las tasas publicadas por el INE y se identifican las provincias y los diagnósticos con sus códigos.",
    "demografia-provincia": "Se toma la población a 1 de enero y se agrupan las edades para calcular recuentos y proporciones.",
    "panel-sanitario": "Se unen las altas respiratorias, la población y el indicador provincial de PM10 por provincia y año.",
}

NOTES = {
    "codigo_estacion": ("Código", "Identificador de la estación de medida."),
    "codigo_provincia": ("Código", "Identificador de provincia, con sus ceros iniciales."),
    "codigo_diagnostico": ("Código", "Grupo de diagnóstico del INE."),
    "punto_muestreo": ("Código", "Identificador que conserva la estación, el contaminante y la técnica."),
    "fecha": ("Fecha", "Día de la observación de PM10."),
    "fecha_objetivo": ("Fecha", "Día para el que se emite el pronóstico."),
    "fecha_ultima_observacion": ("Fecha", "Último día de PM10 disponible para construir las entradas."),
    "inicio_ciclo_utc": ("Fecha y hora UTC", "Ciclo GFS usado para la previsión."),
    "emision_simulada_utc": ("Fecha y hora UTC", "Instante de emisión simulado para la evaluación."),
    "anio": ("Entero", "Año de la observación o del dato agregado."),
    "anio_objetivo": ("Entero", "Año de la fecha objetivo."),
    "pm10_valido": ("Decimal o nulo", "Concentración diaria de PM10 aceptada, en µg/m³."),
    "pm10_t": ("Decimal o nulo", "PM10 observado en el día previo al objetivo, en µg/m³."),
    "pm10_objetivo": ("Decimal o nulo", "PM10 observado para la fecha objetivo, en µg/m³."),
    "pm10_elevado_objetivo": ("Entero o nulo", "Vale 1 si el PM10 de la fecha objetivo supera 27 µg/m³ y 0 si no lo supera. Queda vacío si falta la medición."),
    "viento_10m_mediodia_ms": ("Decimal o nulo", "Velocidad del viento prevista a mediodía, en m/s."),
    "precipitacion_diaria_mm": ("Decimal o nulo", "Precipitación prevista acumulada en el día UTC, en mm."),
    "fila_comun_utilizable": ("Booleano", "Marca si ambos modelos disponen de predictores y objetivo completos."),
    "tasa_altas_por_100000": ("Decimal o nulo", "Tasa de altas respiratorias por cada 100.000 habitantes."),
    "poblacion_total": ("Entero o nulo", "Población total del territorio a 1 de enero."),
    "media_pm10_estaciones_fondo": ("Decimal o nulo", "Indicador provincial agregado de PM10, en µg/m³."),
}


def describe_column(name):
    if name in NOTES:
        return NOTES[name]
    if name.startswith(("es_", "hay_", "fila_", "predictores_", "objetivo_disponible", "comienzo_")):
        return "Booleano o nulo", "Indicador de disponibilidad, calidad o selección de la fila."
    if name.startswith("fecha_"):
        return "Fecha", "Fecha de referencia del valor en la fila."
    if name.startswith(("n_", "poblacion_", "dia_semana_", "mes_")) and name not in {"mes_sin", "mes_cos"}:
        return "Entero o nulo", "Recuento o componente del calendario."
    if name.startswith(("pm10_t_menos_", "media_", "desviacion_", "semana_", "mes_", "latitud_", "longitud_",
                        "proporcion_", "cobertura_", "minimo_medias_", "maximo_medias_")) or name == "concentracion":
        return "Decimal o nulo", "Medida, proporción o variable numérica derivada en el flujo."
    return "Texto o código", "Etiqueta, estado o metadato conservado para interpretar la fila."


def treated_catalog(root: Path):
    result = []
    for key, kind, scope, name, group, local, mapper, keys, grain, purpose in TABLES:
        path = root / local
        names = []
        if path.is_file():
            with path.open(encoding="utf-8-sig", newline="") as stream:
                names = next(csv.reader(stream))
            if not set(keys).issubset(names):
                raise ValueError(f"Faltan columnas de la clave en {path.name}.")
        columns = []
        for field in names:
            field_type, notes = describe_column(field)
            columns.append({"name": field, "type": field_type,
                            "notes": f"Parte de la clave. {notes}" if field in keys else notes})
        result.append(dict(id=f"treated-{key}", name=name, group=group, scope=scope, kind=kind, local=local, format="CSV", reader="csv", delimiter=",",
                           columns=columns, mapper=mapper, preparation=PREPARATION[key], keys=keys, grain=grain, purpose=purpose))
    return {table["id"]: table for table in result}
