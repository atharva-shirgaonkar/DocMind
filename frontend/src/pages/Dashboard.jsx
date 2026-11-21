import Layout from '../components/Layout.jsx'
import { useAuth } from '../auth/AuthContext.jsx'
import { Link } from 'react-router-dom'

const sections = [
  { title: 'Documents', description: 'Upload and organize your team’s files.', symbol: '▤' },
  { title: 'Ask', description: 'Find answers grounded in your documents.', symbol: '⌕' },
  { title: 'History', description: 'Return to your recent questions and answers.', symbol: '◷' },
]

export default function Dashboard() {
  const { user } = useAuth()
  const firstName = user?.full_name?.trim().split(/\s+/)[0]

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
            return title === 'Documents'
              ? <Link key={title} to="/documents" className="block rounded-2xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">{card}</Link>
              : <div key={title}>{card}</div>
          })}
        </div>
      </main>
    </Layout>
  )
}
