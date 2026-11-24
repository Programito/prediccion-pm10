"""Explain source and treated columns using the project's schemas and rules."""

import re


SOURCE = {
    "PROVINCIA": ("Código", "Provincia de la estación. Al normalizar se conservan dos posiciones, incluidos los ceros iniciales."),
    "MUNICIPIO": ("Código", "Municipio dentro de la provincia. Ocupa tres posiciones en el código normalizado."),
    "ESTACION": ("Código", "Número de estación dentro del municipio. Ocupa las últimas tres posiciones de su código completo."),
    "MAGNITUD": ("Código", "Identifica qué se mide. En MITECO, 10 corresponde a PM10. La hoja Magnitudes da el nombre y la unidad."),
    "PUNTO_MUESTREO": ("Código", "Combina el código completo de estación, el código de magnitud y la técnica de medida, separados por guiones bajos."),
    "ANNO": ("Entero", "Año de la medida, con cuatro cifras."),
    "MES": ("Entero", "Mes de la medida. De 1 para enero a 12 para diciembre."),
    "DIA": ("Entero", "Día del mes en que comienza la jornada de medición."),
    "ABREVIATURA": ("Texto", "Abreviatura de la magnitud o del contaminante, como PM10 o SO2."),
    "UNIDAD": ("Texto", "Unidad en que se expresa la concentración de esa magnitud, como µg/m³ o mg/m³."),
    "GRUPO": ("Texto", "Agrupación de la magnitud en el catálogo, por ejemplo contaminantes con valor legislado."),
    "COD_LOCAL": ("Código", "Identificador completo de estación. Concatena provincia, municipio y estación y se normaliza a ocho posiciones."),
    "COD_ESTACION_DEM": ("Código o nulo", "Identificador europeo de la estación, útil para contrastar series de distintas fuentes."),
    "N_RED": ("Texto", "Nombre de la red de vigilancia que gestiona la estación."),
    "FECHA_INI": ("Fecha o nulo", "Fecha de inicio de actividad consignada para la estación."),
    "FECHA_FIN": ("Fecha o nulo", "Fecha de fin de actividad consignada. En blanco si el fichero no registra una fecha de fin."),
    "LATITUD_G": ("Decimal", "Latitud de la estación en grados geográficos. Los valores positivos indican el norte."),
    "LONGITUD_G": ("Decimal", "Longitud de la estación en grados geográficos. Los valores negativos indican el oeste."),
    "ALTITUD": ("Decimal o nulo", "Altitud de la estación en metros."),
    "N_CCAA": ("Texto", "Nombre de la comunidad autónoma de la estación."),
    "N_PROVINCIA": ("Texto", "Nombre de la provincia de la estación."),
    "N_MUNICIPIO": ("Texto", "Nombre del municipio de la estación."),
    "TIPO_ESTACION": ("Categoría", "Tipo de estación según la influencia dominante, por ejemplo tráfico, industrial o fondo."),
    "TIPO_AREA": ("Categoría", "Tipo de entorno de la estación, por ejemplo urbano, suburbano o rural."),
    "TIPO_SUBAREA_RURAL": ("Categoría o nulo", "Subclasificación del entorno para estaciones rurales."),
    "EST": ("Código", "Código EST del catálogo de estaciones. Se conserva como aparece en el proveedor y no se utiliza en el modelado."),
    "ZONA": ("Categoría o nulo", "Uso predominante de la zona donde está la estación, por ejemplo residencial."),
    "DIRECCION": ("Texto o nulo", "Dirección consignada para localizar la estación."),
    "TECNICA": ("Código", "Código del procedimiento con el que se mide la magnitud. Puede formar parte del identificador del punto."),
    "NOMBRE_I": ("Texto o nulo", "Nombre en inglés que figura en el catálogo de técnicas."),
    "OTROS CÓDIGOS": ("Código o nulo", "Códigos alternativos del catálogo de técnicas, como A para automática y M para manual en partículas."),
    "Diagnóstico principal (CIE10MC)": ("Texto con código", "Código y nombre del grupo de diagnóstico principal según la clasificación CIE-10-MC."),
    "Provincia, Comunidad y Ciudad autónoma de residencia": ("Texto con código", "Territorio de residencia con que se publica la tasa, incluida la fila nacional cuando existe."),
    "Total Nacional": ("Texto o nulo", "Nivel nacional de la jerarquía territorial de la tabla del INE."),
    "Comunidades y Ciudades Autónomas": ("Texto o nulo", "Comunidad o ciudad autónoma del territorio de residencia."),
    "Edad simple": ("Categoría", "Edad en años cumplidos o grupo publicado por el INE, como 100 y más o todas las edades."),
    "Sexo": ("Categoría", "Sexo de la población contada o total de ambos sexos."),
    "Periodo": ("Fecha en texto", "Fecha de referencia del recuento que figura en la tabla, por ejemplo 1 de enero de 2024."),
    "Validity": ("Código entero", "Validez de la medida. 1 es válida, 2 y 3 indican valores válidos por debajo del límite de detección. Los negativos indican invalidez."),
    "Verification": ("Código entero", "Estado de verificación de EEA. 1 verificada, 2 verificación preliminar y 3 sin verificar."),
    "DataCapture": ("Decimal o nulo", "Dato de captura de observaciones declarado en el registro EEA."),
    "Start": ("Fecha y hora", "Inicio del intervalo en la hora del archivo EEA, UTC+1 fijo. Se resta una hora para convertirlo a UTC."),
    "End": ("Fecha y hora", "Fin del intervalo en la hora del archivo EEA, UTC+1 fijo. Se resta una hora para convertirlo a UTC."),
    "Value": ("Decimal o nulo", "Valor observado en el intervalo. Su unidad está en Unit y sus controles en Validity y Verification."),
}

TREATED = {
    "NOMBRE": ("Texto", "Nombre de la estación de vigilancia asignado desde el catálogo MITECO."),
    "TIPO_AREA": ("Categoría", "Entorno de la estación, urbano, suburbano o rural."),
    "concentracion": ("Decimal o nulo", "Concentración diaria elegida en µg/m³. El estado indica si se acepta para el análisis."),
    "estado": ("Categoría", "Estado de calidad de la medida elegida. Permite distinguir una lectura válida, ausente o pendiente de revisión."),
    "origen_diario": ("Categoría o nulo", "Indica si se usó una medida diaria oficial o una media calculada con horas válidas."),
    "n_horas_validas": ("Entero o nulo", "Horas válidas disponibles para la media diaria derivada. Puede estar vacío cuando se usa la medida diaria oficial."),
    "archivo_origen": ("Texto o nulo", "Nombre del archivo descargado del que procede la observación original."),
    "miembro_zip": ("Texto o nulo", "Nombre del fichero de medidas dentro del ZIP original."),
    "unidad": ("Texto", "Unidad de la concentración diaria, µg/m³ en las series de PM10."),
    "es_valido": ("Booleano", "Sí si la observación diaria se aceptó para el análisis. No si está ausente o no pasa el control de calidad."),
    "dia_semana_objetivo": ("Entero", "Día de la semana de la fecha objetivo. Lunes es 0 y domingo es 6."),
    "mes_objetivo": ("Entero", "Mes de la fecha objetivo, de 1 a 12."),
    "particion": ("Categoría", "Grupo de la evaluación original de PM10, asignado por el año de la fecha objetivo."),
    "particion_meteo": ("Categoría", "Grupo de la comparación con GFS, asignado por el año de la fecha objetivo."),
    "objetivo_disponible": ("Booleano", "True si se dispone del PM10 observado para el día objetivo."),
    "predictores_completos": ("Booleano", "True si todas las variables de PM10 necesarias para el modelo tienen valor."),
    "fila_utilizable": ("Booleano", "True si están completos los predictores y el objetivo y la fecha pertenece a un grupo de evaluación."),
    "latitud_gfs": ("Decimal o nulo", "Latitud en grados de la celda de GFS seleccionada para la estación."),
    "longitud_gfs": ("Decimal o nulo", "Longitud en grados de la celda GFS seleccionada, en el intervalo de −180 a 180 grados."),
    "estado_viento": ("Categoría", "Indica si pudo calcularse el viento previsto. Un guion en Registros representa un mensaje de GFS ausente o que no pudo leerse."),
    "estado_precipitacion": ("Categoría", "Indica si pudo calcularse la precipitación prevista y si hubo algún ajuste. Un guion en Registros representa un mensaje de GFS ausente o que no pudo leerse."),
    "fila_gfs_presente": ("Booleano", "True si la tabla de previsiones tiene la misma clave de estación y fecha objetivo."),
    "predictores_meteo_completos": ("Booleano", "True si están disponibles tanto el viento como la precipitación previstos."),
    "comienzo_pm10_elevado": ("Booleano o nulo", "True si el día objetivo supera 27 µg/m³ y la última observación era de 27 µg/m³ o menos."),
    "diagnostico_original": ("Texto", "Etiqueta del diagnóstico tal como aparece publicada por el INE."),
    "territorio_original": ("Texto", "Etiqueta territorial que figura en la fuente original."),
    "territorio": ("Texto", "Nombre normalizado del territorio de residencia."),
    "nivel_geografico_original": ("Categoría", "Nivel territorial con el que se publicó la fila, por ejemplo provincia o comunidad autónoma."),
    "nivel_geografico": ("Categoría", "Nivel territorial asignado después de normalizar la fila."),
    "codigo_ccaa": ("Código", "Código de la comunidad o ciudad autónoma asociada al territorio."),
    "tasa_original": ("Texto", "Tasa tal como se publicó en el CSV, con sus separadores originales."),
    "fuente_tabla": ("Texto", "Identificador de la tabla INE que publicó la tasa."),
    "fecha_referencia_poblacion": ("Fecha", "Fecha del recuento de población utilizado, el 1 de enero del año."),
    "fuente_demografia": ("Texto", "Referencia de la tabla y la serie de población de la que procede el recuento."),
    "minimo_medias_estacion": ("Decimal o nulo", "Menor media anual de PM10 entre las estaciones elegidas en el territorio, en µg/m³."),
    "maximo_medias_estacion": ("Decimal o nulo", "Mayor media anual de PM10 entre las estaciones elegidas en el territorio, en µg/m³."),
    "n_estaciones": ("Entero", "Número de estaciones que contribuyen al indicador provincial."),
    "cobertura_minima_estacion": ("Proporción o nulo", "Menor proporción de días efectivos entre las estaciones utilizadas."),
    "cobertura_media_estaciones": ("Proporción o nulo", "Promedio de las proporciones de días efectivos de las estaciones utilizadas."),
    "n_urbanas": ("Entero", "Número de estaciones del territorio en área urbana que contribuyen al indicador."),
    "n_suburbanas": ("Entero", "Número de estaciones del territorio en área suburbana que contribuyen al indicador."),
    "n_rurales": ("Entero", "Número de estaciones del territorio en área rural que contribuyen al indicador."),
    "n_area_no_clasificada": ("Entero", "Número de estaciones contribuyentes sin clasificación de área."),
    "unidad_pm10": ("Texto o nulo", "Unidad en que se expresa el indicador provincial de PM10."),
    "metodo_pm10": ("Texto o nulo", "Método indicado para agregar las medidas de PM10 por territorio y año."),
    "cruce_ambiental": ("Categoría", "Resultado de la unión al panel de sanidad. both indica coincidencia y left_only una fila sanitaria sin indicador ambiental."),
    "hay_indicador_pm10": ("Booleano", "True si existe un indicador de PM10 en ese territorio y año."),
}


def describe_source(name, table, profile):
    if profile == "sanidad" and name == "Total":
        return "Decimal o nulo", "Tasa anual de altas hospitalarias por cada 100.000 habitantes para el territorio y diagnóstico de la fila."
    if profile == "demografia" and name == "Total":
        return "Entero o nulo", "Número de personas para la edad, territorio, sexo y fecha de referencia de la fila."
    if name == "Provincias" and profile in {"sanidad", "demografia"}:
        return "Texto con código", "Código y nombre de la provincia en el fichero del INE."
    if name == "NOMBRE" and profile == "estaciones":
        sheet = table.get("sheet", "").casefold()
        kind = "magnitud" if "magnitud" in sheet else "técnica de medida" if re.search(r"t[eé]cnic", sheet) else "estación"
        return "Texto", f"Nombre de la {kind} tal como figura en esta hoja."
    if profile in {"aire-diario", "aire-horario"} and re.fullmatch(r"[DH]\d{2}", name):
        n = int(name[1:])
        unit = "La unidad depende de MAGNITUD. Para PM10 es µg/m³."
        description = f"Concentración del día {n} del mes. {unit}" if name.startswith("D") else (
            f"Concentración del intervalo de {n - 1:02d}:00 a {n:02d}:00 UTC. Las 24:00 son las 00:00 del día siguiente. {unit}")
        return "Decimal o nulo", description
    if name.startswith("Unnamed:"):
        return "Columna auxiliar", "La hoja original no tiene encabezado en esta posición. Se conserva el valor publicado si existe."
    return SOURCE.get(name)


def describe_treated(name):
    if name in TREATED:
        return TREATED[name]
    if name.startswith("pm10_t_menos_"):
        return "Decimal o nulo", f"PM10 de la misma estación {name.rsplit('_', 1)[1]} días antes de la última observación, en µg/m³."
    if name.startswith("media_") and name.endswith("_dias"):
        return "Decimal o nulo", f"Media de PM10 de los últimos {name.split('_')[1]} días, incluido el último observado, en µg/m³. Queda vacía si falta una medición en la ventana."
    if name == "desviacion_7_dias":
        return "Decimal o nulo", "Desviación típica muestral del PM10 durante los últimos siete días consecutivos, en µg/m³."
    if name in {"semana_sin", "semana_cos", "mes_sin", "mes_cos"}:
        term = "día de la semana" if name.startswith("semana_") else "mes"
        function = "seno" if name.endswith("_sin") else "coseno"
        return "Decimal", f"Codificación cíclica mediante {function} del {term} de la fecha objetivo. Su rango va de −1 a 1."
    if re.fullmatch(r"(?:poblacion|proporcion)_(0_14|65_mas|80_mas)", name):
        band = {"0_14": "0 a 14 años", "65_mas": "65 años o más", "80_mas": "80 años o más"}[name.split("_", 1)[1]]
        return ("Entero o nulo", f"Número de personas de {band} en el territorio a 1 de enero.") if name.startswith("poblacion") else (
            "Proporción o nulo", f"Personas de {band} divididas por la población total. Va de 0 a 1.")
    return None


def enrich_columns(table, profile=None):
    storage = {"csv": "Texto en CSV", "xls": "Celda de Excel (.xls)", "xlsx": "Celda de Excel (.xlsx)",
               "parquet": "Campo tipado en Parquet", "json": "Campo JSON"}[table["reader"]]
    for field in table["columns"]:
        name = field["name"]
        specific = describe_treated(name) if profile is None else describe_source(name, table, profile)
        if specific:
            field["type"], field["notes"] = specific
        field["storage"] = storage
        field["isKey"] = name in table.get("keys", [])
