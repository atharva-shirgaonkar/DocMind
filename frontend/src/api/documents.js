import { request } from './client.js'

export function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  return request('/documents/upload', { method: 'POST', body: form, includeStatus: true })
}

export function listDocuments(limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return request(`/documents/?${params}`)
}

export function deleteDocument(id) {
  return request(`/documents/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function reprocessDocument(id) {
  return request(`/documents/${encodeURIComponent(id)}/reprocess`, { method: 'POST' })
}

export function listChunks(id, limit = 10, offset = 0) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return request(`/documents/${encodeURIComponent(id)}/chunks?${params}`)
}
