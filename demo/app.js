"use strict";

const data = globalThis.PM10_DEMO;
const id = (name) => document.getElementById(name);
const station = id("station");
const targetDate = id("target-date");
const dateFormat = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const compactDate = new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const measure = new Intl.NumberFormat("es-ES", { maximumFractionDigits: 2 });
const percent = new Intl.NumberFormat("es-ES", { style: "percent", maximumFractionDigits: 2 });
const datesForMode = { classification: "2025-08-05", regression: "2024-01-01" };
let mode = "classification";
let cases = [];

function element(tag, text, className) {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = text;
  if (className) item.className = className;
  return item;
}

function reading(label, value, unit) {
  const box = element("div", undefined, "reading");
  box.append(element("span", label), element("strong", measure.format(value)), element("small", unit));
  return box;
}

function classification(caseData) {
  const table = element("table");
  const heading = table.createTHead().insertRow();
  for (const [label, numeric] of [["Método", false], ["Probabilidad", true], ["Corte", true], ["Decisión", true]]) {
    const cell = element("th", label, numeric ? "num" : "");
    cell.scope = "col";
    heading.append(cell);
  }
  const body = table.createTBody();
  for (const [key, label] of [["logistica_con_meteo", "Logística con meteorología"], ["logistica_sin_meteo", "Logística sin meteorología"], ["persistencia", "Persistencia"]]) {
    const { alert, probability } = caseData.results[key];
    const row = body.insertRow();
    const title = element("th", label);
    title.scope = "row";
    row.append(title, element("td", probability === null ? "—" : percent.format(probability), "num"),
      element("td", probability === null ? "—" : percent.format(data.probabilityCuts[key]), "num"));
    row.appendChild(element("td", undefined, "num")).append(element("span", alert ? "Aviso" : "Sin aviso", alert ? "badge alert" : "badge"));
  }
  id("comparison").replaceChildren(table);
  id("comparison-title").textContent = "Avisos de PM10 elevado";
  id("comparison-unit").textContent = `Umbral observado > ${data.eventThreshold} µg/m³`;
  id("comparison-note").textContent = "Cada logística avisa cuando su probabilidad alcanza el corte fijado en 2023. La persistencia avisa si el valor anterior supera el umbral.";
}

function regression(caseData) {
  const { ridge, persistencia } = caseData.results;
  const maximum = Math.max(ridge, persistencia, caseData.observed, 1);
  const bars = [["Observado", caseData.observed, "observed"], ["Ridge", ridge, ""], ["Persistencia", persistencia, "reference"]];
  id("comparison").replaceChildren(...bars.map(([label, value, kind]) => {
    const row = element("div", undefined, "bar-row");
    const track = element("span", undefined, "track");
    const bar = element("span", undefined, `bar ${kind}`);
    bar.style.width = `${100 * value / maximum}%`;
    track.setAttribute("aria-hidden", "true");
    track.append(bar);
    row.append(element("span", label), track, element("strong", measure.format(value)));
    return row;
  }));
  id("comparison-title").textContent = "Concentración prevista y observada";
  id("comparison-unit").textContent = "µg/m³";
  id("comparison-note").textContent = `Error absoluto de Ridge: ${measure.format(Math.abs(ridge - caseData.observed))} µg/m³. Error de la persistencia: ${measure.format(Math.abs(persistencia - caseData.observed))} µg/m³.`;
}

function renderCase() {
  const position = targetDate.selectedIndex;
  const result = cases[position];
  const isClassification = mode === "classification";
  id("previous-date").disabled = position <= 0;
  id("next-date").disabled = position >= cases.length - 1;
  id("case-date").textContent = dateFormat.format(new Date(result.date));
  id("result-title").textContent = data.stations[result.station];
  const elevated = result.observed > data.eventThreshold;
  const status = id("result-status");
  status.hidden = !isClassification;
  status.textContent = !elevated ? "Día no elevado" : result.previous <= data.eventThreshold ? "Comienzo observado" : "Continuación observada";
  status.className = elevated ? "badge alert" : "badge positive";
  const readings = [reading("PM10 del día anterior", result.previous, "µg/m³"), reading("PM10 observado", result.observed, "µg/m³")];
  const cycle = id("cycle");
  cycle.hidden = !isClassification;
  if (isClassification) {
    readings.push(reading("Viento previsto", result.weather.wind, "m/s"), reading("Lluvia prevista", result.weather.rain, "mm"));
    cycle.textContent = `Previsión NOAA GFS del ${dateFormat.format(new Date(result.weather.cycle))} a las 12:00 UTC.`;
    classification(result);
  } else {
    regression(result);
  }
  id("readings").replaceChildren(...readings);
  id("announcement").textContent = `${data.stations[result.station]}, ${id("case-date").textContent}. PM10 observado: ${measure.format(result.observed)} microgramos por metro cúbico.`;
}

function selectCases(wantedDate) {
  cases = data[mode].filter((row) => row.station === station.value);
  targetDate.replaceChildren(...cases.map(({ date }) => new Option(compactDate.format(new Date(date)), date)));
  if (cases.some((row) => row.date === wantedDate)) targetDate.value = wantedDate;
  id("coverage").textContent = `${cases.length} fechas evaluadas en esta estación.`;
  renderCase();
}

const modes = document.querySelectorAll("[data-mode]");
for (const button of modes) {
  button.addEventListener("click", () => {
    if (mode === button.dataset.mode) return;
    mode = button.dataset.mode;
    for (const tab of modes) tab.setAttribute("aria-pressed", String(tab === button));
    id("examples").hidden = mode !== "classification";
    selectCases(datesForMode[mode]);
  });
}
for (const button of document.querySelectorAll("[data-example]")) {
  button.addEventListener("click", () => {
    station.value = "28079060";
    selectCases(button.dataset.example);
  });
}
for (const [name, step] of [["previous-date", -1], ["next-date", 1]]) {
  id(name).addEventListener("click", () => {
    targetDate.selectedIndex += step;
    renderCase();
  });
}
station.addEventListener("change", () => selectCases(targetDate.value));
targetDate.addEventListener("change", renderCase);
station.replaceChildren(...Object.entries(data.stations).map(([key, label]) => new Option(label, key)));
selectCases(datesForMode[mode]);
