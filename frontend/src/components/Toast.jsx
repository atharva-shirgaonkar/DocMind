import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toast, setToast] = useState(null)
  const showToast = useCallback((message, type = 'success') => setToast({ id: Date.now(), message, type }), [])
  useEffect(() => {
    if (!toast) return undefined
    const timeout = window.setTimeout(() => setToast(null), 4000)
    return () => window.clearTimeout(timeout)
  }, [toast])

  return <ToastContext.Provider value={showToast}>
    {children}
    {toast && <div className="fixed bottom-4 right-4 z-[60] flex max-w-sm items-start gap-3 rounded-xl border bg-white px-4 py-3 shadow-lg" role={toast.type === 'error' ? 'alert' : 'status'} aria-live={toast.type === 'error' ? 'assertive' : 'polite'}>
      <span className={`mt-0.5 size-2.5 shrink-0 rounded-full ${toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'}`} aria-hidden="true" />
      <p className="text-sm text-slate-800">{toast.message}</p>
      <button type="button" aria-label="Dismiss notification" onClick={() => setToast(null)} className="ml-auto rounded px-1 text-slate-500 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-indigo-600">×</button>
    </div>}
  </ToastContext.Provider>
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside ToastProvider')
  return context
}
