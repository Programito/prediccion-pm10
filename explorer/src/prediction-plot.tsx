import { useEffect, useRef } from 'react';
import type { MouseEvent } from 'react';
import type { PredictionDay } from './api';

export const PREDICTION_SERIES = [
  { key: 'observed', label: 'Observado', dash: [] },
  { key: 'ridge', label: 'Ridge', dash: [7, 4] },
  { key: 'persistencia', label: 'Persistencia', dash: [2, 4] },
] satisfies { key: Exclude<keyof PredictionDay, 'date'>; label: string; dash: number[] }[];

const LEFT = 37;
const RIGHT = 14;
export const shortDate = (date: string) => `${date.slice(8)}/${date.slice(5, 7)}`;

function drawPlot(canvas: HTMLCanvasElement, days: PredictionDay[], threshold: number, selected: string) {
  const { width, height } = canvas.getBoundingClientRect();
  if (!width || !height) return;
  const density = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * density);
  canvas.height = Math.round(height * density);
  const context = canvas.getContext('2d');
  if (!context) return;
  context.scale(density, density);
  const style = getComputedStyle(canvas);
  const color = (name: string) => style.getPropertyValue(name).trim();
  const chartWidth = width - LEFT - RIGHT;
  const top = 26;
  const bottom = height - 26;
  const maximum = Math.max(threshold, ...days.flatMap(day => PREDICTION_SERIES.map(({ key }) => day[key] ?? 0)));
  const step = Math.ceil(maximum / 30) * 10;
  const x = (index: number) => LEFT + index * chartWidth / (days.length - 1);
  const y = (value: number) => bottom - value * (bottom - top) / (step * 3);
  const selectedIndex = days.findIndex(day => day.date === selected);

  context.font = `11px ${style.fontFamily}`;
  context.fillStyle = color('--muted');
  context.fillText('µg/m³', 0, 12);
  context.textAlign = 'right';
  for (const value of [0, step, 2 * step, 3 * step]) {
    context.beginPath();
    context.strokeStyle = color('--line');
    context.moveTo(LEFT, y(value));
    context.lineTo(width - RIGHT, y(value));
    context.stroke();
    context.fillText(String(value), LEFT - 6, y(value) + 4);
  }

  const tickIntervals = Math.min(Math.max(1, Math.floor(chartWidth / 57)), days.length - 1);
  context.textAlign = 'center';
  for (let tick = 0; tick <= tickIntervals; tick++) {
    const index = Math.round(tick * (days.length - 1) / tickIntervals);
    context.fillText(shortDate(days[index].date), Math.min(x(index), width - 16), bottom + 18);
  }

  context.beginPath();
  context.strokeStyle = color('--model-without-weather');
  context.setLineDash([5, 4]);
  context.moveTo(LEFT, y(threshold));
  context.lineTo(width - RIGHT, y(threshold));
  context.stroke();
  context.beginPath();
  context.setLineDash([]);
  context.strokeStyle = color('--muted');
  context.globalAlpha = 0.45;
  context.moveTo(x(selectedIndex), top);
  context.lineTo(x(selectedIndex), bottom);
  context.stroke();
  context.globalAlpha = 1;

  for (const { key, dash } of PREDICTION_SERIES) {
    context.strokeStyle = color(`--prediction-${key}`);
    context.lineWidth = 2;
    context.setLineDash(dash);
    context.beginPath();
    let previous = false;
    days.forEach((day, index) => {
      const value = day[key];
      if (value !== undefined) {
        if (previous) context.lineTo(x(index), y(value));
        else context.moveTo(x(index), y(value));
      }
      previous = value !== undefined;
    });
    context.stroke();

    context.fillStyle = context.strokeStyle;
    days.forEach((day, index) => {
      const value = day[key];
      if (value === undefined) return;
      context.beginPath();
      context.arc(x(index), y(value), index === selectedIndex ? 4 : 1.8, 0, 2 * Math.PI);
      context.fill();
    });
  }
}

export function PredictionPlot({ days, threshold, selected, onSelect }: {
  days: PredictionDay[];
  threshold: number;
  selected: string;
  onSelect: (date: string) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const draw = () => drawPlot(element, days, threshold, selected);
    const observer = new ResizeObserver(draw);
    observer.observe(element);
    draw();
    return () => observer.disconnect();
  }, [days, threshold, selected]);

  function selectDay(event: MouseEvent<HTMLCanvasElement>) {
    const { left, width } = event.currentTarget.getBoundingClientRect();
    const fraction = (event.clientX - left - LEFT) / (width - LEFT - RIGHT);
    const index = Math.round(fraction * (days.length - 1));
    if (days[index]) onSelect(days[index].date);
  }

  return <canvas
    className="prediction-plot"
    ref={canvas}
    aria-hidden="true"
    onClick={selectDay}
  />;
}
