import { useEffect, useId, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader } from './api';
import './boxplot.css';

interface BoxGroup {
  group: string; label: string; row_count: number; valid_count: number; missing_count: number; invalid_count: number;
  minimum: number | null; maximum: number | null; p25: number | null; median: number | null; p75: number | null; mean: number | null;
  boxplot: { whisker_low: number | null; whisker_high: number | null; outliers: number[] };
}
interface BoxData { column: string; group_by: string; row_count: number; groups: BoxGroup[] }
interface NumericColumn { name: string; description: string }
const number = new Intl.NumberFormat('es-ES', { maximumSignificantDigits: 6 });
const format = (value: number | null) => value === null ? '—' : number.format(value);
const label = (row: BoxGroup) => row.group === 'all' ? row.label : row.label + ' · ' + row.group;

function BoxFigure({ data }: { data: BoxData }) {
  const id = useId();
  const available = data.groups.filter(group => group.valid_count > 0);
  if (!available.length) return <p role="status">No hay valores numéricos válidos para dibujar la caja con estos filtros.</p>;
  const minimum = Math.min(...available.map(group => group.minimum!));
  const maximum = Math.max(...available.map(group => group.maximum!));
  const padding = maximum === minimum ? Math.max(1, Math.abs(minimum) * .05) : (maximum - minimum) * .05;
  const rawStep = (maximum - minimum + 2 * padding) / 5;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const step = [1, 2, 5, 10].find(value => value * magnitude >= rawStep)! * magnitude;
  const low = minimum >= 0 ? Math.max(0, Math.floor((minimum - padding) / step) * step) : Math.floor((minimum - padding) / step) * step;
  const high = Math.ceil((maximum + padding) / step) * step;
  const x = (value: number) => 260 + (value - low) / (high - low) * 700;
  const height = 100 + data.groups.length * 90;
  return <div className="boxplot-scroll"><svg viewBox={'0 0 1000 ' + height} role="img" aria-labelledby={id + '-title ' + id + '-description'}>
    <title id={id + '-title'}>Diagrama de caja de {data.column}</title>
    <desc id={id + '-description'}>Una escala común que incluye todos los valores válidos. La caja abarca P25 a P75, la línea marca la mediana, el rombo marca la media y los círculos muestran valores exteriores. Los bigotes terminan en observaciones dentro de 1,5 rangos intercuartílicos. Los valores exactos están en la tabla siguiente.</desc>
    {Array.from({ length: Math.round((high - low) / step) + 1 }, (_, index) => {
      const value = low + step * index;
      return <g key={index} aria-hidden="true"><line x1={x(value)} x2={x(value)} y1="25" y2={height - 45} className="boxplot-grid" /><text x={x(value)} y={height - 20} textAnchor="middle">{number.format(value)}</text></g>;
    })}
    {data.groups.map((group, index) => {
      const y = 65 + index * 90;
      return <g key={group.group}>
        <text x="240" y={y - 3} textAnchor="end"><title>{label(group)}</title>{group.label.length > 31 ? group.label.slice(0, 29) + '…' : group.label}
          <tspan x="240" dy="18">{group.group === 'all' ? '' : group.group + ' · '}n = {group.valid_count}</tspan></text>
        {group.valid_count > 0 ? <>
          <line x1={x(group.boxplot.whisker_low!)} x2={x(group.boxplot.whisker_high!)} y1={y} y2={y} className="boxplot-whisker" />
          {[group.boxplot.whisker_low!, group.boxplot.whisker_high!].map((value, end) => <line key={end} x1={x(value)} x2={x(value)} y1={y - 10} y2={y + 10} className="boxplot-whisker"><title>Bigote: {format(value)}</title></line>)}
          <rect x={x(group.p25!)} y={y - 17} width={Math.max(1, x(group.p75!) - x(group.p25!))} height="34" className="boxplot-box"><title>P25: {format(group.p25)} · P75: {format(group.p75)}</title></rect>
          <line x1={x(group.median!)} x2={x(group.median!)} y1={y - 17} y2={y + 17} className="boxplot-median"><title>Mediana: {format(group.median)}</title></line>
          {group.mean !== null && <polygon points={[[x(group.mean), y - 6], [x(group.mean) + 6, y], [x(group.mean), y + 6], [x(group.mean) - 6, y]].map(point => point.join(',')).join(' ')} className="boxplot-mean"><title>Media: {format(group.mean)}</title></polygon>}
          {group.boxplot.outliers.map((value, point) => <circle key={point} cx={x(value)} cy={y + ((point % 5) - 2) * 3} r="3" className="boxplot-outlier"><title>Valor exterior: {format(value)}</title></circle>)}
        </> : <text x="270" y={y}>Sin valores numéricos válidos</text>}
      </g>;
    })}
  </svg></div>;
}

export function BoxPlot({ url, columns, canGroup, loadJson, selection, onSelection }: {
  url: string; columns: NumericColumn[]; canGroup: boolean; loadJson: JsonLoader;
  selection: { field: string; group: string }; onSelection: (value: { field: string; group: string }) => void;
}) {
  const { field, group } = selection;
  const selected = columns.find(column => column.name === field) ?? columns.find(column => column.name === 'pm10_valido') ?? columns[0];
  const selectedGroup = canGroup ? group : 'none';
  const [base, query = ''] = url.split('?');
  const params = new URLSearchParams(query);
  params.set('field', selected.name);
  params.set('group_by', selectedGroup);
  const endpoint = base.replace('/statistics', '/boxplot') + '?' + params;
  const [result, setResult] = useState<{ url: string; data?: BoxData; error?: string }>();
  useEffect(() => {
    const controller = new AbortController();
    loadJson<BoxData>(endpoint, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ url: endpoint, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ url: endpoint, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [endpoint, loadJson]);
  const current = result?.url === endpoint ? result : undefined;
  const data = current?.data;
  return <section className="statistics-boxplot" tabIndex={-1} aria-label="Diagrama de caja y bigotes">
    <h3>Diagrama de caja y bigotes</h3>
    <div className="chart-controls"><label>Columna del diagrama <select value={selected.name} onChange={event => onSelection({ ...selection, field: event.target.value })}>{columns.map(column => <option key={column.name} value={column.name}>{column.name}</option>)}</select></label>
      <label>Comparación del diagrama <select value={selectedGroup} onChange={event => onSelection({ ...selection, group: event.target.value })}>
        <option value="none">Selección completa</option>{canGroup && <option value="codigo_estacion">Por estación</option>}
      </select></label></div>
    <p>{selected.description}</p>
    {!current ? <p role="status">Calculando el diagrama con todas las filas filtradas…</p> : current.error ? <p role="alert">{current.error}</p> : data && <>
      <p>{data.row_count} filas filtradas · Escala común en las unidades de la columna. Se conservan todos los valores exteriores.</p>
      <BoxFigure data={data} />
      <div className="boxplot-legend"><span><i className="boxplot-key-box" />Caja P25–P75</span><span><i className="boxplot-key-median" />Mediana</span><span><i className="boxplot-key-mean" />Media</span><span><i className="boxplot-key-outlier" />Valores exteriores</span></div>
      <div className="table-scroll"><table className="values"><caption>Valores exactos del diagrama</caption><thead><tr><th>Grupo</th><th>Válidos</th><th>Ausentes</th><th>Inválidos</th><th>P25</th><th>Mediana</th><th>P75</th><th>Media</th><th>Bigote inferior</th><th>Bigote superior</th><th>Exteriores</th></tr></thead>
        <tbody>{data.groups.map(row => <tr key={row.group}><th scope="row">{label(row)}</th><td>{row.valid_count}</td><td>{row.missing_count}</td><td>{row.invalid_count}</td><td>{format(row.p25)}</td><td>{format(row.median)}</td><td>{format(row.p75)}</td><td>{format(row.mean)}</td><td>{format(row.boxplot.whisker_low)}</td><td>{format(row.boxplot.whisker_high)}</td><td>{row.boxplot.outliers.length}</td></tr>)}</tbody></table></div>
    </>}
    <p>Los bigotes llegan hasta los valores observados dentro de P25−1,5×(P75−P25) y P75+1,5×(P75−P25). Un punto exterior es potencialmente atípico y puede ser una medición real válida. No se elimina ni cambia el cálculo de las estadísticas. La separación vertical de los círculos facilita su lectura y no representa otra variable.</p>
  </section>;
}
