import { useState } from 'react';
import type { TablePage } from './api';
import { columnLabel } from './column-title';
import { displayValue } from './provenance';

const GROUPS = {
  'Datos y formatos': {
    Endpoint: 'Dirección a la que se envía una petición para consultar o descargar datos.',
    'GET / POST': 'GET consulta o descarga. POST envía datos en el cuerpo de la petición, como los filtros de la consulta EEA.',
    CSV: 'Archivo de texto con campos separados por un delimitador, normalmente coma o punto y coma.',
    ZIP: 'Contenedor comprimido que puede incluir varios archivos, por ejemplo un CSV por contaminante.',
    'XLS / XLSX': 'Formatos de libro de Excel. Un libro contiene hojas y cada hoja contiene celdas.',
    JSON: 'Formato de texto para objetos, listas, números y otros valores. Se usa en consultas, manifiestos y en la API local.',
    Parquet: 'Formato binario que guarda datos por columnas con tipos explícitos. La EEA lo usa para publicar sus series horarias.',
    GRIB2: 'Formato binario para campos meteorológicos en cuadrícula. NOAA GFS lo usa para sus previsiones.',
    'Índice .idx / Range': 'El índice indica dónde empieza cada mensaje GRIB2. Range solicita solo los bytes elegidos.',
    'Manifiesto / SHA-256': 'El manifiesto enumera las fuentes y descargas. SHA-256 es la huella que permite comprobar un archivo.',
  },
  'Tipos y claves': {
    'Tipo de valor / almacenamiento': 'Consulta qué representa cada columna, cómo se guarda y un ejemplo de los registros de esta página. Un decimal puede estar escrito como texto en un CSV.',
    Código: 'Identificador de una estación, territorio u otra entidad. Se trata como texto cuando hay que conservar ceros iniciales.',
    'Entero / decimal': 'El entero carece de parte fraccionaria. Un decimal puede tenerla, como 24,42 µg/m³.',
    'Categoría / booleano': 'Una categoría toma uno de varios valores definidos. Un booleano expresa una condición verdadera o falsa.',
    'Fecha ISO / UTC': 'Las fechas usan año, mes y día, por ejemplo 2025-08-05. UTC es la referencia horaria. La Z al final de una fecha y hora indica UTC.',
    'Nulo / — / ..': 'Un nulo indica ausencia. El explorador muestra los vacíos con un guion. El INE también puede publicar .. para indicar ausencia. Cero es un valor.',
    Proporción: 'Parte dividida entre el total. Una proporción de 0,25 equivale al 25 %.',
    Granularidad: 'Lo que representa una fila, por ejemplo una estación y un día.',
    'Clave / PK': 'Columna o combinación que identifica una fila. PK marca sus componentes en los esquemas Mermaid.',
    Mapeador: 'Código que adapta las columnas, fechas, tipos u otros datos originales al formato del proyecto.',
  },
  'Aire y meteorología': {
    'PM10 / µg/m³': 'PM10 designa partículas con un diámetro aerodinámico de hasta 10 micrómetros. La concentración se expresa en microgramos por metro cúbico de aire.',
    'Estación / punto de muestreo': 'La estación es el lugar de vigilancia. El punto de muestreo distingue la serie medida en ese lugar, con su magnitud y técnica.',
    'Magnitud / técnica': 'La magnitud identifica qué se mide. La técnica identifica el procedimiento de medida.',
    'D01–D31 / H01–H24': 'D indica el día del mes. H indica el fin de la hora UTC en los archivos horarios de MITECO.',
    'NOAA GFS / ciclo / plazo': 'GFS (Global Forecast System) es el modelo de previsión meteorológica de NOAA. El TFM usa sus previsiones de viento y precipitación. El ciclo indica cuándo se inició el pronóstico y el plazo indica cuántas horas cubre hasta el momento previsto.',
    'Celda GFS': 'Punto de la cuadrícula meteorológica. Dos estaciones pueden compartir la misma celda.',
    'UGRD / VGRD / APCP': 'Componentes este y norte del viento y precipitación acumulada, respectivamente.',
    'm/s / mm': 'Metros por segundo para la velocidad del viento y milímetros de agua para la precipitación.',
    'EEA / E1a': 'EEA es la Agencia Europea de Medio Ambiente. E1a identifica su archivo de mediciones verificadas.',
  },
  'Sanidad y modelado': {
    'CIE-10-MC / alta hospitalaria': 'CIE-10-MC clasifica diagnósticos. Un alta es la finalización de un ingreso y es lo que cuenta la tasa sanitaria.',
    'Tasa por 100.000': 'Frecuencia de altas expresada por cada 100.000 habitantes para comparar territorios con poblaciones diferentes.',
    'Predictor / objetivo / retardo': 'Un predictor es una entrada del modelo. El objetivo es lo que se quiere predecir. Un retardo recupera una observación de días anteriores.',
    Persistencia: 'Predice que el PM10 del día siguiente será igual al último valor observado en la estación.',
    Ridge: 'Modelo que aprende a combinar observaciones anteriores y datos de calendario para estimar el PM10 del día siguiente.',
    'Ventana móvil': 'Conjunto de días consecutivos que se desplaza cada día para calcular una media u otra medida.',
    'PM10 elevado / comienzo': 'Un día es elevado si supera 27 µg/m³. Hay un comienzo cuando el día anterior era de 27 µg/m³ o menos.',
    'Entrenamiento / validación / prueba': 'El entrenamiento ajusta el modelo. La validación orienta decisiones. La prueba mide el rendimiento posterior a esas decisiones.',
  },
};

function searchable(value: string) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es');
}

export function ColumnDictionary({ data, treated }: { data: TablePage; treated: boolean }) {
  const [search, setSearch] = useState('');
  const query = searchable(search.trim());
  const fields = data.columns.map((field, index) => ({ field, index })).filter(({ field }) =>
    searchable([field.name, treated ? columnLabel(field.name) : "", field.type, field.notes].join(' ')).includes(query));
  return <section className="column-dictionary" aria-label="Explicación de las columnas">
    <div className="dictionary-tools">
      <p className="muted">Consulta qué representa cada columna, cómo se guarda y un ejemplo de los registros de esta página.</p>
      <label htmlFor="column-search" className="sr-only">Buscar una columna</label>
      <input type="search" id="column-search" placeholder="Buscar una columna" value={search} onChange={e => setSearch(e.target.value)} />
    </div>
    {!fields.length ? <p className="empty" role="status">Ninguna columna coincide con la búsqueda.</p> :
      <div className="table-scroll" role="region" tabIndex={0} aria-label="Diccionario de columnas">
        <table className="schema dictionary-table"><thead><tr><th scope="col">Columna</th><th scope="col">Qué significa</th><th scope="col">Tipo de valor</th><th scope="col">Cómo viene guardado</th><th scope="col">Ejemplo de la página</th></tr></thead>
          <tbody>{fields.map(({ field, index }) => {
            const sample = data.rows.find(row => row[index] != null && String(row[index]).trim() !== '' && row[index] !== '..');
            const example = sample ? displayValue(sample[index]) : '—';
            return <tr key={field.name}><th scope="row">{treated && <span>{columnLabel(field.name)}</span>}<code className={treated ? "column-technical-name" : undefined}>{field.name}</code>{field.isKey && <span className="tag dictionary-key">Clave</span>}</th>
              <td>{field.notes}</td><td>{field.type}</td><td>{field.storage}</td><td><code title={sample ? example : 'Sin ejemplo en esta página'}>{example}</code></td></tr>;
          })}</tbody>
        </table>
      </div>}
  </section>;
}

export function Glossary() {
  const [search, setSearch] = useState('');
  const query = searchable(search.trim());
  const visible = Object.entries(GROUPS).map(([group, terms]) => ({
    group,
    terms: Object.entries(terms).filter(([term, description]) =>
      searchable([group, term, description].join(' ')).includes(query)),
  })).filter(({ terms }) => terms.length);
  return <section className="glossary" aria-label="Glosario">
    <div className="dictionary-tools"><h2>Glosario</h2><label htmlFor="term-search" className="sr-only">Buscar un término</label>
      <input type="search" id="term-search" placeholder="Busca PM10, UTC, ZIP…" value={search} onChange={e => setSearch(e.target.value)} /></div>
    {!visible.length && <p className="empty" role="status">Ningún término coincide con la búsqueda.</p>}
    {visible.map(({ group, terms }) => <div className="glossary-group" key={group}><h4>{group}</h4>
      <dl>{terms.map(([term, explanation]) => <div key={term}><dt>{term}</dt><dd>{explanation}</dd></div>)}</dl>
    </div>)}
  </section>;
}
