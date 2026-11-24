import { Fragment, lazy, Suspense, useEffect, useState } from 'react';
import type { CSSProperties, Dispatch, SetStateAction } from 'react';
import { errorMessage } from './api';
import type { DailySeries, JsonLoader, ModelMetrics, OnsetMetric, PredictionDay, PredictionSeries, RegressionMetric } from './api';
import { PredictionPlot, PREDICTION_SERIES, shortDate } from './prediction-plot';
import { ModelExplanations } from './explanations';
import { RegressionErrorAnalysis } from './error-analysis';
import { ModelUncertainty } from './uncertainty';
import { dateForTerritory, CHART_VIEWS, TERRITORIES, TERRITORY_STATIONS } from './chart-selection';
import type { ChartSelection, ChartView, Territory } from './chart-selection';
import './charts.css';

const StationMap = lazy(() => import('./station-map').then(module => ({ default: module.StationMap })));

const monthName = new Intl.DateTimeFormat('es-ES', { month: 'long', timeZone: 'UTC' });
const MONTHS = Array.from({ length: 12 }, (_, index) => [
  String(index + 1).padStart(2, '0'),
  monthName.format(Date.UTC(2025, index, 1)),
]);
const MODEL_LABELS = {
  persistencia: 'Persistencia',
  ridge: 'Ridge',
  logistica_sin_meteo: 'Logística sin meteo',
  logistica_con_meteo: 'Logística con meteo',
};
const decimal = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const UNIT = 'µg/m³';

type ChartResult<T> = { url: string; data: T; error?: never } | { url: string; data?: never; error: string };

function useChartData<T>(url: string, loadJson: JsonLoader) {
  const [result, setResult] = useState<ChartResult<T> | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    loadJson<T>(url, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ url, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ url, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [url, loadJson]);
  return result?.url === url ? result : null;
}

function DailyPlot({ data, date, onDate }: { data: DailySeries; date: string; onDate: (date: string) => void }) {
  const { days, threshold, source } = data;
  const selected = date;
  const setSelected = onDate;
  const day = days.find(item => item.date === selected) ?? days[0];
  const valid = days.map(item => item.value).filter(value => value !== null);
  const elevated = valid.filter(value => value > threshold);
  const step = Math.ceil(Math.max(threshold, ...valid) / 30) * 10;
  const limit = step * 3;
  const percent = (value: number) => `${100 * value / limit}%`;
  const reading = (value: number | null) => value === null ? 'Sin dato válido' : `${decimal.format(value)} ${UNIT}`;
  const barsStyle: CSSProperties & { '--days': number } = { '--days': days.length };

  return <>
    <div className="chart-overview">
      <span><strong>{valid.length}/{days.length}</strong> días con dato válido</span>
      <span><strong>{elevated.length}</strong> días por encima de {threshold} {UNIT}</span>
    </div>
    <div className="daily-chart">
      <div className="axis-unit" aria-hidden="true">{UNIT}</div>
      <div className="daily-plot">
        {[0, step, step * 2, limit].map(tick => (
          <div key={tick} className="daily-gridline" style={{ bottom: percent(tick) }} aria-hidden="true">
            <span>{tick}</span>
          </div>
        ))}
        <div className="daily-threshold" style={{ bottom: percent(threshold) }} aria-hidden="true" />
        <div className="daily-bars" style={barsStyle}>
          {days.map(({ date, value }, index) => (
            <button
              key={date}
              type="button"
              tabIndex={-1}
              aria-label={`${date} · ${reading(value)}`}
              title={`${date} · ${reading(value)}`}
              aria-pressed={date === selected}
              onClick={() => setSelected(date)}
              className={value === null ? 'day-gap' : value > threshold ? 'day-elevated' : ''}
            >
              <span className="day-bar" style={{ height: percent(value ?? 0) }} />
              {(index === 0 || (index + 1) % 5 === 0) && (
                <span className="day-tick" aria-hidden="true">{index + 1}</span>
              )}
            </button>
          ))}
        </div>
      </div>
      <div className="axis-day" aria-hidden="true">Día del mes</div>
    </div>
    <div className="daily-legend">
      <span><i className="normal-mark" /> Hasta {threshold} {UNIT}</span>
      <span><i className="elevated-mark" /> Por encima de {threshold} {UNIT}</span>
      <span><i className="gap-mark" /> Sin dato válido</span>
    </div>
    <div className="daily-reading">
      <label>Día <select value={selected} onChange={event => setSelected(event.target.value)}>
        {days.map(item => <option key={item.date} value={item.date}>{item.date.slice(-2)}</option>)}
      </select></label>
      <strong role="status">{reading(day.value)}</strong>
    </div>
    <p className="chart-note">Fuente de las observaciones de este mes · {source}. La línea discontinua marca el umbral estadístico del TFM.</p>
  </>;
}

function DailyChart({ loadJson, territory, station, date, onDate }: {
  loadJson: JsonLoader; territory: Territory; station: string; date: string; onDate: (date: string) => void;
}) {
  const years = Array.from({ length: territory === 'barcelona' ? 8 : 9 }, (_, index) => (territory === 'barcelona' ? 2024 : 2025) - index);
  const year = date.slice(0, 4);
  const month = date.slice(5, 7);
  function changeMonth(nextYear: string, nextMonth: string) {
    const lastDay = new Date(Date.UTC(Number(nextYear), Number(nextMonth), 0)).getUTCDate();
    const day = String(Math.min(Number(date.slice(8)), lastDay)).padStart(2, '0');
    onDate(nextYear + '-' + nextMonth + '-' + day);
  }
  const query = new URLSearchParams({ territory, station, month: `${year}-${month}` });
  const result = useChartData<DailySeries>(`/api/charts/pm10?${query}`, loadJson);

  return <section className="panel chart-card" aria-labelledby="daily-chart-title">
    <div className="chart-card-header">
      <div>
        <h2 id="daily-chart-title">PM10 diario por estación</h2>
        <p>Consulta la concentración observada y localiza picos y días sin datos.</p>
      </div>
      <div className="chart-controls">
        <label>Año <select value={year} onChange={event => changeMonth(event.target.value, month)}>
          {years.map(value => <option key={value}>{value}</option>)}
        </select></label>
        <label>Mes <select value={month} onChange={event => changeMonth(year, event.target.value)}>
          {MONTHS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select></label>
      </div>
    </div>
    {result?.data ? <DailyPlot key={result.url} data={result.data} date={date} onDate={onDate} /> :
      result?.error ? <p role="alert">{result.error}</p> : <p role="status">Cargando observaciones…</p>}
  </section>;
}

function PredictionReadings({ days, threshold, selected, onDate }: {
  days: PredictionDay[];
  threshold: number;
  selected: string;
  onDate: (date: string) => void;
}) {
  const setSelected = onDate;
  const day = days.find(item => item.date === selected);
  return <>
    <div className="daily-legend prediction-legend">
      {PREDICTION_SERIES.map(({ key, label }) => (
        <span key={key}><i className={`prediction-line prediction-${key}`} aria-hidden="true" />{label}</span>
      ))}
      <span><i className="prediction-line prediction-threshold" aria-hidden="true" />Umbral del TFM ({threshold} {UNIT})</span>
    </div>
    <PredictionPlot days={days} threshold={threshold} selected={selected} onSelect={setSelected} />
    <div className="daily-reading">
      <label>Día objetivo <select value={selected} onChange={event => setSelected(event.target.value)}>
        {days.map(item => <option key={item.date} value={item.date}>{shortDate(item.date)}</option>)}
      </select></label>
      {day?.observed === undefined ? <strong role="status">Día fuera de la muestra evaluada</strong> : (
        <dl className="prediction-readings" aria-live="polite" aria-label="Valores de PM10 del día objetivo">
          {PREDICTION_SERIES.map(({ key, label }) => <div key={key}>
            <dt>{label}</dt><dd>{day[key] === undefined ? 'Sin predicción' : `${decimal.format(day[key])} ${UNIT}`}</dd>
          </div>)}
        </dl>
      )}
    </div>
  </>;
}

function predictionWindow(data: PredictionSeries, period: string) {
  const episode = data.episodes.find(item => item.start === period);
  if (!episode) return data.days.filter(day => day.date.slice(5, 7) === period);
  const first = data.days.findIndex(day => day.date === episode.start);
  const last = data.days.findIndex(day => day.date === episode.end);
  return data.days.slice(Math.max(0, first - 3), last + 4);
}

function PredictionPeriods({ data, date, onDate }: {
  data: PredictionSeries; date: string; onDate: (date: string) => void;
}) {
  const { episodes, threshold } = data;
  const [period, setPeriod] = useState(date.slice(5, 7));
  const candidate = predictionWindow(data, period);
  const activePeriod = candidate.some(day => day.date === date) ? period : date.slice(5, 7);
  const visible = activePeriod === period ? candidate : predictionWindow(data, activePeriod);
  function changePeriod(value: string) {
    setPeriod(value);
    const episode = episodes.find(item => item.start === value);
    onDate(episode?.peak ?? ('2024-' + value + '-01'));
  }
  return <>
    <div className="chart-controls prediction-period">
      <label>Periodo <select value={activePeriod} onChange={event => changePeriod(event.target.value)}>
        {episodes.length > 0 && <optgroup label="Episodios por pico observado">
          {episodes.map(({ start, end }) => (
            <option key={start} value={start}>{start === end ? shortDate(start) : `${shortDate(start)} a ${shortDate(end)}`}</option>
          ))}
        </optgroup>}
        <optgroup label="Meses de 2024">
          {MONTHS.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </optgroup>
      </select></label>
      <span>{shortDate(visible[0].date)} a {shortDate(visible[visible.length - 1].date)} de 2024</span>
    </div>
    <PredictionReadings days={visible} threshold={threshold} selected={date} onDate={onDate} />
  </>;
}

function PredictionChart({ loadJson, territory, station, date, onDate }: {
  loadJson: JsonLoader; territory: Territory; station: string; date: string; onDate: (date: string) => void;
}) {
  const result = useChartData<PredictionSeries>(`/api/charts/predictions?${new URLSearchParams({ territory, station })}`, loadJson);

  return <section className="panel chart-card" aria-labelledby="prediction-chart-title">
    <div className="chart-card-header">
      <div>
        <h2 id="prediction-chart-title">PM10 observado y predicho en 2024</h2>
        <p>Compara las predicciones a un día de Ridge y persistencia con la medición de la fecha objetivo.</p>
      </div>
    </div>
    {result?.data ? <PredictionPeriods key={station} data={result.data} date={date} onDate={onDate} /> :
      result?.error ? <p role="alert">{result.error}</p> : <p role="status">Cargando predicciones…</p>}
    <p className="chart-note">La fecha seleccionada se conserva al cambiar de vista. Los episodios incluyen hasta tres días de contexto a cada lado. Las fechas fuera de la prueba aparecen como huecos.</p>
  </section>;
}

function MetricBars<T extends { model: keyof typeof MODEL_LABELS }>({ rows, value, limit }: {
  rows: T[];
  value: (row: T) => number;
  limit: number;
}) {
  return <ul className="metric-bars">
    {rows.map(row => <li key={row.model} className={`model-${row.model}`}>
      <span>{MODEL_LABELS[row.model]}</span>
      <i className="metric-track" aria-hidden="true">
        <span style={{ width: `${100 * value(row) / limit}%` }} />
      </i>
      <strong>{decimal.format(value(row))}</strong>
    </li>)}
  </ul>;
}

const ONSET_MODELS: OnsetMetric['model'][] = ['persistencia', 'logistica_sin_meteo', 'logistica_con_meteo'];

function describeRegressionResult(rows: RegressionMetric[], group: RegressionMetric['group']) {
  const ridge = rows.find(row => row.group === group && row.model === 'ridge');
  const persistence = rows.find(row => row.group === group && row.model === 'persistencia');
  if (!ridge || !persistence) return undefined;

  const scope = group === 'todos' ? 'En el conjunto de la prueba' : 'En los días con PM10 elevado';
  if (decimal.format(ridge.mae) === decimal.format(persistence.mae)) {
    return `${scope}, ambos métodos tuvieron el mismo error medio con la precisión mostrada.`;
  }

  const better = ridge.mae < persistence.mae ? 'Ridge' : 'la persistencia';
  return `${scope}, ${better} se acercó más al PM10 medido.`;
}

function ModelCharts({ loadJson, territory }: { loadJson: JsonLoader; territory: Territory }) {
  const result = useChartData<ModelMetrics>('/api/charts/metrics?territory=' + territory, loadJson);
  if (!result) return <p role="status">Cargando resultados de los modelos…</p>;
  if (!result.data) return <p role="alert">{result.error}</p>;

  const { regression, onsets, threshold } = result.data;
  const overallConclusion = describeRegressionResult(regression, 'todos');
  const elevatedConclusion = describeRegressionResult(regression, 'elevado');
  const regressionLimit = Math.max(...regression.map(row => row.mae));
  const onsetsLimit = Math.max(...onsets.flatMap(row => [row.positives, row.falseAlarms]));
  const withWeather = onsets.find(row => row.model === 'logistica_con_meteo');
  const withoutWeather = onsets.find(row => row.model === 'logistica_sin_meteo');
  const onsetConclusion = withWeather && withoutWeather &&
    withWeather.detected > withoutWeather.detected && withWeather.falseAlarms > withoutWeather.falseAlarms
    ? `Añadir la previsión de viento y precipitación permitió anticipar ${withWeather.detected - withoutWeather.detected} inicios más, a costa de ${withWeather.falseAlarms - withoutWeather.falseAlarms} falsas alarmas adicionales.`
    : undefined;
  const onsetsInOrder = ONSET_MODELS
    .map(model => onsets.find(row => row.model === model))
    .filter(row => row !== undefined);
  return <div className="model-charts">
    <section className="panel chart-card" aria-labelledby="regression-chart-title">
      <div className="chart-card-header">
        <div>
          <h2 id="regression-chart-title">Error de predicción en 2024</h2>
          <p>Error absoluto medio ({UNIT}). Cuanto menor, mejor.</p>
        </div>
      </div>
      {Object.entries({ todos: 'Todas las observaciones', elevado: 'Días con PM10 elevado' }).map(([group, title]) => {
        const rows = regression.filter(row => row.group === group);
        return <div className="metric-group" key={group}>
          <h3>{title} <small>{decimal.format(rows[0].n)} casos</small></h3>
          <MetricBars rows={rows} value={row => row.mae} limit={regressionLimit} />
        </div>;
      })}
      {(overallConclusion || elevatedConclusion) && <div className="regression-conclusion">
        <h3>Conclusión de la prueba</h3>
        <p>{overallConclusion} {elevatedConclusion}</p>
      </div>}
      <p className="chart-note">La persistencia usa como predicción el último valor observado. Los días elevados superan {threshold} {UNIT}.</p>
      {territory === 'barcelona' && <p className="chart-note">
        En Barcelona provincia se evaluó la predicción de la concentración de PM10 en 2024.
        La prueba de avisos de inicio de 2025 se realizó en Madrid.
      </p>}
    </section>
    {onsets.length > 0 && <section className="panel chart-card" aria-labelledby="onset-chart-title">
      <div className="chart-card-header">
        <div>
          <h2 id="onset-chart-title">Avisos de inicio en 2025</h2>
          <p>Evaluación en {decimal.format(onsets[0].n)} casos cuyo día previo estaba en {threshold} {UNIT} o menos.</p>
        </div>
      </div>
      <div className="metric-group">
        <h3>Inicios detectados <small>de {onsets[0].positives} inicios reales</small></h3>
        <MetricBars rows={onsetsInOrder} value={row => row.detected} limit={onsetsLimit} />
      </div>
      <div className="metric-group">
        <h3>Falsas alarmas</h3>
        <MetricBars rows={onsetsInOrder} value={row => row.falseAlarms} limit={onsetsLimit} />
      </div>
      {onsetConclusion && <div className="regression-conclusion">
        <h3>Conclusión de los avisos</h3>
        <p>{onsetConclusion}</p>
      </div>}
      <p className="chart-note">Un inicio es el primer día por encima del umbral tras un día en el umbral o por debajo.</p>
    </section>}
  </div>;
}

export function Charts({ loadJson, selection, onSelection }: {
  loadJson: JsonLoader;
  selection: ChartSelection;
  onSelection: Dispatch<SetStateAction<ChartSelection>>;
}) {
  const { view, station, date, territory } = selection;
  const stations = TERRITORY_STATIONS[territory];
  const lastYear = territory === 'barcelona' ? 2024 : 2025;
  const changeDate = (value: string) => onSelection(previous => ({ ...previous, date: value }));
  const showDate = view === 'map' || view === 'observations' || view === 'predictions' || view === 'explanations';
  const needsStation = showDate && view !== 'map' && station === 'todas';
  const needs2024 = (view === 'predictions' || view === 'explanations') && !date.startsWith('2024-');
  const labels = (Object.entries(CHART_VIEWS) as [ChartView, string][])
    .filter(([id]) => territory === 'madrid' || id !== 'explanations');
  function changeTerritory(next: Territory) {
    onSelection(previous => {
      if (next === previous.territory) return previous;
      return {
        ...previous,
        territory: next,
        view: next === 'barcelona' && previous.view === 'explanations' ? 'predictions' : previous.view,
        station: previous.station === 'todas' ? 'todas' : TERRITORY_STATIONS[next][0][0],
        date: dateForTerritory(previous.date, next),
      };
    });
  }

  return <div className="workspace">
    <nav className="chart-navigation chart-territories" aria-label="Territorio de los gráficos">
      {(Object.keys(TERRITORIES) as Territory[]).map(id =>
        <button key={id} type="button" aria-pressed={territory === id} onClick={() => changeTerritory(id)}>
          {TERRITORIES[id]}
        </button>
      )}
    </nav>
    <nav className="chart-navigation" aria-label="Vistas de gráficos">
      {labels.map(([id, label]) => <button key={id} type="button" aria-pressed={view === id}
        onClick={() => onSelection(previous => ({ ...previous, view: id }))}>{label}</button>)}
    </nav>
    <Fragment key={territory}>
      <section className="panel chart-selection" aria-label="Selección compartida de gráficos">
        {view !== 'results' && <><label>Estación compartida <select value={station} onChange={event => onSelection(previous => ({ ...previous, station: event.target.value }))}>
          <option value="todas">Todas las estaciones</option>
          {stations.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
        </select></label>
        {showDate ? <label>Fecha compartida <input type="date" min="2017-01-01" max={`${lastYear}-12-31`} value={date}
          onInput={event => { if (event.currentTarget.validity.valid && event.currentTarget.value) changeDate(event.currentTarget.value); }} /></label> :
          <p>Análisis de la prueba de 2024 · {CHART_VIEWS[view]}</p>}</>}
        <p>{TERRITORIES[territory]} · Observaciones 2017–{lastYear} · Regresión evaluada en 2024.</p>
      </section>
      {needsStation ? <p className="panel chart-message" role="status">Elige una estación concreta para consultar el caso diario.</p> :
        needs2024 ? <div className="panel chart-message" role="status">
          <p>Las predicciones y explicaciones disponibles corresponden a la prueba de 2024.</p>
          <button onClick={() => changeDate('2024-10-31')}>Ver el caso del 31 de octubre de 2024</button>
        </div> :
        view === 'map' ? <Suspense fallback={<p role="status">Cargando mapa…</p>}><StationMap loadJson={loadJson} territory={territory} station={station} date={date}
          onStation={code => onSelection(previous => ({ ...previous, station: code }))}
          onView={next => onSelection(previous => ({ ...previous, view: next }))} /></Suspense> :
        view === 'observations' ? <DailyChart loadJson={loadJson} territory={territory} station={station} date={date} onDate={changeDate} /> :
        view === 'predictions' ? <PredictionChart loadJson={loadJson} territory={territory} station={station} date={date} onDate={changeDate} /> :
        view === 'results' ? <ModelCharts loadJson={loadJson} territory={territory} /> :
        view === 'errors' ? <RegressionErrorAnalysis loadJson={loadJson} territory={territory} station={station} /> :
        view === 'uncertainty' ? <ModelUncertainty loadJson={loadJson} territory={territory} station={station} /> :
        <ModelExplanations loadJson={loadJson} station={station} date={date} onDate={changeDate} />}
    </Fragment>
  </div>;
}
