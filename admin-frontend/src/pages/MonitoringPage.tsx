import { useState, useEffect, useRef } from 'react'
import { adminApi } from '../api'
import type { SystemHealthResponse, MonitoringAlertsResponse, MonitoringAlertItem } from '../api'
import {
  AlertTriangle, CheckCircle2, XCircle, RefreshCw,
  Server, Bell, AlertCircle, Loader2, Clock, Activity,
} from 'lucide-react'

// ─── Constants ───────────────────────────────────────────────
const RESOURCE_LABELS: Record<string, string> = {
  users: '使用者',
  documents: '文件',
  storage: '儲存空間',
  queries: '查詢次數',
  tokens: 'Token 量',
}

type AlertFilter = 'all' | 'exceeded' | 'warning'

// ─── Shared primitives ───────────────────────────────────────

function Loader() {
  return (
    <div className="flex h-40 items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
    </div>
  )
}

function SummaryCard({
  icon: Icon, label, value, color,
}: {
  icon: typeof AlertCircle; label: string; value: string | number; color: string
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500">{label}</p>
          <p className="text-xl font-bold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  )
}

function MetricRow({ label, value, danger }: { label: string; value: string | number; danger?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
      <span className="text-xs text-gray-600">{label}</span>
      <span className={`text-xs font-medium ${danger ? 'text-red-600' : 'text-gray-800'}`}>{value}</span>
    </div>
  )
}

function UsageBar({ ratio }: { ratio: number }) {
  const pct = Math.min(ratio * 100, 100)
  const color = ratio >= 1 ? 'bg-red-500' : ratio >= 0.8 ? 'bg-amber-400' : 'bg-green-400'
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-20 overflow-hidden rounded-full bg-gray-200">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700">{pct.toFixed(0)}%</span>
    </div>
  )
}

// ─── System Health Panel ──────────────────────────────────────

function HealthPanel({ health, loading }: { health: SystemHealthResponse | null; loading: boolean }) {
  if (loading && !health) return <Loader />
  if (!health) return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <p className="text-sm text-gray-400">無法取得系統健康資料</p>
    </div>
  )

  const backendMetrics = health.backend_api_metrics ?? {}
  const tasks = health.task_summary ?? {}

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-700">
          <Server className="h-4 w-4" /> 系統健康快照
        </h2>
        {loading && <Loader2 className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {/* 服務狀態 */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">服務狀態</p>
          {[
            { label: 'PostgreSQL', status: health.database },
            { label: 'Redis', status: health.redis },
            { label: 'Celery Worker', status: tasks.ping_ok ? 'healthy' : 'degraded' },
          ].map(s => (
            <div key={s.label} className="flex items-center justify-between rounded-lg bg-gray-50 px-3 py-2">
              <span className="text-xs text-gray-700">{s.label}</span>
              <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                s.status === 'healthy' ? 'text-green-600' : 'text-red-500'
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${s.status === 'healthy' ? 'bg-green-500' : 'bg-red-400'}`} />
                {s.status === 'healthy' ? '正常' : '異常'}
              </span>
            </div>
          ))}
        </div>

        {/* 前台 API 指標 */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">前台 API 指標 (1h)</p>
          <MetricRow label="請求數" value={backendMetrics.requests ?? '—'} />
          <MetricRow
            label="5xx 錯誤率"
            value={backendMetrics.error_rate_5xx != null
              ? `${(backendMetrics.error_rate_5xx * 100).toFixed(2)}%`
              : '—'}
            danger={(backendMetrics.error_rate_5xx ?? 0) > 0.01}
          />
          <MetricRow label="平均延遲" value={backendMetrics.avg_latency_ms != null ? `${backendMetrics.avg_latency_ms} ms` : '—'} />
          <MetricRow label="P95 延遲" value={backendMetrics.p95_latency_ms != null ? `${backendMetrics.p95_latency_ms} ms` : '—'} />
        </div>

        {/* 任務佇列 */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wider text-gray-500">任務佇列</p>
          <MetricRow label="在線 Worker" value={tasks.workers_online ?? 0} />
          <MetricRow label="執行中任務" value={tasks.active_tasks ?? 0} />
          <MetricRow
            label="等待佇列 (celery)"
            value={tasks.queue_depth?.celery ?? 0}
            danger={(tasks.queue_depth?.celery ?? 0) > 10}
          />
          <MetricRow
            label="批次佇列 (bulk)"
            value={tasks.queue_depth?.bulk ?? 0}
            danger={(tasks.queue_depth?.bulk ?? 0) > 5}
          />
          <MetricRow
            label="可觀測性"
            value={[
              health.observability?.sentry_enabled ? 'Sentry ✓' : 'Sentry ✗',
              health.observability?.langfuse_enabled ? 'Langfuse ✓' : 'Langfuse ✗',
            ].join('  ·  ')}
          />
        </div>
      </div>
    </div>
  )
}

// ─── Alerts Table ─────────────────────────────────────────────

function AlertsTable({
  alerts,
  loading,
  filter,
  onFilterChange,
}: {
  alerts: MonitoringAlertItem[]
  loading: boolean
  filter: AlertFilter
  onFilterChange: (f: AlertFilter) => void
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200 bg-white">
      {/* Table header */}
      <div className="flex items-center justify-between border-b border-gray-100 px-5 py-3">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-700">
          <Bell className="h-4 w-4" /> 跨租戶配額告警（近 7 天）
        </h2>
        <div className="flex overflow-hidden rounded-lg border border-gray-200">
          {(['all', 'exceeded', 'warning'] as AlertFilter[]).map(f => (
            <button
              key={f}
              onClick={() => onFilterChange(f)}
              className={`px-3 py-1 text-xs font-medium transition-colors ${
                filter === f ? 'bg-gray-900 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'
              }`}
            >
              {f === 'all' ? '全部' : f === 'exceeded' ? '超額' : '警告'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Loader />
      ) : alerts.length === 0 ? (
        <div className="flex flex-col items-center py-14 text-gray-400">
          <CheckCircle2 className="mb-2 h-8 w-8 text-green-400" />
          <p className="text-sm">此範圍內無告警記錄</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                <th className="px-5 py-3">嚴重度</th>
                <th className="px-5 py-3">租戶</th>
                <th className="px-5 py-3">資源</th>
                <th className="px-5 py-3">使用率</th>
                <th className="px-5 py-3">用量 / 上限</th>
                <th className="px-5 py-3">通知</th>
                <th className="px-5 py-3">時間</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {alerts.map(a => (
                <tr key={a.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
                      a.alert_type === 'exceeded'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {a.alert_type === 'exceeded'
                        ? <XCircle className="h-3 w-3" />
                        : <AlertTriangle className="h-3 w-3" />
                      }
                      {a.alert_type === 'exceeded' ? '超額' : '警告'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-sm font-medium text-gray-900">{a.tenant_name}</td>
                  <td className="px-5 py-3">
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                      {RESOURCE_LABELS[a.resource] ?? a.resource}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <UsageBar ratio={a.usage_ratio} />
                  </td>
                  <td className="px-5 py-3 text-sm tabular-nums text-gray-600">
                    {a.current_value.toLocaleString()} / {a.limit_value != null ? a.limit_value.toLocaleString() : '∞'}
                  </td>
                  <td className="px-5 py-3">
                    <span className={`text-xs font-medium ${a.notified ? 'text-green-600' : 'text-gray-400'}`}>
                      {a.notified ? '✓ 已通知' : '未通知'}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-xs text-gray-400">
                    {a.created_at ? new Date(a.created_at).toLocaleString('zh-TW') : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────

export default function MonitoringPage() {
  const [filter, setFilter] = useState<AlertFilter>('all')
  const [alertsData, setAlertsData] = useState<MonitoringAlertsResponse | null>(null)
  const [health, setHealth] = useState<SystemHealthResponse | null>(null)
  const [loadingAlerts, setLoadingAlerts] = useState(true)
  const [loadingHealth, setLoadingHealth] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchAlerts = (currentFilter: AlertFilter) => {
    const params: Record<string, string> = { days: '7' }
    if (currentFilter !== 'all') params.alert_type = currentFilter
    setLoadingAlerts(true)
    adminApi.monitoringAlerts(params)
      .then(setAlertsData)
      .catch(() => null)
      .finally(() => setLoadingAlerts(false))
  }

  const fetchHealth = () => {
    setLoadingHealth(true)
    adminApi.systemHealth()
      .then(setHealth)
      .catch(() => null)
      .finally(() => setLoadingHealth(false))
  }

  const refresh = (currentFilter: AlertFilter) => {
    fetchAlerts(currentFilter)
    fetchHealth()
  }

  // Initial load
  useEffect(() => {
    fetchAlerts(filter) // eslint-disable-line react-hooks/set-state-in-effect
    fetchHealth() // eslint-disable-line react-hooks/set-state-in-effect
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Re-fetch when filter changes
  useEffect(() => {
    fetchAlerts(filter) // eslint-disable-line react-hooks/set-state-in-effect
  }, [filter])

  // Auto-refresh timer
  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current)
    if (autoRefresh) {
      timerRef.current = setInterval(() => refresh(filter), 30_000)
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [autoRefresh, filter]) // eslint-disable-line react-hooks/exhaustive-deps

  const alerts = alertsData?.alerts ?? []

  const systemStatusColor = health
    ? health.status === 'healthy' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'
    : 'bg-gray-100 text-gray-400'

  const SystemStatusIcon = health
    ? health.status === 'healthy' ? CheckCircle2 : AlertTriangle
    : Activity

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-2">
          <Bell className="h-5 w-5 text-red-600" />
          <h1 className="text-lg font-semibold text-gray-900">監控中心</h1>
          <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">Superuser</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refresh(filter)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            立即刷新
          </button>
          <button
            onClick={() => setAutoRefresh(v => !v)}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              autoRefresh
                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                : 'border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            <Clock className="h-4 w-4" />
            {autoRefresh ? '自動刷新 (30s)' : '自動刷新'}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-6 overflow-y-auto p-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <SummaryCard
            icon={Bell}
            label="總告警數（7天）"
            value={alertsData ? alertsData.total : '—'}
            color="bg-gray-100 text-gray-600"
          />
          <SummaryCard
            icon={XCircle}
            label="超額告警"
            value={alertsData ? alertsData.exceeded_count : '—'}
            color="bg-red-50 text-red-600"
          />
          <SummaryCard
            icon={AlertTriangle}
            label="警告告警"
            value={alertsData ? alertsData.warning_count : '—'}
            color="bg-amber-50 text-amber-600"
          />
          <SummaryCard
            icon={SystemStatusIcon}
            label="系統狀態"
            value={health ? (health.status === 'healthy' ? '健康' : '異常') : '—'}
            color={systemStatusColor}
          />
        </div>

        {/* System Health */}
        <HealthPanel health={health} loading={loadingHealth} />

        {/* Alerts Table */}
        <AlertsTable
          alerts={alerts}
          loading={loadingAlerts}
          filter={filter}
          onFilterChange={setFilter}
        />
      </div>
    </div>
  )
}
