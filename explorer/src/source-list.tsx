import { useEffect, useId, useState } from 'react';
import type { Source } from './api';

const DOMAINS = ['Calidad del aire', 'Sanidad', 'Demografía', 'Meteorología'];
const PROFILES = ['aire-diario', 'aire-horario', 'estaciones', 'eea', 'sanidad', 'demografia', 'noaa'];
interface Family { id: string; domain: string; provider: string; title: string; sources: Source[] }

function groupSources(sources: Source[]): Family[] {
  const groups = new Map<string, Family>();
  for (const source of sources) {
    const id = JSON.stringify([source.domain, source.provider, source.profile, source.title]);
    if (!groups.has(id)) groups.set(id, { id, domain: source.domain, provider: source.provider, title: source.title, sources: [] });
    groups.get(id)!.sources.push(source);
  }
  return [...groups.values()].map(group => ({ ...group, sources: [...group.sources].sort((a, b) =>
    b.year.localeCompare(a.year, 'es', { numeric: true }) ||
    Number(a.scope === 'initial_feasibility_sample') - Number(b.scope === 'initial_feasibility_sample') ||
    a.id.localeCompare(b.id)) })).sort((a, b) =>
    PROFILES.indexOf(a.sources[0].profile) - PROFILES.indexOf(b.sources[0].profile) || a.title.localeCompare(b.title, 'es'));
}

function SourceFamily({ family, selectedId, choice, onSelect }: {
  family: Family; selectedId: string; choice?: string; onSelect: (id: string) => void;
}) {
  const selectId = useId();
  const active = family.sources.find(source => source.id === selectedId);
  const source = active ?? family.sources.find(source => source.id === choice) ?? family.sources[0];
  return <div className="source-family" data-selected={Boolean(active)}>
    <button className="source-item" aria-pressed={Boolean(active)} onClick={() => onSelect(source.id)}>
      <span className="source-provider">{family.provider}</span><strong>{family.title}</strong>
      <span className="source-secondary">{source.format}{source.scope === 'initial_feasibility_sample' ? ' · Muestra inicial' : ''}</span>
    </button>
    <div className="source-period"><label htmlFor={selectId}>Año o periodo</label>
      <select id={selectId} aria-label={`Año o periodo de ${family.title} · ${family.provider}`} value={source.id}
        onChange={event => onSelect(event.target.value)}>
        {family.sources.map(item => <option key={item.id} value={item.id}>
          {item.year}{item.scope === 'initial_feasibility_sample' ? ' · Muestra inicial' : ''}
        </option>)}
      </select>
    </div>
  </div>;
}

export function SourceList({ sources, selectedId, onSelect }: {
  sources: Source[]; selectedId: string; onSelect: (id: string) => void;
}) {
  const [domain, setDomain] = useState('Todas');
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set([sources.find(s => s.id === selectedId)?.domain ?? DOMAINS[0]]));
  const [choices, setChoices] = useState<Record<string, string>>({});
  const groupId = useId();
  const domains = [...new Set([...DOMAINS, ...sources.map(s => s.domain)])];
  const selectedDomain = sources.find(source => source.id === selectedId)?.domain;
  useEffect(() => {
    if (selectedDomain) setExpanded(previous => new Set([...previous, selectedDomain]));
  }, [selectedId, selectedDomain]);
  const normalized = query.trim().toLocaleLowerCase('es');
  const visible = sources.filter(source => (domain === 'Todas' || source.domain === domain) &&
    [source.domain, source.provider, source.title, source.year, source.format, source.file,
      source.scope === 'initial_feasibility_sample' ? 'Muestra inicial' : '', ...source.tables.map(t => t.name)]
      .some(value => value?.toLocaleLowerCase('es').includes(normalized)));
  const families = groupSources(visible);
  return <aside className="panel source-sidebar" aria-label="Fuentes de datos">
    <div className="sidebar-title"><h2>Fuentes</h2><span>{visible.length} de {sources.length} archivos</span></div>
    <label className="sr-only" htmlFor="source-search">Buscar fuente</label>
    <input id="source-search" type="search" placeholder="Buscar fuente o año" value={query} onChange={event => {
      setQuery(event.target.value); setExpanded(new Set(domains));
    }} />
    <label className="sr-only" htmlFor="domain-filter">Área</label>
    <select id="domain-filter" value={domain} onChange={event => { setDomain(event.target.value); setExpanded(new Set(domains)); }}>
      {['Todas', ...domains].map(item => <option key={item}>{item}</option>)}
    </select>
    <p className="source-group-count" role="status">{families.length} {families.length === 1 ? 'tipo' : 'tipos'} de fuente</p>
    <div className="source-list source-groups">
      {domains.map((topic, index) => {
        const groups = families.filter(family => family.domain === topic);
        if (!groups.length) return null;
        const open = expanded.has(topic);
        const panelId = `${groupId}-group-${index}`;
        return <section key={topic} className="source-topic">
          <h3><button className="source-topic-toggle" aria-expanded={open} aria-controls={panelId} onClick={() => setExpanded(previous => {
            const next = new Set(previous); if (next.has(topic)) next.delete(topic); else next.add(topic); return next;
          })}><span aria-hidden="true">{open ? '▾' : '▸'}</span><span>{topic}</span><span className="source-topic-count">{groups.length}</span></button></h3>
          <div id={panelId} hidden={!open} className="source-topic-content">{groups.map(family => <SourceFamily key={family.id} family={family}
            selectedId={selectedId} choice={choices[family.id]} onSelect={id => {
              setChoices(previous => ({ ...previous, [family.id]: id })); onSelect(id);
            }} />)}</div>
        </section>;
      })}
      {!visible.length && <p className="muted empty">Ninguna fuente coincide con la búsqueda.</p>}
    </div>
  </aside>;
}
