import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <main className="grid min-h-screen place-items-center px-6">
        <p className="text-sm font-medium text-slate-500" role="status">Restoring your session…</p>
      </main>
    )
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />
}
