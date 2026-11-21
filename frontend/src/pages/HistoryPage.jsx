import { useCallback, useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import { deleteHistory, getHistory, listHistory } from '../api/history.js'
import { useToast } from '../components/Toast.jsx'
import PageTitle from '../components/PageTitle.jsx'

const PAGE_SIZE = 10

function prettyDate(value) {
  return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export default function HistoryPage() {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})
  const [deleting, setDeleting] = useState(null)
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await listHistory(PAGE_SIZE, page * PAGE_SIZE)
      setItems(result.items || [])
      setTotal(result.total || 0)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [page])

  useEffect(() => { refresh() }, [refresh])

  async function toggle(item) {
    if (expanded[item.id]) {
      setExpanded((current) => ({ ...current, [item.id]: null }))
      return
    }
    setExpanded((current) => ({ ...current, [item.id]: { loading: true } }))
    try {
      const detail = await getHistory(item.id)
      setExpanded((current) => ({ ...current, [item.id]: { detail } }))
    } catch (err) {
      setExpanded((current) => ({ ...current, [item.id]: { error: err.message } }))
    }
  }

  async function remove() {
    if (!deleting) return
    setBusy(true)
    try {
      await deleteHistory(deleting.id)
      setDeleting(null)
      setNotice('History entry deleted.')
      toast('History entry deleted.')
      if (items.length === 1 && page > 0) setPage((value) => value - 1)
      else await refresh()
    } catch (err) {
      toast(err.message, 'error')
      setError(err.message)
      setDeleting(null)
    } finally {
      setBusy(false)
    }
  }

  return <Layout>
    <PageTitle title="History" />
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <p className="text-sm font-semibold text-indigo-600">Your workspace</p>
      <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">Query history</h1>
      {notice && <p role="status" className="mt-4 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">{notice}</p>}
      {error && <p role="alert" className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
      <section className="mt-6 space-y-3" aria-label="Previous questions">
        {loading && Array.from({ length: 4 }, (_, index) => <div key={index} className="h-24 animate-pulse rounded-xl bg-slate-200/70" />)}
        {!loading && !error && items.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center text-sm text-slate-600">No questions yet. Ask something about your documents to start a history.</div>}
        {!loading && items.map((item) => {
          const state = expanded[item.id]
          return <article key={item.id} className="rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-4 p-4 sm:p-5">
              <button type="button" onClick={() => toggle(item)} aria-expanded={Boolean(state)} className="min-w-0 flex-1 rounded-lg text-left focus-visible:outline-2 focus-visible:outline-indigo-600">
                <h2 className="font-semibold text-slate-900">{item.question}</h2>
                <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">{item.answer}</p>
                <p className="mt-2 text-xs text-slate-400">{item.latency_ms} ms <span aria-hidden="true">·</span> {prettyDate(item.created_at)}</p>
              </button>
              <button type="button" onClick={() => setDeleting(item)} aria-label={`Delete history entry: ${item.question}`} className="rounded-lg border border-red-200 px-3 py-2 text-sm font-semibold text-red-700 hover:bg-red-50 focus-visible:outline-2 focus-visible:outline-red-600">Delete</button>
            </div>
            {state && <div className="border-t border-slate-100 px-4 py-4 sm:px-5">
              {state.loading && <p role="status" className="text-sm text-slate-500">Loading details…</p>}
              {state.error && <p role="alert" className="text-sm text-red-700">{state.error}</p>}
              {state.detail && <>
                <h3 className="text-sm font-semibold text-slate-800">Full answer</h3>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{state.detail.answer}</p>
                {state.detail.sources?.length > 0 && <div className="mt-4 space-y-3"><h3 className="text-sm font-semibold text-slate-800">Sources</h3>{state.detail.sources.map((source, index) => <div key={source.citation_number || index} className="rounded-lg bg-slate-50 p-3 text-sm"><p className="font-semibold text-slate-800">[{source.citation_number}] {source.document_name}{source.page_number ? ` · page ${source.page_number}` : ''}</p><p className="mt-1 whitespace-pre-wrap text-slate-600">{source.snippet}</p></div>)}</div>}
              </>}
            </div>}
          </article>
        })}
      </section>
      {!loading && total > PAGE_SIZE && <nav aria-label="History pages" className="mt-5 flex items-center justify-between"><span className="text-sm text-slate-500">Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}</span><div className="flex gap-2"><button type="button" disabled={!page} onClick={() => setPage((value) => value - 1)} className="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold disabled:opacity-40">Previous</button><button type="button" disabled={(page + 1) * PAGE_SIZE >= total} onClick={() => setPage((value) => value + 1)} className="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold disabled:opacity-40">Next</button></div></nav>}
    </main>
    <ConfirmDialog open={Boolean(deleting)} title="Delete this history entry?" description="This question and answer will be removed from your history." busy={busy} onConfirm={remove} onCancel={() => setDeleting(null)} />
  </Layout>
}
