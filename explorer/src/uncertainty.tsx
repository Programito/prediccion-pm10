import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { BootstrapAnalysis, JsonLoader } from './api';
import type { Territory } from './chart-selection';
import './uncertainty.css';

const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3, signDisplay: 'exceptZero' });

export function ModelUncertainty({ loadJson, station, territory }: { loadJson: JsonLoader; station: string; territory: Territory }) {
  const [result, setResult] = useState<{ data?: BootstrapAnalysis; error?: string }>();
  useEffect(() => {
    const controller = new AbortController();
    loadJson<BootstrapAnalysis>('/api/charts/uncertainty?territory=' + territory, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ data }); })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult({ error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [loadJson, territory]);
  if (!result) return <p role="status">Calculando la vista de incertidumbre…</p>;
  if (!result.data) return <p role="alert">{result.error}</p>;
  const data = result.data;
  const rows = data.rows.filter(row => row.station === station);
  const primary = rows.find(row => row.block_days === data.primaryBlockDays);
  const limit = Math.max(...rows.flatMap(row => [Math.abs(row.lower), Math.abs(row.upper), Math.abs(row.estimate)]), .001) * 1.12;
  const position = (value: number) => (value + limit) / (2 * limit) * 100;
  return <section className="panel chart-card" aria-labelledby="uncertainty-title">
    <div className="chart-card-header"><div>
      <h2 id="uncertainty-title">Incertidumbre de la diferencia de MAE</h2>
      <p>Ridge menos persistencia en 2024. Intervalos percentiles bootstrap de nivel nominal {data.coverage * 100} %.</p>
    </div></div>
    {primary && <div className="chart-overview" aria-live="polite">
      <span><strong>{primary.n}</strong> observaciones</span>
      <span>Diferencia observada <strong>{number.format(primary.estimate)} µg/m³</strong></span>
      <span>Bloque principal <strong>{data.primaryBlockDays} días</strong></span>
    </div>}
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Intervalos por longitud de bloque">
      <table className="uncertainty-table">
        <thead><tr><th scope="col">Bloque</th><th scope="col">Intervalo (µg/m³)</th><th scope="col">Comparación con cero</th><th scope="col">Límite inferior</th><th scope="col">Límite superior</th></tr></thead>
        <tbody>{rows.map(row => <tr key={row.block_days}>
          <th scope="row">{row.block_days} días{row.block_days === data.primaryBlockDays && <small>Principal</small>}</th>
          <td><span className="uncertainty-track" aria-hidden="true">
            <i className="uncertainty-zero" />
            <i className="uncertainty-range" style={{ left: position(row.lower) + '%', width: (position(row.upper) - position(row.lower)) + '%' }} />
            <i className="uncertainty-estimate" style={{ left: position(row.estimate) + '%' }} />
          </span></td>
          <td>{row.includes_zero ? 'Incluye cero' : row.upper < 0 ? 'Valores negativos' : 'Valores positivos'}</td>
          <td>{number.format(row.lower)}</td><td>{number.format(row.upper)}</td>
        </tr>)}</tbody>
      </table>
    </div>
    <p className="chart-note">Cada línea es un intervalo y el punto marca la diferencia observada. La referencia vertical marca cero. Los valores negativos favorecen a Ridge.</p>
    <p className="chart-note">{data.replicates.toLocaleString('es-ES')} réplicas por longitud. Se remuestrean fechas consecutivas manteniendo juntas sus estaciones y sus huecos. La longitud de bloque y la estacionalidad afectan la interpretación de este diagnóstico posterior a la prueba.</p>
    {primary?.includes_zero && <p>El intervalo principal incluye cero. Esta muestra y este remuestreo dejan abierta la dirección de la diferencia.</p>}
  </section>;
}
