import { useState } from 'react'

export default function SourceCard({ source, onHighlight }) {
  const [expanded, setExpanded] = useState(false)
  const snippet = source.snippet || source.content || ''
  const long = snippet.length > 220
  return (
    <article id={`source-${source.citation_number}`} className="rounded-xl border border-slate-200 bg-white p-4 transition-colors">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <button type="button" onClick={() => onHighlight(source.citation_number)} className="flex min-w-0 items-center gap-2 rounded-md text-left focus-visible:outline-2 focus-visible:outline-indigo-600">
          <span className="grid size-6 shrink-0 place-items-center rounded-md bg-indigo-100 text-xs font-bold text-indigo-700">{source.citation_number}</span>
          <span className="truncate text-sm font-semibold text-slate-800">{source.document_name}</span>
        </button>
        <span className="text-xs text-slate-500">{source.page_number ? `Page ${source.page_number}` : 'Page —'} · {Number(source.score || 0).toFixed(2)}</span>
      </div>
      <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">{long && !expanded ? `${snippet.slice(0, 220)}…` : snippet}</p>
      {long && <button type="button" onClick={() => setExpanded((value) => !value)} className="mt-2 rounded text-xs font-semibold text-indigo-700 hover:text-indigo-900 focus-visible:outline-2 focus-visible:outline-indigo-600">{expanded ? 'Show less' : 'Show more'}</button>}
    </article>
  )
}
