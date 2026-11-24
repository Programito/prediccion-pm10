import { useEffect, useState } from 'react';
import type { JsonLoader, PredictionDay } from './api';
import { errorMessage } from './api';
import { PredictionPlot, PREDICTION_SERIES } from './prediction-plot';
import { CoverageAudit } from './coverage-audit';
import { WindowAblation } from './window-ablation';
import { GroupedPermutation } from './grouped-permutation';
import { Projections } from './projections';
import { TERRITORIES } from './chart-selection';
import type { Territory as TerritoryId } from './chart-selection';
import './experiments.css';

interface Scores {
  n: number; mae_ridge: number; mae_persistencia: number; rmse_ridge: number;
  rmse_persistencia: number; sesgo_ridge: number; delta_mae: number; improvement_pct: number;
}
interface Experiment {
  id: string; name: string; trainingRows: number; validationRows: number;
  expectedStationDays: number; testCoverage: number; summary: Scores;
  interval: { lower: number; upper: number; includes_zero: boolean; block_days: number };
  observed: { mean: number; p95: number; maximum: number };
  stations: (Omit<Scores, 'improvement_pct'> & { code: string; name: string; area: string; latitude: number; longitude: number; validObservedDays: number; longestMissingDays: number })[];
  monthly: (Omit<Scores, 'improvement_pct'> & { month: number })[];
  levels: (Omit<Scores, 'improvement_pct'> & { level: string })[];
  validationMetrics: { modelo: string; n: number; mae: number; rmse: number }[];
}
interface Comparison {
  testYear: number; threshold: number; training: string; validation: string;
  experiments: Experiment[]; matchedDates: string[]; matched: (Scores & { experiment: string })[];
  limitations: string[]; sources: { path: string; sha256: string }[];
}
interface Series {
  month: string; station: string; threshold: number; source: string;
  observedSource: string; predictionsSource: string;
  days: (PredictionDay & { evaluated: boolean })[];
}
const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 1 });
const signed = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3, signDisplay: 'exceptZero' });
const month = new Intl.DateTimeFormat('es-ES', { month: 'long', timeZone: 'UTC' });

function useData<T>(url: string, loadJson: JsonLoader) {
  const [result, setResult] = useState<{ url: string; data?: T; error?: string }>();
  useEffect(() => {
    const controller = new AbortController();
    loadJson<T>(url, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ url, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ url, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [url, loadJson]);
  return result?.url === url ? result : undefined;
}

function ErrorBars({ experiments, scores }: { experiments: Experiment[]; scores: Scores[] }) {
  const limit = Math.max(...scores.flatMap(row => [row.mae_ridge, row.mae_persistencia]));
  return <section className="panel chart-card" aria-labelledby="comparison-bars-title">
    <h2 id="comparison-bars-title">Error absoluto medio en la misma escala</h2>
    <p className="chart-note">µg/m³ · Menos error es mejor. La comparación relativa con persistencia ayuda a interpretar contextos distintos.</p>
    {experiments.map((experiment, index) => <div key={experiment.id} className="experiment-bars">
      <h3>{experiment.name}</h3>
      {(['ridge', 'persistencia'] as const).map(model => <div key={model}>
        <span>{model === 'ridge' ? 'Ridge' : 'Persistencia'}</span>
        <i aria-hidden="true"><b className={model} style={{ width: 100 * scores[index]['mae_' + model as 'mae_ridge' | 'mae_persistencia'] / limit + '%' }} /></i>
        <strong>{number.format(scores[index]['mae_' + model as 'mae_ridge' | 'mae_persistencia'])}</strong>
      </div>)}
    </div>)}
  </section>;
}

function Compare({ data }: { data: Comparison }) {
  const [basis, setBasis] = useState('all');
  const scores = data.experiments.map(experiment => basis === 'all' ? experiment.summary : data.matched.find(row => row.experiment === experiment.id)!);
  const rows: [string, (score: Scores, experiment: Experiment) => string][] = [
    ['Casos evaluados', score => number.format(score.n)],
    ['MAE Ridge (µg/m³)', score => number.format(score.mae_ridge)],
    ['MAE persistencia (µg/m³)', score => number.format(score.mae_persistencia)],
    ['Mejora de MAE frente a persistencia', score => number.format(score.improvement_pct) + ' %'],
    ['RMSE Ridge (µg/m³)', score => number.format(score.rmse_ridge)],
    ['Sesgo Ridge (µg/m³)', score => signed.format(score.sesgo_ridge)],
    ['Cobertura de casos del calendario 2024', (score, experiment) => percent.format(score.n / experiment.expectedStationDays)],
  ];
  return <>
    <section className="panel chart-card" aria-labelledby="comparison-title">
      <h2 id="comparison-title">Dos réplicas territoriales de regresión</h2>
      <p>Entrenamiento {data.training}, validación {data.validation}, prueba {data.testYear}. Cada territorio ajusta su propio Ridge con las mismas variables y parámetros y lo compara con persistencia. Madrid conserva sus modelos y resultados originales.</p>
      <label className="comparison-basis">Base de comparación <select value={basis} onChange={event => setBasis(event.target.value)}>
        <option value="all">Todas las filas evaluables de cada territorio</option>
        <option value="matched">Solo fechas completas en las seis estaciones</option>
      </select></label>
      {basis === 'matched' ? <p role="status">{data.matchedDates.length} fechas comunes, con tres estaciones por territorio. Esta sensibilidad reduce la muestra y puede cambiar la composición de meses y episodios. Los intervalos de la muestra completa no se aplican a este subconjunto.</p> :
        <p>Las muestras contienen distintas fechas y coberturas. Consulta también la sensibilidad de fechas comunes.</p>}
      <div className="table-scroll"><table className="values experiment-table"><caption>Prueba de regresión de {data.testYear} · {basis === 'all' ? 'muestras completas' : 'fechas compartidas'}</caption>
        <thead><tr><th scope="col">Indicador</th>{data.experiments.map(experiment => <th scope="col" key={experiment.id}>{experiment.name}</th>)}</tr></thead>
        <tbody>{rows.map(([label, format]) => <tr key={label}><th scope="row">{label}</th>{data.experiments.map((experiment, index) => <td key={experiment.id}>{format(scores[index], experiment)}</td>)}</tr>)}</tbody>
      </table></div>
    </section>
    <ErrorBars experiments={data.experiments} scores={scores} />
    {basis === 'all' && <div className="experiment-grid">{data.experiments.map(experiment => <section className="panel chart-card" key={experiment.id}>
      <h2>{experiment.name} · Incertidumbre</h2>
      <strong className="experiment-interval">[{signed.format(experiment.interval.lower)}; {signed.format(experiment.interval.upper)}] µg/m³</strong>
      <p>Intervalo bootstrap nominal del 95 % de MAE Ridge menos persistencia. Bloques de 14 días y 5.000 réplicas sincronizadas por fecha dentro de cada territorio.</p>
      <p>{experiment.interval.includes_zero ? 'Incluye cero; la dirección de la diferencia queda incierta.' : 'No incluye cero; en este diagnóstico de la muestra el intervalo favorece a Ridge.'} Es una estimación exploratoria condicionada a los modelos y a las muestras evaluadas.</p>
      <p className="chart-note">PM10 observado en la muestra: media {number.format(experiment.observed.mean)}, percentil 95 {number.format(experiment.observed.p95)} y máximo {number.format(experiment.observed.maximum)} µg/m³.</p>
    </section>)}</div>}
    <section className="panel chart-card" aria-labelledby="comparison-limits"><h2 id="comparison-limits">Cómo interpretar la comparación</h2>
      <ul className="experiment-limits">{data.limitations.map(text => <li key={text}>{text}.</li>)}</ul>
      <p>La diferencia entre territorios no identifica una causa ni demuestra que un modelo entrenado en Madrid funcione en Barcelona. Para eso haría falta otro diseño de evaluación.</p>
      <details><summary>Archivos de resultados utilizados</summary>{data.sources.map(source => <p className="experiment-path" key={source.path}><code>{source.path}</code></p>)}</details>
    </section>
  </>;
}

function DailyExperiment({ experiment, loadJson }: { experiment: Experiment; loadJson: JsonLoader }) {
  const [station, setStation] = useState(experiment.stations[0].code);
  const [selected, setSelected] = useState('2024-10-01');
  const result = useData<Series>('/api/experiments/' + experiment.id + '/series?' + new URLSearchParams({ station, month: selected.slice(0, 7) }), loadJson);
  const data = result?.data;
  const day = data?.days.find(row => row.date === selected);
  const value = (input: number | undefined) => input === undefined ? 'Sin dato' : number.format(input) + ' µg/m³';
  return <section className="panel chart-card" aria-labelledby="experiment-daily-title">
    <h2 id="experiment-daily-title">Observaciones y predicciones · {experiment.name}</h2>
    <div className="chart-controls">
      <label>Estación del experimento <select value={station} onChange={event => setStation(event.target.value)}>{experiment.stations.map(point => <option key={point.code} value={point.code}>{point.name}</option>)}</select></label>
      <label>Fecha del experimento <input type="date" min="2017-01-01" max="2024-12-31" value={selected}
        onInput={event => { if (event.currentTarget.validity.valid && event.currentTarget.value) setSelected(event.currentTarget.value); }} /></label>
    </div>
    {result?.error ? <p role="alert">{result.error}</p> : data ? <>
      <PredictionPlot days={data.days} threshold={data.threshold} selected={selected} onSelect={setSelected} />
      <div className="daily-legend prediction-legend">{PREDICTION_SERIES.map(({ key, label }) => <span key={key}><i className={'prediction-line prediction-' + key} aria-hidden="true" />{label}</span>)}<span><i className="prediction-line prediction-threshold" aria-hidden="true" />Umbral común del TFM: {data.threshold} µg/m³</span></div>
      <label>Día consultado <select value={selected} onChange={event => setSelected(event.target.value)}>{data.days.map(row => <option key={row.date} value={row.date}>{row.date}</option>)}</select></label>
      {day && <dl className="prediction-readings"><div><dt>Observado</dt><dd>{value(day.observed)}</dd></div><div><dt>Ridge</dt><dd>{value(day.ridge)}</dd></div><div><dt>Persistencia</dt><dd>{value(day.persistencia)}</dd></div></dl>}
      {day && !day.evaluated && <p role="status">{selected.startsWith('2024-') ? 'Día fuera de la muestra de prueba evaluada: puede haber una observación y faltar entradas históricas completas para predecir.' : 'Las predicciones de prueba consultables corresponden a 2024. En este periodo se muestran las observaciones.'}</p>}
      <details><summary>Valores diarios y procedencia</summary>
        <div className="table-scroll"><table className="values"><caption>Valores del mes · µg/m³</caption><thead><tr><th>Fecha</th><th>Observado</th><th>Ridge</th><th>Persistencia</th></tr></thead>
          <tbody>{data.days.map(row => <tr key={row.date}><th scope="row">{row.date}</th><td>{value(row.observed)}</td><td>{value(row.ridge)}</td><td>{value(row.persistencia)}</td></tr>)}</tbody></table></div>
        <p className="experiment-path">Fuente: {data.source}, CSV diario derivado de los originales ZIP diarios y horarios. <code>{data.observedSource}</code></p>
        <p className="experiment-path">Predicciones: CSV local del modelo congelado. <code>{data.predictionsSource}</code></p>
      </details>
    </> : <p role="status">Cargando serie del experimento…</p>}
  </section>;
}

function Territory({ experiment, loadJson, threshold }: { experiment: Experiment; loadJson: JsonLoader; threshold: number }) {
  return <>
    <section className="panel chart-card"><h2>{experiment.name} · Prueba de 2024</h2>
      <p>Tres estaciones de fondo. Entrenamiento: {number.format(experiment.trainingRows)} filas de 2017–2022. Validación: {number.format(experiment.validationRows)} filas de 2023. Prueba: {number.format(experiment.summary.n)} de {number.format(experiment.expectedStationDays)} días-estación, {percent.format(experiment.testCoverage)} del calendario.</p>
      <p>MAE Ridge: <strong>{number.format(experiment.summary.mae_ridge)} µg/m³</strong> · Persistencia: <strong>{number.format(experiment.summary.mae_persistencia)} µg/m³</strong> · Mejora relativa: <strong>{number.format(experiment.summary.improvement_pct)} %</strong>.</p>
      <div className="table-scroll"><table className="values experiment-table"><caption>Estaciones y cobertura de 2024</caption>
        <thead><tr><th>Estación</th><th>Área</th><th>Días con medición válida / 366</th><th>Mayor hueco observado (días)</th><th>Casos evaluados / 366</th><th>MAE Ridge</th><th>MAE persistencia</th></tr></thead>
        <tbody>{experiment.stations.map(point => <tr key={point.code}><th scope="row">{point.name}<span className="column-type">{point.code}</span></th><td>{point.area}</td><td>{point.validObservedDays}</td><td>{point.longestMissingDays}</td><td>{point.n}</td><td>{number.format(point.mae_ridge)}</td><td>{number.format(point.mae_persistencia)}</td></tr>)}</tbody>
      </table></div>
      <p className="chart-note">Tener una medición del día objetivo no garantiza una fila evaluable: las ventanas necesitan hasta 14 días completos. Los ausentes permanecen ausentes y los picos válidos se conservan.</p>
    </section>
    <DailyExperiment key={experiment.id} experiment={experiment} loadJson={loadJson} />
    <section className="panel chart-card"><h2>Error por mes y días elevados</h2>
      <div className="table-scroll"><table className="values"><caption>2024 · MAE en µg/m³</caption><thead><tr><th>Periodo</th><th>Casos</th><th>Ridge</th><th>Persistencia</th><th>Diferencia</th></tr></thead><tbody>
        {experiment.monthly.map(row => <tr key={row.month}><th scope="row">{month.format(Date.UTC(2024, row.month - 1, 1))}</th><td>{row.n}</td><td>{number.format(row.mae_ridge)}</td><td>{number.format(row.mae_persistencia)}</td><td>{signed.format(row.delta_mae)}</td></tr>)}
        {experiment.levels.filter(row => row.level === 'elevado').map(row => <tr key={row.level}><th scope="row">Días con PM10 mayor de {threshold} µg/m³</th><td>{row.n}</td><td>{number.format(row.mae_ridge)}</td><td>{number.format(row.mae_persistencia)}</td><td>{signed.format(row.delta_mae)}</td></tr>)}
      </tbody></table></div>
      <details><summary>Comparación de modelos en validación de 2023</summary>
        <p>Ridge se mantiene como modelo de la comparación territorial con la especificación de Madrid. En Barcelona se fijó antes del ajuste y de evaluar 2024; Random Forest se conserva como candidato de validación.</p>
        <table className="values"><thead><tr><th>Modelo</th><th>Casos</th><th>MAE</th><th>RMSE</th></tr></thead><tbody>{experiment.validationMetrics.map(row => <tr key={row.modelo}><th scope="row">{row.modelo}</th><td>{row.n}</td><td>{number.format(row.mae)}</td><td>{number.format(row.rmse)}</td></tr>)}</tbody></table>
      </details>
    </section>
  </>;
}

const EXPERIMENT_VIEWS = {
  results: 'Resultados',
  audit: 'Auditoría de cobertura',
  windows: 'Comparación de ventanas',
  permutation: 'Importancia agrupada',
  projections: 'PCA y LDA',
};

type ExperimentView = keyof typeof EXPERIMENT_VIEWS;
type ExperimentScope = TerritoryId | 'comparison';

export function Experiments({ loadJson }: { loadJson: JsonLoader }) {
  const result = useData<Comparison>('/api/experiments', loadJson);
  const [scope, setScope] = useState<ExperimentScope>('madrid');
  const [view, setView] = useState<ExperimentView>('results');
  if (!result) return <p role="status">Cargando experimentos territoriales…</p>;
  if (!result.data) return <p role="alert">{result.error}</p>;
  const data = result.data;
  const experiment = data.experiments.find(item => item.id === scope);
  const views = (Object.entries(EXPERIMENT_VIEWS) as [ExperimentView, string][])
    .filter(([id]) => scope === 'madrid' || id !== 'projections');

  function selectScope(next: ExperimentScope) {
    setScope(next);
    if (next === 'barcelona' && view === 'projections') setView('results');
  }

  return <div className="workspace experiments-workspace">
    <nav className="chart-navigation chart-territories" aria-label="Ámbito de los experimentos">
      {(Object.entries(TERRITORIES) as [TerritoryId, string][]).map(([id, label]) =>
        <button key={id} type="button" aria-pressed={scope === id} onClick={() => selectScope(id)}>{label}</button>
      )}
      <button type="button" aria-pressed={scope === 'comparison'} onClick={() => selectScope('comparison')}>Comparación</button>
    </nav>
    {scope === 'comparison' ? <Compare data={data} /> : <>
      <nav className="chart-navigation" aria-label="Vistas del experimento">
        {views.map(([id, label]) =>
          <button key={id} type="button" aria-pressed={view === id} onClick={() => setView(id)}>{label}</button>
        )}
      </nav>
      {!experiment ? <p role="status">No hay datos del experimento de {TERRITORIES[scope]}.</p> :
        view === 'projections' ? <Projections loadJson={loadJson} /> :
        view === 'permutation' ? <GroupedPermutation territory={scope} loadJson={loadJson} /> :
        view === 'windows' ? <WindowAblation territory={scope} loadJson={loadJson} /> :
        view === 'audit' ? <CoverageAudit key={scope} experiment={experiment} loadJson={loadJson} /> :
        <Territory key={scope} experiment={experiment} loadJson={loadJson} threshold={data.threshold} />}
    </>}
  </div>;
}
