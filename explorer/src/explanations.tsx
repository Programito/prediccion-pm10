import { useEffect, useState } from 'react';
import type { CSSProperties } from 'react';
import { errorMessage } from './api';
import type { JsonLoader, ModelExplanation } from './api';
import './explanations.css';

const STATIONS = [
  ['28079060', 'Tres Olivos'],
  ['28080003', 'Majadahonda'],
  ['28133002', 'San Martín de Valdeiglesias'],
];
const LABELS: Record<string, string> = {
  pm10_t: 'PM10 del día previo',
  pm10_t_menos_1: 'PM10 de dos días antes',
  pm10_t_menos_2: 'PM10 de tres días antes',
  pm10_t_menos_6: 'PM10 de una semana antes',
  media_3_dias: 'Media de los últimos 3 días',
  media_7_dias: 'Media de los últimos 7 días',
  media_14_dias: 'Media de los últimos 14 días',
  desviacion_7_dias: 'Variabilidad de los últimos 7 días',
  semana_sin: 'Día de la semana · seno',
  semana_cos: 'Día de la semana · coseno',
  mes_sin: 'Mes · seno',
  mes_cos: 'Mes · coseno',
};
const format = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 3 });
const percent = new Intl.NumberFormat('es-ES', { style: 'percent', maximumFractionDigits: 1 });
const number = (value: number) => format.format(value);

function featureLabel(name: string) {
  const raw = name.replace(/^numeric__/, '');
  if (LABELS[raw]) return LABELS[raw];
  const station = STATIONS.find(([code]) => name === `station__codigo_estacion_${code}`);
  return station ? `Estación · ${station[1]}` : name;
}

function SignedBar({ value, limit }: { value: number; limit: number }) {
  const width = Math.abs(value) / limit * 50;
  const style: CSSProperties = {
    width: `${width}%`,
    left: `${value < 0 ? 50 - width : 50}%`,
  };
  return <span className="signed-bar" aria-hidden="true">
    <i className={value < 0 ? 'negative' : 'positive'} style={style} />
  </span>;
}

function GlobalExplanation({ data }: { data: ModelExplanation }) {
  const coefficients = [...data.features].sort((a, b) => Math.abs(b.coefficient) - Math.abs(a.coefficient));
  const maximum = Math.max(...coefficients.map(row => Math.abs(row.coefficient)), 0.001);
  return <div className="model-charts">
    <section className="panel chart-card" aria-labelledby="ridge-coefficients-title">
      <div className="chart-card-header"><div>
        <h2 id="ridge-coefficients-title">Coeficientes de Ridge</h2>
        <p>Aportación por unidad transformada, en µg/m³. Verde aumenta la predicción y marrón la reduce.</p>
      </div></div>
      <ul className="explanation-bars">
        {coefficients.map(row => <li key={row.name}>
          <span>{featureLabel(row.name)}</span>
          <SignedBar value={row.coefficient} limit={maximum} />
          <strong>{number(row.coefficient)}</strong>
        </li>)}
      </ul>
      <p className="chart-note">Las variables numéricas están estandarizadas con el entrenamiento. Los indicadores de estación valen 0 o 1. Las variables correlacionadas pueden repartirse el peso.</p>
    </section>
    <section className="panel chart-card" aria-labelledby="forest-importance-title">
      <div className="chart-card-header"><div>
        <h2 id="forest-importance-title">Importancia en Random Forest</h2>
        <p>Proporción de la reducción de impureza atribuida a cada variable durante el entrenamiento.</p>
      </div></div>
      <ul className="explanation-bars forest-bars">
        {data.forest.map(row => <li key={row.name}>
          <span>{featureLabel(row.name)}</span>
          <i className="metric-track" aria-hidden="true"><span style={{ width: `${100 * row.importance}%` }} /></i>
          <strong>{percent.format(row.importance)}</strong>
        </li>)}
      </ul>
      <p className="chart-note">Mayor importancia indica más uso en las divisiones de los árboles. Este indicador puede favorecer ciertas variables y repartir peso entre variables correlacionadas. Su valor expresa magnitud y carece de signo.</p>
    </section>
  </div>;
}

function LocalExplanation({ data, onDate }: { data: ModelExplanation; onDate: (date: string) => void }) {
  const current = data.case;
  const maximum = Math.max(...current.contributions.map(Math.abs), 0.001);
  const rows = data.features.map((feature, index) => ({
    ...feature,
    contribution: current.contributions[index],
    transformed: current.transformed[index],
  })).sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution));
  const sum = current.contributions.reduce((total, value) => total + value, 0);
  return <section className="panel chart-card" aria-labelledby="local-explanation-title">
    <div className="chart-card-header"><div>
      <h2 id="local-explanation-title">Cómo se construye una predicción de Ridge</h2>
      <p>La aportación de cada variable es su valor transformado multiplicado por su coeficiente.</p>
    </div><div className="chart-controls">
      <label>Fecha explicada <select value={current.date} onChange={event => onDate(event.target.value)}>
        {data.dates.map(date => <option key={date}>{date}</option>)}
      </select></label>
    </div></div>
    <div className="chart-overview" aria-live="polite">
      <span>Observado <strong>{number(current.observed)} µg/m³</strong></span>
      <span>Predicción <strong>{number(current.prediction)} µg/m³</strong></span>
      <span>Error absoluto <strong>{number(Math.abs(current.prediction - current.observed))} µg/m³</strong></span>
    </div>
    <p className="prediction-equation">
      Base {number(data.intercept)} + aportaciones ({number(sum)}) = {number(current.rawPrediction)} µg/m³
    </p>
    {current.rawPrediction < 0 && <p className="chart-note">El resultado se limita a cero al aplicar la restricción de concentración no negativa.</p>}
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Aportaciones de las variables de Ridge">
      <table className="contribution-table">
        <thead><tr><th scope="col">Variable</th><th scope="col">Entrada</th><th scope="col">Valor transformado</th><th scope="col">Coeficiente</th><th scope="col">Aportación (µg/m³)</th></tr></thead>
        <tbody>{rows.map(row => {
          const isNumeric = row.name.startsWith('numeric__');
          const input = isNumeric ? current.inputs[row.name.replace(/^numeric__/, '')] : row.transformed;
          return <tr key={row.name}>
            <th scope="row">{featureLabel(row.name)}</th>
            <td>{number(input)}</td><td>{number(row.transformed)}</td><td>{number(row.coefficient)}</td>
            <td><div className="contribution-value"><SignedBar value={row.contribution} limit={maximum} /><strong>{number(row.contribution)}</strong></div></td>
          </tr>;
        })}</tbody>
      </table>
    </div>
    <p className="chart-note">La base es el intercepto. La explicación reconstruye la predicción antes de limitarla a cero. Los valores mostrados están redondeados a tres decimales.</p>
  </section>;
}

export function ModelExplanations({ loadJson, station, date, onDate }: {
  loadJson: JsonLoader; station: string; date: string; onDate: (date: string) => void;
}) {
  const [result, setResult] = useState<{ query: string; data?: ModelExplanation; error?: string }>();
  const parameters = new URLSearchParams({ station });
  if (date) parameters.set('date', date);
  const query = `/api/charts/explanations?${parameters}`;
  useEffect(() => {
    const controller = new AbortController();
    loadJson<ModelExplanation>(query, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ query, data }); })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult({ query, error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [query, loadJson]);
  const current = result?.query === query ? result : undefined;
  return <div className="workspace">
    <section className="panel chart-card" aria-labelledby="model-explanation-title">
      <div className="chart-card-header"><div>
        <h2 id="model-explanation-title">Explicabilidad de los modelos</h2>
        <p>Modelos entrenados hasta 2022 y comparados en 2023. Las explicaciones locales corresponden a Ridge en la prueba de 2024.</p>
      </div></div>
      <p className="chart-note">Las aportaciones y las importancias describen el funcionamiento de cada modelo. Las mediciones recientes, las medias y los retardos están relacionados entre sí. La interpretación requiere considerar esa dependencia.</p>
    </section>
    {current?.data ? <>
      <LocalExplanation data={current.data} onDate={onDate} />
      <GlobalExplanation data={current.data} />
    </> : current?.error ? <p role="alert">{current.error}</p> : <p role="status">Cargando explicación…</p>}
  </div>;
}
