import { useState, useEffect } from 'react'
import { MapPin, Loader2, Shield, Globe, Server, Database } from 'lucide-react'
import api from '../api'

interface RegionInfo {
  code: string
  name: string
  display_name_zh: string
  data_residency: string
  compliance_notes: string
}

interface CurrentRegion {
  region: string
  name: string
  display_name_zh: string
}

export default function RegionsPage() {
  const [regions, setRegions] = useState<RegionInfo[]>([])
  const [current, setCurrent] = useState<CurrentRegion | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get<RegionInfo[]>('/regions/').then(r => r.data).catch(() => []),
      api.get<CurrentRegion>('/regions/current').then(r => r.data).catch(() => null),
    ]).then(([r, c]) => {
      setRegions(r)
      setCurrent(c)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    )
  }

  const regionIcons: Record<string, string> = {
    ap: '🌏',
    us: '🌎',
    eu: '🌍',
    jp: '🗾',
  }

  const complianceBadgeColor: Record<string, string> = {
    PDPA: 'bg-blue-100 text-blue-700',
    'SOC 2': 'bg-purple-100 text-purple-700',
    GDPR: 'bg-green-100 text-green-700',
    APPI: 'bg-orange-100 text-orange-700',
  }

  return (
    <div className="flex h-full flex-col overflow-auto">
      {/* Header */}
      <div className="border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center gap-3">
          <MapPin className="h-6 w-6 text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900">區域與資料駐留</h1>
        </div>
        <p className="mt-1 text-sm text-gray-500">查看系統部署區域與資料落地合規資訊</p>
      </div>

      <div className="flex-1 p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Current region */}
          {current && (
            <div className="rounded-xl border-2 border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100">
                  <Globe className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs font-medium text-blue-600">您的資料所在區域</p>
                  <p className="text-lg font-bold text-gray-900">
                    {regionIcons[current.region] || '🌐'} {current.display_name_zh}
                  </p>
                </div>
              </div>
              <p className="text-xs text-gray-500">
                您的所有資料（文件、對話記錄、向量索引）均儲存於此區域的基礎設施中，
                符合當地資料保護法規要求。如需變更區域，請聯繫系統管理員。
              </p>
            </div>
          )}

          {/* All regions */}
          <div>
            <h2 className="mb-4 text-sm font-semibold text-gray-700">所有支援區域</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {regions.map((r) => {
                const isActive = current?.region === r.code
                return (
                  <div
                    key={r.code}
                    className={`rounded-xl border p-5 transition-colors ${
                      isActive
                        ? 'border-blue-300 bg-blue-50/50 ring-1 ring-blue-200'
                        : 'border-gray-200 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{regionIcons[r.code] || '🌐'}</span>
                        <div>
                          <p className="text-sm font-semibold text-gray-900">{r.display_name_zh}</p>
                          <p className="text-xs text-gray-500">{r.name}</p>
                        </div>
                      </div>
                      {isActive && (
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                          目前區域
                        </span>
                      )}
                    </div>
                    <div className="mt-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Shield className="h-3.5 w-3.5 text-gray-400" />
                        <span className="text-xs text-gray-600">資料駐留：</span>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${complianceBadgeColor[r.data_residency] || 'bg-gray-100 text-gray-600'}`}>
                          {r.data_residency}
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <Server className="mt-0.5 h-3.5 w-3.5 text-gray-400" />
                        <p className="text-xs text-gray-500">{r.compliance_notes}</p>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Info box */}
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-start gap-3">
              <Database className="mt-0.5 h-4 w-4 text-gray-400" />
              <div className="text-xs text-gray-500 space-y-1">
                <p className="font-medium text-gray-700">關於資料駐留</p>
                <p>UniHR 支援多區域部署，確保您的資料儲存在合規的地理位置。每個區域擁有獨立的資料庫、快取與向量搜尋基礎設施。</p>
                <p>區域變更需要由平台管理員執行資料遷移操作，包含資料庫匯出/匯入、向量索引重建與 DNS 路由更新。如需遷移，請聯繫客服團隊。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
