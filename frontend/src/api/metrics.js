import { request } from './client.js'

export function getUsageMetrics() {
  return request('/metrics/usage')
}
