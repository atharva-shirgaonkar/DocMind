import { useCallback, useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import UploadBox from '../components/UploadBox.jsx'
import DocumentRow from '../components/DocumentRow.jsx'
import ChunkViewer from '../components/ChunkViewer.jsx'
import { listDocuments } from '../api/documents.js'

const PAGE_SIZE = 10

function LoadingRows() {
  return <div className="space-y-3" role="status" aria-label="Loading documents">{Array.from({ length: 4 }, (_, index) => <div key={index} className="h-24 animate-pulse rounded-xl bg-slate-200/70" />)}</div>
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [viewing, setViewing] = useState(null)

  const refresh = useCallback(async ({ initial = false } = {}) => {
    if (initial) setLoading(true)
    try {
      const result = await listDocuments(PAGE_SIZE, page * PAGE_SIZE)
      setDocuments(result.documents || [])
      setTotal(result.total || 0)
      setListError('')
    } catch (err) {
      setListError(err.message || 'Could not load documents.')
    } finally {
      if (initial) setLoading(false)
    }
  }, [page])

  useEffect(() => { refresh({ initial: true }) }, [refresh])

  const hasProcessing = documents.some((document) => ['pending', 'processing'].includes(String(document.status).toLowerCase()))
  useEffect(() => {
    if (!hasProcessing) return undefined
    const interval = window.setInterval(() => refresh(), 3000)
    return () => window.clearInterval(interval)
  }, [hasProcessing, refresh])

  async function refreshAfterUpload() {
    if (page !== 0) setPage(0)
    else await refresh()
  }

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <Layout>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
        <div className="mb-7 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-indigo-600">Workspace</p>
            <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">Documents</h1>
          </div>
          <p className="text-sm text-slate-500"><span className="font-semibold text-slate-800">{total}</span> {total === 1 ? 'document' : 'documents'}</p>
        </div>

        <UploadBox onUploaded={refreshAfterUpload} />

        <section className="mt-8" aria-labelledby="uploaded-documents-heading">
          <div className="mb-4 flex items-center justify-between">
            <h2 id="uploaded-documents-heading" className="text-lg font-semibold text-slate-900">Your files</h2>
            {hasProcessing && <p className="text-xs font-medium text-amber-700" role="status">Refreshing processing status…</p>}
          </div>

          {listError && <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{listError}</div>}
          {loading ? <LoadingRows /> : documents.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-5 py-12 text-center text-sm text-slate-600">No documents yet. Upload a PDF or DOCX to begin.</div>
          ) : (
            <div className="space-y-3">
              {documents.map((document) => <DocumentRow key={document.id} document={document} onRefresh={refresh} onViewChunks={setViewing} />)}
            </div>
          )}

          {!loading && total > PAGE_SIZE && <nav aria-label="Document pages" className="mt-5 flex items-center justify-between">
            <p className="text-sm text-slate-500">Page {page + 1} of {pageCount}</p>
            <div className="flex gap-2">
              <button type="button" disabled={page === 0} onClick={() => setPage((current) => Math.max(0, current - 1))} className="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-white focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-40">Previous</button>
              <button type="button" disabled={page + 1 >= pageCount} onClick={() => setPage((current) => Math.min(pageCount - 1, current + 1))} className="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-white focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-40">Next</button>
            </div>
          </nav>}
        </section>
      </main>
      {viewing && <ChunkViewer document={viewing} onClose={() => setViewing(null)} />}
    </Layout>
  )
}
