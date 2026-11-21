const styles = {
  pending: 'bg-slate-100 text-slate-700',
  processing: 'bg-amber-50 text-amber-800',
  ready: 'bg-green-50 text-green-800',
  failed: 'bg-red-50 text-red-700',
}

export default function StatusBadge({ status }) {
  const value = String(status || 'pending').toLowerCase()
  const label = value.charAt(0).toUpperCase() + value.slice(1)
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-xs font-semibold ${styles[value] || styles.pending}`}>
      {value === 'processing' && <span className="size-3 animate-spin rounded-full border-2 border-amber-700/30 border-t-amber-700" aria-hidden="true" />}
      {label}
    </span>
  )
}
