const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')
const TOKEN_KEY = 'docmind_token'

export function getToken() {
  return window.localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  window.localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY)
}

export async function request(path, { method = 'GET', body, headers = {}, loginCall = false, includeStatus = false } = {}) {
  const requestHeaders = new Headers(headers)
  const token = getToken()
  if (token) requestHeaders.set('Authorization', `Bearer ${token}`)

  let requestBody = body
  if (body instanceof FormData) {
    // The browser supplies the multipart boundary.
  } else if (body instanceof URLSearchParams) {
    requestHeaders.set('Content-Type', 'application/x-www-form-urlencoded;charset=UTF-8')
  } else if (body !== undefined) {
    requestHeaders.set('Content-Type', 'application/json')
    requestBody = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: requestHeaders,
    body: requestBody,
  })

  if (response.status === 401 && !loginCall) {
    clearToken()
    window.location.assign('/login')
  }

  if (response.status === 204) return includeStatus ? { data: null, status: response.status } : null

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json().catch(() => null)
    : null

  if (!response.ok) {
    if (response.status === 429) {
      const retryAfter = response.headers.get('Retry-After')
      const wait = retryAfter ? ` Please retry in ${retryAfter} seconds.` : ''
      throw new Error(`Too many requests. Please wait a moment.${wait}`)
    }
    throw new Error(typeof payload?.detail === 'string' ? payload.detail : 'Something went wrong. Please try again.')
  }

  return includeStatus ? { data: payload, status: response.status } : payload
}

export async function login(email, password) {
  const form = new URLSearchParams({ username: email, password })
  const result = await request('/auth/login', { method: 'POST', body: form, loginCall: true })
  if (result?.access_token) setToken(result.access_token)
  return result
}

export async function register(tenantName, email, password, fullName) {
  const result = await request('/auth/register', {
    method: 'POST',
    body: {
      tenant_name: tenantName,
      email,
      password,
      full_name: fullName || null,
    },
  })
  if (result?.access_token) setToken(result.access_token)
  return result
}

export function getMe() {
  return request('/auth/me')
}
