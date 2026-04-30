import axios from 'axios'
import type { User } from './types'

const api = axios.create({ baseURL: '/api/v1' })

export interface RequestMetricsSummary {
  window_seconds: number
  requests: number
  server_errors: number
  client_errors: number
  error_rate_5xx: number
  error_rate_4xx: number
  avg_latency_ms: number
  p95_latency_ms: number
}

export interface SystemTaskSummary {
  workers_online: number
  worker_names: string[]
  ping_ok: boolean
  active_tasks: number
  reserved_tasks: number
  scheduled_tasks: number
  queue_depth: Record<string, number>
  error?: string
}

export interface SystemHealthResponse {
  status: string
  database: string
  redis: string
  uptime_seconds: number
  python_version: string
  active_connections: number
  api_metrics: RequestMetricsSummary
  backend_api_metrics: RequestMetricsSummary
  observability: {
    sentry_enabled: boolean
    langfuse_enabled: boolean
  }
  task_summary: SystemTaskSummary
}

export interface TenantSummary {
  id: string
  name: string
  plan: string | null
  status: string | null
  created_at: string | null
  user_count: number
  document_count: number
  total_actions: number
  total_cost: number
}

export interface TenantUserSummary {
  id: string
  email: string
  full_name?: string | null
  role?: string | null
  status?: string | null
}

export interface TenantRecentAction {
  id: string
  action: string
  actor_user_id?: string | null
  created_at?: string | null
}

export interface TenantStatsResponse {
  tenant_id: string
  tenant_name: string
  plan: string | null
  status: string | null
  created_at: string | null
  user_count: number
  document_count: number
  conversation_count: number
  total_input_tokens: number
  total_output_tokens: number
  total_pinecone_queries: number
  total_embedding_calls: number
  total_cost: number
  total_actions: number
  recent_actions: TenantRecentAction[]
  users: TenantUserSummary[]
}

export interface LLMQualitySummary {
  tenant_id?: string | null
  window_days: number
  trace_count: number
  avg_latency_ms: number
  p95_latency_ms: number
  total_cost_usd: number
  positive_feedback: number
  negative_feedback: number
  positive_feedback_rate?: number | null
  langfuse_enabled: boolean
  source: string
}

// ─── Request interceptor: attach JWT ───
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ─── Response interceptor: auto-logout on 401 ───
// Don't redirect if already on login page (prevents interference with login flow)
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ─── Auth ───
export const authApi = {
  login: async (email: string, password: string) => {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    const { data } = await api.post<{ access_token: string }>('/auth/login/access-token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },
  me: () => api.get<User>('/users/me').then(r => r.data),
}

// ─── Platform Admin ───
export const adminApi = {
  dashboard: () => api.get('/admin/dashboard').then(r => r.data),
  tenants: (params?: Record<string, string>) => api.get<TenantSummary[]>('/admin/tenants', { params }).then(r => r.data),
  tenantStats: (id: string) => api.get<TenantStatsResponse>(`/admin/tenants/${id}/stats`).then(r => r.data),
  updateTenant: (id: string, data: Record<string, unknown>) => api.put(`/admin/tenants/${id}`, data).then(r => r.data),
  users: (params?: Record<string, string>) => api.get('/admin/users', { params }).then(r => r.data),
  systemHealth: () => api.get<SystemHealthResponse>('/admin/system/health').then(r => r.data),
  systemTasks: () => api.get<SystemTaskSummary>('/admin/system/tasks').then(r => r.data),
  llmQuality: (params?: Record<string, string>) => api.get<LLMQualitySummary>('/admin/llm/quality', { params }).then(r => r.data),
  // ─ Quota Management ─
  tenantQuota: (id: string) => api.get(`/admin/tenants/${id}/quota`).then(r => r.data),
  updateQuota: (id: string, data: Record<string, unknown>) => api.put(`/admin/tenants/${id}/quota`, data).then(r => r.data),
  applyPlan: (id: string, plan: string) => api.post(`/admin/tenants/${id}/quota/apply-plan?plan=${plan}`).then(r => r.data),
  tenantAlerts: (id: string) => api.get(`/admin/tenants/${id}/alerts`).then(r => r.data),
  checkAlerts: (id: string) => api.post(`/admin/tenants/${id}/alerts/check`).then(r => r.data),
  quotaPlans: () => api.get('/admin/quota/plans').then(r => r.data),
  // ─ Security Config ─
  tenantSecurity: (id: string) => api.get(`/admin/tenants/${id}/security`).then(r => r.data),
  updateSecurity: (id: string, data: Record<string, unknown>) => api.put(`/admin/tenants/${id}/security`, data).then(r => r.data),
  // ─ Monitoring Center ─
  monitoringAlerts: (params?: Record<string, string>) =>
    api.get<MonitoringAlertsResponse>('/admin/monitoring/alerts', { params }).then(r => r.data),
}

// ─── Monitoring ───
export interface MonitoringAlertItem {
  id: string
  tenant_id: string
  tenant_name: string
  alert_type: 'exceeded' | 'warning'
  resource: string
  current_value: number
  limit_value: number | null
  usage_ratio: number
  message: string | null
  notified: boolean
  created_at: string | null
}

export interface MonitoringAlertsResponse {
  total: number
  exceeded_count: number
  warning_count: number
  alerts: MonitoringAlertItem[]
}

// ─── Cost Analytics ───
export const analyticsApi = {
  dailyTrend: (params?: Record<string, string>) =>
    api.get('/analytics/trends/daily', { params }).then(r => r.data),
  monthlyByTenant: (params?: Record<string, string>) =>
    api.get('/analytics/trends/monthly-by-tenant', { params }).then(r => r.data),
  anomalies: (params?: Record<string, string>) =>
    api.get('/analytics/anomalies', { params }).then(r => r.data),
  budgetAlerts: () => api.get('/analytics/budget-alerts').then(r => r.data),
  // ─ P&L ─
  platformPnl: (params?: Record<string, string>) =>
    api.get('/analytics/platform-pnl', { params }).then(r => r.data),
  tenantPnl: (params?: Record<string, string>) =>
    api.get('/analytics/tenant-pnl', { params }).then(r => r.data),
}

export default api
