import { useEffect, useId, useRef } from 'react';
import type { Column, Cell, SelectedCell, TreatedTable } from './api';
import { columnLabel } from './column-title';
import { displayValue } from './provenance';

export interface RowTrace { position: number; values: Cell[]; columns: Column[]; trigger: HTMLButtonElement }

export function isRowSourceColumn(name: string) {
  return name.startsWith('fuente_') || ['archivo_origen', 'miembro_zip', 'origen_diario'].includes(name);
}

const PREDICTION_ROW_DETAILS = new Set([
  'punto_muestreo', 'TIPO_AREA', 'es_valido', 'n_horas_validas', 'codigo_provincia', 'anio', 'unidad', 'emision_simulada_utc',
]);

export function isPredictionRowDetail(name: string) {
  return PREDICTION_ROW_DETAILS.has(name);
}

export function RowTraceDialog({ row, table, onClose, onInspect }: {
  row: RowTrace; table: TreatedTable; onClose: () => void; onInspect: (cell: SelectedCell) => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => { dialog?.close(); if (row.trigger.isConnected) row.trigger.focus({ preventScroll: true }); };
  }, [row]);
  const predictive = row.columns.some(column => column.name === 'pm10_t');
  const identityNames = new Set([...table.keys, 'NOMBRE', predictive ? 'fecha_ultima_observacion' : 'fecha']);
  if (!predictive) identityNames.add('punto_muestreo');
  const detailNames = new Set(['concentracion', 'pm10_valido', 'es_valido', 'estado', 'n_horas_validas', 'horas_validas',
    'estado_viento', 'estado_precipitacion', 'inicio_ciclo_utc']);
  const fields = row.columns.map((column, index) => ({ ...column, value: row.values[index] }));
  const measurement = fields.find(field => field.name === 'pm10_valido') ?? fields.find(field => field.name === 'concentracion') ??
    fields.find(field => /^(Decimal|Proporción)/.test(field.type)) ?? fields[0];
  const value = (field: typeof fields[number]) => {
    if (field.name === 'es_valido') {
      if (field.value === true || String(field.value).toLowerCase() === 'true') return 'Sí';
      if (field.value === false || String(field.value).toLowerCase() === 'false') return 'No';
    }
    return displayValue(field.value);
  };
  const details = fields.filter(({ name }) => detailNames.has(name) || isRowSourceColumn(name) ||
    (predictive && isPredictionRowDetail(name)));
  return <dialog ref={ref} className="provenance-dialog" aria-labelledby={titleId} onCancel={onClose}>
    <header className="provenance-header"><div><p className="eyebrow">{table.name}</p><h2 id={titleId}>Trazabilidad del registro {row.position}</h2></div>
      <button type="button" aria-label="Cerrar trazabilidad" onClick={onClose}>×</button></header>
    <h3>Identificación de la fila</h3><dl className="stored-location">
      {fields.filter(field => identityNames.has(field.name)).map(field => <div key={field.name}><dt>{columnLabel(field.name)}</dt><dd>{value(field)}</dd></div>)}
    </dl>
    <h3>Estado, contexto y fuentes del registro</h3>
    {details.length ? <dl className="stored-location">{details.map(field => <div key={field.name}>
      <dt>{columnLabel(field.name)}<code className="column-technical-name">{field.name}</code></dt><dd>{value(field)}</dd>
    </div>)}</dl> : <p>Esta tabla no conserva columnas adicionales de estado o archivo por fila. Puedes consultar la transformación y la procedencia del valor.</p>}
    <p>«Válida» indica si la observación se aceptó; «Estado» conserva el detalle de calidad. Un guion indica un dato ausente, no un «No».</p>
    <h3>Dónde se conserva</h3><dl className="stored-location"><div><dt>Tabla tratada · {table.format}</dt><dd><code>{table.local}</code></dd></div>
      <div><dt>Transformación</dt><dd><code>{table.mapper}</code></dd></div></dl>
    <p>El archivo de origen es el contenedor descargado y el archivo dentro del ZIP identifica su contenido concreto. Son datos de auditoría.</p>
    {measurement && <button className="trace-value-link" onClick={() => onInspect({ row: row.position, column: measurement.name })}>
      Ver fuentes y transformación de {columnLabel(measurement.name)}</button>}
  </dialog>;
}
