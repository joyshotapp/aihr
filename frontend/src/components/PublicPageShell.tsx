import type { ReactNode } from 'react'
import PublicSiteFooter from './PublicSiteFooter'
import PublicSiteNav from './PublicSiteNav'

type PublicPageShellProps = {
  children: ReactNode
  mainClassName?: string
  contentClassName?: string
}

export default function PublicPageShell({
  children,
  mainClassName = 'bg-white',
  contentClassName = 'mx-auto max-w-6xl px-6 py-16 sm:py-20',
}: PublicPageShellProps) {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      <PublicSiteNav />
      <main className={mainClassName}>
        <div className={contentClassName}>{children}</div>
      </main>
      <PublicSiteFooter />
    </div>
  )
}