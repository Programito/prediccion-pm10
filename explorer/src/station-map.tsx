import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import type { JsonLoader } from './api';
import { errorMessage } from './api';
import { TERRITORIES } from './chart-selection';
import type { ChartView, Territory } from './chart-selection';
import 'leaflet/dist/leaflet.css';
import './station-map.css';

interface MapData {
  date: string;
  threshold: number;
  source: string;
  coordinateSource: string;
  coordinateYear: number;
  coordinateColumns: string[];
  stations: { code: string; name: string; latitude: number; longitude: number; value: number | null }[];
}

const decimal = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const reading = (value: number | null) => value === null ? 'Sin dato válido' : decimal.format(value) + ' µg/m³';
const category = (value: number | null, threshold: number) => value === null ? 'missing' : value > threshold ? 'elevated' : 'normal';

export function StationMap({ loadJson, territory, station, date, onStation, onView }: {
  loadJson: JsonLoader; territory: Territory; station: string; date: string;
  onStation: (code: string) => void; onView: (view: ChartView) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const fitted = useRef(false);
  const select = useRef(onStation);
  select.current = onStation;
  const [result, setResult] = useState<{ date: string; data?: MapData; error?: string } | null>(null);
  const [tilesFailed, setTilesFailed] = useState(false);
  const current = result?.date === date ? result : null;

  useEffect(() => {
    const controller = new AbortController();
    loadJson<MapData>('/api/charts/map?' + new URLSearchParams({ date, territory }), controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ date, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ date, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [date, territory, loadJson]);

  useEffect(() => {
    if (!container.current) return;
    // Territory changes remount the map: avoid a zoom transition completing on a removed pane.
    const instance = L.map(container.current, { scrollWheelZoom: false, zoomAnimation: false, fadeAnimation: false,
      markerZoomAnimation: false }).setView(territory === 'barcelona' ? [41.55, 2.1] : [40.43, -4.03], 10);
    map.current = instance;
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).on('tileerror', () => setTilesFailed(true)).addTo(instance);
    L.control.scale({ imperial: false }).addTo(instance);
    const resize = new ResizeObserver(() => instance.invalidateSize());
    resize.observe(container.current);
    return () => { resize.disconnect(); instance.stop(); instance.remove(); map.current = null; fitted.current = false; };
  }, []);

  useEffect(() => {
    if (!map.current || !current?.data) return;
    if (!fitted.current) {
      map.current.fitBounds(current.data.stations.map(point => [point.latitude, point.longitude] as [number, number]), { padding: [38, 38], maxZoom: 11, animate: false });
      fitted.current = true;
    }
    const layer = L.layerGroup().addTo(map.current);
    for (const point of current.data.stations) {
      const description = point.name + ' · ' + reading(point.value);
      const marker = L.marker([point.latitude, point.longitude], {
        title: description, alt: description, keyboard: true,
        icon: L.divIcon({
          className: 'station-pin ' + category(point.value, current.data.threshold) + (point.code === station ? ' selected' : ''),
          html: '<span aria-hidden="true"></span>', iconSize: [28, 28], iconAnchor: [14, 14],
        }),
      }).addTo(layer);
      const label = document.createElement('span');
      label.textContent = description;
      marker.bindTooltip(label, { direction: 'top' });
      marker.on('click', () => select.current(point.code));
    }
    return () => { layer.remove(); };
  }, [current, station]);

  const data = current?.data;
  const chosen = data?.stations.find(point => point.code === station);
  return <section className="panel chart-card station-map-card" aria-labelledby="station-map-title">
    <h2 id="station-map-title">PM10 en las estaciones del estudio</h2>
    <p>Selecciona un punto del mapa o una estación de la lista para ver sus datos.</p>
    <div className="station-map-toolbar">
      <p>Fecha observada <strong><time dateTime={date}>{date.split('-').reverse().join('/')}</time></strong>
        {data && <> · Fuente <strong>{data.source}</strong></>}
      </p>
      {data && <button type="button" onClick={() => map.current?.fitBounds(
        data.stations.map(point => [point.latitude, point.longitude] as [number, number]),
        { padding: [38, 38], maxZoom: 11, animate: false }
      )}>Centrar las tres estaciones</button>}
    </div>
    <div ref={container} className="station-map" role="region" aria-label={`Mapa interactivo de las tres estaciones de ${TERRITORIES[territory]}`} />
    {tilesFailed && <p role="status">El fondo cartográfico no se ha podido cargar por completo. Puedes consultar los puntos y la lista de estaciones.</p>}
    {!current ? <p role="status">Cargando observaciones del mapa…</p> : current.error ? <p role="alert">{current.error}</p> : null}
    {data && <>
      <div className="station-map-legend" aria-label="Leyenda del mapa">
        <span><i className="normal" /> Hasta {data.threshold} µg/m³</span>
        <span><i className="elevated" /> Más de {data.threshold} µg/m³</span>
        <span><i className="missing" /> Sin dato válido</span>
      </div>
      <p className="chart-note">{data.threshold} µg/m³ es el umbral que usa el estudio para distinguir los días con PM10 elevado.</p>
      <div className="station-map-list" aria-label="Estaciones y concentraciones">
        {data.stations.map(point => <button key={point.code} aria-pressed={station === point.code}
          className={'station-summary ' + category(point.value, data.threshold)} onClick={() => onStation(point.code)}>
          <strong>{point.name}</strong><span>{reading(point.value)}</span>
        </button>)}
      </div>
      {chosen && <div className="station-map-detail" aria-label="Detalle de la estación seleccionada">
        <h3>{chosen.name}</h3>
        <div className="chart-controls">
          <button onClick={() => onView('observations')}>Ver evolución</button>
          {date.startsWith('2024-') && <button onClick={() => onView('predictions')}>Ver predicción de este día</button>}
        </div>
        {!date.startsWith('2024-') && <p className="chart-note">Las predicciones consultables corresponden a la prueba de 2024.</p>}
        <details key={chosen.code}>
          <summary>Detalles de la estación</summary>
          <p>Código {chosen.code}</p>
          <p>Latitud {chosen.latitude}° · Longitud {chosen.longitude}°</p>
        </details>
      </div>}
      <p className="chart-note">Las tres estaciones representan ubicaciones concretas. La concentración entre ellas no se interpola.</p>
      <details><summary>Procedencia de las coordenadas y del fondo</summary>
        <p>Coordenadas de MITECO, referencia de estaciones de {data.coordinateYear}, columnas {data.coordinateColumns.join(' y ')} en grados. Se usan como referencia fija de ubicación para todas las fechas.</p>
        <p><code>{data.coordinateSource}</code></p>
        <p>El fondo de OpenStreetMap necesita conexión a Internet. Las observaciones y coordenadas se leen de los archivos locales. La lista y las fichas siguen disponibles si falla el fondo.</p>
      </details>
    </>}
  </section>;
}
