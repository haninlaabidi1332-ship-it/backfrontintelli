import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' }
})

api.interceptors.request.use(config => {
  const token = useCookie('access_token').value
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  async error => {
    if (error.response?.status === 401) {
      const refresh = useCookie('refresh_token').value
      if (refresh) {
        try {
          const { data } = await axios.post('http://localhost:8000/api/auth/jwt/refresh/', { refresh })
          useCookie('access_token').value = data.access
          error.config.headers.Authorization = `Bearer ${data.access}`
          return api.request(error.config)
        } catch {
          useCookie('access_token').value = null
          useCookie('refresh_token').value = null
          navigateTo('/login')
        }
      }
    }
    return Promise.reject(error)
  }
)

export const useApi = () => api

// Auth
export const useAuth = () => ({
  login: (email: string, password: string) =>
    api.post('/auth/jwt/token/', { email, password }),
  logout: () => {
    useCookie('access_token').value = null
    useCookie('refresh_token').value = null
  }
})

// KPIs
export const useKpis = () => ({
  getCurrent: () => api.get('/analytics/kpis/current/'),
  getTrend: (metric: string, days = 7) =>
    api.get(`/analytics/kpis/trend/?metric=${metric}&days=${days}`),
  list: (params?: object) => api.get('/analytics/kpis/', { params })
})

// OLTs
export const useOlts = () => ({
  list: (params?: object) => api.get('/equipements/olts/', { params }),
  get: (id: string) => api.get(`/equipements/olts/${id}/`),
  create: (data: object) => api.post('/equipements/olts/', data),
  update: (id: string, data: object) => api.patch(`/equipements/olts/${id}/`, data),
  delete: (id: string) => api.delete(`/equipements/olts/${id}/`)
})

// ONTs
export const useOnts = () => ({
  list: (params?: object) => api.get('/equipements/onts/', { params }),
  get: (id: string) => api.get(`/equipements/onts/${id}/`),
  create: (data: object) => api.post('/equipements/onts/', data),
  update: (id: string, data: object) => api.patch(`/equipements/onts/${id}/`, data),
  delete: (id: string) => api.delete(`/equipements/onts/${id}/`)
})

// Alerts
export const useAlerts = () => ({
  list: (params?: object) => api.get('/alerting/alerts/', { params }),
  get: (id: string) => api.get(`/alerting/alerts/${id}/`),
  acknowledge: (id: string) => api.post(`/alerting/alerts/${id}/acknowledge/`),
  bulkAcknowledge: (ids: string[]) => api.post('/alerting/alerts/bulk_acknowledge/', { ids }),
  rules: {
    list: () => api.get('/alerting/rules/'),
    toggle: (id: string) => api.post(`/alerting/rules/${id}/toggle/`)
  }
})

// Anomalies
export const useAnomalies = () => ({
  list: (params?: object) => api.get('/ai/anomalies/', { params }),
  resolve: (id: string) => api.post(`/ai/anomalies/${id}/resolve/`),
  run: (oltId: string) => api.post('/ai/anomalies/run/', { olt_id: oltId })
})

// AI Models
export const useAiModels = () => ({
  list: (params?: object) => api.get('/ai/models/', { params }),
  activate: (id: string) => api.post(`/ai/models/${id}/activate/`),
  train: (id: string, dataStart: string, dataEnd: string) =>
    api.post(`/ai/models/${id}/train/`, { data_start: dataStart, data_end: dataEnd })
})

// BFD
export const useBfd = () => ({
  sessions:         (params?: object) => api.get('/bfd/sessions/', { params }),
  history:          (params?: object) => api.get('/bfd/history/',  { params }),
  alerts:           (params?: object) => api.get('/bfd/alerts/',   { params }),
  acknowledgeAlert: (id: string)      => api.post(`/bfd/alerts/${id}/acknowledge/`),
})

// SNMP Metrics
export const useSnmp = () => ({
  metrics:    (params?: object) => api.get('/snmp/metrics/', { params }),
  timeseries: (params?: object) => api.get('/snmp/metrics/timeseries/', { params }),
  latest:     (params?: object) => api.get('/snmp/metrics/latest/', { params }),
  stats:      (params?: object) => api.get('/snmp/metrics/stats/', { params }),
  jobs:       (params?: object) => api.get('/snmp/jobs/', { params })
})

// Reports
export const useReports = () => ({
  list: () => api.get('/analytics/reports/'),
  create: (data: object) => api.post('/analytics/reports/', data),
  download: (id: string) => api.get(`/analytics/reports/${id}/download/`, { responseType: 'blob' })
})

// Network Traffic
export const useNetworkTraffic = () => ({
  list: (params?: object) => api.get('/analytics/network-traffic/', { params }),
  congested: (hours = 1) => api.get(`/analytics/network-traffic/congested/?hours=${hours}`),
  topThroughput: (hours = 1) => api.get(`/analytics/network-traffic/top-throughput/?hours=${hours}`)
})

// AI Assistant (Ollama)
export const useAiAssistant = () => ({
  ask: (question: string, oltId?: number) =>
    api.post('/ai/ask/', { question, ...(oltId ? { olt_id: oltId } : {}) })
})
