import { useCallback, useEffect, useState } from 'react'
import { companyApi } from '../api'
import { Loader2, FileBarChart, Search, AlertTriangle, XCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'

interface DocumentQuality {
  total_documents: number
  completed: number
  failed: number
  avg_quality_score: number | null
  quality_distribution: Record<string, number>
  low_quality_documents: {
    id: string
    filename: string
    quality_score: number
    quality_level: string
    warnings: string[]
  }[]
}

interface RetrievalQuality {
  total_queries: number
  avg_chunk_score: number | null
  low_score_queries: number
  score_distribution: Record<string, number>
}

interface QualityData {
  document_quality: DocumentQuality
  retrieval_quality: RetrievalQuality
}

const QUALITY_COLORS: Record<string, string> = {
  excellent: '#22c55e',
  good: '#3b82f6',
  fair: '#f59e0b',
  poor: '#ef4444',
}

const SCORE_COLORS = ['#ef4444', '#f59e0b', '#eab308', '#3b82f6', '#22c55e']

const QUALITY_LABELS: Record<string, string> = {
  excellent: '優秀',
  good: '良好',
  fair: '普通',
  poor: '不佳',
}

export default function QualityDashboardPage() {
  const [data, setData] = useState<QualityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const result = await companyApi.qualityDashboard(days)
      setData(result)
    } catch {
      toast.error('載入品質儀表板失敗')
    } finally {
      setLoading(false)
    }
  }, [days])

  useEffect(() => {
    void load()
  }, [load])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!data) return null

  const dq = data.document_quality
  const rq = data.retrieval_quality

  const qualityPieData = Object.entries(dq.quality_distribution)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({ name: QUALITY_LABELS[k] || k, value: v }))

  const scorePieData = Object.entries(rq.score_distribution)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => ({ name: k, value: v }))

  const failRate = dq.total_documents > 0
    ? ((dq.failed / dq.total_documents) * 100).toFixed(1)
    : '0'

  const lowScoreRate = rq.total_queries > 0
    ? ((rq.low_score_queries / rq.total_queries) * 100).toFixed(1)
    : '0'

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-4 md:p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h1 className="text-xl font-bold text-gray-900">品質監控儀表板</h1>
          <select
            value={days}
            onChange={e => setDays(Number(e.target.value))}
            className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value={7}>最近 7 天</option>
            <option value={30}>最近 30 天</option>
            <option value={90}>最近 90 天</option>
          </select>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KPICard
            icon={FileBarChart}
            label="平均文件品質"
            value={dq.avg_quality_score != null ? `${(dq.avg_quality_score * 100).toFixed(0)}%` : 'N/A'}
            color="blue"
          />
          <KPICard
            icon={XCircle}
            label="文件失敗率"
            value={`${failRate}%`}
            color={Number(failRate) > 10 ? 'red' : 'green'}
          />
          <KPICard
            icon={Search}
            label="平均檢索品質"
            value={rq.avg_chunk_score != null ? `${(rq.avg_chunk_score * 100).toFixed(0)}%` : 'N/A'}
            color="purple"
          />
          <KPICard
            icon={AlertTriangle}
            label="低品質查詢"
            value={`${lowScoreRate}%`}
            color={Number(lowScoreRate) > 20 ? 'red' : 'green'}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Document quality distribution */}
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">文件品質分佈</h3>
            {qualityPieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={qualityPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  >
                    {qualityPieData.map((entry) => (
                      <Cell key={entry.name} fill={QUALITY_COLORS[Object.keys(QUALITY_LABELS).find(k => QUALITY_LABELS[k] === entry.name) || ''] || '#8884d8'} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-sm text-gray-400 py-12">尚無品質數據</p>
            )}
            <div className="mt-2 grid grid-cols-4 gap-2 text-center text-xs">
              <div><span className="font-bold text-green-600">{dq.quality_distribution.excellent || 0}</span><br/>優秀</div>
              <div><span className="font-bold text-blue-600">{dq.quality_distribution.good || 0}</span><br/>良好</div>
              <div><span className="font-bold text-amber-500">{dq.quality_distribution.fair || 0}</span><br/>普通</div>
              <div><span className="font-bold text-red-500">{dq.quality_distribution.poor || 0}</span><br/>不佳</div>
            </div>
          </div>

          {/* Retrieval score distribution */}
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">檢索品質分佈（chunk 相關度）</h3>
            {scorePieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={scorePieData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="value" name="查詢數" radius={[4, 4, 0, 0]}>
                    {scorePieData.map((_, i) => (
                      <Cell key={i} fill={SCORE_COLORS[i] || '#8884d8'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-sm text-gray-400 py-12">此期間無檢索數據</p>
            )}
          </div>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">文件統計</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-gray-900">{dq.total_documents}</p>
                <p className="text-xs text-gray-500 mt-1">總文件數</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-green-600">{dq.completed}</p>
                <p className="text-xs text-gray-500 mt-1">已完成</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-500">{dq.failed}</p>
                <p className="text-xs text-gray-500 mt-1">失敗</p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">檢索統計</h3>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-gray-900">{rq.total_queries}</p>
                <p className="text-xs text-gray-500 mt-1">總查詢數</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-blue-600">
                  {rq.avg_chunk_score != null ? (rq.avg_chunk_score * 100).toFixed(0) + '%' : 'N/A'}
                </p>
                <p className="text-xs text-gray-500 mt-1">平均相關度</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-red-500">{rq.low_score_queries}</p>
                <p className="text-xs text-gray-500 mt-1">低品質查詢</p>
              </div>
            </div>
          </div>
        </div>

        {/* Low quality documents alert */}
        {dq.low_quality_documents.length > 0 && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5">
            <h3 className="text-sm font-semibold text-red-700 mb-3 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              品質不佳的文件（建議重新處理）
            </h3>
            <div className="space-y-2">
              {dq.low_quality_documents.map(doc => (
                <div key={doc.id} className="flex items-center justify-between rounded-lg bg-white px-4 py-2 text-sm border border-red-100">
                  <div className="flex-1 truncate">
                    <span className="font-medium text-gray-900">{doc.filename}</span>
                    {doc.warnings.length > 0 && (
                      <span className="ml-2 text-xs text-gray-500">({doc.warnings[0]})</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                      {(doc.quality_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function KPICard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string | number
  color: 'blue' | 'green' | 'red' | 'purple' | 'amber'
}) {
  const colorMap = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  }

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <div className={`inline-flex rounded-lg p-2 ${colorMap[color]}`}>
        <Icon className="h-5 w-5" />
      </div>
      <p className="mt-3 text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-xs text-gray-500">{label}</p>
    </div>
  )
}
