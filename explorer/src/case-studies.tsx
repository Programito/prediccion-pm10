import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader, PredictionDay } from './api';
import type { ChartSelection } from './chart-selection';
import { PredictionPlot } from './prediction-plot';
import './charts.css';
import './case-studies.css';

interface StudyCase {
  id: string; title: string; station: string; name: string; date: string;
  kind: 'regression' | 'classification'; emission: string; lastObservation: string;
  observed: number; prior: number; days: PredictionDay[];
  predictions?: { model: string; value: number; absoluteError: number }[];
  intercept?: number; rawPrediction?: number;
  inputs?: Record<string, number>;
  contributions?: { feature: string; coefficient: number; transformed: number; contribution: number }[];
  alerts?: { model: string; alert: boolean; probability: number | null; cut: number | null }[];
  weather?: { inicio_ciclo_utc: string; viento_10m_mediodia_ms: number; precipitacion_diaria_mm: number;
    latitud_gfs: number; longitud_gfs: number };
  evidence: { file: string; rows: number; format: string; sha256: string; url: string }[];
}
interface CaseReport {
  threshold: number; scope: string; selection: { candidates: number; median: number; rule: string };
  cases: StudyCase[]; sources: { path: string; format: string; sha256: string }[];
  onsets: { model: string; n: number; onsets: number; detected: number; falseAlarms: number }[];
}

const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 2 });
const signed = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3, signDisplay: 'always' });
const fmt = (value: number | undefined) => value === undefined ? 'Sin dato' : number.format(value);
const modelName = (name: string) => ({ ridge: 'Ridge', persistencia: 'Persistencia',
  logistica_sin_meteo: 'Logística sin meteorología', logistica_con_meteo: 'Logística con meteorología' })[name] ?? name;
const scripts: Record<string, { question: string; lesson: string; limitation: string; rehearsal: string }> = {
  typical: {
    question: '¿Cómo explicamos una predicción en un día con concentración habitual?',
    lesson: 'Ridge aproxima el valor observado y mejora aquí la referencia de repetir el día anterior. Las aportaciones permiten reconstruir su cálculo.',
    limitation: 'Habitual significa cercano a la mediana de concentración de los días no elevados. No significa representativo de todas las variables ni del error del modelo.',
    rehearsal: 'Explica qué información conocíamos antes de este día y calcula el error de ambos modelos. ¿Permite este ejemplo afirmar que Ridge siempre mejora?',
  },
  peak: {
    question: '¿Qué ocurre cuando la concentración sube mucho?',
    lesson: 'Ridge subestima el pico y tiene más error que persistencia. El historial reciente ayuda, pero este modelo no anticipa la magnitud del episodio.',
    limitation: 'Un ejemplo extremo ilustra un fallo conocido. No identifica la causa del pico ni demuestra por sí solo cómo se comporta el modelo en todos los episodios.',
    rehearsal: 'Compara los dos errores y explica por qué una pequeña mejora del MAE global puede coexistir con un fallo importante en un pico.',
  },
  onset: {
    question: '¿Podemos avisar de un día elevado cuando el anterior no lo era?',
    lesson: 'La logística con meteorología supera su corte de aviso; la logística sin meteorología y persistencia no avisan. El objetivo sí supera 27 µg/m³.',
    limitation: 'Cambian las variables, la función ajustada y el corte de cada logística. Este contraste no permite atribuir el acierto al viento ni demuestra causalidad.',
    rehearsal: 'Explica la diferencia entre probabilidad, corte y concentración. Después abre la falsa alarma y relaciona anticipación con avisos erróneos.',
  },
  false_alarm: {
    question: '¿Qué coste tiene avisar antes de observar el episodio?',
    lesson: 'La logística con meteorología avisa, pero el día siguiente queda por debajo del umbral. Este aviso es un falso positivo.',
    limitation: 'Una probabilidad superior al corte no garantiza un episodio. El corte se eligió en 2023; no se modifica para corregir este caso de 2025.',
    rehearsal: '¿Qué pasaría con sensibilidad y falsas alarmas si elevásemos el corte? Ese cambio exigiría una nueva selección y evaluación independiente.',
  },
};

function CaseDetail({ item, threshold, onsets, onCharts }: { item: StudyCase; threshold: number; onsets: CaseReport['onsets'];
  onCharts: (selection: Partial<ChartSelection>) => void }) {
  const [contextDate, setContextDate] = useState(item.date);
  const day = item.days.find(d => d.date === contextDate);
  const script = scripts[item.id];
  return <>
    <section className="panel case-summary" aria-labelledby="case-title">
      <p className="eyebrow">{item.kind === 'regression' ? 'Regresión · prueba de 2024' : 'Clasificación · prueba de 2025'} · Madrid</p>
      <h2 id="case-title">{item.title}</h2><p><strong>{item.name} · {item.date}</strong></p>
      <p>{script.question}</p>
      <dl className="case-readings"><div><dt>PM10 observado</dt><dd>{fmt(item.observed)} µg/m³</dd></div>
        <div><dt>PM10 del día anterior</dt><dd>{fmt(item.prior)} µg/m³</dd></div>
        <div><dt>Objetivo elevado (&gt; {threshold})</dt><dd>{item.observed > threshold ? 'Sí' : 'No'}</dd></div></dl>
      <p className="muted">Emisión simulada: {item.emission}. Último día observado: {item.lastObservation}.
        Se supone disponible su agregado a las 00:00 UTC; no se ha verificado la latencia real de publicación.</p>
    </section>
    <div className="case-columns">
      <section className="panel case-summary"><h2>Qué hizo el modelo</h2><p>{script.lesson}</p>
        {item.predictions && <div className="table-scroll"><table><caption>Predicción y error absoluto · µg/m³</caption>
          <thead><tr><th>Modelo</th><th>Predicción</th><th>Error absoluto</th></tr></thead>
          <tbody>{item.predictions.map(row => <tr key={row.model}><th scope="row">{modelName(row.model)}</th>
            <td>{fmt(row.value)}</td><td>{fmt(row.absoluteError)}</td></tr>)}</tbody></table></div>}
        {item.alerts && <><div className="table-scroll"><table><caption>Decisiones guardadas y cortes seleccionados en 2023</caption>
          <thead><tr><th>Modelo</th><th>Probabilidad</th><th>Corte</th><th>Aviso</th></tr></thead>
          <tbody>{item.alerts.map(row => <tr key={row.model}><th scope="row">{modelName(row.model)}</th>
            <td>{row.probability === null ? 'No aplica' : percent.format(row.probability)}</td>
            <td>{row.cut === null ? 'PM10 anterior > 27' : percent.format(row.cut)}</td><td>{row.alert ? 'Sí' : 'No'}</td></tr>)}</tbody></table></div>
          <p className="muted">Probabilidad de superar {threshold} µg/m³, no de enfermedad. Se avisa si probabilidad ≥ corte. Persistencia es una regla, sin probabilidad estimada.</p>
          <p>Comparación completa de 2025 cuando el día previo no era elevado (no solo estos ejemplos):</p>
          <ul>{onsets.map(row => <li key={row.model}>{modelName(row.model)}: {row.detected} de {row.onsets} comienzos detectados y {row.falseAlarms} falsas alarmas, en {row.n} casos.</li>)}</ul></>}
      </section>
      <section className="panel case-summary"><h2>Cómo defenderlo</h2><p>{script.rehearsal}</p>
        <h3>El límite que debemos explicar</h3><p>{script.limitation}</p>
        <p>Son ejemplos retrospectivos de pruebas ya conocidas. No constituyen una nueva evaluación independiente ni una estimación de utilidad clínica.</p>
        <button onClick={() => onCharts({ station: item.station, date: item.date,
          view: item.kind === 'regression' ? 'explanations' : 'observations' })}>
          {item.kind === 'regression' ? 'Abrir explicación completa de Ridge' : 'Abrir observaciones de este día'}</button>
      </section>
    </div>
    <section className="panel chart-card case-summary"><h2>El caso en su contexto</h2>
      <p>Ventana retrospectiva de siete días. Los días posteriores al objetivo se muestran para interpretar el episodio; no fueron entradas de la predicción.</p>
      <div className="daily-legend prediction-legend"><span><i className="prediction-line prediction-observed" />Observado</span>
        {item.kind === 'regression' && <><span><i className="prediction-line prediction-ridge" />Ridge</span><span><i className="prediction-line prediction-persistencia" />Persistencia</span></>}
        <span><i className="prediction-line prediction-threshold" />Umbral estadístico: {threshold} µg/m³</span></div>
      <PredictionPlot days={item.days} threshold={threshold} selected={contextDate} onSelect={setContextDate} />
      <label className="case-context-label">Día del contexto <select value={contextDate} onChange={event => setContextDate(event.target.value)}>
        {item.days.map(d => <option key={d.date}>{d.date}</option>)}</select></label>
      <p>Observado del día consultado: <strong>{fmt(day?.observed)} µg/m³</strong>. El caso de estudio sigue siendo {item.date}.</p>
      <details><summary>Tabla accesible del contexto</summary><div className="table-scroll"><table>
        <thead><tr><th>Fecha</th><th>Observado (µg/m³)</th>{item.kind === 'regression' && <><th>Ridge</th><th>Persistencia</th></>}</tr></thead>
        <tbody>{item.days.map(d => <tr key={d.date}><th scope="row">{d.date}</th><td>{fmt(d.observed)}</td>
          {item.kind === 'regression' && <><td>{fmt(d.ridge)}</td><td>{fmt(d.persistencia)}</td></>}</tr>)}</tbody>
      </table></div></details><p className="muted">Las ausencias se conservan como huecos; no se interpolan ni se sustituyen por cero.</p>
    </section>
    {item.contributions && <section className="panel case-summary"><h2>Reconstruir la predicción de Ridge</h2>
      <p>Intercepto {fmt(item.intercept)} + suma de aportaciones = {fmt(item.rawPrediction)} µg/m³. La salida final aplica máximo entre cero y esa suma.</p>
      <p>Una aportación es el coeficiente multiplicado por la entrada transformada. Describe el cálculo del modelo; no mide efectos causales.</p>
      <details><summary>Ver las {item.contributions.length} aportaciones y las entradas</summary>
        <div className="table-scroll"><table><thead><tr><th>Variable transformada</th><th>Coeficiente</th><th>Entrada transformada</th><th>Aportación (µg/m³)</th></tr></thead>
          <tbody>{item.contributions.map(row => <tr key={row.feature}><th scope="row">{row.feature}</th><td>{fmt(row.coefficient)}</td>
            <td>{fmt(row.transformed)}</td><td>{signed.format(row.contribution)}</td></tr>)}</tbody></table></div>
        <dl className="case-inputs">{Object.entries(item.inputs ?? {}).map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{fmt(value)}</dd></div>)}</dl>
      </details></section>}
    {item.weather && <section className="panel case-summary"><h2>Meteorología disponible antes del objetivo</h2>
      <p>Ciclo GFS: <strong>{item.weather.inicio_ciclo_utc}</strong>, 12 horas antes de la emisión simulada.</p>
      <dl className="case-readings"><div><dt>Viento a 10 m, mediodía</dt><dd>{fmt(item.weather.viento_10m_mediodia_ms)} m/s</dd></div>
        <div><dt>Precipitación diaria prevista</dt><dd>{fmt(item.weather.precipitacion_diaria_mm)} mm</dd></div></dl>
      <p className="muted">Celda GFS: {item.weather.latitud_gfs}, {item.weather.longitud_gfs}. Son coordenadas de la rejilla, no de la estación.
        Se usan previsiones archivadas, no meteorología observada del futuro. La latencia de publicación del ciclo tampoco está verificada.</p>
    </section>}
    <section className="panel case-summary"><h2>Evidencias descargables</h2><p>Extractos de los archivos locales utilizados, sin volver a entrenar los modelos.</p>
      <ul className="case-evidence">{item.evidence.map(file => <li key={file.file}><a href={file.url} download>{file.file}</a> · {file.format} · {file.rows} filas
        <details><summary>Huella SHA-256</summary><code>{file.sha256}</code></details></li>)}</ul>
    </section>
  </>;
}

export function CaseStudies({ loadJson, selected, onSelect, onCharts }: { loadJson: JsonLoader;
  selected: string; onSelect: (id: string) => void; onCharts: (selection: Partial<ChartSelection>) => void }) {
  const [result, setResult] = useState<{ data?: CaseReport; error?: string }>({});
  useEffect(() => {
    const controller = new AbortController();
    loadJson<CaseReport>('/api/case-studies', controller.signal).then(data => setResult({ data }))
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ error: errorMessage(error) }); });
    return () => controller.abort();
  }, [loadJson]);
  if (result.error) return <p role="alert">No se pudieron cargar los casos: {result.error}</p>;
  if (!result.data) return <p role="status">Cargando los casos de estudio…</p>;
  const report = result.data;
  const item = report.cases.find(c => c.id === selected) ?? report.cases[0];
  return <div className="case-workspace">
    <nav className="case-selector" aria-label="Elegir caso de estudio">{report.cases.map((c, index) =>
      <button key={c.id} aria-pressed={item.id === c.id} onClick={() => onSelect(c.id)}><span>{index + 1}</span>{c.title}</button>)}</nav>
    <p className="muted">{report.scope}. Tres ejemplos para la defensa y una falsa alarma para contrastar el último. El ensayo con el autor sigue pendiente.</p>
    {item.id === 'typical' && <section className="panel case-summary"><h2>Por qué elegimos este día</h2>
      <p>{report.selection.rule}</p><p>{report.selection.candidates} candidatos; mediana: {fmt(report.selection.median)} µg/m³.
        La selección utiliza la concentración observada para ilustrar un caso retrospectivo, no para entrenar o ajustar el modelo.</p></section>}
    <CaseDetail key={item.id} item={item} threshold={report.threshold} onsets={report.onsets} onCharts={onCharts} />
    <section className="panel case-summary"><h2>Archivos de origen</h2><p>CSV: tablas; JSON: explicaciones y protocolo. El documento «Casos de estudio para la defensa» recoge el guion y las columnas de los extractos.</p>
      <details><summary>Ver procedencia y huellas de los {report.sources.length} archivos</summary>
        <ul className="case-evidence">{report.sources.map(source => <li key={source.path}><code>{source.path}</code> · {source.format}<br />
          <small>SHA-256: <code>{source.sha256}</code></small></li>)}</ul></details>
    </section>
  </div>;
}
