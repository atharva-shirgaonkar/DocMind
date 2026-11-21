import { request } from './client.js'

export function listHistory(limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return request(`/history?${params}`)
}

export function getHistory(id) {
  return request(`/history/${encodeURIComponent(id)}`)
}

export function deleteHistory(id) {
  return request(`/history/${encodeURIComponent(id)}`, { method: 'DELETE' })
}
