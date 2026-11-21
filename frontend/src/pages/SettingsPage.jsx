import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { generateApiKey, revokeApiKey } from '../api/apikey.js'

export default function SettingsPage() {
  const { user } = useAuth()
  const [key, setKey] = useState('')
  const [note, setNote] = useState('')
  const [showRevoke, setShowRevoke] = useState(false)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => () => setKey(''), [])

  async function createKey() {
    setWorking(true)
    setError('')
    setNotice('')
    setKey('')
    try {
      const result = await generateApiKey()
      setKey(result.api_key)
      setNote(result.note)
    } catch (err) {
      setError(err.message)
    } finally {
      setWorking(false)
    }
  }

  async function copyKey() {
    try {
      await navigator.clipboard.writeText(key)
      setNotice('API key copied. Keep it somewhere secure.')
    } catch {
      setError('Could not access the clipboard. Select and copy the key manually.')
    }
  }

  async function removeKey() {
    setWorking(true)
    setError('')
    try {
      await revokeApiKey()
      setKey('')
      setNote('')
      setShowRevoke(false)
      setNotice('API key revoked.')
    } catch (err) {
      setError(err.message)
      setShowRevoke(false)
    } finally {
      setWorking(false)
    }
  }

  return <Layout>
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <p className="text-sm font-semibold text-indigo-600">Personalize access</p>
      <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
      {error && <p role="alert" className="mt-5 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{error}</p>}
      {notice && <p role="status" className="mt-5 rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">{notice}</p>}

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <h2 className="text-lg font-semibold text-slate-900">Account</h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Email</dt><dd className="mt-1 break-all text-sm text-slate-800">{user?.email}</dd></div>
          <div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Organization</dt><dd className="mt-1 text-sm text-slate-800">{user?.tenant_name}</dd></div>
          <div><dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">Role</dt><dd className="mt-1 text-sm capitalize text-slate-800">{user?.role?.toLowerCase()}</dd></div>
        </dl>
      </section>

      <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div><h2 className="text-lg font-semibold text-slate-900">API key</h2><p className="mt-1 max-w-lg text-sm leading-6 text-slate-600">Generate a key for API access. The full key is shown only once and is never saved in your browser storage.</p></div>
          <button type="button" disabled={working} onClick={createKey} className="min-h-10 rounded-lg bg-indigo-600 px-4 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:bg-indigo-300">{working ? 'Working…' : key ? 'Generate new key' : 'Generate key'}</button>
        </div>
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">Generating a new key replaces the previous key immediately.</p>
        {key && <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
          <p className="text-sm font-semibold text-indigo-900">Your new API key</p>
          <code className="mt-2 block break-all rounded-lg bg-white p-3 font-mono text-sm text-slate-800">{key}</code>
          <p className="mt-2 text-xs text-indigo-800">{note}</p>
          <div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={copyKey} className="min-h-9 rounded-lg bg-indigo-600 px-3 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-indigo-600">Copy</button><button type="button" onClick={() => setKey('')} className="min-h-9 rounded-lg border border-indigo-200 px-3 text-sm font-semibold text-indigo-800 hover:bg-white focus-visible:outline-2 focus-visible:outline-indigo-600">Dismiss key</button></div>
        </div>}
        <div className="mt-5 border-t border-slate-100 pt-5"><button type="button" disabled={working} onClick={() => setShowRevoke(true)} className="min-h-10 rounded-lg border border-red-200 px-4 text-sm font-semibold text-red-700 hover:bg-red-50 focus-visible:outline-2 focus-visible:outline-red-600 disabled:opacity-50">Revoke key</button></div>
      </section>
    </main>
    <ConfirmDialog open={showRevoke} title="Revoke your API key?" description="Applications using this key will no longer be able to authenticate." busy={working} onConfirm={removeKey} onCancel={() => setShowRevoke(false)} />
  </Layout>
}
