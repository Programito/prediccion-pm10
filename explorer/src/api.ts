export type Cell = string | number | boolean | null | Cell[];

export interface TableSummary {
  id: string;
  name: string;
  local: string;
  format: string;
  url?: string;
}

export interface TreatedTable extends TableSummary {
  group: string;
  scope: 'madrid' | 'barcelona' | 'provincial';
  kind: 'mapped' | 'supervised' | 'joined';
  purpose: string;
  grain: string;
  keys: string[];
  mapper: string;
  preparation: string;
}

export interface Source {
  id: string;
  profile: string;
  year: string;
  format: string;
  file?: string;
  scope?: string;
  method: string;
  url: string;
  catalog?: string;
  requestNote?: string;
  payload?: Record<string, unknown>;
  provider: string;
  title: string;
  domain: string;
  purpose: string;
  tables: TableSummary[];
}

export interface Column {
  name: string;
  type: string;
  notes: string;
  storage: string;
  isKey: boolean;
}

export interface TablePage {
  columns: Column[];
  rows: Cell[][];
  positions: number[];
  page: number;
  size: number;
  start: number;
  hasNext: boolean;
}

export interface SelectedCell {
  row: number;
  column: string;
}

export interface ProvenanceSource {
  label?: string | null;
  format?: string;
  file?: string;
  container?: string | null;
  member?: string | null;
  sheet?: string | null;
  byteRange?: [number, number] | null;
  url?: string | null;
  indexUrl?: string | null;
}

export interface Provenance {
  column: string;
  value: Cell;
  description: Column;
  stored: {
    file: string;
    format: string;
    position: number;
    container: string | null;
    member: string | null;
    sheet: string | null;
    cell?: string;
  };
  rule: string;
  sources: ProvenanceSource[];
}

export interface Article {
  title: string;
  path: string;
  markdown: string;
}

export type ArticleSummary = Pick<Article, 'title' | 'path'> & { id: string };

export interface DailySeries {
  threshold: number;
  source: 'MITECO' | 'EEA';
  days: { date: string; value: number | null }[];
}

export interface PredictionDay {
  date: string;
  observed?: number;
  ridge?: number;
  persistencia?: number;
}

export interface PredictionSeries {
  threshold: number;
  days: PredictionDay[];
  episodes: { start: string; end: string; peak: string }[];
}

export interface RegressionMetric {
  group: 'todos' | 'elevado';
  model: 'persistencia' | 'ridge';
  mae: number;
  n: number;
}

export interface OnsetMetric {
  model: 'persistencia' | 'logistica_sin_meteo' | 'logistica_con_meteo';
  detected: number;
  falseAlarms: number;
  positives: number;
  n: number;
}

export interface ModelMetrics {
  threshold: number;
  regression: RegressionMetric[];
  onsets: OnsetMetric[];
}

export interface ErrorMetrics {
  n: number;
  mae_ridge: number;
  mae_persistencia: number;
  rmse_ridge: number;
  rmse_persistencia: number;
  sesgo_ridge: number;
  sesgo_persistencia: number;
  delta_mae: number;
}

export interface BootstrapAnalysis {
  primaryBlockDays: number;
  coverage: number;
  replicates: number;
  seed: number;
  rows: {
    station: string;
    name: string;
    block_days: number;
    n: number;
    replicates: number;
    estimate: number;
    lower: number;
    upper: number;
    includes_zero: boolean;
    minimum_resampled_cases: number;
    maximum_resampled_cases: number;
  }[];
}

export interface ErrorAnalysis {
  threshold: number;
  groups: (ErrorMetrics & {
    station: string;
    name: string;
    month: number;
    level: 'todos' | 'resto' | 'elevado';
  })[];
  sensitivity: (ErrorMetrics & { scenario: string; excluded_dates: string })[];
}

export interface ModelExplanation {
  trainingEnd: string;
  testYear: number;
  intercept: number;
  features: { name: string; coefficient: number }[];
  forest: { name: string; importance: number }[];
  dates: string[];
  case: {
    station: string;
    date: string;
    observed: number;
    prediction: number;
    rawPrediction: number;
    inputs: Record<string, number>;
    transformed: number[];
    contributions: number[];
  };
}

export async function loadJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const detail: unknown = await response.json().catch(() => null);
    const message = typeof detail === 'object' && detail !== null && 'error' in detail && typeof detail.error === 'string'
      ? detail.error
      : `La petición falló (${response.status}).`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export type JsonLoader = typeof loadJson;

export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
