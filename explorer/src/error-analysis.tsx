import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { ErrorAnalysis, JsonLoader } from './api';
import type { Territory } from './chart-selection';
import './error-analysis.css';

const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const signed = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3, signDisplay: 'exceptZero' });
const months = new Intl.DateTimeFormat('es-ES', { month: 'long', timeZone: 'UTC' });
const SCENARIOS: Record<string, string> = {
  muestra_completa: 'Muestra completa',
  sin_fechas_mas_favorables: 'Retirando las 5 fechas más favorables para Ridge',
  sin_fechas_mas_desfavorables: 'Retirando las 5 fechas más desfavorables para Ridge',
};

function MonthlyErrors({ data, station }: { data: ErrorAnalysis; station: string }) {
  const [level, setLevel] = useState('todos');
  const rows = data.groups.filter(row => row.station === station && row.level === level);
  const annual = rows.find(row => row.month === 0);
  const limit = Math.max(...rows.map(row => Math.abs(row.delta_mae)), 0.001);
  return <section className="panel chart-card" aria-labelledby="monthly-errors-title">
    <div className="chart-card-header"><div>
      <h2 id="monthly-errors-title">¿Dónde cambia el error en 2024?</h2>
      <p>Diferencia de MAE entre Ridge y persistencia, en µg/m³. Un valor negativo favorece a Ridge.</p>
    </div><div className="chart-controls">
      <label>Nivel observado <select value={level} onChange={event => setLevel(event.target.value)}>
        <option value="todos">Todos los días evaluados</option>
        <option value="resto">PM10 hasta {data.threshold} µg/m³</option>
        <option value="elevado">PM10 mayor de {data.threshold} µg/m³</option>
      </select></label>
    </div></div>
    {annual && <div className="chart-overview" aria-live="polite">
      <span><strong>{annual.n}</strong> observaciones</span>
      <span>MAE Ridge <strong>{number.format(annual.mae_ridge)}</strong></span>
      <span>MAE persistencia <strong>{number.format(annual.mae_persistencia)}</strong></span>
      <span>Diferencia <strong>{signed.format(annual.delta_mae)} µg/m³</strong></span>
    </div>}
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Errores mensuales comparados">
      <table className="error-months">
        <thead><tr><th scope="col">Mes</th><th scope="col">Casos</th><th scope="col">MAE Ridge</th><th scope="col">MAE persistencia</th><th scope="col">Diferencia (µg/m³)</th></tr></thead>
        <tbody>{Array.from({ length: 12 }, (_, index) => {
          const month = index + 1;
          const row = rows.find(item => item.month === month);
          const width = row ? Math.abs(row.delta_mae) / limit * 50 : 0;
          return <tr key={month}>
            <th scope="row">{months.format(Date.UTC(2024, index, 1))}</th>
            <td>{row?.n ?? 0}</td>
            <td>{row ? number.format(row.mae_ridge) : '—'}</td>
            <td>{row ? number.format(row.mae_persistencia) : '—'}</td>
            <td>{row ? <div className="error-delta">
              <span aria-hidden="true" className="error-delta-track"><i className={row.delta_mae < 0 ? 'ridge-favored' : 'baseline-favored'} style={{
                width: width + '%',
                left: (row.delta_mae < 0 ? 50 - width : 50) + '%',
              }} /></span>
              <strong>{signed.format(row.delta_mae)}</strong>
            </div> : 'Sin casos evaluables'}</td>
          </tr>;
        })}</tbody>
      </table>
    </div>
    <p className="chart-note">El nivel se determina con el PM10 observado. Los filtros describen errores de predicciones ya guardadas. Las barras comparten escala dentro de la selección y los meses pueden tener pocas observaciones.</p>
  </section>;
}

export function RegressionErrorAnalysis({ loadJson, station, territory }: { loadJson: JsonLoader; station: string; territory: Territory }) {
  const [result, setResult] = useState<{ data?: ErrorAnalysis; error?: string }>();
  useEffect(() => {
    const controller = new AbortController();
    loadJson<ErrorAnalysis>('/api/charts/errors?territory=' + territory, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ data }); })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult({ error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [loadJson, territory]);
  if (!result) return <p role="status">Cargando análisis de errores…</p>;
  if (!result.data) return <p role="alert">{result.error}</p>;
  return <div className="workspace">
    <MonthlyErrors data={result.data} station={station} />
    {result.data.sensitivity.length > 0 ? <section className="panel chart-card" aria-labelledby="date-sensitivity-title">
      <div className="chart-card-header"><div>
        <h2 id="date-sensitivity-title">Sensibilidad a cinco fechas influyentes</h2>
        <p>Comparación global de las tres estaciones. Las fechas se ordenan por su contribución a la ventaja de Ridge en error absoluto.</p>
      </div></div>
      <div className="table-scroll" tabIndex={0} role="region" aria-label="Sensibilidad global a fechas influyentes">
        <table className="error-sensitivity">
          <thead><tr><th scope="col">Escenario</th><th scope="col">Casos</th><th scope="col">MAE Ridge</th><th scope="col">MAE persistencia</th><th scope="col">Diferencia</th></tr></thead>
          <tbody>{result.data.sensitivity.map(row => <tr key={row.scenario}>
            <th scope="row">{SCENARIOS[row.scenario]}{row.excluded_dates && <small>Fechas retiradas · {row.excluded_dates.split('|').join(', ')}</small>}</th>
            <td>{row.n}</td><td>{number.format(row.mae_ridge)}</td>
            <td>{number.format(row.mae_persistencia)}</td><td>{signed.format(row.delta_mae)}</td>
          </tr>)}</tbody>
        </table>
      </div>
      <p className="chart-note">Se retiran todas las observaciones evaluadas de las fechas elegidas, en las tres estaciones. Es una sensibilidad descriptiva posterior a la prueba. Los modelos conservan su ajuste y la muestra completa sigue siendo el resultado principal.</p>
    </section> : <p className="panel chart-message">La sensibilidad a cinco fechas influyentes solo está preparada para Madrid. Los errores mensuales de arriba corresponden a Barcelona provincia.</p>}
  </div>;
}
