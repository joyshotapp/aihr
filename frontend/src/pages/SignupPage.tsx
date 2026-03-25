import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authApi } from '../api'
import { Building2, Mail, User, Lock, ArrowRight, Check } from 'lucide-react'
import PublicPageShell from '../components/PublicPageShell'

export default function SignupPage() {
  const [companyName, setCompanyName] = useState('')
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [agreeTerms, setAgreeTerms] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!agreeTerms) {
      setError('請先勾選同意服務條款與隱私權政策')
      return
    }
    if (password.length < 8) {
      setError('密碼至少需要 8 個字元')
      return
    }
    if (!/[A-Za-z]/.test(password)) {
      setError('密碼必須包含至少一個英文字母')
      return
    }
    if (!/\d/.test(password)) {
      setError('密碼必須包含至少一個數字')
      return
    }
    setLoading(true)
    setError('')
    try {
      await authApi.register({
        email,
        password,
        full_name: fullName,
        company_name: companyName,
        agree_terms: agreeTerms,
      })
      setSuccess(true)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        '註冊失敗，請稍後再試'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <PublicPageShell
        mainClassName="bg-gradient-to-br from-white via-rose-50/30 to-orange-50/20"
        contentClassName="mx-auto flex min-h-[calc(100vh-168px)] max-w-6xl items-center justify-center px-6 py-12"
      >
        <div className="w-full max-w-md rounded-2xl border border-gray-100 bg-white p-10 text-center shadow-xl">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
            <Mail className="h-8 w-8 text-emerald-600" />
          </div>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">請確認您的信箱</h2>
          <p className="mx-auto mt-3 max-w-sm text-sm leading-relaxed text-gray-500">
            我們已寄送一封驗證信至 <strong className="text-gray-700">{email}</strong>，
            請點擊信中的連結完成帳號啟用。
          </p>
          <div className="mt-8 rounded-xl border border-amber-100 bg-amber-50 p-4 text-left text-sm text-amber-700">
            沒有收到？請檢查垃圾郵件資料夾，或
            <button
              onClick={async () => {
                try {
                  await authApi.resendVerification(email)
                  setError('')
                } catch { /* ignore */ }
              }}
              className="ml-1 font-semibold text-[#d15454] hover:underline"
            >
              重新寄送
            </button>。
          </div>
          <Link
            to="/login"
            className="mt-8 inline-block text-sm font-medium text-[#d15454] hover:underline"
          >
            前往登入頁面
          </Link>
        </div>
      </PublicPageShell>
    )
  }

  return (
    <PublicPageShell
      mainClassName="bg-gradient-to-br from-white via-rose-50/40 to-orange-50/30"
      contentClassName="mx-auto grid min-h-[calc(100vh-168px)] max-w-6xl gap-10 px-6 py-12 lg:grid-cols-[0.95fr_1.05fr] lg:items-center lg:py-20"
    >
      <div className="flex items-center justify-center lg:justify-start">
        <div className="w-full max-w-md rounded-[28px] border border-white/80 bg-white p-8 shadow-[0_24px_80px_rgba(0,0,0,0.08)] sm:p-10">
          <Link to="/" className="text-2xl font-bold tracking-tight text-gray-900">
            Uni<span className="text-[#d15454]">HR</span>
          </Link>
          <h1 className="mt-8 text-3xl font-extrabold text-gray-900">建立帳號</h1>
          <p className="mt-2 text-sm text-gray-500">免費方案，不需信用卡，30 秒完成。</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            {/* Company */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">公司名稱</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:border-[#d15454] focus:bg-white focus:ring-2 focus:ring-rose-100"
                  placeholder="例如：台灣科技股份有限公司"
                />
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">您的姓名</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:border-[#d15454] focus:bg-white focus:ring-2 focus:ring-rose-100"
                  placeholder="王小明"
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">電子郵件</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:border-[#d15454] focus:bg-white focus:ring-2 focus:ring-rose-100"
                  placeholder="you@company.com"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-gray-700">設定密碼</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full rounded-xl border border-gray-200 bg-gray-50 py-3 pl-10 pr-4 text-sm outline-none transition-colors focus:border-[#d15454] focus:bg-white focus:ring-2 focus:ring-rose-100"
                  placeholder="至少 8 個字元，需含英文字母與數字"
                />
              </div>
              {password.length > 0 && (
                <div className="mt-2 space-y-1">
                  {(() => {
                    const checks = [
                      { ok: password.length >= 8, label: '至少 8 個字元' },
                      { ok: /[A-Za-z]/.test(password), label: '包含英文字母' },
                      { ok: /\d/.test(password), label: '包含數字' },
                    ]
                    return checks.map((c) => (
                      <p key={c.label} className={`text-xs flex items-center gap-1.5 ${c.ok ? 'text-emerald-600' : 'text-gray-400'}`}>
                        <span className={`inline-block h-1.5 w-1.5 rounded-full ${c.ok ? 'bg-emerald-500' : 'bg-gray-300'}`} />
                        {c.label}
                      </p>
                    ))
                  })()}
                </div>
              )}
            </div>

            {/* Terms */}
            <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-gray-100 bg-gray-50 p-4 transition-colors hover:bg-gray-100/70">
              <input
                type="checkbox"
                checked={agreeTerms}
                onChange={(e) => setAgreeTerms(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-[#d15454] focus:ring-[#d15454]"
              />
              <span className="text-sm text-gray-600">
                我已閱讀並同意{' '}
                <Link to="/terms" target="_blank" className="font-medium text-[#d15454] hover:underline">服務條款</Link>
                {' '}及{' '}
                <Link to="/privacy" target="_blank" className="font-medium text-[#d15454] hover:underline">隱私權政策</Link>
              </span>
            </label>

            {error && (
              <p className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-600">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#d15454] py-3.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-[#c04444] hover:shadow-md disabled:opacity-50"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <>
                  免費建立帳號
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-400">
            已有帳號？
            <Link to="/login" className="ml-1 font-medium text-[#d15454] hover:underline">登入</Link>
          </p>
        </div>
      </div>

      <div className="rounded-[32px] border border-white/60 bg-white/60 p-8 shadow-sm backdrop-blur lg:p-12">
        <div className="max-w-lg">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#d15454]">Public Site</p>
          <h2 className="mt-4 text-3xl font-bold text-gray-900 sm:text-4xl">企業專屬AI人資長</h2>
          <p className="mt-4 text-base leading-relaxed text-gray-500">
            讓每位員工都能即時取得公司規章的精準解答，減少 HR 重複回答，提升整體效率。
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              '上傳公司規章，AI 自動建立知識庫',
              '員工用自然語言提問，即時取得答案',
              '多租戶隔離，資料安全有保障',
              '符合台灣個人資料保護法',
            ].map((item) => (
              <div key={item} className="flex items-center gap-3 rounded-2xl border border-white/80 bg-white/80 px-4 py-4 shadow-sm">
                <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-emerald-100">
                  <Check className="h-3.5 w-3.5 text-emerald-600" />
                </div>
                <span className="text-sm text-gray-600">{item}</span>
              </div>
            ))}
          </div>
          <div className="mt-10 rounded-2xl border border-rose-100 bg-rose-50/80 p-5">
            <p className="text-sm font-semibold text-gray-900">註冊後可立即使用</p>
            <p className="mt-2 text-sm leading-6 text-gray-600">
              公開網站提供方案、FAQ、聯絡資訊與註冊入口；登入後則進入 `/app` 工作台處理文件、問答與管理流程。
            </p>
          </div>
        </div>
      </div>
    </PublicPageShell>
  )
}
