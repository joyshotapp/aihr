import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '../api'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'

export default function VerifyEmailPage() {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [status, setStatus] = useState<'loading' | 'success' | 'already' | 'error'>('loading')
  const [errorMsg, setErrorMsg] = useState('')

  useEffect(() => {
    void (async () => {
      if (!token) {
        setStatus('error')
        setErrorMsg('缺少驗證令牌')
        return
      }
      try {
        const res = await authApi.verifyEmail(token)
        setStatus(res.already_verified ? 'already' : 'success')
      } catch (err) {
        setStatus('error')
        setErrorMsg(
          (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
            '驗證連結無效或已過期'
        )
      }
    })()
  }, [token])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-white via-rose-50/30 to-orange-50/20 px-4">
      <div className="w-full max-w-md rounded-2xl border border-gray-100 bg-white p-10 text-center shadow-xl">
        {status === 'loading' && (
          <>
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-[#d15454]" />
            <h2 className="mt-6 text-xl font-bold text-gray-900">正在驗證...</h2>
            <p className="mt-2 text-sm text-gray-500">請稍候</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-50">
              <CheckCircle2 className="h-10 w-10 text-emerald-500" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">驗證成功！</h2>
            <p className="mt-3 text-sm text-gray-500">
              您的電子郵件已驗證完成，現在可以登入開始使用 UniHR。
            </p>
            <Link
              to="/login"
              className="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#d15454] px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-[#c04444] transition-colors"
            >
              前往登入
            </Link>
          </>
        )}

        {status === 'already' && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-50">
              <CheckCircle2 className="h-10 w-10 text-blue-500" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">已驗證過</h2>
            <p className="mt-3 text-sm text-gray-500">
              此電子郵件先前已完成驗證，直接登入即可。
            </p>
            <Link
              to="/login"
              className="mt-8 inline-flex items-center gap-2 rounded-xl bg-[#d15454] px-8 py-3 text-sm font-semibold text-white shadow-sm hover:bg-[#c04444] transition-colors"
            >
              前往登入
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-50">
              <XCircle className="h-10 w-10 text-red-500" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">驗證失敗</h2>
            <p className="mt-3 text-sm text-gray-500">{errorMsg}</p>
            <div className="mt-8 flex flex-col items-center gap-3">
              <Link
                to="/login"
                className="text-sm font-medium text-[#d15454] hover:underline"
              >
                前往登入
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
