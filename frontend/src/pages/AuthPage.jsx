import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import PageTitle from '../components/PageTitle.jsx'

export default function AuthPage() {
  const { user, login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [organization, setOrganization] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const isRegister = mode === 'register'

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      if (isRegister) await register(organization.trim(), email.trim(), password, fullName.trim())
      else await login(email.trim(), password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message || 'Unable to sign in. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-50 px-4 py-10 sm:px-6">
      <PageTitle title={isRegister ? 'Create account' : 'Sign in'} />
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-4 grid size-12 place-items-center rounded-2xl bg-indigo-600 text-xl font-bold text-white shadow-md shadow-indigo-200" aria-hidden="true">D</span>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Welcome to DocMind</h1>
          <p className="mt-2 text-sm text-slate-600">Your documents, ready to search and understand.</p>
        </div>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-lg shadow-slate-200/60 sm:p-8">
          <div className="grid grid-cols-2 rounded-xl bg-slate-100 p-1" role="tablist" aria-label="Account access">
            <button
              type="button"
              role="tab"
              aria-selected={!isRegister}
              onClick={() => { setMode('login'); setError('') }}
              className={`rounded-lg px-3 py-2.5 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-indigo-600 ${!isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
            >Sign in</button>
            <button
              type="button"
              role="tab"
              aria-selected={isRegister}
              onClick={() => { setMode('register'); setError('') }}
              className={`rounded-lg px-3 py-2.5 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-indigo-600 ${isRegister ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
            >Create account</button>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            {isRegister && (
              <>
                <div>
                  <label htmlFor="organization" className="mb-1.5 block text-sm font-medium text-slate-700">Organization name</label>
                  <input id="organization" name="organization" required autoComplete="organization" value={organization} onChange={(event) => setOrganization(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100" placeholder="Acme Inc." />
                </div>
                <div>
                  <label htmlFor="fullName" className="mb-1.5 block text-sm font-medium text-slate-700">Full name <span className="font-normal text-slate-400">(optional)</span></label>
                  <input id="fullName" name="fullName" autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100" placeholder="Your name" />
                </div>
              </>
            )}
            <div>
              <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
              <input id="email" name="email" type="email" required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100" placeholder="you@company.com" />
            </div>
            <div>
              <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
              <input id="password" name="password" type="password" required minLength={8} autoComplete={isRegister ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3.5 py-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-4 focus:ring-indigo-100" placeholder="At least 8 characters" />
              {isRegister && <p className="mt-1.5 text-xs text-slate-500">Use at least 8 characters.</p>}
            </div>

            {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3.5 py-3 text-sm text-red-700">{error}</div>}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-300"
            >
              {submitting ? (isRegister ? 'Creating account…' : 'Signing in…') : (isRegister ? 'Create account' : 'Sign in')}
              {!submitting && <span aria-hidden="true">→</span>}
            </button>
          </form>
        </section>
        <p className="mt-6 text-center text-xs text-slate-500">Secure access to your team’s document workspace.</p>
      </div>
    </main>
  )
}
