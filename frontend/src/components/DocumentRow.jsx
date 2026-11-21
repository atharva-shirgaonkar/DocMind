import { useState } from 'react'
import { deleteDocument, reprocessDocument } from '../api/documents.js'
import ConfirmDialog from './ConfirmDialog.jsx'
import StatusBadge from './StatusBadge.jsx'
import { useToast } from './Toast.jsx'

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric' }).format(new Date(value))
}

export default function DocumentRow({ document, onRefresh, onViewChunks }) {
  const [action, setAction] = useState('')
  const [error, setError] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)
  const toast = useToast()
  const busy = Boolean(action)
  const displayName = document.original_filename || document.filename || 'Untitled document'

  async function retry() {
    setAction('retry')
    setError('')
    try {
      await reprocessDocument(document.id)
      toast('Document queued for reprocessing.')
      await onRefresh()
    } catch (err) {
      toast(err.message, 'error')
      setError(err.message)
    } finally {
      setAction('')
    }
  }

  async function remove() {
    setAction('delete')
    setError('')
    try {
      await deleteDocument(document.id)
      setConfirmOpen(false)
      toast('Document deleted.')
      await onRefresh()
    } catch (err) {
      setConfirmOpen(false)
      toast(err.message, 'error')
      setError(err.message)
    } finally {
      setAction('')
    }
  }

  return (
    <>
      <article className="grid gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:p-5">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="max-w-full truncate font-semibold text-slate-900" title={displayName}>{displayName}</h2>
            <StatusBadge status={document.status} />
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 sm:text-sm">
            <span>{String(document.file_type || '').toUpperCase()}</span>
            <span>{formatSize(document.file_size_bytes || 0)}</span>
            <span>{document.chunk_count || 0} chunks</span>
            <span>Uploaded {formatDate(document.created_at)}</span>
          </div>
          {document.status === 'failed' && document.error_message && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{document.error_message}</p>}
          {error && <p role="alert" className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
        </div>
        <div className="flex flex-wrap gap-2 sm:justify-end">
          {document.status === 'ready' && <button type="button" disabled={busy} onClick={() => onViewChunks(document)} className="min-h-9 rounded-lg border border-slate-300 px-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:opacity-50">View chunks</button>}
          {document.status === 'failed' && <button type="button" disabled={busy} onClick={retry} className="min-h-9 rounded-lg bg-indigo-600 px-3 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-300">{action === 'retry' ? 'Retrying…' : 'Retry'}</button>}
          <button type="button" disabled={busy} onClick={() => setConfirmOpen(true)} className="min-h-9 rounded-lg border border-red-200 px-3 text-sm font-semibold text-red-700 hover:bg-red-50 focus-visible:outline-2 focus-visible:outline-red-600 disabled:cursor-not-allowed disabled:opacity-50">{action === 'delete' ? 'Deleting…' : 'Delete'}</button>
        </div>
      </article>
      <ConfirmDialog
        open={confirmOpen}
        title={`Delete ${displayName}?`}
        description="This removes its chunks and cannot be undone."
        busy={action === 'delete'}
        onConfirm={remove}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  )
}
