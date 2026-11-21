import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import * as api from '../api/client.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const restoreSession = useCallback(async () => {
    if (!api.getToken()) {
      setLoading(false)
      return
    }
    try {
      const currentUser = await api.getMe()
      setUser(currentUser)
      setError('')
    } catch (err) {
      api.clearToken()
      setUser(null)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    restoreSession()
  }, [restoreSession])

  const signIn = useCallback(async (email, password) => {
    setLoading(true)
    setError('')
    try {
      await api.login(email, password)
      const currentUser = await api.getMe()
      setUser(currentUser)
      return currentUser
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const signUp = useCallback(async (tenantName, email, password, fullName) => {
    setLoading(true)
    setError('')
    try {
      await api.register(tenantName, email, password, fullName)
      const currentUser = await api.getMe()
      setUser(currentUser)
      return currentUser
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    api.clearToken()
    setUser(null)
    setError('')
  }, [])

  const value = useMemo(() => ({
    user,
    loading,
    error,
    login: signIn,
    register: signUp,
    logout,
  }), [user, loading, error, signIn, signUp, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
