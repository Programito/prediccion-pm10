import type { Territory as TerritoryId } from './chart-selection';
import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader } from './api';
import './window-ablation.css';

interface Metric { cohorte: string; modelo: string; n: number; mae: number; rmse: number; sesgo: number }
interface Territory {
  id: string; name: string;
  counts: { train_common: number; train_expanded: number; validation_common: number; validation_additional: number; validation_expanded: number; calendar_validation: number };
  coverage: { station: string; name: string; calendar: number; common: number; additional: number; expanded: number; trainingCommon: number; trainingExpanded: number }[];
  metrics: Metric[]; sampleLevels: { cohort: string; n: number; elevated: number }[];
  maxTrainingDate: string; maxValidationDate: string; originalValidationMatches: boolean;
  sources: { path: string; sha256: string }[];
}
interface Report { train: string; validation: string; models: Record<string,string>; experiments: Territory[]; interpretation: string; originalArtifactsUnchanged: boolean }
const number = new Intl.NumberFormat('es-ES',{ maximumFractionDigits:3 });
const percent = new Intl.NumberFormat('es-ES',{ style:'percent',maximumFractionDigits:1 });
const signed = new Intl.NumberFormat('es-ES',{ maximumFractionDigits:3,signDisplay:'exceptZero' });
const ORDER=['ridge_actual','ridge_sin14_mismo_train','ridge_sin14_train_ampliado','persistencia'];

export function WindowAblation({ loadJson, territory }: { loadJson: JsonLoader; territory: TerritoryId }) {
  const [result,setResult]=useState<{data?:Report;error?:string}>();
  const [cohort,setCohort]=useState('comun');
  useEffect(()=>{
    const controller=new AbortController();
    loadJson<Report>('/api/experiments/window-ablation',controller.signal)
      .then(data=>{if(!controller.signal.aborted)setResult({data});})
      .catch((error:unknown)=>{if(!controller.signal.aborted)setResult({error:errorMessage(error)});});
    return ()=>controller.abort();
  },[loadJson]);
  if(!result)return <p role="status">Cargando comparación de ventanas…</p>;
  if(!result.data)return <p role="alert">{result.error}</p>;
  const data=result.data;
  const experiment=data.experiments.find(item=>item.id===territory)!;
  const rows=ORDER.map(model=>experiment.metrics.find(row=>row.cohorte===cohort&&row.modelo===model)).filter((row):row is Metric=>row!==undefined);
  const maximum=Math.max(1,...rows.map(row=>row.mae));
  const counts=experiment.counts;
  const common=(model:string)=>experiment.metrics.find(row=>row.cohorte==='comun'&&row.modelo===model)!;
  const variableDelta=common('ridge_sin14_mismo_train').mae-common('ridge_actual').mae;
  const trainingDelta=common('ridge_sin14_train_ampliado').mae-common('ridge_sin14_mismo_train').mae;
  const sample=experiment.sampleLevels.find(row=>row.cohort===cohort)!;
  return <div className="workspace window-ablation">
    <section className="panel chart-card" aria-labelledby="window-title"><h2 id="window-title">¿Qué cambia al retirar la media de 14 días?</h2>
      <p>Entrenamiento {data.train} y validación {data.validation}. Se comparan las mismas variables salvo media_14_dias, con Ridge y los mismos parámetros. Las ventanas restantes necesitan hasta siete días completos; no se imputan ausencias.</p>
      <dl className="coverage-totals"><div><dt>Casos originales de validación</dt><dd>{number.format(counts.validation_common)}</dd></div>
        <div><dt>Casos evaluables adicionales</dt><dd>{number.format(counts.validation_additional)}</dd></div>
        <div><dt>Casos con la variante</dt><dd>{number.format(counts.validation_expanded)}</dd></div>
        <div><dt>Cobertura del calendario</dt><dd className="window-rate">{percent.format(counts.validation_common/counts.calendar_validation)} → {percent.format(counts.validation_expanded/counts.calendar_validation)}</dd></div></dl>
      <p>Son casos con objetivo observado y entradas completas según cada conjunto de variables. No equivalen a disponibilidad operativa verificada de las fuentes.</p>
    </section>
    <section className="panel chart-card"><h2>Tres diseños para separar los efectos</h2>
      <div className="table-scroll"><table className="values"><thead><tr><th>Diseño</th><th>Variables numéricas</th><th>Filas de entrenamiento</th><th>Qué permite comparar</th></tr></thead><tbody>
        <tr><th scope="row">A · Ridge actual congelado</th><td>Las 12 originales</td><td>{counts.train_common}</td><td>Referencia original</td></tr>
        <tr><th scope="row">B · Sin media de 14 días</th><td>Las 11 restantes</td><td>{counts.train_common}</td><td>B frente a A: efecto de retirar la variable con el mismo entrenamiento</td></tr>
        <tr><th scope="row">C · Sin media de 14 días, más entrenamiento</th><td>Las mismas 11 de B</td><td>{counts.train_expanded}</td><td>C frente a B: efecto de ampliar el entrenamiento, manteniendo las variables</td></tr>
      </tbody></table></div>
      <p>Sobre las {counts.validation_common} filas comunes, el cambio de MAE de B menos A es <strong>{signed.format(variableDelta)} µg/m³</strong> y el de C menos B es <strong>{signed.format(trainingDelta)} µg/m³</strong>. Son diferencias descriptivas de validación.</p>
    </section>
    <section className="panel chart-card"><h2>Precisión y disponibilidad por separado</h2>
      <label className="window-picker">Cohorte de validación <select value={cohort} onChange={event=>setCohort(event.target.value)}>
        <option value="comun">Filas comunes · Comparación de precisión</option><option value="adicional">Solo casos adicionales · Disponibilidad recuperada</option><option value="ampliada">Todas las filas de la variante</option>
      </select></label>
      <p role="status">{sample.n} casos de 2023, {sample.elevated} por encima de 27 µg/m³.</p>
      <p>{cohort==='comun'?'Todos los modelos se evalúan en las mismas estaciones, fechas y objetivos.':'El modelo original no tiene todos sus predictores en los casos adicionales. Compara las variantes con persistencia sobre esta cohorte; su MAE no es directamente comparable con el del modelo original en otra muestra.'}</p>
      <div className="table-scroll"><table className="values"><caption>Métricas en 2023 · Error y sesgo en µg/m³</caption><thead><tr><th>Modelo</th><th>Casos</th><th>MAE</th><th>RMSE</th><th>Sesgo</th></tr></thead><tbody>
        {rows.map(row=><tr key={row.modelo}><th scope="row">{data.models[row.modelo]}</th><td>{row.n}</td><td>{number.format(row.mae)}</td><td>{number.format(row.rmse)}</td><td>{signed.format(row.sesgo)}</td></tr>)}
      </tbody></table></div>
      <div className="window-error-bars" aria-label="MAE de los modelos en la cohorte seleccionada">{rows.map(row=><div key={row.modelo}><span>{data.models[row.modelo]}</span><i aria-hidden="true"><b className={row.modelo} style={{width:100*row.mae/maximum+'%'}}/></i><strong>{number.format(row.mae)}</strong></div>)}</div>
      {!rows.length&&<p>No hay casos en esta cohorte.</p>}
    </section>
    <section className="panel chart-card"><h2>Casos recuperados por estación</h2>
      <div className="table-scroll"><table className="values"><caption>Validación de 2023</caption><thead><tr><th>Estación</th><th>Calendario</th><th>Comunes</th><th>Adicionales</th><th>Variante completa</th><th>Entrenamiento original</th><th>Entrenamiento ampliado</th></tr></thead><tbody>{experiment.coverage.map(row=><tr key={row.station}><th scope="row">{row.name}<span className="column-type">{row.station}</span></th><td>{row.calendar}</td><td>{row.common}</td><td>{row.additional}</td><td>{row.expanded}</td><td>{row.trainingCommon}</td><td>{row.trainingExpanded}</td></tr>)}</tbody></table></div>
    </section>
    <section className="panel chart-card"><h2>Alcance de la conclusión</h2>
      <p>Más casos evaluables pueden venir acompañados de un pequeño aumento del error en las filas comunes. La media del conjunto ampliado también cambia porque incorpora fechas diferentes.</p>
      <p>Este análisis se planteó tras conocer la auditoría de 2024 y utiliza un año ya empleado para validar. No constituye una nueva prueba independiente ni demuestra que diferencias pequeñas sean estadísticamente sólidas.</p>
      <p>{data.interpretation}</p>
      <p>Último objetivo de entrenamiento: {experiment.maxTrainingDate}. Último objetivo de validación: {experiment.maxValidationDate}. Referencia original contrastada con sus predicciones guardadas: {experiment.originalValidationMatches?'sí':'no'}. Integridad de modelos y pruebas originales: {data.originalArtifactsUnchanged?'verificada':'sin verificar'}.</p>
      <details><summary>Archivos y protocolo</summary><p>Protocolo, predicciones y métricas por cohorte, estación y mes en <code>output/experiments/window_ablation/{experiment.id}/</code>.</p>{experiment.sources.map(source=><p className="experiment-path" key={source.path}><code>{source.path}</code></p>)}</details>
    </section>
  </div>;
}
