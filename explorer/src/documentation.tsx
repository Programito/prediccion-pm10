import { useEffect, useState } from 'react';
import Markdown from 'react-markdown';
import type { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Glossary } from './dictionary';
import { errorMessage } from './api';
import type { Article, ArticleSummary, JsonLoader } from './api';

interface ArticleResult {
  selected?: string;
  article?: Article;
  error?: string;
}

export function Documentation({ loadJson }: { loadJson: JsonLoader }) {
  const [catalog, setCatalog] = useState<ArticleSummary[]>([]);
  const [selected, setSelected] = useState('fuentes');
  const [result, setResult] = useState<ArticleResult>({});
  const [catalogError, setCatalogError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    loadJson<ArticleSummary[]>('/api/documentation', controller.signal).then(setCatalog)
      .catch((error: unknown) => { if (!controller.signal.aborted) setCatalogError(errorMessage(error)); });
    return () => controller.abort();
  }, [loadJson]);
  useEffect(() => {
    if (selected === 'glossary') return;
    const controller = new AbortController();
    loadJson<Article>(`/api/documentation/${selected}`, controller.signal).then(article => setResult({ selected, article }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult({ selected, error: errorMessage(error) });
      });
    return () => controller.abort();
  }, [loadJson, selected]);
  const current = result.selected === selected ? result : {};
  const article = current.article;
  const articleLink: Components['a'] = ({ href = '', children }) => {
    if (/^https?:\/\//i.test(href)) return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
    if (!article) return <span>{children}</span>;
    const base = `https://atlas.invalid/docs/${article.path}`;
    const path = new URL(href, base).pathname;
    const match = catalog.find(item => path === `/docs/${item.path}`);
    if (match && match.id !== selected) return <button type="button" className="doc-link" onClick={() => setSelected(match.id)}>{children}</button>;
    return <span className="doc-reference" title={path.slice(1)}>{children}</span>;
  };
  return <div className="layout documentation-layout">
    <aside className="panel source-sidebar" aria-label="Guías del proyecto">
      <div className="sidebar-title"><h2>Guías</h2></div>
      {catalogError && <p role="alert">{catalogError}</p>}
      <div className="documentation-list">
        <button type="button" className="source-item" aria-pressed={selected === 'glossary'} onClick={() => setSelected('glossary')}>Glosario</button>
        {catalog.map(item => <button key={item.id} type="button" className="source-item"
        aria-pressed={item.id === selected} onClick={() => setSelected(item.id)}>{item.title}</button>)}</div>
    </aside>
    <article className="panel documentation-article" aria-label="Documentación de datos">
      {selected === 'glossary' ? <Glossary /> : current.error ? <p role="alert">{current.error}</p> : article ?
        <Markdown remarkPlugins={[remarkGfm]} components={{ a: articleLink,
          table: ({ children }) => <div className="table-scroll" tabIndex={0} role="region" aria-label="Tabla de documentación"><table>{children}</table></div>,
        }}>{article.markdown}</Markdown> :
        <p role="status">Cargando la guía…</p>}
    </article>
  </div>;
}
