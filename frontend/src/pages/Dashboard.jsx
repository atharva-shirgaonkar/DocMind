import Layout from '../components/Layout.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getUsageMetrics } from '../api/metrics.js'

const sections = [
  { title: 'Documents', description: 'Upload and organize your team’s files.', symbol: '▤' },
  { title: 'Ask', description: 'Find answers grounded in your documents.', symbol: '?' },
  { title: 'History', description: 'Return to your recent questions and answers.', symbol: '↺' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const firstName = user?.full_name?.trim().split(/\s+/)[0]
  const [metrics, setMetrics] = useState(null)
  const [metricsLoading, setMetricsLoading] = useState(true)
  const [metricsError, setMetricsError] = useState('')

  useEffect(() => {
    getUsageMetrics().then(setMetrics).catch((err) => setMetricsError(err.message)).finally(() => setMetricsLoading(false))
  }, [])

  return (
    <Layout>
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
        <div className="mb-9">
          <p className="text-sm font-semibold text-indigo-600">Your workspace</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Welcome{firstName ? `, ${firstName}` : ''}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600">
            <span>{user?.tenant_name || 'Your organization'}</span>
            <span aria-hidden="true" className="text-slate-300">·</span>
            <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold capitalize text-indigo-700">{user?.role?.toLowerCase()}</span>
          </div>
        </div>

        <section aria-label="Usage metrics" className="mb-8">
          {metricsError && <p role="alert" className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">{metricsError}</p>}
          {metricsLoading ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[0, 1, 2, 3].map((index) => <div key={index} className="h-28 animate-pulse rounded-2xl bg-slate-200/70" />)}</div> : metrics && <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard title="Documents" value={metrics.total_documents} detail={`${metrics.documents_by_status?.ready || 0} ready · ${metrics.documents_by_status?.processing || 0} processing`} />
            <MetricCard title="Chunks" value={metrics.total_chunks} detail="Across your workspace" />
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Questions · 24 hours</p><p className="mt-2 text-2xl font-bold text-slate-900">{metrics.queries_last_24h}<span className="text-base font-medium text-slate-400"> / {metrics.daily_query_limit}</span></p>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600" style={{ width: `${Math.min(100, metrics.daily_query_limit ? (metrics.queries_last_24h / metrics.daily_query_limit) * 100 : 100)}%` }} /></div>
              <p className="mt-2 text-xs text-slate-500">{metrics.queries_remaining} remaining</p>
            </div>
            <MetricCard title="Avg. response" value={metrics.avg_latency_ms == null ? 'n/a' : `${metrics.avg_latency_ms} ms`} detail="Last 24 hours" />
          </div>}
        </section>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {sections.map(({ title, description, symbol }) => {
            const card = (
              <section className="h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
              <span className="grid size-11 place-items-center rounded-xl bg-indigo-50 text-indigo-600">
                <span className="text-xl font-semibold" aria-hidden="true">{symbol}</span>
              </span>
              <h2 className="mt-5 text-lg font-semibold text-slate-900">{title}</h2>
              <p className="mt-1.5 min-h-10 text-sm leading-6 text-slate-600">{description}</p>
              <span className="mt-5 inline-flex rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">Coming soon</span>
              </section>
            )
            const target = title === 'Documents' ? '/documents' : title === 'Ask' ? '/chat' : '/history'
            return <Link key={title} to={target} className="block rounded-2xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">{card}</Link>
          })}
        </div>
      </main>
    </Layout>
  )
}

function MetricCard({ title, value, detail }) {
  return <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p><p className="mt-2 text-2xl font-bold text-slate-900">{value}</p><p className="mt-2 text-xs text-slate-500">{detail}</p></div>
}
