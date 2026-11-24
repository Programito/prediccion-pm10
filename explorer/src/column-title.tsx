const LABELS: Record<string, string> = {
  punto_muestreo: 'Punto de muestreo', codigo_estacion: 'Código de estación', nombre: 'Nombre', tipo_area: 'Tipo de área',
  fecha: 'Fecha', concentracion: 'Concentración', estado: 'Estado', origen_diario: 'Origen diario',
  n_horas_validas: 'Horas válidas', horas_validas: 'Horas válidas', archivo_origen: 'Archivo de origen', miembro_zip: 'Archivo dentro del ZIP',
  pm10_valido: 'PM10 válido', anio: 'Año', codigo_provincia: 'Código de provincia', unidad: 'Unidad',
  es_valido: 'Válida', fecha_objetivo: 'Fecha objetivo', fecha_ultima_observacion: 'Última observación',
  pm10_t: 'PM10 del último día observado', pm10_objetivo: 'PM10 real del día objetivo', emision_simulada_utc: 'Emisión simulada (UTC)',
  pm10_t_menos_1: 'PM10 · 1 día antes',
  pm10_t_menos_2: 'PM10 · 2 días antes',
  pm10_t_menos_6: 'PM10 · 6 días antes',
  media_3_dias: 'Media de 3 días', media_7_dias: 'Media de 7 días', media_14_dias: 'Media de 14 días',
  desviacion_7_dias: 'Desviación de 7 días', inicio_ciclo_utc: 'Inicio del ciclo (UTC)',
  latitud_gfs: 'Latitud de la celda GFS', longitud_gfs: 'Longitud de la celda GFS',
  viento_10m_mediodia_ms: 'Viento a 10 m al mediodía (m/s)', precipitacion_diaria_mm: 'Precipitación diaria (mm)',
};

export function columnLabel(name: string): string {
  const key = name.toLocaleLowerCase('es');
  if (LABELS[key]) return LABELS[key];
  const label = key.replace(/_/g, ' ').replace(/\bpm10\b/g, 'PM10').replace(/\butc\b/g, 'UTC').replace(/\bgfs\b/g, 'GFS');
  return label.charAt(0).toLocaleUpperCase('es') + label.slice(1);
}

export function ColumnTitle({ name, type }: { name: string; type: string }) {
  return <><span>{columnLabel(name)}</span><code className="column-technical-name">{name}</code><span className="column-type">{type}</span></>;
}
