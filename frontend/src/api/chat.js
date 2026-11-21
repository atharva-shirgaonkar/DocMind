import { request } from './client.js'

export function askQuestion({ question, top_k = 4, document_id, mode = 'hybrid' }) {
  return request('/ask', { method: 'POST', body: { question, top_k, document_id: document_id || null, mode } })
}

export function searchChunks({ query, top_k = 4, document_id, mode = 'hybrid' }) {
  return request('/search', { method: 'POST', body: { query, top_k, document_id: document_id || null, mode } })
}
