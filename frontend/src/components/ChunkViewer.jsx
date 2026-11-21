import { useCallback, useEffect, useState } from 'react'
import { listChunks } from '../api/documents.js'

const PAGE_SIZE = 10

export default function ChunkViewer({ document, onClose }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await listChunks(document.id, PAGE_SIZE, offset)
      setItems(result.items || [])
      setTotal(result.total || 0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [document.id, offset])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    function onKeyDown(event) {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-slate-950/40" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
      <aside role="dialog" aria-modal="true" aria-labelledby="chunks-title" className="flex h-full w-full max-w-2xl flex-col bg-white shadow-2xl">
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 sm:px-7">
          <div className="min-w-0">
            <h2 id="chunks-title" className="text-lg font-semibold text-slate-900">Document chunks</h2>
            <p className="mt-1 truncate text-sm text-slate-500">{document.original_filename}</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close chunks" className="grid size-10 shrink-0 place-items-center rounded-lg text-xl text-slate-500 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-indigo-600">×</button>
        </header>
        <div className="min-h-0 flex-1 overflow-y-auto p-5 sm:p-7">
          {loading && <div role="status" className="space-y-4"><p className="text-sm text-slate-500">Loading chunks…</p>{[0, 1, 2].map((item) => <div key={item} className="h-28 animate-pulse rounded-xl bg-slate-100" />)}</div>}
          {!loading && error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}
          {!loading && !error && items.length === 0 && <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No chunks found.</p>}
          {!loading && !error && items.map((chunk) => (
            <article key={chunk.id} className="mb-4 rounded-xl border border-slate-200 p-4">
              <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-semibold text-slate-500">
                <span>Chunk {chunk.chunk_index + 1}</span>
                {chunk.page_number != null && <span>Page {chunk.page_number}</span>}
                <span>{chunk.char_count} characters</span>
              </div>
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 font-mono text-xs leading-5 text-slate-700">{chunk.content}</pre>
            </article>
          ))}
        </div>
        <footer className="flex items-center justify-between border-t border-slate-200 px-5 py-4 sm:px-7">
          <p className="text-xs text-slate-500">{total ? `${offset + 1}–${Math.min(offset + PAGE_SIZE, total)} of ${total}` : '0 chunks'}</p>
          <div className="flex gap-2">
            <button type="button" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-40">Previous</button>
            <button type="button" disabled={offset + PAGE_SIZE >= total || loading} onClick={() => setOffset(offset + PAGE_SIZE)} className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-40">Next</button>
          </div>
        </footer>
      </aside>
    </div>
  )
}
