import { Link } from 'react-router-dom'
import { MessageSquare, FileText, Shield, Users, Zap, BarChart3, ArrowRight, Check } from 'lucide-react'

const FEATURES = [
  { icon: MessageSquare, title: 'AI 智慧問答', desc: '上傳公司規章，員工直接用自然語言提問，AI 即時回覆正確答案。' },
  { icon: FileText, title: '文件知識庫', desc: '支援 PDF、Word、Excel 等格式，自動解析並建立可搜尋的向量知識庫。' },
  { icon: Shield, title: '多租戶隔離', desc: '每間公司資料完全隔離，符合個資法規範，企業級安全防護。' },
  { icon: Users, title: '團隊協作', desc: '依角色分權管理（Owner / Admin / HR / 員工），靈活掌控存取範圍。' },
  { icon: Zap, title: '混合檢索', desc: '語意搜尋 + 關鍵字搜尋 + 重排序，確保找到最精準的答案。' },
  { icon: BarChart3, title: '用量分析', desc: '即時追蹤查詢次數、Token 使用量、文件數量，透明掌握成本。' },
]

const STEPS = [
  { num: '1', title: '註冊帳號', desc: '輸入公司名稱與 Email，30 秒完成。' },
  { num: '2', title: '上傳文件', desc: '拖曳公司規章、辦法、FAQ 到知識庫。' },
  { num: '3', title: '開始提問', desc: '員工直接向 AI 助理提問，立即獲得答案。' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-gray-100 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-xl font-bold tracking-tight text-gray-900">
            Uni<span className="text-[#d15454]">HR</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link to="/pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              方案與價格
            </Link>
            <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
              登入
            </Link>
            <Link
              to="/signup"
              className="rounded-lg bg-[#d15454] px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#c04444] transition-colors"
            >
              免費開始
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-rose-50/60 via-white to-orange-50/40" />
        <div className="relative mx-auto max-w-4xl px-6 pb-20 pt-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-rose-200 bg-rose-50 px-4 py-1.5 text-sm font-medium text-[#d15454]">
            <Zap className="h-4 w-4" />
            AI 驅動的人資知識管理
          </div>
          <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
            讓每位員工都有
            <br />
            <span className="text-[#d15454]">專屬 HR 助理</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-500">
            上傳公司規章制度，AI 自動建立知識庫。員工隨時提問，即時獲得準確解答。
            <br className="hidden sm:block" />
            不再翻文件、不再等 HR 回覆。
          </p>
          <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              to="/signup"
              className="inline-flex items-center gap-2 rounded-xl bg-[#d15454] px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-rose-200/50 hover:bg-[#c04444] transition-all hover:shadow-xl"
            >
              免費註冊
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/pricing"
              className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-8 py-3.5 text-base font-semibold text-gray-700 shadow-sm hover:border-gray-300 hover:bg-gray-50 transition-all"
            >
              查看方案
            </Link>
          </div>
          <p className="mt-4 text-sm text-gray-400">免費方案 · 不需信用卡 · 5 位使用者</p>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-gray-100 bg-gray-50/50 py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-3xl font-bold text-gray-900">三步驟開始使用</h2>
          <p className="mt-3 text-center text-gray-500">簡單到不需要教學</p>
          <div className="mt-14 grid gap-8 sm:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.num} className="text-center">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#d15454] text-2xl font-bold text-white shadow-md">
                  {s.num}
                </div>
                <h3 className="mt-5 text-lg font-semibold text-gray-900">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="text-center text-3xl font-bold text-gray-900">核心功能</h2>
          <p className="mt-3 text-center text-gray-500">專為台灣企業人資場景打造</p>
          <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="rounded-2xl border border-gray-100 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-50 text-[#d15454]">
                  <f.icon className="h-5 w-5" />
                </div>
                <h3 className="mt-4 text-base font-semibold text-gray-900">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-gray-500">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social proof / trust */}
      <section className="border-t border-gray-100 bg-gray-50/50 py-20">
        <div className="mx-auto max-w-4xl px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900">企業級安全與合規</h2>
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              '個人資料保護法 (PDPA) 合規',
              'AES-256 資料加密',
              '行列級安全 (RLS) 隔離',
              'SOC 2 等級稽核日誌',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-xl border border-gray-100 bg-white px-4 py-3 text-left shadow-sm">
                <Check className="h-5 w-5 flex-shrink-0 text-emerald-500" />
                <span className="text-sm font-medium text-gray-700">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-3xl font-bold text-gray-900">準備好了嗎？</h2>
          <p className="mt-4 text-lg text-gray-500">
            免費方案無需信用卡，立即體驗 AI 人資助理。
          </p>
          <Link
            to="/signup"
            className="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#d15454] px-10 py-4 text-lg font-semibold text-white shadow-lg shadow-rose-200/50 hover:bg-[#c04444] transition-all"
          >
            免費開始使用
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 sm:flex-row sm:justify-between">
          <p className="text-sm text-gray-400">&copy; {new Date().getFullYear()} UniHR. All rights reserved.</p>
          <div className="flex gap-6 text-sm text-gray-400">
            <Link to="/terms" className="hover:text-gray-600 transition-colors">服務條款</Link>
            <Link to="/privacy" className="hover:text-gray-600 transition-colors">隱私權政策</Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
