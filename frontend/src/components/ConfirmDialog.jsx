import { useEffect, useRef } from 'react'

export default function ConfirmDialog({ open, title, description, confirmLabel = 'Delete', busy = false, onConfirm, onCancel }) {
  const safeButton = useRef(null)

  useEffect(() => {
    if (!open) return undefined
    safeButton.current?.focus()
    function onKeyDown(event) {
      if (event.key === 'Escape' && !busy) onCancel()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, busy, onCancel])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget && !busy) onCancel() }}>
      <section role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-description" className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <h2 id="confirm-title" className="text-lg font-semibold text-slate-900">{title}</h2>
        <p id="confirm-description" className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button ref={safeButton} type="button" disabled={busy} onClick={onCancel} className="min-h-10 rounded-lg border border-slate-300 px-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50">Cancel</button>
          <button type="button" disabled={busy} onClick={onConfirm} className="min-h-10 rounded-lg bg-red-600 px-4 text-sm font-semibold text-white hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600 disabled:cursor-not-allowed disabled:bg-red-300">{busy ? 'Deleting…' : confirmLabel}</button>
        </div>
      </section>
    </div>
  )
}
