import { useEffect, useState } from 'react'
import { listDocuments } from '../api/documents.js'

export default function ChatInput({ onSend, waiting }) {
  const [text, setText] = useState('')
  const [mode, setMode] = useState('hybrid')
  const [documentId, setDocumentId] = useState('')
  const [topK, setTopK] = useState(4)
  const [searchOnly, setSearchOnly] = useState(false)
  const [documents, setDocuments] = useState([])

  useEffect(() => {
    listDocuments(100, 0).then((result) => setDocuments((result.documents || []).filter((item) => item.status === 'ready'))).catch(() => {})
  }, [])

  function submit(event) {
    event?.preventDefault()
    const question = text.trim()
    if (!question || waiting) return
    onSend({ question, mode, document_id: documentId || undefined, top_k: Number(topK), searchOnly })
    setText('')
  }

  return <form onSubmit={submit} className="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm sm:p-4">
    <label htmlFor="chat-question" className="sr-only">Ask a question about your documents</label>
    <textarea id="chat-question" value={text} maxLength={1000} rows={2} disabled={waiting} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit(event) } }} placeholder="Ask something about your documents…" className="w-full resize-y rounded-xl border-0 bg-transparent px-2 py-2 text-sm leading-6 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60" />
    <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">
      <label className="sr-only" htmlFor="search-mode">Search mode</label>
      <select id="search-mode" value={mode} disabled={waiting} onChange={(event) => setMode(event.target.value)} className="min-h-9 rounded-lg border border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600">
        <option value="hybrid">Hybrid</option><option value="vector">Vector</option><option value="keyword">Keyword</option>
      </select>
      <label className="sr-only" htmlFor="chat-document">Document filter</label>
      <select id="chat-document" value={documentId} disabled={waiting} onChange={(event) => setDocumentId(event.target.value)} className="max-w-44 min-h-9 rounded-lg border border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600">
        <option value="">All documents</option>{documents.map((doc) => <option key={doc.id} value={doc.id}>{doc.original_filename}</option>)}
      </select>
      <label className="sr-only" htmlFor="top-k">Number of sources</label>
      <select id="top-k" value={topK} disabled={waiting} onChange={(event) => setTopK(event.target.value)} className="min-h-9 rounded-lg border border-slate-200 bg-white px-2 text-xs font-medium text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600"><option value={3}>3 sources</option><option value={4}>4 sources</option><option value={6}>6 sources</option></select>
      <label className="ml-1 inline-flex min-h-9 items-center gap-2 rounded-lg px-2 text-xs font-medium text-slate-600"><input type="checkbox" checked={searchOnly} disabled={waiting} onChange={(event) => setSearchOnly(event.target.checked)} className="size-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 disabled:opacity-50" />Search only</label>
      <span className="ml-auto text-xs tabular-nums text-slate-400">{text.length}/1000</span>
      <button type="submit" disabled={waiting || !text.trim()} className="min-h-9 rounded-lg bg-indigo-600 px-4 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-300">{waiting ? 'Sending…' : 'Send'}</button>
    </div>
  </form>
}
