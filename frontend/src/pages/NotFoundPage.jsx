import { Link } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import PageTitle from '../components/PageTitle.jsx'

export default function NotFoundPage() {
  return <Layout><PageTitle title="Page not found" /><main className="mx-auto max-w-3xl px-5 py-24 text-center"><p className="text-sm font-semibold text-indigo-600">404</p><h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Page not found</h1><p className="mt-3 text-slate-600">That page doesn’t exist or may have moved.</p><Link to="/" className="mt-6 inline-flex rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">Back to dashboard</Link></main></Layout>
}
