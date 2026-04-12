import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Loader2, Mail, ArrowLeft } from 'lucide-react'
import PublicPageShell from '../components/PublicPageShell'
import { api } from '../api'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await api.post('/auth/forgot-password', { email })
      setSent(true)
    } catch {
      // Show success regardless to prevent email enumeration
      setSent(true)
    } finally {
      setLoading(false)
    }
  }

  return (
    <PublicPageShell>
      <div className="flex min-h-[calc(100vh-168px)] items-center justify-center px-6 py-12">
        <div className="mx-auto w-full max-w-md rounded-[28px] border border-white/80 bg-white p-8 shadow-[0_24px_80px_rgba(0,0,0,0.08)] sm:p-10">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-rose-50">
              <Mail className="h-6 w-6 text-[#d15454]" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">忘記密碼</h1>
            <p className="mt-2 text-sm text-gray-500">
              輸入您的電子郵件，我們將傳送重設連結。
            </p>
          </div>

          {sent ? (
            <div className="space-y-6">
              <div className="rounded-xl border border-green-200 bg-green-50 p-5 text-center">
                <p className="text-sm font-medium text-green-800">郵件已傳送</p>
                <p className="mt-1 text-sm text-green-600">
                  若該信箱已註冊，您將收到一封密碼重設郵件，請查看收件匣。
                </p>
              </div>
              <Link
                to="/login"
                className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700"
              >
                <ArrowLeft className="h-4 w-4" />
                返回登入頁
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-gray-700">電子郵件</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-[#d15454] focus:ring-2 focus:ring-[#d15454]/20 focus:outline-none transition-shadow"
                />
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={loading}
                className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50 transition-colors"
                style={{ backgroundColor: '#d15454' }}
                onMouseEnter={e => (e.currentTarget.style.backgroundColor = '#c04444')}
                onMouseLeave={e => (e.currentTarget.style.backgroundColor = '#d15454')}
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? '傳送中...' : '傳送重設連結'}
              </button>
              <Link
                to="/login"
                className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700"
              >
                <ArrowLeft className="h-4 w-4" />
                返回登入頁
              </Link>
            </form>
          )}
        </div>
      </div>
    </PublicPageShell>
  )
}
