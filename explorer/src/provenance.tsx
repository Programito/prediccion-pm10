import { useEffect, useRef, useState } from 'react';
import { errorMessage } from './api';
import type { Cell, JsonLoader, Provenance, ProvenanceSource, SelectedCell } from './api';

export function displayValue(value: Cell | undefined) {
  return Array.isArray(value) ? value.join(' – ') : value == null ? '—' : String(value);
}

function SourceEvidence({ source }: { source: ProvenanceSource }) {
  return <li>
    {source.label && <strong>{source.label}</strong>}{source.format && <span className="tag">{source.format}</span>}
    {source.file && <code>{source.file}</code>}
    {source.container && <span>Contenedor {source.container}</span>}
    {source.member && <span>Archivo interno <code>{source.member}</code></span>}
    {source.sheet && <span>Hoja <code>{source.sheet}</code></span>}
    {source.byteRange && <span>Rango {displayValue(source.byteRange)} bytes</span>}
    {source.url && (source.byteRange ? <span className="provenance-url">{source.url}</span> : <a href={source.url} target="_blank" rel="noreferrer">Ver descarga original ↗</a>)}
    {source.indexUrl && <a href={source.indexUrl} target="_blank" rel="noreferrer">Ver índice del fichero GRIB2 ↗</a>}
  </li>;
}

export function ProvenanceDialog({ tableId, selected, loadJson, onClose }: {
  tableId: string;
  selected: SelectedCell;
  loadJson: JsonLoader;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [result, setResult] = useState<{ data?: Provenance; error?: string }>({});
  useEffect(() => {
    dialog.current?.showModal();
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ row: String(selected.row), column: selected.column });
    loadJson<Provenance>(`/api/tables/${tableId}/provenance?${params}`, controller.signal).then(data => setResult({ data }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult({ error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [loadJson, selected, tableId]);
  const data = result.data;
  const stored = data?.stored;
  return <dialog ref={dialog} className="provenance-dialog" aria-labelledby="origin-title" onClose={onClose}>
    <div className="provenance-header"><div><p className="eyebrow">Trazabilidad de datos</p><h2 id="origin-title">Procedencia del valor</h2></div>
      <button type="button" aria-label="Cerrar procedencia" onClick={() => dialog.current?.close()}>×</button></div>
    {result.error ? <p role="alert">{result.error}</p> : !data || !stored ? <p role="status">Buscando su procedencia…</p> : <>
      <div className="current-value"><code>{data.column}</code><strong>{displayValue(data.value)}</strong><span className="tag">{data.description.type}</span>
        <p>{data.description.notes}</p></div>
      <h3>Dónde está guardado</h3>
      <dl className="stored-location">
        <div><dt>Formato</dt><dd>{stored.container ? `${stored.container} → ${stored.format}` : stored.format}</dd></div>
        <div><dt>Archivo local</dt><dd><code>{stored.file}</code></dd></div>
        <div><dt>Almacenamiento</dt><dd>{data.description.storage}</dd></div>
        {stored.member && <div><dt>Archivo dentro del ZIP</dt><dd><code>{stored.member}</code></dd></div>}
        {stored.sheet && <div><dt>Hoja de Excel</dt><dd>{stored.sheet}</dd></div>}
        {stored.cell ? <div><dt>Celda de Excel</dt><dd>{stored.cell}</dd></div> : <div><dt>Posición en la tabla</dt><dd>Registro {stored.position}</dd></div>}
      </dl>
      <h3>De dónde sale</h3><p>{data.rule}</p>
      {!!data.sources.length && <ul className="evidence">{data.sources.map((source, index) => <SourceEvidence source={source} key={index} />)}</ul>}
    </>}
  </dialog>;
}
