export const CHART_STATIONS = [
  ['28079060', 'Tres Olivos'],
  ['28080003', 'Majadahonda'],
  ['28133002', 'San Martín de Valdeiglesias'],
];

export const TERRITORIES = { madrid: 'Madrid', barcelona: 'Barcelona provincia' };
export type Territory = keyof typeof TERRITORIES;
export const TERRITORY_STATIONS = {
  madrid: CHART_STATIONS,
  barcelona: [['08184006', 'Rubí (Ca n’Oriol)'], ['08202001', 'Sant Celoni'], ['08263001', 'Sant Vicenç dels Horts']],
};

export function dateForTerritory(date: string, territory: Territory) {
  return territory === 'barcelona' && date > '2024-12-31' ? '2024' + date.slice(4) : date;
}

export const CHART_VIEWS = {
  map: 'Mapa',
  observations: 'Observaciones',
  predictions: 'Predicciones',
  results: 'Resultados',
  errors: 'Errores',
  uncertainty: 'Incertidumbre',
  explanations: 'Explicabilidad',
};

export type ChartView = keyof typeof CHART_VIEWS;

export interface ChartSelection {
  territory: Territory;
  view: ChartView;
  station: string;
  date: string;
}

export const INITIAL_CHART_SELECTION: ChartSelection = {
  territory: 'madrid',
  view: 'observations',
  station: '28079060',
  date: '2024-10-31',
};
