import { useEffect, useState } from 'react';
import { errorMessage } from './api';
import type { JsonLoader, ModelMetrics } from './api';
import { TERRITORIES, TERRITORY_STATIONS } from './chart-selection';
import type { ChartSelection, Territory } from './chart-selection';
import './home.css';

const decimal = new Intl.NumberFormat('es-ES', { maximumFractionDigits: 2 });
const integer = new Intl.NumberFormat('es-ES');

function useSummary<T>(url: string, loadJson: JsonLoader) {
  const [result, setResult] = useState<{ data?: T; error?: string }>({});
  useEffect(() => {
    const controller = new AbortController();
    loadJson<T>(url, controller.signal)
      .then(data => { if (!controller.signal.aborted) setResult({ data }); })
      .catch((error: unknown) => { if (!controller.signal.aborted) setResult({ error: errorMessage(error) }); });
    return () => controller.abort();
  }, [url, loadJson]);
  return result;
}

function RegressionSummary({ territory, result, onCharts }: {
  territory: Territory;
  result: { data?: ModelMetrics; error?: string };
  onCharts: (selection: Partial<ChartSelection>) => void;
}) {
  const rows = result.data?.regression;
  const ridge = rows?.find(row => row.group === 'todos' && row.model === 'ridge');
  const persistence = rows?.find(row => row.group === 'todos' && row.model === 'persistencia');
  const highRidge = rows?.find(row => row.group === 'elevado' && row.model === 'ridge');
  const highPersistence = rows?.find(row => row.group === 'elevado' && row.model === 'persistencia');

  return <article className="panel home-result-card">
    <h3>{TERRITORIES[territory]}</h3>
    {ridge && persistence ? <>
      <dl className="home-metrics">
        <div><dt>Error medio de Ridge</dt><dd>{decimal.format(ridge.mae)} <small>µg/m³</small></dd></div>
        <div><dt>Error medio de persistencia</dt><dd>{decimal.format(persistence.mae)} <small>µg/m³</small></dd></div>
      </dl>
      <p>{integer.format(ridge.n)} casos evaluados. {ridge.mae < persistence.mae && 'Ridge se acercó más al valor medido en el conjunto de la prueba.'}</p>
      {highRidge && highPersistence && highPersistence.mae < highRidge.mae &&
        <p>En los días con PM10 elevado, la persistencia obtuvo menos error.</p>}
    </> : result.error ? <p role="alert">No se pudieron cargar los resultados de {TERRITORIES[territory]}.</p> :
      <p role="status">Cargando resultados de 2024…</p>}
    <button type="button" onClick={() => onCharts({ territory, view: 'results' })}>Ver resultados de {TERRITORIES[territory]}</button>
  </article>;
}

export function Home({ loadJson, onCharts, onScreen }: {
  loadJson: JsonLoader;
  onCharts: (selection: Partial<ChartSelection>) => void;
  onScreen: (screen: 'docs') => void;
}) {
  const madrid = useSummary<ModelMetrics>('/api/charts/metrics?territory=madrid', loadJson);
  const barcelona = useSummary<ModelMetrics>('/api/charts/metrics?territory=barcelona', loadJson);
  const withWeather = madrid.data?.onsets.find(row => row.model === 'logistica_con_meteo');
  const withoutWeather = madrid.data?.onsets.find(row => row.model === 'logistica_sin_meteo');

  return <div className="home-workspace">
    <div className="home-bottom-grid">
      <section className="panel home-intro" aria-labelledby="home-pm10">
        <h2 id="home-pm10">¿Qué es el PM10?</h2>
        <p>Es el nombre que se da a las partículas suspendidas en el aire de unas 10 micras o menos. Son lo bastante pequeñas para entrar en las vías respiratorias. Pueden proceder del polvo que se levanta del suelo, de obras, de incendios o de otras actividades y procesos naturales.</p>
        <p>La concentración se expresa en <strong>µg/m³</strong>, es decir, cuántos microgramos de partículas hay en un metro cúbico de aire.</p>
        <a href="https://www.miteco.gob.es/es/calidad-y-evaluacion-ambiental/temas/emisiones-a-la-atmosfera/emisiones-problematica-ambiental/particulas.html">Más sobre las partículas en suspensión (MITECO)</a>
      </section>
      <section className="panel home-intro" aria-labelledby="home-objective">
        <h2 id="home-objective">¿Qué intentamos predecir?</h2>
        <p>En <strong>Madrid y Barcelona provincia</strong>, estimamos el PM10 medio de mañana en cada estación. <strong>Persistencia</strong> repite el valor de hoy. <strong>Ridge</strong> aprende a combinar mediciones recientes y datos del calendario.</p>
        <p>En <strong>Madrid</strong> también probamos en 2025 si la previsión de viento y lluvia ayuda a anticipar el primer día por encima de <strong>27 µg/m³</strong>, el umbral de trabajo del estudio.</p>
      </section>
    </div>

    <section className="panel home-intro" aria-labelledby="home-stations">
      <h2 id="home-stations">Estaciones del estudio</h2>
      <div className="home-station-grid">
        {(Object.keys(TERRITORIES) as Territory[]).map(territory => <div key={territory}>
          <h3>{TERRITORIES[territory]}</h3>
          <p>{TERRITORY_STATIONS[territory].map(([, name]) => name).join(' · ')}</p>
          <button type="button" onClick={() => onCharts({ territory, view: 'map' })}>Ver mapa de {TERRITORIES[territory]}</button>
        </div>)}
      </div>
    </section>

    <section aria-labelledby="home-results">
      <h2 id="home-results" className="home-section-title">Qué muestran los resultados</h2>
      <p className="home-results-note">En la prueba de 2024 medimos cuánto se alejaba cada predicción del valor real, tanto por exceso como por defecto. Cuanto menor es el error medio, más cerca quedó la predicción.</p>
      <div className="home-result-grid">
        <RegressionSummary territory="madrid" result={madrid} onCharts={onCharts} />
        <RegressionSummary territory="barcelona" result={barcelona} onCharts={onCharts} />
        <article className="panel home-result-card">
          <h3>Avisos de inicio · Madrid 2025</h3>
          {withWeather && withoutWeather ? <>
            <p>Con viento y precipitación previstos se anticiparon <strong>{withWeather.detected} de {withWeather.positives} inicios reales</strong> y se registraron {withWeather.falseAlarms} falsas alarmas.</p>
            <p>Sin meteorología se anticiparon {withoutWeather.detected} inicios y se registraron {withoutWeather.falseAlarms} falsas alarmas.</p>
          </> : madrid.error ? <p role="alert">No se pudieron cargar los resultados de avisos.</p> :
            <p role="status">Cargando resultados de avisos…</p>}
          <button type="button" onClick={() => onCharts({ territory: 'madrid', view: 'results' })}>Consultar la prueba de avisos</button>
        </article>
      </div>
      <p className="muted home-results-source">Las cifras proceden de los resultados de las evaluaciones.</p>
    </section>

    <section className="panel home-periods" aria-labelledby="home-periods-title">
      <h2 id="home-periods-title">Cómo probamos los modelos</h2>
      <ol><li><strong>2017–2022</strong><span>Los modelos aprenden de las mediciones anteriores.</span></li>
        <li><strong>2023</strong><span>Comparamos alternativas y elegimos cómo evaluar los avisos.</span></li>
        <li><strong>2024</strong><span>Probamos la predicción de concentración en Madrid y Barcelona provincia.</span></li>
        <li><strong>2025</strong><span>Probamos los avisos de inicio con y sin meteorología en Madrid.</span></li></ol>
      <p className="muted">La comparación meteorológica se entrena en 2021–2022 por disponibilidad de GFS y se valida en 2023. Cada predicción utiliza las entradas disponibles según el corte temporal del experimento.</p>
    </section>

    <section className="panel home-limits" aria-labelledby="home-limits-title">
      <h2 id="home-limits-title">Qué conviene tener presente</h2>
      <ul><li>El estudio incluye tres estaciones por territorio. Las pruebas comparan fechas con los datos necesarios.</li>
        <li>Los picos pueden quedar muy subestimados, aunque el promedio global mejore.</li>
        <li>Los 27 µg/m³ son el umbral de trabajo del estudio para identificar días elevados.</li>
        <li>Los históricos están revisados. La disponibilidad real de los datos y sus retrasos deben verificarse antes de emitir avisos operativos.</li></ul>
      <button onClick={() => onScreen('docs')}>Consultar metodología y limitaciones</button>
    </section>
  </div>;
}
