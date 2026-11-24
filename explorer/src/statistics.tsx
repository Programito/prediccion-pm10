import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader } from './api';
import { BoxPlot } from './boxplot';
import { columnLabel } from './column-title';
import './statistics.css';

interface NumericSummary {
  name: string; type: string; description: string;
  valid_count: number; missing_count: number; invalid_count: number; missing_pct: number | null;
  minimum: number | null; p25: number | null; median: number | null; mean: number | null;
  p75: number | null; maximum: number | null; std_dev: number | null;
  calculation_errors: string[];
}
interface TableStatistics {
  row_count: number; columns: NumericSummary[]; excluded_columns: string[];
  quantile_method: string; std_dev_ddof: number;
  filters: { q: string; column: string; op: string; value: string };
}
const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const smallNumber = new Intl.NumberFormat('es-ES', { maximumSignificantDigits: 3 });
const integer = new Intl.NumberFormat('es-ES');
const format = (value: number | null) => value === null ? '—' :
  value !== 0 && Math.abs(value) < .01 ? smallNumber.format(value) : number.format(value);
const YEAR_COLUMNS = new Set(['anio', 'anio_objetivo', 'year']);
const QUALITY_COLUMNS = new Set(['n_horas_validas', 'horas_validas']);
const CONTEXT_COLUMNS = new Set([
  'latitud_gfs', 'longitud_gfs', 'dia_semana_objetivo', 'mes_objetivo',
  'semana_sin', 'semana_cos', 'mes_sin', 'mes_cos', 'pm10_elevado_objetivo',
]);
const SECONDARY_COLUMNS = /^(pm10_t_menos_|media_\d+_dias$|desviacion_\d+_dias$|proporcion_|minimo_medias_|maximo_medias_|cobertura_|n_estaciones$|n_(urbanas|suburbanas|rurales|area_no_clasificada)$)/;

function SummaryTable({ columns, caption }: { columns: NumericSummary[]; caption: string }) {
  return <div className="table-scroll"><table className="values statistics-table">
    <caption>{caption}</caption>
    <thead><tr><th scope="col">Columna</th><th scope="col">Mínimo</th><th scope="col">P25</th><th scope="col">Mediana</th><th scope="col">Media</th><th scope="col">P75</th><th scope="col">Máximo</th><th scope="col">Válidos</th><th scope="col">Ausentes</th><th scope="col">Inválidos</th><th scope="col">Ausentes (%)</th><th scope="col">Desv. estándar</th></tr></thead>
    <tbody>{columns.map(row => <tr key={row.name}>
      <th scope="row">{columnLabel(row.name)}</th>
      <td>{format(row.minimum)}</td><td>{format(row.p25)}</td><td>{format(row.median)}</td><td>{format(row.mean)}</td><td>{format(row.p75)}</td><td>{format(row.maximum)}</td>
      <td>{integer.format(row.valid_count)}</td><td>{integer.format(row.missing_count)}</td><td>{integer.format(row.invalid_count)}</td>
      <td>{format(row.missing_pct)}</td><td>{format(row.std_dev)}</td>
    </tr>)}</tbody>
  </table></div>;
}

export function StatisticsTable({ url, loadJson, grain }: {
  url: string; loadJson: JsonLoader; grain: string;
}) {
  const [boxSelection, setBoxSelection] = useState({ field: 'pm10_valido', group: 'codigo_estacion' });
  const [result, setResult] = useState<{ url: string; data?: TableStatistics; error?: string }>();
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    loadJson<TableStatistics>(url, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ url, data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ url, error: errorMessage(error) }); });
    return () => controller.abort();
  }, [url, loadJson, retry]);
  const current = result?.url === url ? result : undefined;
  if (!current) return <p role="status" className="empty">Calculando estadísticas de todas las filas filtradas…</p>;
  if (!current.data) return <div role="alert" className="empty">{current.error} <button onClick={() => { setResult(undefined); setRetry(value => value + 1); }}>Reintentar estadísticas</button></div>;
  const data = current.data;
  const filtered = Boolean(data.filters.q || data.filters.column);
  const names = new Set(data.columns.map(row => row.name));
  const redundant = (name: string) => (name === 'concentracion' && (names.has('pm10_valido') || names.has('pm10_t'))) ||
    (name === 'pm10_valido' && names.has('pm10_t'));
  const quality = data.columns.filter(row => QUALITY_COLUMNS.has(row.name));
  const period = data.columns.find(row => row.name === 'anio_objetivo') ?? data.columns.find(row => YEAR_COLUMNS.has(row.name));
  const available = data.columns.filter(({ name }) =>
    !YEAR_COLUMNS.has(name) && !QUALITY_COLUMNS.has(name) && !CONTEXT_COLUMNS.has(name) && !redundant(name)
  );
  const measures = available.filter(row => !SECONDARY_COLUMNS.test(row.name));
  const secondary = available.filter(row => SECONDARY_COLUMNS.test(row.name));
  const hidden = data.columns.filter(row => CONTEXT_COLUMNS.has(row.name) || redundant(row.name));
  const chart = data.row_count > 0 && available.length > 0 &&
    <BoxPlot url={url} columns={[...measures, ...secondary]} canGroup={data.excluded_columns.includes('codigo_estacion')}
      loadJson={loadJson} selection={boxSelection} onSelection={setBoxSelection} />;
  const secondaryDetails = data.row_count > 0 && secondary.length > 0 &&
    <details className="statistics-quality"><summary>Variables complementarias ({secondary.length})</summary>
      <SummaryTable columns={secondary} caption="Predictores derivados e indicadores complementarios" />
    </details>;
  return <div className="table-statistics">
    <div className="statistics-intro">
      <h3>Resumen de medidas principales</h3>
      <p role="status"><strong>{integer.format(data.row_count)}</strong> filas {filtered ? 'que cumplen los filtros aplicados' : 'de la tabla completa'} · {data.row_count > 0 ? measures.length : 0} {data.row_count > 0 && measures.length === 1 ? 'medida en el resumen principal' : 'medidas en el resumen principal'}.</p>
      {period && <p className="statistics-period">Periodo {period.name === 'anio_objetivo' ? 'del objetivo' : 'disponible'}: <strong>{period.minimum === null || period.maximum === null ? 'Sin años disponibles' :
        period.minimum === period.maximum ? integer.format(period.minimum) : `${integer.format(period.minimum)}–${integer.format(period.maximum)}`}</strong>{filtered && ' · Filas que cumplen los filtros.'}</p>}
      <p><strong>Unidad del resumen.</strong> {grain}{' '}
        Las cifras reúnen todas las filas {filtered ? 'que cumplen los filtros' : 'de la tabla'} en un solo resumen.</p>
      <p>Los ausentes se cuentan por separado y los valores extremos se conservan. Cifras redondeadas para facilitar la lectura.</p>
      {filtered && <p>Filtros activos: {data.filters.q && <>búsqueda «{data.filters.q}»{data.filters.column ? ' · ' : ''}</>}
        {data.filters.column && <>{data.filters.column} {data.filters.op === 'missing' ? 'está vacío' : data.filters.op === 'equals' ? 'es igual a' : 'contiene'} {data.filters.op !== 'missing' && '«' + data.filters.value + '»'}</>}</p>}
    </div>
    {!data.row_count && <p className="empty">No hay filas que cumplan estos filtros.</p>}
    {data.row_count > 0 && measures.length > 0 &&
      <SummaryTable columns={measures} caption={measures.length === 1 && measures[0].name === 'pm10_valido' ?
        'PM10 · µg/m³ · Estadísticas de las filas consultadas' : 'Estadísticas de las medidas principales'} />}
    {chart}
    {secondaryDetails}
    {data.row_count > 0 && quality.length > 0 && <details className="statistics-quality"><summary>Calidad de los datos · Cobertura horaria</summary>
      <p>Horas válidas disponibles para calcular medias diarias. Estos recuentos describen cobertura, no concentración de PM10. Un recuento numérico válido no implica que el día supere el control de calidad.</p>
      <p>La media derivada del horario requiere al menos 18 horas válidas. Una medición diaria oficial puede no tener un recuento horario asociado: su ausencia no significa cero horas ni medición inválida.</p>
      <SummaryTable columns={quality} caption="Cobertura de las filas filtradas · Horas" />
    </details>}
    <div className="statistics-notes">
      {available.some(row => row.invalid_count > 0) && <p role="status">Hay valores inválidos: no se han incluido textos no numéricos, booleanos o infinitos en las medidas. Puedes revisar las columnas afectadas en Registros.</p>}
      {available.some(row => row.calculation_errors.length > 0) && <p role="status">Alguna medida no se ha podido representar numéricamente y aparece con un guion.</p>}
      <details><summary>Cómo interpretar las estadísticas</summary>
        <dl><div><dt>P25 y P75</dt><dd>Percentiles 25 y 75: sitúan aproximadamente el 25 % y el 75 % de los valores por debajo de esos puntos. Se calculan con interpolación lineal en la posición (n−1)×p.</dd></div>
          <div><dt>Mediana y media</dt><dd>La mediana es el percentil 50. La media suma los valores válidos y divide entre su cantidad; los extremos pueden influir mucho en ella.</dd></div>
          <div><dt>Desviación estándar</dt><dd>Describe la dispersión en las unidades de la columna. Se usa la versión muestral, con divisor n−1, y hacen falta al menos dos valores válidos.</dd></div>
          <div><dt>Ausentes e inválidos</dt><dd>Los blancos, nulos, NaN y la marca «..» se consideran ausentes. El porcentaje de ausentes se calcula sobre todas las filas coincidentes. Los valores que no pueden convertirse de forma válida se cuentan aparte.</dd></div>
          <div><dt>Válidos</dt><dd>Son números finitos aceptados por el cálculo estadístico. Para consultar las concentraciones aceptadas por el control ambiental se utiliza PM10 válido. El redondeo de la pantalla no modifica los datos ni las estadísticas originales de la API.</dd></div>
          <div><dt>Guion</dt><dd>Indica que la medida no está definida o no se puede representar; un cero es un resultado numérico válido.</dd></div></dl>
        <p>Estas estadísticas describen los datos consultados.</p>
      </details>
      {hidden.length > 0 && <details><summary>Columnas numéricas de contexto o repetidas ({hidden.length})</summary>
        <p>Los códigos de calendario, las coordenadas y las etiquetas de clasificación se consultan en Registros.</p>
        <p>Para la misma observación se muestra <code>pm10_t</code> en tablas predictivas o <code>pm10_valido</code> en tablas diarias.</p>
        <p>{hidden.map(row => row.name).join(', ')}</p>
      </details>}
    </div>
  </div>;
}
