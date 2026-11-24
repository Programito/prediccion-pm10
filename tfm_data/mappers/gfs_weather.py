"""Build daily weather predictors from four decoded GFS grid values."""

from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class GridValue:
    latitude: float
    longitude: float
    value: float | None


def map_daily_weather(points: dict[str, GridValue | None]) -> dict:
    cells = {(point.latitude, point.longitude) for point in points.values() if point is not None}
    row = dict(latitud_gfs=None, longitud_gfs=None, viento_10m_mediodia_ms=None, precipitacion_diaria_mm=None,
               estado_viento="sin_mensaje", estado_precipitacion="sin_mensaje")
    if len(cells) > 1:
        return dict(row, estado_viento="celda_incoherente", estado_precipitacion="celda_incoherente")
    if cells:
        (latitude, longitude), = cells
        row.update(latitud_gfs=latitude, longitud_gfs=(longitude + 180) % 360 - 180)

    u, v = points["wind_u"], points["wind_v"]
    if u is not None and v is not None:
        if u.value is None or v.value is None:
            row["estado_viento"] = "ausente_grib"
        else:
            speed = hypot(u.value, v.value)
            if isfinite(speed):
                row.update(viento_10m_mediodia_ms=speed, estado_viento="valido")
            else:
                row["estado_viento"] = "no_finito"

    start, end = points["rain_start"], points["rain_end"]
    if start is not None and end is not None:
        if start.value is None or end.value is None:
            row["estado_precipitacion"] = "ausente_grib"
        else:
            rain = end.value - start.value
            if not all(isfinite(value) for value in (start.value, end.value, rain)):
                row["estado_precipitacion"] = "no_finito"
            elif min(start.value, end.value, rain) < -0.01:
                row["estado_precipitacion"] = "acumulado_incoherente"
            else:
                status = "ajuste_tolerancia" if min(start.value, end.value, rain) < 0 else "valido"
                row.update(precipitacion_diaria_mm=max(0.0, rain), estado_precipitacion=status)
    return row
