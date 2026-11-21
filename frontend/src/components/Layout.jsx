import { useAuth } from '../auth/AuthContext.jsx'

function BrandMark() {
  return <span className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-lg font-bold text-white shadow-sm" aria-hidden="true">D</span>
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const organization = user?.tenant_name || 'Your organization'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <a href="/" className="flex items-center gap-3 rounded-lg text-slate-900 no-underline">
            <BrandMark />
            <span className="text-lg font-bold tracking-tight">DocMind</span>
          </a>
          <div className="flex items-center gap-3 sm:gap-5">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-slate-800">{user?.email}</p>
              <p className="text-xs text-slate-500">{organization}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              <span aria-hidden="true">↗</span>
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </header>
      {children}
    </div>
  )
}
