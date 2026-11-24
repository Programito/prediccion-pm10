import type { Territory as TerritoryId } from './chart-selection';
import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader } from './api';
import './grouped-permutation.css';

interface Importance {
  group:string; label:string; features:string[]; kind:'primary'|'sensitivity'; method:string;
  repetitions:number; mean:number; median:number; std:number|null; minimum:number; maximum:number; meanPermutedMae:number;
}
interface Territory {
  id:string; name:string; n:number; baselineMae:number; seed:number; minimumShiftRows:number;
  rows:Importance[]; stations:{code:string;name:string;n:number}[];
  stationMappings:{repetition:number;mapping:Record<string,string>}[];
  referenceFeatures:{ridge:{variable_transformada:string;coeficiente:number}[];forest:{variable_transformada:string;importancia_impureza:number}[]};
}
interface Report {year:number;repeats:number;experiments:Territory[];limitations:string[];originalArtifactsUnchanged:boolean}
const number=new Intl.NumberFormat('es-ES',{maximumFractionDigits:3});
const signed=new Intl.NumberFormat('es-ES',{maximumFractionDigits:3,signDisplay:'exceptZero'});
const percent=new Intl.NumberFormat('es-ES',{style:'percent',maximumFractionDigits:1});

export function GroupedPermutation({ loadJson, territory }: { loadJson: JsonLoader; territory: TerritoryId }) {
  const [result,setResult]=useState<{data?:Report;error?:string}>();
  const [joint,setJoint]=useState(false);
  useEffect(()=>{
    const controller=new AbortController();
    loadJson<Report>('/api/experiments/grouped-permutation',controller.signal)
      .then(data=>{if(!controller.signal.aborted)setResult({data});})
      .catch((error:unknown)=>{if(!controller.signal.aborted)setResult({error:errorMessage(error)});});
    return ()=>controller.abort();
  },[loadJson]);
  if(!result)return <p role="status">Cargando importancia por permutación…</p>;
  if(!result.data)return <p role="alert">{result.error}</p>;
  const data=result.data;
  const experiment=data.experiments.find(item=>item.id===territory)!;
  const rows=experiment.rows.filter(row=>row.kind==='primary'||joint).sort((a,b)=>b.mean-a.mean);
  const minimum=Math.min(0,...rows.map(row=>row.minimum));
  const maximum=Math.max(0,...rows.map(row=>row.maximum));
  const extent=Math.max(maximum-minimum,.001);
  const low=minimum-.05*extent;
  const high=maximum+.05*extent;
  const x=(value:number)=>100*(value-low)/(high-low);
  return <div className="workspace permutation-workspace">
    <section className="panel chart-card" aria-labelledby="permutation-title">
      <h2 id="permutation-title">¿De qué grupos de variables depende Ridge?</h2>
      <p>Modelos originales congelados, ajustados hasta 2022. Se altera un grupo cada vez en las filas originales de validación de {data.year}, sin cambiar sus objetivos ni reajustar el modelo.</p>
      <dl className="coverage-totals"><div><dt>Casos de validación</dt><dd>{experiment.n}</dd></div><div><dt>MAE original</dt><dd>{number.format(experiment.baselineMae)} <small>µg/m³</small></dd></div><div><dt>Alteraciones por grupo numérico</dt><dd>{data.repeats}</dd></div><div><dt>Rotaciones de etiquetas de estación</dt><dd>{experiment.stationMappings.length}</dd></div></dl>
      <p>La importancia es MAE alterado menos MAE original, en µg/m³. Un valor positivo significa más error al alterar el grupo. Un valor negativo significa que esa alteración concreta reduce el error; no basta para decidir eliminar variables.</p>
    </section>
    <section className="panel chart-card"><h2>Aumento del error al alterar cada grupo</h2>
      <label className="permutation-toggle"><input type="checkbox" checked={joint} onChange={event=>setJoint(event.target.checked)}/> Mostrar sensibilidad conjunta del historial</label>
      <div className="permutation-bars" aria-label="Diferencias de MAE por grupo">{rows.map(row=><div key={row.group} className={row.kind==='sensitivity'?'permutation-joint':''}>
        <span>{row.label}{row.kind==='sensitivity'&&<small>Se solapa con los grupos de retardos y medias</small>}</span>
        <div className="permutation-track" aria-hidden="true">
          <i className="permutation-zero" style={{left:x(0)+'%'}}/>
          <i className="permutation-range" style={{left:x(row.minimum)+'%',width:x(row.maximum)-x(row.minimum)+'%'}}/>
          <i className="permutation-mean-bar" style={{left:Math.min(x(0),x(row.mean))+'%',width:Math.abs(x(row.mean)-x(0))+'%'}}/>
          <i className="permutation-dot" style={{left:x(row.mean)+'%'}}/>
        </div><strong>{signed.format(row.mean)}</strong>
      </div>)}</div>
      <p className="chart-note">Punto y barra: aumento medio de MAE. Línea horizontal: mínimo y máximo entre alteraciones. La referencia vertical marca cero. El rango describe estas alteraciones y no es un intervalo de confianza.</p>
      <div className="table-scroll"><table className="values"><caption>Importancia agrupada en {data.year} · µg/m³</caption><thead><tr><th>Grupo</th><th>Alteraciones</th><th>MAE alterado medio</th><th>Aumento medio</th><th>Mínimo</th><th>Máximo</th><th>Desviación entre alteraciones</th></tr></thead><tbody>
        {rows.map(row=><tr key={row.group}><th scope="row">{row.label}</th><td>{row.repetitions}</td><td>{number.format(row.meanPermutedMae)}</td><td>{signed.format(row.mean)}</td><td>{signed.format(row.minimum)}</td><td>{signed.format(row.maximum)}</td><td>{row.std===null?'—':number.format(row.std)}</td></tr>)}
      </tbody></table></div>
      <p>Los grupos comparten información y los aumentos no se suman. La sensibilidad conjunta desplaza los ocho predictores históricos a la vez para conservar sus relaciones dentro de la fila; no es un quinto grupo independiente.</p>
    </section>
    <section className="panel chart-card"><h2>Cómo se alteran las entradas</h2>
      <p>Los grupos numéricos se desplazan circularmente dentro de cada estación, manteniendo juntas sus columnas y el orden de la secuencia salvo el punto de cierre. Cada desplazamiento separa al menos {experiment.minimumShiftRows} posiciones evaluables. Las filas pueden tener saltos: no equivale a {experiment.minimumShiftRows} días naturales.</p>
      <p>Una alteración puede colocar datos de una fecha posterior a la del objetivo. Es una perturbación artificial para interpretar el modelo; no se usa para entrenar ni representa una predicción temporal realizable.</p>
      <p>Se usan los mismos desplazamientos para todos los grupos numéricos de una repetición. Las etiquetas de estación se sustituyen de forma coherente en toda su serie mediante las dos rotaciones sin identidad de los tres códigos. Es un diagnóstico distinto al desplazamiento temporal.</p>
      <details><summary>Variables, estaciones y reproducibilidad</summary>
        <p>Semilla: {experiment.seed}. Se conservan las mismas {experiment.n} filas y objetivos en todas las alteraciones.</p>
        <div className="table-scroll"><table className="values"><thead><tr><th>Grupo</th><th>Variables</th></tr></thead><tbody>{experiment.rows.map(row=><tr key={row.group}><th scope="row">{row.label}</th><td className="permutation-fields">{row.features.join(', ')}</td></tr>)}</tbody></table></div>
        <p>{experiment.stations.map(station=>station.name+' ('+station.code+'): '+station.n+' filas').join(' · ')}</p>
        {experiment.stationMappings.map(item=><p key={item.repetition}>Rotación {item.repetition}: {Object.entries(item.mapping).map(([from,to])=>from+' → '+to).join(', ')}</p>)}
        <p>Protocolos, resultados, repeticiones y desplazamientos en <code>output/experiments/grouped_permutation/{experiment.id}/</code>.</p>
      </details>
    </section>
    <section className="panel chart-card"><h2>Comparar con coeficientes e importancias existentes</h2>
      <p>La permutación mide cambio de error de Ridge en validación. Los coeficientes describen su función ajustada y las importancias de Random Forest describen reducción de impureza durante el entrenamiento de otro modelo. Sus unidades y significados difieren.</p>
      <details><summary>Ver coeficientes de Ridge e importancias de Random Forest</summary>
        <p>Las entradas numéricas de Ridge están estandarizadas con entrenamiento. Sus indicadores de estación toman valores cero o uno. La colinealidad puede repartir peso entre variables.</p>
        <div className="permutation-reference-grid"><div className="table-scroll"><table className="values"><caption>Coeficientes del Ridge original</caption><thead><tr><th>Variable transformada</th><th>Coeficiente</th></tr></thead><tbody>{experiment.referenceFeatures.ridge.map(row=><tr key={row.variable_transformada}><th scope="row">{row.variable_transformada}</th><td>{signed.format(row.coeficiente)}</td></tr>)}</tbody></table></div>
          <div className="table-scroll"><table className="values"><caption>Importancia por impureza del bosque original</caption><thead><tr><th>Variable transformada</th><th>Importancia</th></tr></thead><tbody>{experiment.referenceFeatures.forest.map(row=><tr key={row.variable_transformada}><th scope="row">{row.variable_transformada}</th><td>{percent.format(row.importancia_impureza)}</td></tr>)}</tbody></table></div></div>
      </details>
    </section>
    <section className="panel chart-card"><h2>Límites de esta interpretación</h2><ul className="experiment-limits">{data.limitations.map(text=><li key={text}>{text}.</li>)}</ul>
      <p>Integridad de modelos y pruebas originales: {data.originalArtifactsUnchanged?'verificada':'sin verificar'}. No se atribuyen causas ni se promueve un nuevo modelo con estos resultados.</p>
    </section>
  </div>;
}
