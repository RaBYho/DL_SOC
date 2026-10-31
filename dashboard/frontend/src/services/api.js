// Centralized API Client for DL_SOC Dashboard

const BASE_URL = '/api/dashboard'

async function request(endpoint, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    })
    if (!res.ok) {
      const errText = await res.text()
      throw new Error(`API Error ${res.status}: ${errText}`)
    }
    return await res.json()
  } catch (err) {
    console.error(`[API Error] ${endpoint}:`, err)
    throw err
  }
}

export const api = {
  getInitData: (timeRange = '15m') => request(`/init?time_range=${encodeURIComponent(timeRange)}`),
  getPcaps: () => request('/pcaps'),
  startReplay: (pcapName, speed = 1.0) => 
    request(`/replay/start?pcap_name=${encodeURIComponent(pcapName)}&speed=${speed}`, { method: 'POST' }),
  pauseReplay: () => request('/replay/pause', { method: 'POST' }),
  resumeReplay: () => request('/replay/resume', { method: 'POST' }),
  stopReplay: () => request('/replay/stop', { method: 'POST' }),
  getReplayStatus: () => request('/replay/status'),
  getSensors: () => request('/sensors'),
  getAlerts: (limit = 100, offset = 0, pred = null, anomalieOnly = false) => {
    const params = new URLSearchParams({ limit, offset, anomalie_only: anomalieOnly })
    if (pred) params.append('pred', pred)
    return request(`/alerts?${params.toString()}`)
  },
  resetDatabase: () => request('/database/reset', { method: 'POST' }),
  updateSettings: (settings) => request('/settings', { method: 'POST', body: JSON.stringify(settings) }),
  getModelLogs: (limit = 100) => request(`/models/logs?limit=${limit}`),
  clearModelLogs: () => request('/models/logs/clear', { method: 'POST' }),
  getSystemHealth: () => request('/system/health'),
  getSystemLogs: (limit = 50, level = null) => {
    const params = new URLSearchParams({ limit })
    if (level) params.append('level', level)
    return request(`/system/logs?${params.toString()}`)
  },
  optimizeDatabase: () => request('/system/optimize-db', { method: 'POST' }),
  testComponent: (component = 'all') => request('/system/test-component', { method: 'POST', body: JSON.stringify({ component }) }),
  getNotificationSettings: () => request('/settings/notifications'),
  updateNotificationSettings: (settings) => request('/settings/notifications', { method: 'POST', body: JSON.stringify(settings) }),
  testTelegramNotification: (payload = {}) => request('/notifications/test-telegram', { method: 'POST', body: JSON.stringify(payload) }),
  testEmailNotification: (payload = {}) => request('/notifications/test-email', { method: 'POST', body: JSON.stringify(payload) }),
  submitIncidentFeedback: (incidentId, payload) => request(`/incidents/${incidentId}/feedback`, { method: 'POST', body: JSON.stringify(payload) }),
  getIncidentFeedback: (incidentId) => request(`/incidents/${incidentId}/feedback`),
  getFeedbackSummary: () => request('/feedback/summary'),
  getFeedbackExportUrl: (format = 'json') => `${BASE_URL}/feedback/export?format=${format}`,
  analyzeIncidentAi: (incidentId, flow) => request(`/incidents/${incidentId}/ai-analysis`, { method: 'POST', body: JSON.stringify({ flow }) }),
  getAiSettings: () => request('/settings/ai'),
  updateAiSettings: (settings) => request('/settings/ai', { method: 'POST', body: JSON.stringify(settings) }),
  testAiConnection: (settings = {}) => request('/ai/test', { method: 'POST', body: JSON.stringify(settings) })
}
