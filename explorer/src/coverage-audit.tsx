import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader } from './api';
import './coverage-audit.css';

interface CoverageGroup {
  calendar: number; evaluated: number; excluded: number; unknownTarget: number; observedExcluded: number;
  elevatedObserved: number; elevatedExcluded: number; otherObserved: number; otherExcluded: number;
  month: number; reasons: Record<string, number>;
}
interface Audit {
  year: number; threshold: number; summary: CoverageGroup; monthly: CoverageGroup[];
  reasonLabels: Record<string, string>;
  features: { feature: string; missingWithTarget: number; soleMissingWithTarget: number }[];
  episodes: { station: string; name: string; start: string; end: string; peakDate: string; peak: number; observedDays: number; excludedDays: number; evaluatedDays: number }[];
  sources: { path: string; sha256: string }[];
}
interface Rows {
  rows: { codigo_estacion: string; NOMBRE: string; fecha_objetivo: string; pm10_objetivo: string; motivo: string; variables_ausentes: string; fechas_historial_ausentes: string }[];
  total: number; page: number; hasNext: boolean; source: string;
}
interface Territory { id: string; name: string; stations: { code: string; name: string }[] }

const integer = new Intl.NumberFormat('es-ES');
const decimal = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 1 });
const rate = (excluded: number, observed: number) => observed ? percent.format(excluded / observed) : 'Sin casos';
const monthName = (month: number) => new Intl.DateTimeFormat('es-ES', { month: 'long', timeZone: 'UTC' }).format(Date.UTC(2024, month - 1, 1));

function useAuditData<T>(url: string, loadJson: JsonLoader) {
  const [result, setResult] = useState<{ url: string; data?: T; error?: string }>();
  useEffect(() => {
    const controller = new AbortController();
    loadJson<T>(url, controller.signal).then(data => { if (!controller.signal.aborted) setResult({ url, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ url, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [url, loadJson]);
  return result?.url === url ? result : undefined;
}

export function CoverageAudit({ experiment, loadJson }: {
  experiment: Territory; loadJson: JsonLoader;
}) {
  const [station, setStation] = useState('todas');
  const [month, setMonth] = useState('0');
  const [status, setStatus] = useState('excluded');
  const [page, setPage] = useState(1);
  const result = useAuditData<Audit>('/api/experiments/' + experiment.id + '/coverage?' + new URLSearchParams({ station }), loadJson);
  const rowsResult = useAuditData<Rows>('/api/experiments/' + experiment.id + '/coverage/rows?' + new URLSearchParams({ station, month, status, page: String(page), size: '10' }), loadJson);
  const data = result?.data;
  const rows = rowsResult?.data;
  const summary = data?.summary;
  const reasons = data ? ['sin_objetivo', 'sin_ultimo_dia', 'historial_3d', 'historial_7d', 'historial_14d', 'otras_variables'].map(key => [key, data.reasonLabels[key]]) : [];
  const maximum = summary ? Math.max(1, ...reasons.map(([key]) => summary.reasons[key])) : 1;
  return <div className="workspace coverage-audit">
    <section className="panel chart-card" aria-labelledby="coverage-audit-title">
      <h2 id="coverage-audit-title">¿Qué días quedan fuera de la evaluación?</h2>
      <p>Auditoría de 2024 sobre los calendarios originales y las tablas supervisadas. Los modelos y sus resultados permanecen congelados.</p>
      <div className="chart-controls">
        <label>Estación de la auditoría <select value={station} onChange={event => { setStation(event.target.value); setPage(1); }}>
          <option value="todas">Todas las estaciones</option>{experiment.stations.map(point => <option key={point.code} value={point.code}>{point.name}</option>)}
        </select></label>
      </div>
      {result?.error ? <p role="alert">{result.error}</p> : !data || !summary ? <p role="status">Cargando auditoría…</p> : <>
        <dl className="coverage-totals"><div><dt>Días-estación de calendario</dt><dd>{integer.format(summary.calendar)}</dd></div>
          <div><dt>Casos evaluados</dt><dd>{integer.format(summary.evaluated)}</dd></div>
          <div><dt>Objetivo ausente</dt><dd>{integer.format(summary.unknownTarget)}</dd></div>
          <div><dt>Objetivo conocido, historial incompleto</dt><dd>{integer.format(summary.observedExcluded)}</dd></div></dl>
        <h3>Causas de exclusión sin duplicar casos</h3>
        <div className="coverage-reasons">{reasons.map(([key, label]) => <div key={key}>
          <span>{label}</span><i aria-hidden="true"><b style={{ width: 100 * summary.reasons[key] / maximum + '%' }} /></i><strong>{summary.reasons[key]}</strong>
        </div>)}</div>
        <p className="chart-note">Se asigna el primer bloque que falla, en este orden: objetivo, último día, bloque de 3 días, de 7 días y media de 14 días. Una fila puede carecer de varias variables; este reparto la cuenta una sola vez.</p>
      </>}
    </section>
    {data && summary && <>
      <section className="panel chart-card"><h2>Cobertura por mes</h2>
        <div className="table-scroll"><table className="values"><caption>2024 · Estación seleccionada o conjunto de estaciones</caption><thead><tr><th>Mes</th><th>Calendario</th><th>Evaluados</th><th>Objetivo ausente</th><th>Observado, sin historial completo</th><th>Cobertura evaluada</th></tr></thead>
          <tbody>{data.monthly.map(row => <tr key={row.month}><th scope="row">{monthName(row.month)}</th><td>{row.calendar}</td><td>{row.evaluated}</td><td>{row.unknownTarget}</td><td>{row.observedExcluded}</td><td>{rate(row.evaluated, row.calendar)}</td></tr>)}</tbody></table></div>
      </section>
      <section className="panel chart-card"><h2>Variables ausentes en días con objetivo conocido</h2>
        <p>Los recuentos de variables se solapan. «Única variable ausente» identifica filas donde todos los demás predictores están disponibles. Es una auditoría de disponibilidad; no estima la precisión de un modelo con menos variables.</p>
        <div className="table-scroll"><table className="values"><thead><tr><th>Variable</th><th>Ausente con objetivo conocido</th><th>Única variable ausente</th></tr></thead>
          <tbody>{data.features.map(row => <tr key={row.feature}><th scope="row"><code>{row.feature}</code></th><td>{row.missingWithTarget}</td><td>{row.soleMissingWithTarget}</td></tr>)}</tbody></table></div>
      </section>
      <section className="panel chart-card"><h2>¿Quedan fuera días elevados?</h2>
        <div className="table-scroll"><table className="values"><thead><tr><th>Grupo observado</th><th>Días conocidos</th><th>Excluidos</th><th>Proporción excluida</th></tr></thead><tbody>
          <tr><th scope="row">Mayor de {data.threshold} µg/m³</th><td>{summary.elevatedObserved}</td><td>{summary.elevatedExcluded}</td><td>{rate(summary.elevatedExcluded, summary.elevatedObserved)}</td></tr>
          <tr><th scope="row">Hasta {data.threshold} µg/m³</th><td>{summary.otherObserved}</td><td>{summary.otherExcluded}</td><td>{rate(summary.otherExcluded, summary.otherObserved)}</td></tr>
        </tbody></table></div>
        <p>Los días sin medición no pueden clasificarse como elevados o no elevados. El umbral es estadístico del TFM. Estas proporciones describen la muestra y no prueban que las ausencias sean aleatorias.</p>
        <details><summary>Tramos elevados observados con días excluidos ({data.episodes.length})</summary>
          <p>Se agrupan días consecutivos observados por encima del umbral. Los huecos y el cambio de año pueden fragmentar un episodio real. La lista está ordenada por días excluidos y pico.</p>
          <div className="table-scroll"><table className="values"><thead><tr><th>Estación</th><th>Inicio observado</th><th>Fin observado</th><th>Pico (µg/m³)</th><th>Días evaluados</th><th>Días excluidos</th></tr></thead><tbody>{data.episodes.map(row => <tr key={row.station + row.start}><th scope="row">{row.name}</th><td>{row.start}</td><td>{row.end}</td><td>{decimal.format(row.peak)}</td><td>{row.evaluatedDays}</td><td>{row.excludedDays}</td></tr>)}</tbody></table></div>
        </details>
      </section>
    </>}
    <section className="panel chart-card"><h2>Revisar los días y sus ausencias</h2>
      <p>El mes y el estado filtran solo esta tabla. El resumen superior mantiene todo 2024 para el territorio y la estación seleccionados.</p>
      <div className="chart-controls"><label>Mes de los días <select value={month} onChange={event => { setMonth(event.target.value); setPage(1); }}>
        <option value="0">Todo 2024</option>{Array.from({ length: 12 }, (_, index) => <option key={index + 1} value={index + 1}>{monthName(index + 1)}</option>)}
      </select></label><label>Estado del día <select value={status} onChange={event => { setStatus(event.target.value); setPage(1); }}>
        <option value="excluded">Excluidos</option><option value="evaluated">Evaluados</option><option value="all">Todos</option>
      </select></label></div>
      {rowsResult?.error ? <p role="alert">{rowsResult.error}</p> : rows ? <>
        <p role="status">{rows.total} días-estación · Página {rows.page}</p>
        <div className="table-scroll"><table className="values coverage-detail"><thead><tr><th>Estación</th><th>Fecha objetivo</th><th>PM10 observado</th><th>Motivo</th><th>Variables ausentes</th><th>Fechas ausentes en los 14 días previos</th></tr></thead><tbody>
          {rows.rows.map(row => <tr key={row.codigo_estacion + row.fecha_objetivo}><th scope="row">{row.NOMBRE}</th><td>{row.fecha_objetivo}</td><td>{row.pm10_objetivo === '' ? 'Sin dato' : decimal.format(Number(row.pm10_objetivo)) + ' µg/m³'}</td><td>{data?.reasonLabels[row.motivo] ?? row.motivo}</td><td>{row.variables_ausentes.split('|').join(', ') || 'Ninguna'}</td><td>{row.fechas_historial_ausentes.split('|').join(', ') || 'Ninguna'}</td></tr>)}
        </tbody></table></div>
        {!rows.rows.length && <p>No hay días que cumplan estos filtros.</p>}
        <div className="page-buttons"><button disabled={page === 1} onClick={() => setPage(previous => previous - 1)}>Página anterior</button><button disabled={!rows.hasNext} onClick={() => setPage(previous => previous + 1)}>Página siguiente</button></div>
        <p className="experiment-path"><code>{rows.source}</code></p>
      </> : <p role="status">Cargando días de la auditoría…</p>}
      {data && <details><summary>Entradas auditadas</summary>{data.sources.map(source => <p className="experiment-path" key={source.path}><code>{source.path}</code></p>)}</details>}
    </section>
  </div>;
}
