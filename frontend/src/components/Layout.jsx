import { useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

function BrandMark() {
  return <span className="grid size-10 place-items-center rounded-xl bg-indigo-600 text-lg font-bold text-white shadow-sm" aria-hidden="true">D</span>
}

const linkClass = ({ isActive }) => `block rounded-lg px-3 py-2 text-sm font-semibold transition focus-visible:outline-2 focus-visible:outline-indigo-600 ${isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'}`

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const organization = user?.tenant_name || 'Your organization'
  const links = [['Dashboard', '/'], ['Documents', '/documents'], ['Ask', '/chat'], ['History', '/history'], ['Settings', '/settings']]

  return <div className="min-h-screen bg-slate-50">
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-5 gap-y-3 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3 rounded-lg text-slate-900 no-underline"><BrandMark /><span className="text-lg font-bold tracking-tight">DocMind</span></Link>
        <button type="button" aria-expanded={menuOpen} aria-controls="main-navigation" aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'} onClick={() => setMenuOpen((open) => !open)} className="ml-auto grid size-10 place-items-center rounded-lg border border-slate-200 text-slate-700 focus-visible:outline-2 focus-visible:outline-indigo-600 sm:hidden">{menuOpen ? '×' : '☰'}</button>
        <div className="order-2 ml-auto flex items-center gap-3 sm:order-3 sm:ml-auto sm:gap-5">
          <div className="hidden text-right sm:block"><p className="text-sm font-semibold text-slate-800">{user?.email}</p><p className="text-xs text-slate-500">{organization}</p></div>
          <button type="button" onClick={logout} className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"><span aria-hidden="true">↗</span><span>Sign out</span></button>
        </div>
        <nav id="main-navigation" aria-label="Main navigation" className={`${menuOpen ? 'flex' : 'hidden'} order-3 w-full flex-col gap-1 sm:order-2 sm:flex sm:w-auto sm:flex-row`}>
          {links.map(([label, to]) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenuOpen(false)} className={linkClass}>{label}</NavLink>)}
        </nav>
      </div>
    </header>
    {children}
  </div>
}
