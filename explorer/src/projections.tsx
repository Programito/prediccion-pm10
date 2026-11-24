import { useEffect, useRef, useState } from 'react';
import type { JsonLoader } from './api';
import { errorMessage } from './api';
import './projections.css';

interface Point { station: string; name: string; date: string; partition: string; elevated: number; x: number; y: number }
interface Metric { modelo: string; contexto?: string; n: number; vp: number; fp: number; fn: number; vn: number;
  positivos: number; precision: number | null; recall: number | null; f1: number | null }
interface Report {
  protocol: { pcaTraining: string; ldaTraining: string; validation: number; threshold: number;
    falseAlarmBudget: number; pcaTrainingRows: number; pcaValidationRows: number; ldaTrainingRows: number;
    ldaValidationRows: number; sourceHashes: Record<string, string> };
  pca: { components90: number; components: { component: number; ratio: number; cumulative: number }[];
    weights: ({ feature: string; mean: number; scale: number } & Record<string, string | number>)[]; points: Point[] };
  lda: { model: string; features: string[]; cut: number; points: Point[] }[];
  metrics: Metric[]; contextMetrics: Metric[];
  ranking: { model: string; rocAuc: number; averagePrecision: number }[];
  logisticCuts: Record<string, number>;
}
const number = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 1 });
const signed = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3, signDisplay: 'always' });
const fmt = (value: number | null) => value === null ? 'No definido' : number.format(value);
const modelName = (name: string) => ({ lda_con_meteo: 'LDA con meteorología', lda_sin_meteo: 'LDA sin meteorología',
  logistica_con_meteo: 'Logística con meteorología', logistica_sin_meteo: 'Logística sin meteorología', persistencia: 'Persistencia' })[name] ?? name;

function Scatter({ points }: { points: Point[] }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !points.length) return;
    const draw = () => {
      const width = canvas.getBoundingClientRect().width, height = 340;
      const ratio = window.devicePixelRatio || 1;
      canvas.width = width * ratio; canvas.height = height * ratio;
      const ctx = canvas.getContext('2d'); if (!ctx) return;
      ctx.scale(ratio, ratio);
      const minX = Math.min(...points.map(p => p.x)), maxX = Math.max(...points.map(p => p.x));
      const minY = Math.min(...points.map(p => p.y)), maxY = Math.max(...points.map(p => p.y));
      const x = (v: number) => 60 + (v - minX) / (maxX - minX || 1) * (width - 85);
      const y = (v: number) => height - 45 - (v - minY) / (maxY - minY || 1) * (height - 70);
      ctx.font = '12px sans-serif'; ctx.fillStyle = '#52615c';
      for (let i = 0; i <= 4; i++) {
        const vx = minX + (maxX - minX) * i / 4, vy = minY + (maxY - minY) * i / 4;
        ctx.strokeStyle = '#e1e8e4'; ctx.beginPath(); ctx.moveTo(60, y(vy)); ctx.lineTo(width - 25, y(vy)); ctx.stroke();
        ctx.fillText(number.format(vy), 4, y(vy) + 4); ctx.fillText(number.format(vx), x(vx) - 14, height - 23);
      }
      ctx.fillText('PC1', width - 35, height - 4); ctx.fillText('PC2', 4, 14);
      // Draw elevated days last so the minority class remains visible.
      for (const label of [0, 1]) for (const p of points.filter(p => p.elevated === label)) {
        ctx.fillStyle = label ? '#ad4f16' : '#246d7e'; ctx.globalAlpha = label ? .85 : .32;
        ctx.beginPath(); if (label) ctx.rect(x(p.x) - 3, y(p.y) - 3, 6, 6); else ctx.arc(x(p.x), y(p.y), 2.5, 0, 2 * Math.PI); ctx.fill();
      }
      ctx.globalAlpha = 1;
    };
    const observer = new ResizeObserver(draw); observer.observe(canvas); draw();
    return () => observer.disconnect();
  }, [points]);
  return <canvas ref={ref} className="projection-scatter" aria-hidden="true" />;
}

function PointTable({ points, lda }: { points: Point[]; lda: boolean }) {
  const [page, setPage] = useState(0);
  const last = Math.max(0, Math.ceil(points.length / 15) - 1);
  const current = Math.min(page, last);
  return <details><summary>Consultar las {points.length} proyecciones en tabla</summary>
    <div className="table-scroll"><table className="values"><caption>Coordenadas sin unidades de concentración · 15 filas por página</caption>
      <thead><tr><th>Estación</th><th>Fecha objetivo</th><th>Elevado</th><th>{lda ? 'LD1' : 'PC1'}</th>{!lda && <th>PC2</th>}</tr></thead>
      <tbody>{points.slice(current * 15, current * 15 + 15).map(p => <tr key={p.station + p.date}><th scope="row">{p.name}</th><td>{p.date}</td>
        <td>{p.elevated ? 'Sí' : 'No'}</td><td>{fmt(p.x)}</td>{!lda && <td>{fmt(p.y)}</td>}</tr>)}</tbody></table></div>
    <div className="projection-pagination"><button disabled={!current} onClick={() => setPage(current - 1)}>Página anterior</button>
      <span role="status">Página {current + 1} de {last + 1}</span><button disabled={current === last} onClick={() => setPage(current + 1)}>Página siguiente</button></div>
  </details>;
}

function Projection({ points, lda }: { points: Point[]; lda: boolean }) {
  const [partition, setPartition] = useState('validation');
  const [station, setStation] = useState('all');
  const visible = points.filter(p => p.partition === partition && (station === 'all' || p.station === station));
  const stations = [...new Map(points.map(p => [p.station, p.name])).entries()];
  const minimum = Math.min(...visible.map(p => p.x)), maximum = Math.max(...visible.map(p => p.x));
  const width = (maximum - minimum || 1) / 20;
  const bins = Array.from({ length: 20 }, (_, i) => ({ start: minimum + i * width, end: minimum + (i + 1) * width,
    counts: [0, 1].map(label => visible.filter(p => p.elevated === label && Math.min(19, Math.floor((p.x - minimum) / width)) === i).length) }));
  const totals = [0, 1].map(label => visible.filter(p => p.elevated === label).length);
  const maxShare = Math.max(.001, ...bins.flatMap(bin => bin.counts.map((count, i) => count / (totals[i] || 1))));
  return <section className="panel chart-card"><h2>{lda ? 'Separación en un único eje: LD1' : 'Proyección sobre PC1 y PC2'}</h2>
    <div className="projection-controls"><label>Periodo mostrado <select value={partition} onChange={event => setPartition(event.target.value)}>
      <option value="validation">Validación de 2023</option><option value="training">Entrenamiento</option></select></label>
      <label>Estación de la proyección <select value={station} onChange={event => setStation(event.target.value)}><option value="all">Todas las estaciones</option>
        {stations.map(([code, name]) => <option key={code} value={code}>{name}</option>)}</select></label></div>
    <p>{visible.length} filas mostradas. Las etiquetas colorean el gráfico; PCA no las utiliza al ajustar. LDA sí utiliza las etiquetas de entrenamiento.</p>
    <div className="projection-legend"><span><i className="projection-low" />● No elevado: {totals[0]}</span><span><i className="projection-high" />■ Elevado: {totals[1]}</span></div>
    {lda ? <><p>Dos clases permiten una sola dimensión discriminante. Cada barra representa la proporción de su clase dentro del intervalo; las clases tienen tamaños distintos.</p>
      <div className="projection-histogram" role="img" aria-label="Distribuciones de ambas clases sobre LD1; frecuencias y límites disponibles en la tabla siguiente">
        {bins.map((bin, i) => <div key={i}>{bin.counts.map((count, label) => <i key={label} className={label ? 'projection-high' : 'projection-low'}
          style={{ height: `${100 * count / (totals[label] || 1) / maxShare}%` }} />)}</div>)}</div>
      <div className="projection-axis"><span>{fmt(minimum)}</span><span>LD1 · coordenada sin unidades</span><span>{fmt(maximum)}</span></div>
      <details><summary>Frecuencias de las distribuciones</summary><div className="table-scroll"><table className="values"><thead><tr><th>Inicio incluido</th><th>Fin</th><th>No elevados</th><th>Elevados</th><th>% no elevados</th><th>% elevados</th></tr></thead>
        <tbody>{bins.map((bin, i) => <tr key={i}><th scope="row">{fmt(bin.start)}</th><td>{fmt(bin.end)}{i === 19 ? ' (incluido)' : ' (excluido)'}</td>
          <td>{bin.counts[0]}</td><td>{bin.counts[1]}</td><td>{percent.format(bin.counts[0] / (totals[0] || 1))}</td><td>{percent.format(bin.counts[1] / (totals[1] || 1))}</td></tr>)}</tbody></table></div></details></>
      : <><Scatter points={visible} /><p className="chart-note">Cada punto es una estación y fecha objetivo. PC1 y PC2 son combinaciones de entradas estandarizadas, sin unidades de concentración. Su signo es convencional; la separación visual no es una métrica predictiva.</p></>}
    <PointTable key={partition + station} points={visible} lda={lda} />
  </section>;
}

export function Projections({ loadJson }: { loadJson: JsonLoader }) {
  const [result, setResult] = useState<{ data?: Report; error?: string }>();
  const [view, setView] = useState('pca');
  const [component, setComponent] = useState('PC1');
  const [ldaModel, setLdaModel] = useState('lda_con_meteo');
  useEffect(() => {
    const controller = new AbortController();
    loadJson<Report>('/api/experiments/projections', controller.signal).then(data => { if (!controller.signal.aborted) setResult({ data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ error: errorMessage(error) }); });
    return () => controller.abort();
  }, [loadJson]);
  if (!result) return <p role="status">Cargando PCA y LDA…</p>;
  if (!result.data) return <p role="alert">{result.error}</p>;
  const data = result.data, protocol = data.protocol;
  const selected = data.lda.find(row => row.model === ldaModel)!;
  const downloads = view === 'pca' ? ['pca_componentes.csv', 'pca_pesos.csv', 'pca_proyecciones.csv'] :
    ['metricas.csv', 'metricas_contexto.csv', 'ranking.csv', 'predicciones_validacion_2023.csv', `${ldaModel}_proyecciones.csv`, `${ldaModel}_barrido.csv`];
  return <div className="workspace projections-workspace">
    <section className="panel chart-card"><p className="eyebrow">Madrid · análisis exploratorio</p><h2>PCA y LDA: resumir y separar variables</h2>
      <p>Escalado y transformaciones se ajustan exclusivamente con entrenamiento. La validación de 2023 ya se ha utilizado en el proyecto: estos resultados son exploratorios. No se vuelven a evaluar 2024 ni 2025.</p>
      <nav className="chart-navigation" aria-label="Técnica de proyección"><button aria-pressed={view === 'pca'} onClick={() => setView('pca')}>PCA · componentes principales</button>
        <button aria-pressed={view === 'lda'} onClick={() => setView('lda')}>LDA · análisis discriminante</button></nav>
    </section>
    {view === 'pca' ? <>
      <section className="panel chart-card"><h2>Cuánta variación conserva PCA</h2><p>{protocol.pcaTrainingRows} filas de entrenamiento ({protocol.pcaTraining}); {protocol.pcaValidationRows} de validación (2023). Se utilizan las 12 entradas numéricas de PM10 y calendario, sin identificadores ni PM10 objetivo.</p>
        <p><strong>{data.pca.components90} componentes explican al menos el 90 % de la varianza de entrenamiento.</strong> Las dos primeras conservan {percent.format(data.pca.components[1].cumulative)}. Explicar varianza no equivale a explicar el objetivo ni a mejorar la predicción.</p>
        <div className="projection-scree" aria-hidden="true">{data.pca.components.map(row => <div key={row.component}><span>PC{row.component}</span><i><b style={{ width: `${100 * row.ratio}%` }} /></i><strong>{percent.format(row.ratio)}</strong></div>)}</div>
        <details><summary>Tabla de varianza explicada</summary><table className="values"><thead><tr><th>Componente</th><th>Varianza</th><th>Acumulada</th></tr></thead>
          <tbody>{data.pca.components.map(row => <tr key={row.component}><th scope="row">PC{row.component}</th><td>{percent.format(row.ratio)}</td><td>{percent.format(row.cumulative)}</td></tr>)}</tbody></table></details>
      </section>
      <Projection key="pca" points={data.pca.points} lda={false} />
      <section className="panel chart-card"><h2>Qué variables forman cada componente</h2><label>Componente interpretada <select value={component} onChange={event => setComponent(event.target.value)}>
        {data.pca.components.map(row => <option key={row.component}>PC{row.component}</option>)}</select></label>
        <p>PC = suma de peso × (entrada − media de entrenamiento) / escala de entrenamiento. Los pesos son coeficientes del eje, no porcentajes ni efectos causales.</p>
        <div className="table-scroll"><table className="values"><thead><tr><th>Variable</th><th>Peso en {component}</th><th>Media al ajustar</th><th>Escala al ajustar</th></tr></thead>
          <tbody>{[...data.pca.weights].sort((a, b) => Math.abs(Number(b[component])) - Math.abs(Number(a[component]))).map(row => <tr key={row.feature}><th scope="row">{row.feature}</th>
            <td>{signed.format(Number(row[component]))}</td><td>{fmt(row.mean)}</td><td>{fmt(row.scale)}</td></tr>)}</tbody></table></div>
      </section>
    </> : <>
      <section className="panel chart-card"><h2>LDA frente a la logística y persistencia</h2>
        <p>{protocol.ldaTrainingRows} filas comunes de entrenamiento ({protocol.ldaTraining}) y {protocol.ldaValidationRows} de validación (2023). Ambas variantes LDA usan las mismas entradas que su logística correspondiente, incluida la estación codificada.</p>
        <p>LDA ajusta distribuciones gaussianas por clase con una covarianza compartida. Se regulariza automáticamente esa covarianza para estabilizar variables relacionadas (solver eigen, shrinkage auto). No se ha buscado una configuración óptima.</p>
        <p>El corte de cada LDA se selecciona en 2023 con la regla existente: priorizar comienzos detectados, después positivos, menos falsas alarmas y mayor corte, sin superar las {protocol.falseAlarmBudget} falsas alarmas totales de persistencia. La selección y estas métricas comparten validación y pueden ser optimistas.</p>
        <div className="table-scroll"><table className="values"><caption>Misma muestra de validación · resultado global</caption><thead><tr><th>Modelo</th><th>Corte</th><th>VP</th><th>FP</th><th>FN</th><th>VN</th><th>Precisión</th><th>Recall</th><th>F1</th></tr></thead>
          <tbody>{data.metrics.map(row => <tr key={row.modelo}><th scope="row">{modelName(row.modelo)}</th><td>{row.modelo === 'persistencia' ? 'PM10 previo > 27' : fmt(data.lda.find(m => m.model === row.modelo)?.cut ?? data.logisticCuts[row.modelo])}</td>
            <td>{row.vp}</td><td>{row.fp}</td><td>{row.fn}</td><td>{row.vn}</td><td>{fmt(row.precision)}</td><td>{fmt(row.recall)}</td><td>{fmt(row.f1)}</td></tr>)}</tbody></table></div>
        <p>En esta validación, LDA no mejora a la logística en F1 ni detección global bajo esta regla. Se mantiene como comparación exploratoria; los modelos finales se conservan.</p>
        <p className="chart-note">VP: elevado avisado; FP: aviso sin elevado; FN: elevado sin aviso; VN: no elevado sin aviso. Precisión: proporción de avisos acertados; recall: proporción de elevados detectados; F1: media armónica de precisión y recall.</p>
        <details><summary>Comienzos: cuando el día anterior no era elevado</summary><table className="values"><thead><tr><th>Modelo</th><th>Casos</th><th>Comienzos</th><th>Detectados</th><th>Falsas alarmas</th><th>No detectados</th></tr></thead>
          <tbody>{data.contextMetrics.filter(row => row.contexto === 'hoy_no_elevado').map(row => <tr key={row.modelo}><th scope="row">{modelName(row.modelo)}</th><td>{row.n}</td><td>{row.positivos}</td><td>{row.vp}</td><td>{row.fp}</td><td>{row.fn}</td></tr>)}</tbody></table></details>
        <details><summary>Capacidad de ordenar casos sin fijar un corte</summary><p>ROC AUC mide discriminación; average precision resume precisión y recall por cortes. Su referencia de prevalencia es {percent.format(data.metrics[0].positivos / data.metrics[0].n)}. No son medidas de calibración ni probabilidad de enfermedad.</p>
          <table className="values"><thead><tr><th>Modelo</th><th>ROC AUC</th><th>Average precision</th></tr></thead><tbody>{data.ranking.map(row => <tr key={row.model}><th scope="row">{modelName(row.model)}</th><td>{fmt(row.rocAuc)}</td><td>{fmt(row.averagePrecision)}</td></tr>)}</tbody></table></details>
      </section>
      <section className="panel chart-card"><label>Variante LDA <select value={ldaModel} onChange={event => setLdaModel(event.target.value)}>{data.lda.map(row => <option key={row.model} value={row.model}>{modelName(row.model)}</option>)}</select></label>
        <p>Corte de aviso: {fmt(selected.cut)}; probabilidad ≥ corte. El eje LD1 no es una probabilidad.</p><details><summary>Entradas de esta variante</summary><p>{selected.features.join(', ')}</p></details></section>
      <Projection key={ldaModel} points={selected.points} lda />
    </>}
    <section className="panel chart-card"><h2>Lectura y evidencias</h2><p>Elevado: PM10 objetivo &gt; {protocol.threshold} µg/m³, umbral estadístico. PM10 y retardos: concentraciones; medias y desviación: resúmenes del historial; semana y mes sin/cos: calendario cíclico. PCA busca variación; LDA busca separación usando clases de entrenamiento.</p>
      <p>Solo filas completas, sin nueva imputación ni recorte de picos. Las variables se estandarizan con estadísticas de entrenamiento. Las observaciones temporales pueden estar relacionadas y las clases están desequilibradas. No se ha entrenado una regresión con PCA ni demostrado una mejora predictiva de esa transformación.</p>
      <ul>{[...downloads, 'protocolo.json'].map(file => <li key={file}><a href={'/api/experiments/projections/files/' + file} download>{file}</a></li>)}</ul>
      <details><summary>Archivos de origen y SHA-256</summary>{Object.entries(protocol.sourceHashes).map(([path, hash]) => <p className="experiment-path" key={path}><code>{path}</code><br /><small>{hash}</small></p>)}</details>
      <p className="chart-note">El documento «PCA y LDA en validación» está disponible en Documentación. La probabilidad de un día elevado no equivale a riesgo sanitario.</p>
    </section>
  </div>;
}
