import { createRoot } from 'react-dom/client';
import { useEffect, useId, useRef, useState } from 'react';
import lineage from './lineage.mmd?raw';
import treatedPm10 from './treated-pm10.mmd?raw';
import treatedBarcelona from './treated-barcelona.mmd?raw';
import treatedHealth from './treated-health.mmd?raw';
import { Documentation } from './documentation';
import { displayValue, ProvenanceDialog } from './provenance';
import { ColumnDictionary } from './dictionary';
import { Charts } from './charts';
import { Home } from './home';
import { Experiments } from './experiments';
import { CaseStudies } from './case-studies';
import { SourceList } from './source-list';
import { StatisticsTable } from './statistics';
import { columnLabel } from './column-title';
import { isPredictionRowDetail, isRowSourceColumn, RowTraceDialog } from './row-trace-dialog';
import type { RowTrace } from './row-trace-dialog';
import { dateForTerritory, INITIAL_CHART_SELECTION, TERRITORIES, TERRITORY_STATIONS } from './chart-selection';
import { errorMessage, loadJson } from './api';
import type { Column, SelectedCell, Source, TablePage, TableSummary, TreatedTable } from './api';
import './styles.css';

interface Filters {
  q: string;
  column: string;
  op: 'contains' | 'equals' | 'missing';
  value: string;
}

const EMPTY_FILTERS: Filters = { q: '', column: '', op: 'contains', value: '' };

function findInitialTable(tables: TableSummary[]) {
  return tables.find(({ name }) => /(?:^|\/)PM10_(?:DD|HH)/i.test(name)) || tables[0];
}

type DiagramTables = {
  nodes: Record<string, TreatedTable>;
  selectedId?: string;
  onSelect: (id: string) => void;
};

function Diagram({ definition = lineage, title = 'Cómo se relacionan las tablas',
  explanation = 'El PM10 y las previsiones de viento y precipitación de GFS se cruzan por estación y fecha objetivo. El análisis sanitario cruza los indicadores anuales por provincia y año.',
  tables }: { definition?: string; title?: string; explanation?: string; tables?: DiagramTables } = {}) {
  const [diagram, setDiagram] = useState<{ svg?: string; error?: string }>({});
  const graphic = useRef<HTMLDivElement>(null);
  const diagramId = `atlas-${useId().replace(/[^a-z0-9-]/gi, '')}`;
  useEffect(() => {
    let active = true;
    async function render() {
      try {
        const { default: mermaid } = await import('mermaid');
        mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'neutral', flowchart: { htmlLabels: false } });
        const { svg } = await mermaid.render(diagramId, definition);
        if (active) setDiagram({ svg });
      } catch {
        if (active) setDiagram({ error: 'No se pudo dibujar el flujo. Puedes consultar su código Mermaid.' });
      }
    }
    render();
    return () => { active = false; };
  }, [diagramId, definition]);

  useEffect(() => {
    if (!tables || !graphic.current) return;

    const cleanup: Array<() => void> = [];
    for (const node of graphic.current.querySelectorAll<SVGGElement>('g.node')) {
      const entity = node.id.match(/-entity-(.+)-[0-9]+$/)?.[1];
      const table = entity && tables.nodes[entity];
      if (!table) continue;

      node.setAttribute('role', 'button');
      node.setAttribute('tabindex', '0');
      node.setAttribute('aria-label', `Ver registros de ${table.name}`);
      node.setAttribute('aria-pressed', String(tables.selectedId === table.id));
      const select = () => tables.onSelect(table.id);
      const onKeyDown = (event: KeyboardEvent) => {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        select();
      };
      node.addEventListener('click', select);
      node.addEventListener('keydown', onKeyDown);
      cleanup.push(() => {
        node.removeEventListener('click', select);
        node.removeEventListener('keydown', onKeyDown);
      });
    }
    return () => cleanup.forEach(remove => remove());
  }, [diagram.svg, tables]);

  return <section className="panel diagram-panel" aria-labelledby="flow-title">
    <h2 id="flow-title">{title}</h2>
    <p className="muted">{explanation}</p>
    {tables && <p>Pulsa una tabla del esquema para ver sus registros debajo.</p>}
    {diagram.error ? <>
      <p role="alert">{diagram.error}</p>
      {tables && <div className="treated-navigation" aria-label="Tablas del esquema">
        {Object.values(tables.nodes).map(table =>
          <button key={table.id} type="button" aria-pressed={tables.selectedId === table.id}
            onClick={() => tables.onSelect(table.id)}>{table.name}</button>
        )}
      </div>}
    </> : diagram.svg
      ? <div ref={graphic} className="diagram-scroll" role={tables ? 'region' : 'img'} aria-label={title}
        tabIndex={tables ? 0 : undefined} dangerouslySetInnerHTML={{ __html: diagram.svg }} />
      : <p role="status">Dibujando el flujo…</p>}
    <details><summary>Ver código Mermaid</summary><pre>{definition}</pre></details>
  </section>;
}

const FORMATS: Partial<Record<string, string>> = {
  CSV: 'CSV con los registros de la tabla. El separador del original es punto y coma.',
  XLSX: 'Libro Excel (.xlsx) con una o más hojas.', XLS: 'Libro Excel (.xls) con una o más hojas.',
  Parquet: 'Archivo binario Parquet con los registros horarios del punto de muestreo.',
};

function EndpointCall({ method, url, response, detail, link = true }: {
  method: string;
  url?: string;
  response: string;
  detail?: string;
  link?: boolean;
}) {
  return <div className="endpoint-call">
    <div className="endpoint"><span className="method">{method}</span>{link ? <a href={url} target="_blank" rel="noreferrer">{url}</a> : <code>{url}</code>}</div>
    <p className="endpoint-format"><strong>Respuesta</strong> <span className="tag">{response}</span> {detail}</p>
  </div>;
}

function SourceInfo({ source, table }: { source: Source; table: TableSummary }) {
  const internalFormat = source.format === 'ZIP' ? [...new Set(source.tables.map(item => item.format))].join(', ') : '';
  const archiveDetail = internalFormat ? `Archivo ZIP que contiene archivos ${internalFormat}. La tabla elegida se lee como ${table.format}.` : '';
  return <section className="panel source-info" aria-labelledby="source-title">
    <p className="eyebrow">{source.domain} <span>·</span> {source.year}</p>
    <div className="source-heading"><h2 id="source-title">{source.title}</h2><span className="tag">{source.provider}</span></div>
    <p>{source.purpose}</p>
    {source.profile === 'noaa' ? <>
      <EndpointCall method="GET" url={source.url} response="Texto .idx" detail="Índice de posiciones de los mensajes en el archivo GRIB2." />
      <EndpointCall method="GET + Range" url={source.url.replace(/\.idx$/, '')} response="GRIB2" link={false} detail="Devuelve bytes del campo solicitado. La vista usa el CSV derivado y el manifiesto JSON local." />
    </> : source.profile === 'eea' ? <>
      <EndpointCall method="POST" url={source.url} response="CSV" detail="Recibe una consulta JSON y devuelve una lista de URLs de archivos Parquet." />
      <EndpointCall method="GET" url={table.url} response="Parquet" detail={FORMATS.Parquet} />
    </> : <EndpointCall method={source.method} url={source.url} response={source.format} detail={archiveDetail || FORMATS[source.format]} />}
    <div className="endpoint-details">
      {source.catalog && <a href={source.catalog} target="_blank" rel="noreferrer">Catálogo del proveedor ↗</a>}
    </div>
    {source.requestNote && <p className="muted call-note">{source.requestNote}</p>}
    {source.payload && <details><summary>Ver cuerpo de la consulta POST</summary><pre>{JSON.stringify(source.payload, null, 2)}</pre></details>}
  </section>;
}

function TreatedInfo({ table }: { table: TreatedTable }) {
  return <section className="panel source-info" aria-labelledby="source-title">
    <p className="eyebrow">{table.group} · Datos tratados</p>
    <div className="source-heading"><h2 id="source-title">{table.name}</h2><span className="tag">{table.format}</span></div>
    <p>{table.purpose}</p>
    <dl className="treated-meta">
      <div><dt>Qué representa cada fila</dt><dd>{table.grain}</dd></div>
      <div><dt>Cómo se identifica</dt><dd><code>{table.keys.join(' + ')}</code></dd></div>
      <div><dt>Cómo se prepara</dt><dd>{table.preparation}</dd><dd className="muted"><code>{table.mapper}</code></dd></div>
    </dl>
    <p className="treated-file">Archivo de la tabla <code>{table.local}</code></p>
  </section>;
}

const PREDICTION_FIELD_ORDER = [
  'NOMBRE', 'fecha_objetivo', 'fecha_ultima_observacion', 'pm10_t', 'pm10_objetivo',
  'pm10_t_menos_1', 'pm10_t_menos_2', 'pm10_t_menos_6', 'media_3_dias', 'media_7_dias',
  'media_14_dias', 'desviacion_7_dias', 'viento_10m_mediodia_ms', 'precipitacion_diaria_mm',
  'fila_utilizable', 'fila_comun_utilizable', 'particion', 'codigo_estacion',
];

function isOptionalColumn(name: string, columns: Column[]) {
  return isRowSourceColumn(name) || name === 'estado' && columns.some(field => field.name === 'es_valido') ||
    name === 'concentracion' && columns.some(field => field.name === 'pm10_valido');
}

function recordValue(value: TablePage['rows'][number][number], field: string, treated: boolean) {
  if (treated && field === 'es_valido') {
    const normalized = typeof value === 'string' ? value.trim().toLowerCase() : value;
    if (normalized === true || normalized === 'true') return 'Sí';
    if (normalized === false || normalized === 'false') return 'No';
  }
  return displayValue(value);
}

function ValueTable({ data, filtered, treated, onTrace, onInspect }: {
  data: TablePage;
  filtered: boolean;
  treated: boolean;
  onTrace: (row: RowTrace) => void;
  onInspect: (cell: SelectedCell) => void;
}) {
  if (!data.rows.length) return <p className="empty" role="status">{filtered ? 'Ningún registro coincide con los filtros.' : 'No hay registros en esta página.'}</p>;
  const names = new Set(data.columns.map(column => column.name));
  const predictive = treated && names.has('pm10_t');
  const stateIndex = data.columns.findIndex(field => field.name === 'estado');
  const fields = data.columns.map((field, index) => ({ field, index }))
    .filter(({ field: { name } }) => !treated || (!isOptionalColumn(name, data.columns) &&
      (!predictive || (!isPredictionRowDetail(name) && name !== 'pm10_valido' &&
        !(name === 'fecha' && names.has('fecha_ultima_observacion'))))));
  if (predictive) {
    const order = (name: string) => {
      const index = PREDICTION_FIELD_ORDER.indexOf(name);
      return index < 0 ? PREDICTION_FIELD_ORDER.length : index;
    };
    fields.sort((a, b) => order(a.field.name) - order(b.field.name));
  } else if (treated && stateIndex >= 0) {
    const order = (item: typeof fields[number]) => item.field.name === 'es_valido' ? stateIndex - .5 : item.index;
    fields.sort((a, b) => order(a) - order(b));
  }
  return <div className="table-scroll" tabIndex={0} role="region" aria-label="Registros de la tabla con desplazamiento horizontal">
    <table className="values"><thead><tr><th scope="col">N.º</th>{fields.map(({ field }) => <th key={field.name} scope="col">
      {treated ? columnLabel(field.name) : <><span>{field.name}</span><span className="column-type">{field.type}</span></>}
    </th>)}{treated && <th scope="col" className="row-info-cell"><span aria-hidden="true">Info</span><span className="sr-only">Trazabilidad</span></th>}</tr></thead><tbody>{data.rows.map((row, index) => <tr key={data.positions[index]}>
      <th scope="row">{data.positions[index]}</th>{fields.map(({ field: column, index: originalIndex }) => {
        const field = column.name;
        const cell = row[originalIndex];
        const missingGfsMessage = cell === 'sin_mensaje' && (field === 'estado_viento' || field === 'estado_precipitacion');
        const value = recordValue(missingGfsMessage ? null : cell, field, treated);
        return <td key={field}>
          <button className={`inspect-value${cell == null || missingGfsMessage ? ' missing' : ''}`} type="button" title="Ver procedencia"
            aria-label={`Procedencia de ${field} en el registro ${data.positions[index]}: ${missingGfsMessage ? 'sin mensaje' : value}`}
            onClick={() => onInspect({ row: data.positions[index], column: field })}>{value}</button>
        </td>;
      })}{treated && <td className="row-info-cell"><button className="row-info-button" type="button" title="Ver trazabilidad"
        aria-label={`Ver trazabilidad del registro ${data.positions[index]}`} onClick={event => onTrace({ position: data.positions[index], values: row, columns: data.columns, trigger: event.currentTarget })}>
        <svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.8">
          <circle cx="12" cy="12" r="9" /><path d="M12 10v7" /><circle cx="12" cy="7" r=".8" fill="currentColor" stroke="none" />
        </svg></button></td>}</tr>)}</tbody></table>
  </div>;
}

function TableFilters({ columns, applied, onApply, treated }: {
  columns: Column[];
  applied: Filters;
  treated: boolean;
  onApply: (filters: Filters) => void;
}) {
  const [draft, setDraft] = useState(applied);
  const change = <Field extends keyof Filters>(field: Field, value: Filters[Field]) =>
    setDraft(previous => ({ ...previous, [field]: value }));
  const needsValue = Boolean(draft.column) && draft.op !== 'missing';
  const booleanFilter = treated && draft.column === 'es_valido';
  const hasDraft = draft.q || draft.column;
  const hasApplied = applied.q || applied.column;
  return <form className="record-filters" aria-label="Filtros de registros" onSubmit={event => {
    event.preventDefault();
    onApply({ q: draft.q.trim(), column: draft.column, op: draft.column ? draft.op : 'contains', value: needsValue ? draft.value.trim() : '' });
  }}>
    <div className="filter-field"><label htmlFor="records-query">Buscar en toda la tabla</label><input id="records-query" type="search" maxLength={200}
      placeholder="Estación, fecha o valor" value={draft.q} onChange={e => change('q', e.target.value)} /></div>
    <div className="filter-field"><label htmlFor="records-column">Columna</label><select id="records-column" value={draft.column} disabled={!columns.length}
      onChange={e => setDraft(previous => ({ ...previous, column: e.target.value, op: treated && e.target.value === 'es_valido' ? 'equals' : 'contains', value: '' }))}>
      <option value="">Sin condición</option>{columns.map(field => <option key={field.name} value={field.name}>{treated ? `${columnLabel(field.name)} · ${field.name}` : field.name}</option>)}
    </select></div>
    <div className="filter-field"><label htmlFor="records-operator">Condición</label><select id="records-operator" value={draft.op} disabled={!draft.column} onChange={e => {
      const op = e.target.value;
      if (op === 'contains' || op === 'equals' || op === 'missing') change('op', op);
    }}>
      <option value="contains">Contiene</option><option value="equals">Es igual a</option><option value="missing">Está vacío</option>
    </select></div>
    <div className="filter-field"><label htmlFor="records-value">Valor</label>{booleanFilter ?
      <select id="records-value" value={needsValue ? draft.value : ''} disabled={!needsValue} onChange={e => change('value', e.target.value)}>
        <option value="">Selecciona Sí o No</option><option value="True">Sí</option><option value="False">No</option>
      </select> : <input id="records-value" maxLength={200} value={needsValue ? draft.value : ''}
        disabled={!needsValue} onChange={e => change('value', e.target.value)} />}</div>
    <div className="filter-actions"><button className="apply-filter" type="submit" disabled={needsValue && !draft.value.trim()}>Aplicar</button>
      <button type="button" disabled={!hasDraft && !hasApplied} onClick={() => { setDraft(EMPTY_FILTERS); onApply(EMPTY_FILTERS); }}>Limpiar</button></div>
  </form>;
}

type TableViewerProps = { source: Source } | { tables: TreatedTable[]; fromDiagram?: boolean };

type TableScope = 'all' | TreatedTable['scope'];
type TableKind = 'all' | TreatedTable['kind'];

const TABLE_SCOPES: Record<TableScope, string> = {
  all: 'Todas las tablas',
  ...TERRITORIES,
  provincial: 'Sanidad y demografía provincial',
};

const TABLE_KINDS: Record<TableKind, string> = {
  all: 'Todos los tipos',
  mapped: 'Mapeadas',
  supervised: 'Supervisadas',
  joined: 'Cruzadas',
};

function filterTreatedTables(tables: TreatedTable[], scope: TableScope, kind: TableKind) {
  return tables.filter(table =>
    (scope === 'all' || table.scope === scope) && (kind === 'all' || table.kind === kind)
  );
}

interface TableResult {
  query?: string;
  tableId?: string;
  data?: TablePage;
  error?: string;
}

function TableViewer(props: TableViewerProps) {
  const treated = 'tables' in props;
  const fromDiagram = treated && props.fromDiagram;
  const [scope, setScope] = useState<TableScope>('all');
  const [kind, setKind] = useState<TableKind>('all');
  const tables = treated ? filterTreatedTables(props.tables, scope, kind) : props.source.tables;
  const [tableId, setTableId] = useState(() => findInitialTable(tables).id);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [view, setView] = useState<'rows' | 'columns' | 'statistics'>('rows');
  const viewButtons = useRef<HTMLDivElement>(null);
  const [viewMinHeight, setViewMinHeight] = useState(0);
  const [result, setResult] = useState<TableResult>({});
  const [retry, setRetry] = useState(0);
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [inspection, setInspection] = useState<SelectedCell | null>(null);
  const [rowTrace, setRowTrace] = useState<RowTrace | null>(null);
  const treatedTable = treated ? props.tables.find(item => item.id === tableId) : undefined;
  const sourceTable = !treated ? props.source.tables.find(item => item.id === tableId) : undefined;
  const table = treatedTable ?? sourceTable;
  const search = new URLSearchParams({ page: String(page), size: String(size) });
  if (filters.q) search.set('q', filters.q);
  if (filters.column) {
    search.set('column', filters.column);
    search.set('op', filters.op);
    if (filters.op !== 'missing') search.set('value', filters.value);
  }
  const query = `/api/tables/${tableId}?${search}`;
  const statisticsSearch = new URLSearchParams(search);
  statisticsSearch.delete('page');
  statisticsSearch.delete('size');
  const current = result.query === query ? result : {};
  const columns = result.tableId === tableId ? result.data?.columns || [] : [];
  useEffect(() => {
    if (!tableId) return;
    const controller = new AbortController();
    loadJson<TablePage>(query, controller.signal).then(data => setResult({ tableId, query, data })).catch((error: unknown) => {
      if (!controller.signal.aborted) setResult(previous => ({ ...previous, query, error: errorMessage(error) }));
    });
    return () => controller.abort();
  }, [query, retry, tableId]);
  function selectView(next: typeof view) {
    if (next === view) return;
    const bottom = viewButtons.current?.getBoundingClientRect().bottom;
    if (bottom !== undefined) {
      // Keep enough content below the buttons to preserve the current scroll while the new view loads.
      setViewMinHeight(Math.max(0, document.documentElement.clientHeight - bottom));
    }
    setView(next);
  }

  function selectTable(id: string) {
    setTableId(id);
    setPage(1);
    setFilters(EMPTY_FILTERS);
  }

  function selectTableFilters(nextScope: TableScope, nextKind: TableKind) {
    if (!treated) return;
    const available = filterTreatedTables(props.tables, nextScope, nextKind);
    setScope(nextScope);
    setKind(nextKind);
    if (!available.some(item => item.id === tableId)) selectTable(available[0]?.id ?? '');
  }

  return <>
    {treatedTable && <TreatedInfo table={treatedTable} />}
    {!treated && sourceTable && <SourceInfo source={props.source} table={sourceTable} />}
    <section className="panel table-panel" aria-labelledby="table-title">
      <div className="table-toolbar"><div><h2 id="table-title">{fromDiagram ? 'Datos de la tabla' : 'Tablas disponibles'}</h2>
        {!fromDiagram && <p className="muted">{tables.length} {tables.length === 1 ? 'tabla' : 'tablas'} {treated ? 'tratadas' : 'en esta fuente'}</p>}</div>
        {!fromDiagram && <div className="table-pickers">
          {treated && <div className="table-picker">
            <label htmlFor="table-scope">Territorio</label>
            <select id="table-scope" value={scope} onChange={event => selectTableFilters(event.target.value as TableScope, kind)}>
              {Object.entries(TABLE_SCOPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </div>}
          {treated && <div className="table-picker">
            <label htmlFor="table-kind">Tipo de tabla</label>
            <select id="table-kind" value={kind} onChange={event => selectTableFilters(scope, event.target.value as TableKind)}>
              {Object.entries(TABLE_KINDS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </div>}
          <div className="table-picker">
            <label htmlFor="table-picker">Tabla</label>
            <select id="table-picker" value={tableId} disabled={!tables.length} onChange={event => selectTable(event.target.value)}>
              {!tables.length && <option value="">Sin tablas disponibles</option>}
              {tables.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>
        </div>}
      </div>
      {treated && !fromDiagram && <details className="table-types-help">
        <summary><span aria-hidden="true">ⓘ</span> Qué significa cada tipo</summary>
        <dl>
          <div><dt>Mapeadas</dt><dd>Limpian y normalizan datos de origen. Por ejemplo, la serie diaria de PM10.</dd></div>
          <div><dt>Supervisadas</dt><dd>Preparan entradas y un valor objetivo para entrenar y evaluar un modelo. Por ejemplo, usan el historial para predecir el PM10 del día siguiente.</dd></div>
          <div><dt>Cruzadas</dt><dd>Unen tablas mediante campos comunes. Por ejemplo, El PM10 y las previsiones de viento y precipitación de GFS se cruzan por estación y fecha objetivo.</dd></div>
        </dl>
      </details>}
      {table ? <>
      {!treated && <p className="file-path"><span className="tag">{table.format}</span> <span>{table.local}</span></p>}
      <div ref={viewButtons} className="view-buttons" aria-label="Contenido de la tabla">
        <button onClick={() => selectView('rows')} aria-pressed={view === 'rows'}>Registros</button>
        {treated && <button onClick={() => selectView('statistics')} aria-pressed={view === 'statistics'}>Estadísticas</button>}
        <button onClick={() => selectView('columns')} aria-pressed={view === 'columns'}>{treated ? 'Descripción de columnas' : 'Diccionario de columnas'}</button>
      </div>
      <div style={{ minHeight: viewMinHeight }}>
        {(view === 'rows' || view === 'statistics') && <TableFilters key={tableId} columns={columns} applied={filters} treated={treated}
          onApply={values => { setFilters(values); setPage(1); }} />}
        {view === 'rows' && <p className="inspect-hint muted">{treated ? 'Consulta el contexto y las fuentes de cada fila en el icono de información de la derecha. También puedes seleccionar un valor para ver su procedencia.' : 'Selecciona cualquier valor para ver su procedencia.'}</p>}
        {view === 'statistics' && treatedTable ? <StatisticsTable url={`/api/tables/${tableId}/statistics?${statisticsSearch}`} loadJson={loadJson} grain={treatedTable.grain} /> : current.error ?
          <div className="empty" role="alert">{current.error} <button onClick={() => { setResult({}); setRetry(retry + 1); }}>Reintentar</button></div> : !current.data ?
            <p className="empty muted" role="status">Cargando la página {page}…</p> : view === 'columns' ?
              <ColumnDictionary key={tableId} data={current.data} treated={treated} /> : <ValueTable data={current.data} treated={treated} onTrace={setRowTrace} filtered={Boolean(filters.q || filters.column)} onInspect={setInspection} />}
        {view === 'rows' && <div className="pagination">
          <label htmlFor="page-size">Filas por página <select id="page-size" value={size} onChange={e => { setSize(Number(e.target.value)); setPage(1); }}>
            {[10, 25, 50].map(n => <option key={n}>{n}</option>)}
          </select></label>
          <div className="page-buttons"><button aria-label="Página anterior" disabled={page === 1} onClick={() => setPage(page - 1)}>←</button>
            <span aria-live="polite">Página {page}{current.data?.rows.length ? ` · ${current.data.start + 1}–${current.data.start + current.data.rows.length}` : ''}</span>
            <button aria-label="Página siguiente" disabled={!current.data?.hasNext} onClick={() => setPage(page + 1)}>→</button>
          </div>
        </div>}
      </div>
      </> : <p className="empty" role="status">No hay tablas para esta combinación de territorio y tipo.</p>}
    </section>
    {inspection && <ProvenanceDialog tableId={tableId} selected={inspection} loadJson={loadJson} onClose={() => setInspection(null)} />}
    {rowTrace && treatedTable && <RowTraceDialog row={rowTrace} table={treatedTable} onClose={() => setRowTrace(null)}
      onInspect={cell => { setRowTrace(null); setInspection(cell); }} />}
  </>;
}

const TREATED_DIAGRAMS = {
  madrid: {
    label: 'Madrid',
    definition: treatedPm10,
    title: 'PM10 y meteorología de Madrid',
    explanation: 'La tabla diaria usa la fecha de observación. GFS es el modelo meteorológico de NOAA (Global Forecast System). Sus previsiones de viento y precipitación se unen a la tabla supervisada por estación y fecha objetivo.',
    entities: { PM10_DIARIO: 'pm10-diario', PM10_SUPERVISADO: 'pm10-supervisado', GFS_DIARIO: 'gfs-estacion', PM10_CON_GFS: 'pm10-meteo' },
  },
  barcelona: {
    label: 'Barcelona provincia',
    definition: treatedBarcelona,
    title: 'PM10 de Barcelona provincia',
    explanation: 'La tabla supervisada se construye a partir de la serie diaria. La fecha objetivo es el día siguiente a la última observación.',
    entities: { PM10_DIARIO: 'pm10-diario-barcelona', PM10_SUPERVISADO: 'pm10-supervisado-barcelona' },
  },
  health: {
    label: 'Sanidad y demografía',
    definition: treatedHealth,
    title: 'Sanidad y demografía provincial',
    explanation: 'El panel une las altas respiratorias y la demografía por provincia y año. El indicador provincial de PM10 puede estar ausente.',
    entities: { ALTAS_PROVINCIA: 'altas-provincia', DEMOGRAFIA_PROVINCIA: 'demografia-provincia', PANEL_SANITARIO: 'panel-sanitario' },
  },
};

type Schema = keyof typeof TREATED_DIAGRAMS;

function TreatedTables({ tables, error }: { tables: TreatedTable[]; error?: string }) {
  const [view, setView] = useState<'rows' | 'schema'>('schema');
  const [schema, setSchema] = useState<Schema>('madrid');
  const [selectedId, setSelectedId] = useState<string>();
  const diagram = TREATED_DIAGRAMS[schema];
  const nodes: Record<string, TreatedTable> = {};
  for (const [entity, id] of Object.entries(diagram.entities)) {
    const table = tables.find(item => item.id === `treated-${id}`);
    if (table) nodes[entity] = table;
  }
  const selectedTable = Object.values(nodes).find(table => table.id === selectedId);

  return <div className="workspace">
    <nav className="treated-navigation" aria-label="Vistas de las tablas tratadas">
      <button aria-pressed={view === 'schema'} onClick={() => setView('schema')}>Esquema Mermaid</button>
      <button aria-pressed={view === 'rows'} onClick={() => setView('rows')}>Consultar tablas</button>
    </nav>
    {view === 'schema' ? <>
      <div className="treated-navigation" aria-label="Área del esquema">
        {Object.entries(TREATED_DIAGRAMS).map(([key, item]) =>
          <button key={key} type="button" aria-pressed={schema === key} onClick={() => {
            if (key === schema) return;
            setSchema(key as Schema);
            setSelectedId(undefined);
          }}>{item.label}</button>
        )}
      </div>
      <Diagram key={schema} {...diagram} tables={Object.keys(nodes).length ? { nodes, selectedId, onSelect: setSelectedId } : undefined} />
      {error && <p role="alert">{error}</p>}
      <p className="sr-only" role="status">{selectedTable ? `Tabla abierta debajo del esquema: ${selectedTable.name}` : ''}</p>
      {selectedTable && <TableViewer key={selectedTable.id} tables={[selectedTable]} fromDiagram />}
    </> : error ? <p role="alert">{error}</p> : tables.length ? <TableViewer tables={tables} /> : <p role="status">Cargando tablas tratadas…</p>}
  </div>;
}

type Screen = 'home' | 'catalog' | 'treated' | 'charts' | 'experiments' | 'cases' | 'flow' | 'docs';

function App() {
  const [sources, setSources] = useState<Source[]>([]);
  const [selected, setSelected] = useState('');
  const [screen, setScreen] = useState<Screen>('home');
  const [chartSelection, setChartSelection] = useState(INITIAL_CHART_SELECTION);
  const [caseSelection, setCaseSelection] = useState('typical');
  const [error, setError] = useState('');
  const [treated, setTreated] = useState<{ tables: TreatedTable[]; error?: string }>({ tables: [] });
  useEffect(() => {
    const controller = new AbortController();
    loadJson<Source[]>('/api/sources', controller.signal).then(list => {
      const initial = list.find(source => source.profile === 'aire-diario' && source.year === '2024') || list[0];
      if (!initial) throw new Error('No hay fuentes en el catálogo.');
      setSources([initial, ...list.filter(source => source.id !== initial.id)]);
      setSelected(initial.id);
    }).catch((error: unknown) => { if (!controller.signal.aborted) setError(errorMessage(error)); });
    loadJson<TreatedTable[]>('/api/treated-tables', controller.signal).then(tables => setTreated({ tables }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setTreated({ tables: [], error: errorMessage(error) });
      });
    return () => controller.abort();
  }, []);
  const source = sources.find(item => item.id === selected);
  const headers = {
    cases: ['Resultados y límites · Madrid', 'Casos de estudio', 'Tres ejemplos verificables para explicar las predicciones y una falsa alarma para discutir sus límites.'],
    home: ['TFM · Predicción y evaluación', 'Anticipar el PM10 en Madrid y Barcelona provincia', 'Comparamos cómo se puede predecir la concentración de partículas en el aire del día siguiente.'],
    experiments: ['Réplicas territoriales · PM10', 'Madrid y Barcelona', 'Dos experimentos de regresión con el mismo protocolo y una comparación que muestra sus diferencias de cobertura.'],
    catalog: ['Fuentes y trazabilidad', 'Explorador de datos', 'Consulta los endpoints utilizados, los registros descargados y sus columnas.'],
    treated: ['Datos preparados', 'Tablas tratadas', 'Explora los valores que usa el TFM y las claves que relacionan sus tablas.'],
    charts: ['Observaciones y modelos · ' + TERRITORIES[chartSelection.territory], 'Gráficos de PM10 en ' + TERRITORIES[chartSelection.territory], 'Selecciona Madrid o Barcelona provincia para explorar sus estaciones y resultados.'],
    flow: ['Fuentes y trazabilidad', 'Flujo de datos', 'Sigue el recorrido desde las fuentes hasta el entrenamiento y el análisis sanitario.'],
    docs: ['Fuentes y transformaciones', 'Documentación', 'Consulta los formatos, los mapeadores y la procedencia documentada en el TFM.'],
  };
  return <>
    <header className="topbar"><div className="shell navigation"><span className="brand"><b aria-hidden="true">▥</b> Atlas de datos</span>
      <nav aria-label="Explorador"><button aria-pressed={screen === 'home'} onClick={() => setScreen('home')}>Inicio</button>
        <button aria-pressed={screen === 'catalog'} onClick={() => setScreen('catalog')}>Endpoints</button>
        <button aria-pressed={screen === 'treated'} onClick={() => setScreen('treated')}>Tablas tratadas</button>
        <button aria-pressed={screen === 'charts'} onClick={() => setScreen('charts')}>Gráficos</button>
        <button aria-pressed={screen === 'experiments'} onClick={() => setScreen('experiments')}>Experimentos</button>
        <button aria-pressed={screen === 'cases'} onClick={() => setScreen('cases')}>Casos</button>
        <button aria-pressed={screen === 'flow'} onClick={() => setScreen('flow')}>Flujo de datos</button>
        <button aria-pressed={screen === 'docs'} onClick={() => setScreen('docs')}>Documentación</button></nav>
      <span className="project-name">TFM · PM10</span>
    </div></header>
    <main className="shell">
      <header className="hero"><p className="eyebrow">{headers[screen][0]}</p><h1>{headers[screen][1]}</h1>
        <p>{headers[screen][2]}</p>
      </header>
      {screen === 'home' ? <Home loadJson={loadJson} onScreen={setScreen}
        onCharts={selection => {
          const territory = selection.territory ?? 'madrid';
          setChartSelection(previous => ({
            ...previous, ...selection, territory,
            station: selection.station ?? TERRITORY_STATIONS[territory][0][0],
            date: dateForTerritory(selection.date ?? previous.date, territory),
          }));
          setScreen('charts');
        }} /> :
        screen === 'experiments' ? <Experiments loadJson={loadJson} /> :
        screen === 'cases' ? <CaseStudies loadJson={loadJson} selected={caseSelection} onSelect={setCaseSelection}
          onCharts={selection => { setChartSelection(previous => ({ ...previous, ...selection, territory: 'madrid', station: selection.station ?? '28079060' })); setScreen('charts'); }} /> :
        screen === 'flow' ? <Diagram /> : screen === 'docs' ? <Documentation loadJson={loadJson} /> :
        screen === 'charts' ? <Charts loadJson={loadJson} selection={chartSelection} onSelection={setChartSelection} /> : screen === 'treated' ? <TreatedTables {...treated} /> :
        error ? <p role="alert">{error}</p> : !source ? <p role="status">Cargando el catálogo…</p> :
        <div className="layout"><SourceList sources={sources} selectedId={selected} onSelect={setSelected} />
          <div className="workspace"><TableViewer key={source.id} source={source} /></div></div>}
      <footer>Proyecto predictivo de PM10 · Copias locales de las fuentes públicas</footer>
    </main>
  </>;
}

const root = document.getElementById('root');
if (!root) throw new Error('No se encontró el elemento raíz del explorador.');
createRoot(root).render(<App />);
