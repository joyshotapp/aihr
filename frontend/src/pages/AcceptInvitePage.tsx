import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { authApi } from '../api'

export default function AcceptInvitePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') || ''

  const [fullName, setFullName] = useState('')
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
    setLoading(true)
    setError('')
    try {
      await authApi.acceptInvite({ token, full_name: fullName, password, agree_terms: agreeTerms })
      setSuccess(true)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '邀請連結無效或已過期'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-stone-50 via-rose-50 to-orange-50 px-4">
        <div className="rounded-2xl border border-red-200 bg-white p-8 shadow-lg">
          <h2 className="text-lg font-semibold text-red-600">無效的邀請連結</h2>
          <p className="mt-2 text-sm text-gray-600">請透過邀請信中的連結進入此頁面。</p>
          <Link to="/login" className="mt-4 inline-block text-sm font-medium text-[#d15454] hover:underline">返回登入</Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-stone-50 via-rose-50 to-orange-50 px-4">
        <div className="rounded-2xl border border-green-200 bg-white p-8 shadow-lg text-center">
          <h2 className="text-lg font-semibold text-green-700">帳號建立成功！</h2>
          <p className="mt-2 text-sm text-gray-600">您現在可以使用電子郵件與密碼登入。</p>
          <button
            onClick={() => navigate('/login')}
            className="mt-4 rounded-lg bg-[#d15454] px-6 py-2 text-sm font-medium text-white hover:bg-[#c04444]"
          >
            前往登入
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-stone-50 via-rose-50 to-orange-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-white/70 bg-white/90 p-8 shadow-2xl backdrop-blur">
        <h1 className="text-2xl font-bold text-gray-900">接受邀請</h1>
        <p className="mt-1 text-sm text-gray-500">完成帳號設定以加入您的團隊</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">姓名</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#d15454] focus:outline-none focus:ring-1 focus:ring-[#d15454]"
              placeholder="請輸入您的姓名"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">設定密碼</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-[#d15454] focus:outline-none focus:ring-1 focus:ring-[#d15454]"
              placeholder="至少 8 個字元"
            />
          </div>

          <label className="flex items-start gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3">
            <input
              type="checkbox"
              checked={agreeTerms}
              onChange={(e) => setAgreeTerms(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-[#d15454] focus:ring-[#d15454]"
            />
            <span className="text-sm text-gray-700">
              我已閱讀並同意{' '}
              <Link to="/terms" target="_blank" className="font-medium text-[#d15454] hover:underline">服務條款</Link>
              {' '}及{' '}
              <Link to="/privacy" target="_blank" className="font-medium text-[#d15454] hover:underline">隱私權政策</Link>
            </span>
          </label>

          {error && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-[#d15454] py-2.5 text-sm font-semibold text-white transition-colors hover:bg-[#c04444] disabled:opacity-50"
          >
            {loading ? '建立中...' : '建立帳號'}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-400">
          已有帳號？<Link to="/login" className="text-[#d15454] hover:underline">登入</Link>
        </p>
      </div>
    </div>
  )
}
