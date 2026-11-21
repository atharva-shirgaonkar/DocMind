import { request } from './client.js'

export function generateApiKey() {
  return request('/auth/api-key', { method: 'POST' })
}

export function revokeApiKey() {
  return request('/auth/api-key', { method: 'DELETE' })
}
