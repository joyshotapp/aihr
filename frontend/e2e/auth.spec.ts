import { test, expect } from '@playwright/test'

test.describe('Login Flow', () => {
  test('public routes should share the same entry bundle and welcome should redirect home', async ({ page }) => {
    const bundleByRoute = new Map<string, { script: string | null; style: string | null }>()

    for (const route of ['/', '/pricing', '/login', '/signup']) {
      await page.goto(route)
      const script = await page.locator('script[src*="/assets/index-"]').first().getAttribute('src')
      const style = await page.locator('link[href*="/assets/index-"][rel="stylesheet"]').first().getAttribute('href')
      bundleByRoute.set(route, { script, style })
    }

    const firstBundle = bundleByRoute.get('/')
    expect(firstBundle?.script).toBeTruthy()
    expect(firstBundle?.style).toBeTruthy()

    for (const [route, bundle] of bundleByRoute.entries()) {
      expect(bundle.script, `${route} should serve the same JS entry bundle`).toBe(firstBundle?.script)
      expect(bundle.style, `${route} should serve the same CSS entry bundle`).toBe(firstBundle?.style)
    }

    await page.goto('/welcome')
    await page.waitForURL(/\/$/, { timeout: 12000 })
    await expect(page).toHaveURL(/\/$/)
  })

  test('public homepage should expose main navigation links', async ({ page }) => {
    await page.goto('/')
    const nav = page.getByRole('navigation')
    await expect(nav.getByRole('link', { name: '方案與價格' })).toBeVisible()
    await expect(nav.getByRole('link', { name: '登入' })).toBeVisible()
    await expect(nav.getByRole('link', { name: '免費開始', exact: true })).toBeVisible()
  })

  test('public links should navigate between marketing pages', async ({ page }) => {
    await page.goto('/')
    const nav = page.getByRole('navigation')
    await nav.getByRole('link', { name: '方案與價格' }).click()
    await expect(page).toHaveURL(/\/pricing$/)

    await page.getByRole('link', { name: '隱私權政策' }).last().click()
    await expect(page).toHaveURL(/\/privacy$/)

    await page.goto('/')
    await nav.getByRole('link', { name: '免費開始', exact: true }).click()
    await expect(page).toHaveURL(/\/signup$/)

    await page.goto('/')
    await nav.getByRole('link', { name: '登入' }).click()
    await expect(page).toHaveURL(/\/login$/)
  })

  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.getByRole('contentinfo')).toBeVisible()
    await expect(page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })

  test('signup page should stay inside public site shell', async ({ page }) => {
    await page.goto('/signup')
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.getByRole('contentinfo')).toBeVisible()
    await expect(page.getByRole('heading', { name: '建立帳號' })).toBeVisible()
    await expect(page.getByText('公開網站提供方案、FAQ、聯絡資訊與註冊入口')).toBeVisible()
  })

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', 'bad@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')
    // Should remain on login page or show error
    await expect(page).toHaveURL(/login/)
  })

  test('should redirect unauthenticated user to login', async ({ page }) => {
    await page.goto('/app/documents')
    await page.waitForURL(/login/, { timeout: 12000 })
    await expect(page).toHaveURL(/login/)
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.getByRole('contentinfo')).toBeVisible()
  })

  test('legacy protected route should redirect into login flow', async ({ page }) => {
    await page.goto('/usage')
    await page.waitForURL(/login/, { timeout: 12000 })
    await expect(page).toHaveURL(/login/)
    await expect(page.getByRole('navigation')).toBeVisible()
  })
})
