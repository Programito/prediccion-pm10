"""Extract a sample of operational GFS forecasts for the three PM10 stations."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta
import hashlib
import json
from pathlib import Path
from threading import Lock
from time import perf_counter, sleep
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import eccodes
import pandas as pd

from pm10_data.mappers.gfs_weather import GridValue, map_daily_weather

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "https://noaa-gfs-bdp-pds.s3.amazonaws.com"
STATIONS = {28079060, 28080003, 28133002}
TARGET_DATES = [date(2021, 11, 14), date(2022, 3, 15), date(2023, 8, 9), date(2025, 12, 31)]
MONTHLY_DATES = [date(year, month, 15) for year in range(2021, 2026) for month in range(1, 13)]
DAILY_DATES = [day.date() for day in pd.date_range("2021-01-01", "2025-12-31")]
FIELDS = {12: {"rain_start": ("APCP", "surface", "0-12 hour acc fcst")},
          24: {"wind_u": ("UGRD", "10 m above ground", "24 hour fcst"),
               "wind_v": ("VGRD", "10 m above ground", "24 hour fcst")},
          36: {"rain_end": ("APCP", "surface", "0-36 hour acc fcst")}}
GRIB_LOCK = Lock()


def download(url, byte_range=None):
    headers = {} if byte_range is None else {"Range": f"bytes={byte_range[0]}-{byte_range[1]}"}
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers), timeout=20) as response:
                if byte_range is not None:
                    first, last = byte_range
                    if response.status != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {first}-{last}/"):
                        raise ValueError("Respuesta inesperada para el rango GRIB2.")
                return response.read()
        except (URLError, OSError) as error:
            retryable = not isinstance(error, HTTPError) or error.code in {429, 500, 502, 503, 504}
            if not retryable or attempt == 2:
                raise
            sleep(2 ** attempt)


def decode(payload, run, valid, stations):
    message = eccodes.codes_new_from_message(payload)
    try:
        for prefix, instant in [("data", run), ("validity", valid)]:
            if (eccodes.codes_get(message, f"{prefix}Date") != int(instant.strftime("%Y%m%d"))
                    or eccodes.codes_get(message, f"{prefix}Time") != instant.hour * 100):
                raise ValueError("Fecha del mensaje incompatible con el ciclo o plazo.")
        bitmap = eccodes.codes_get_array(message, "bitmap") if eccodes.codes_get(message, "bitmapPresent") else None
        missing = eccodes.codes_get(message, "missingValue") if bitmap is None and eccodes.codes_get(message, "numberOfMissing") else None
        points = {}
        for station in stations.itertuples(index=False):
            nearest, = eccodes.codes_grib_find_nearest(message, station.LATITUD_G, station.LONGITUD_G % 360)
            absent = bitmap[nearest.index] == 0 if bitmap is not None else nearest.value == missing
            points[station.COD_LOCAL] = GridValue(nearest.lat, nearest.lon, None if absent else nearest.value)
        return points
    finally:
        eccodes.codes_release(message)


def download_index(day, lead):
    directory = f"{BUCKET}/gfs.{day}/12"
    filename = f"gfs.t12z.pgrb2.0p25.f{lead:03d}"
    url = f"{directory}/atmos/{filename}"
    try:
        return url, download(url + ".idx")
    except HTTPError as error:
        if error.code != 404:
            raise
    legacy = f"{directory}/{filename}"
    return legacy, download(legacy + ".idx")


def fetch_fields(run, stations):
    day = run.strftime("%Y%m%d")
    values, provenance, incidents = {}, [], []
    index_bytes = 0
    expected_errors = (URLError, OSError, ValueError, eccodes.CodesInternalError)
    for lead, fields in FIELDS.items():
        valid = run + timedelta(hours=lead)
        try:
            url, raw_index = download_index(day, lead)
            index_bytes += len(raw_index)
            entries = [line.split(":") for line in raw_index.decode("ascii").splitlines()]
        except expected_errors as error:
            incidents.append(dict(plazo_h=lead, campo="indice", url=getattr(error, "url", None), error=str(error),
                                  permanente=isinstance(error, HTTPError) and error.code == 404))
            continue
        for field, signature in fields.items():
            try:
                matches = [i for i, row in enumerate(entries) if tuple(row[3:6]) == signature]
                if len(matches) != 1 or matches[0] + 1 >= len(entries):
                    raise ValueError(f"Campo sin rango único en el índice: {signature}")
                index = matches[0]
                first, last = int(entries[index][1]), int(entries[index + 1][1]) - 1
                if not 0 <= first <= last:
                    raise ValueError("Rango GRIB2 inválido.")
                payload = download(url, (first, last))
                provenance.append(dict(campo=field, url=url, indice=url + ".idx", rango=[first, last],
                                       bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest(),
                                       inicio_ciclo_utc=run.isoformat() + "Z", validez_utc=valid.isoformat() + "Z"))
                if len(payload) != last - first + 1 or not payload.startswith(b"GRIB") or not payload.endswith(b"7777"):
                    raise ValueError("Mensaje GRIB2 incompleto.")
                # ecCodes on Windows uses a shared definitions parser.
                with GRIB_LOCK:
                    values[field] = decode(payload, run, valid, stations)
            except expected_errors as error:
                incidents.append(dict(plazo_h=lead, campo=field, url=url, error=str(error)))
    return values, provenance, incidents, index_bytes


def sample_day(day, stations):
    run = datetime.combine(day - timedelta(days=1), datetime.min.time()).replace(hour=12)
    values, sources, incidents, index_bytes = fetch_fields(run, stations)
    rows = []
    for code in stations.COD_LOCAL:
        points = {field: values.get(field, {}).get(code) for fields in FIELDS.values() for field in fields}
        rows.append(dict(codigo_estacion=code, fecha_objetivo=day.isoformat(), inicio_ciclo_utc=run.isoformat() + "Z",
                         **map_daily_weather(points)))
    events = [dict(fecha_objetivo=day.isoformat(), **event) for event in incidents]
    complete = sum(row["viento_10m_mediodia_ms"] is not None and row["precipitacion_diaria_mm"] is not None for row in rows)
    summary = dict(fecha_objetivo=day.isoformat(), estaciones_completas=complete, mensajes=len(sources),
                   bytes_grib=sum(source["bytes"] for source in sources), bytes_indices=index_bytes, incidencias=len(events))
    return rows, sources, events, summary


def write_checkpoint(path, result):
    pending = path.with_suffix(".tmp")
    pending.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    pending.replace(path)


def seed_monthly_checkpoints(cache):
    monthly = ROOT / "output/pm10_weather_feasibility/monthly"
    sample = monthly / "muestra_gfs.csv"
    sample_coverage = monthly / "cobertura_por_fecha.csv"
    sample_manifest = monthly / "mensajes_gfs.json"
    if not all(path.is_file() for path in (sample, sample_coverage, sample_manifest)):
        return
    rows = pd.read_csv(sample).to_dict("records")
    coverage = pd.read_csv(sample_coverage).to_dict("records")
    messages = json.loads(sample_manifest.read_text(encoding="utf-8"))
    for row in coverage:
        target = row["fecha_objetivo"]
        path = cache / f"{target}.json"
        if path.exists() or row["estaciones_completas"] != len(STATIONS) or row["incidencias"]:
            continue
        target_rows = [record for record in rows if record["fecha_objetivo"] == target]
        cycle = target_rows[0]["inicio_ciclo_utc"]
        sources = [record for record in messages if record["inicio_ciclo_utc"] == cycle]
        if {record["codigo_estacion"] for record in target_rows} != STATIONS or len(sources) != row["mensajes"]:
            raise ValueError(f"La fecha mensual no coincide con su manifiesto: {target}")
        write_checkpoint(path, (target_rows, sources, [], row))


def fetch_days(dates, stations, workers, cache=None):
    results = {}
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
        if not any(cache.glob("*.json")):
            seed_monthly_checkpoints(cache)
        for day in dates:
            path = cache / f"{day}.json"
            if path.exists():
                result = json.loads(path.read_text(encoding="utf-8"))
                if not result[2] or all(event.get("permanente", False) for event in result[2]):
                    results[day] = result
        print(f"{len(results)}/{len(dates)} fechas recuperadas de los resultados previos.", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        tasks = {executor.submit(sample_day, day, stations): day for day in dates if day not in results}
        for future in as_completed(tasks):
            day = tasks[future]
            result = future.result()
            if cache is not None:
                write_checkpoint(cache / f"{day}.json", result)
            results[day] = result
            if len(results) % (50 if cache is not None else 12) == 0:
                print(f"{len(results)}/{len(dates)} fechas comprobadas.", flush=True)
    return [results[day] for day in dates]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--monthly", action="store_true", help="Muestra el día 15 de cada mes de 2021 a 2025.")
    mode.add_argument("--daily", action="store_true", help="Extrae el histórico completo de 2021 a 2025.")
    parser.add_argument("--workers", type=int, default=4, help="Número de fechas que se procesan en paralelo.")
    args = parser.parse_args()
    if not 1 <= args.workers <= 24:
        parser.error("--workers debe estar entre 1 y 24.")
    started = perf_counter()
    source = ROOT / "data/raw/health_air_history/miteco_estaciones_2024.xlsx"
    stations = pd.read_excel(source, sheet_name="Estaciones_2024")
    stations = stations.loc[stations.COD_LOCAL.isin(STATIONS)]
    if set(stations.COD_LOCAL) != STATIONS or len(stations) != len(STATIONS):
        raise ValueError("Las coordenadas deben corresponder a las tres estaciones.")
    dates = DAILY_DATES if args.daily else MONTHLY_DATES if args.monthly else TARGET_DATES
    cache = ROOT / "tmp/gfs_daily_2021_2025" if args.daily else None
    rows, sources, incidents, days = [], [], [], []
    for day_rows, messages, events, summary in fetch_days(dates, stations, args.workers, cache):
        rows.extend(day_rows)
        sources.extend(messages)
        incidents.extend(events)
        days.append(summary)
    output = ROOT / "output/pm10_weather_feasibility"
    if args.monthly:
        output = output / "monthly"
    if args.daily:
        output = ROOT / "data/interim/weather_forecasts/gfs_2021_2025"
    output.mkdir(parents=True, exist_ok=True)
    filename = "previsiones_gfs_diarias.csv" if args.daily else "muestra_gfs.csv"
    pd.DataFrame(rows).to_csv(output / filename, index=False, encoding="utf-8-sig")
    (output / "mensajes_gfs.json").write_text(json.dumps(sources, indent=2) + "\n", encoding="utf-8")
    (output / "incidencias.json").write_text(json.dumps(incidents, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(days).to_csv(output / "cobertura_por_fecha.csv", index=False, encoding="utf-8-sig")
    total = dict(fechas_solicitadas=len(dates), fechas_completas=sum(day["estaciones_completas"] == len(STATIONS) for day in days),
                 filas=len(rows), filas_completas=sum(day["estaciones_completas"] for day in days),
                 mensajes=len(sources), bytes_grib=sum(day["bytes_grib"] for day in days),
                 bytes_indices=sum(day["bytes_indices"] for day in days), segundos=round(perf_counter() - started, 2))
    (output / "resumen.json").write_text(json.dumps(total, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(total, ensure_ascii=False))


if __name__ == "__main__":
    main()
