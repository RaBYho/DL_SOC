/**
 * REST API client for NIDS SOC Dashboard.
 */

const API_BASE = "/api/dashboard"

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    const errorBody = await response.text()
    throw new Error(`API Error [${response.status}] ${url}: ${errorBody}`)
  }

  return response.json()
}

export const api = {
  getInitState: () => request("/init"),
  getRecentFlows: (limit = 100, threatOnly = false, excludeLoopback = false) =>
    request(`/flows/recent?limit=${limit}&threat_only=${threatOnly}&exclude_loopback=${excludeLoopback}`),
  getThreatActors: (limit = 50, excludeLoopback = false) =>
    request(`/threat-actors?limit=${limit}&exclude_loopback=${excludeLoopback}`),
  getTargetedStats: (excludeLoopback = false) =>
    request(`/stats/targets?exclude_loopback=${excludeLoopback}`),
  getTimeline: (windowMinutes = 15, buckets = 20, excludeLoopback = false) =>
    request(`/stats/timeline?window_minutes=${windowMinutes}&buckets=${buckets}&exclude_loopback=${excludeLoopback}`),
  getEngineDistribution: (excludeLoopback = false) =>
    request(`/stats/engine-distribution?exclude_loopback=${excludeLoopback}`),
  getFlowForensics: (flowId) => request(`/flows/${flowId}/forensics`),
  getAlerts: (params = {}) => {
    const searchParams = new URLSearchParams()
    if (params.limit) searchParams.append("limit", params.limit)
    if (params.offset) searchParams.append("offset", params.offset)
    if (params.severity) searchParams.append("severity", params.severity)
    if (params.status) searchParams.append("status", params.status)
    if (params.search) searchParams.append("search", params.search)
    if (params.exclude_loopback !== undefined) searchParams.append("exclude_loopback", params.exclude_loopback)
    return request(`/alerts?${searchParams.toString()}`)
  },
  updateAlertStatus: (incidentId, status, notes = "") =>
    request(`/alerts/${incidentId}/status`, {
      method: "POST",
      body: JSON.stringify({ status, notes }),
    }),
  getPcaps: () => request("/pcaps"),
  startReplay: (pcapPath, speed = 1.0) =>
    request("/replay/start", {
      method: "POST",
      body: JSON.stringify({ pcap_path: pcapPath, speed_multiplier: speed }),
    }),
  resetDatabase: () =>
    request("/flows/reset", {
      method: "POST",
    }),
  getModels: () => request("/models"),
}
