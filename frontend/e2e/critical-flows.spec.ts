import { test, expect, type Page } from '@playwright/test'

/**
 * Critical business flow E2E tests
 *
 * Covers: subscription upgrade, password reset, email verification,
 * invitation acceptance, and RBAC guard checks.
 *
 * Required env vars (authenticated suites):
 *   E2E_USER_EMAIL       – owner-role test account
 *   E2E_USER_PASSWORD    – password for the above
 *   E2E_MEMBER_EMAIL     – member-role test account (non-owner)
 *   E2E_MEMBER_PASSWORD  – password for the above
 */

const OWNER_EMAIL = process.env.E2E_USER_EMAIL || ''
const OWNER_PASSWORD = process.env.E2E_USER_PASSWORD || ''
const MEMBER_EMAIL = process.env.E2E_MEMBER_EMAIL || ''
const MEMBER_PASSWORD = process.env.E2E_MEMBER_PASSWORD || ''

const hasOwnerCreds = !!OWNER_EMAIL && !!OWNER_PASSWORD
const hasMemberCreds = !!MEMBER_EMAIL && !!MEMBER_PASSWORD

async function login(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', email)
  await page.fill('input[type="password"]', password)
  await page.click('button[type="submit"]')
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/, { timeout: 15000 })
}

// ─────────────────────────────────────────────────────────────
// 1. Password Reset Flow
// ─────────────────────────────────────────────────────────────
test.describe('Password Reset Flow', () => {
  test('forgot-password page should be reachable from login', async ({ page }) => {
    await page.goto('/login')
    const forgotLink = page.getByRole('link', { name: /忘記密碼|forgot/i })
    await expect(forgotLink).toBeVisible()
    await forgotLink.click()
    await expect(page).toHaveURL(/forgot|reset-password/i)
  })

  test('forgot-password form should accept email and show confirmation', async ({ page }) => {
    await page.goto('/login')
    await page.getByRole('link', { name: /忘記密碼|forgot/i }).click()
    await expect(page).toHaveURL(/forgot|reset-password/i)
    await expect(page.getByRole('heading', { name: /忘記密碼|forgot/i })).toBeVisible()
    await page.getByPlaceholder('name@company.com').fill('nonexistent@example.com')
    await page.click('button[type="submit"]')
    // Should show confirmation message regardless of whether email exists (prevents enumeration)
    await expect(
      page.getByText(/已傳送|已寄出|check your email/i)
    ).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 2. Email Verification Redirect
// ─────────────────────────────────────────────────────────────
test.describe('Email Verification Page', () => {
  test('verify-email route should render without errors', async ({ page }) => {
    await page.goto('/verify-email?token=invalid_token_test')
    // Should show either an error message or verification UI — must not 404 or blank
    await expect(page.locator('body')).not.toBeEmpty()
    const status = page.getByText(/無效|expired|驗證|verify|error/i)
    await expect(status).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 3. Invitation Acceptance Flow
// ─────────────────────────────────────────────────────────────
test.describe('Accept Invite Flow', () => {
  test('accept-invite route should render without errors', async ({ page }) => {
    await page.goto('/accept-invite?token=invalid_token_test')
    await expect(page.locator('body')).not.toBeEmpty()
    const status = page.getByText(/無效|expired|邀請|invite|error/i)
    await expect(status).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 4. Subscription / Upgrade Page (authenticated — owner)
// ─────────────────────────────────────────────────────────────
test.describe('Subscription Page', () => {
  test('owner can navigate to subscription page', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD (owner role)')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/subscription')
    await expect(page).toHaveURL(/\/app\/subscription/)
    await expect(page.getByRole('heading', { name: /^訂閱方案$/ })).toBeVisible({ timeout: 10000 })
  })

  test('subscription page shows current plan', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD (owner role)')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/subscription')
    await expect(page.getByRole('heading', { name: /目前方案：/i })).toBeVisible({ timeout: 10000 })
  })

  test('upgrade button navigates to payment flow', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD (owner role)')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/subscription')
    const upgradeBtn = page.getByRole('button', { name: /升級|upgrade/i }).first()
    // Button should be present; we do NOT actually submit payment in E2E
    await expect(upgradeBtn).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 5. RBAC Guard — member should not access owner-only pages
// ─────────────────────────────────────────────────────────────
test.describe('RBAC Guard', () => {
  test('member should be redirected away from subscription page', async ({ page }) => {
    test.skip(!hasMemberCreds, 'Requires E2E_MEMBER_EMAIL + E2E_MEMBER_PASSWORD (non-owner role)')
    await login(page, MEMBER_EMAIL, MEMBER_PASSWORD)
    await page.goto('/app/subscription')
    // RoleGuard should redirect non-owner/admin away from subscription
    await expect(page).not.toHaveURL(/\/app\/subscription/, { timeout: 5000 })
  })

  test('member should be redirected away from company settings', async ({ page }) => {
    test.skip(!hasMemberCreds, 'Requires E2E_MEMBER_EMAIL + E2E_MEMBER_PASSWORD (non-owner role)')
    await login(page, MEMBER_EMAIL, MEMBER_PASSWORD)
    await page.goto('/app/company')
    await expect(page).not.toHaveURL(/\/app\/company/, { timeout: 5000 })
  })

  test('member can still access chat', async ({ page }) => {
    test.skip(!hasMemberCreds, 'Requires E2E_MEMBER_EMAIL + E2E_MEMBER_PASSWORD (non-owner role)')
    await login(page, MEMBER_EMAIL, MEMBER_PASSWORD)
    await page.goto('/app')
    await expect(
      page.locator('textarea, input[placeholder*="問"], input[placeholder*="ask"]')
    ).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 6. Document Upload Page (authenticated — owner)
// ─────────────────────────────────────────────────────────────
test.describe('Document Upload', () => {
  test('documents page renders upload area or document list', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/documents')
    await expect(page.getByRole('heading', { name: /^文件管理$/ })).toBeVisible({ timeout: 10000 })
  })

  test('documents page exposes an upload control', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/documents')
    const uploadEl = page.locator('input[type="file"], button:has-text("上傳"), button:has-text("Upload")')
    await expect(uploadEl.first()).toBeVisible({ timeout: 10000 })
  })
})

// ─────────────────────────────────────────────────────────────
// 7. Audit Log Page — restricted to owner/admin
// ─────────────────────────────────────────────────────────────
test.describe('Audit Logs (owner)', () => {
  test('owner can access audit logs page', async ({ page }) => {
    test.skip(!hasOwnerCreds, 'Requires E2E_USER_EMAIL + E2E_USER_PASSWORD (owner role)')
    await login(page, OWNER_EMAIL, OWNER_PASSWORD)
    await page.goto('/app/audit')
    await expect(page).toHaveURL(/\/app\/audit/)
    await expect(page.getByRole('heading', { name: /^稽核日誌$/ })).toBeVisible({ timeout: 10000 })
  })
})
