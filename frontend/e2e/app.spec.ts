import { test, expect } from '@playwright/test'

/**
 * These tests require a running backend with a valid test user.
 * Set E2E_USER_EMAIL and E2E_USER_PASSWORD env vars.
 */
const OWNER_EMAIL = process.env.E2E_USER_EMAIL || ''
const OWNER_PASSWORD = process.env.E2E_USER_PASSWORD || ''
const hasCreds = !!OWNER_EMAIL && !!OWNER_PASSWORD

async function loginAsOwner(page: Parameters<Parameters<typeof test>[1]>[0]['page']) {
  await page.goto('/login')
  await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', OWNER_EMAIL)
  await page.fill('input[type="password"]', OWNER_PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/, { timeout: 15000 })
}

test.describe('Document Upload Flow', () => {
  test('should navigate to documents page', async ({ page }) => {
    test.skip(!hasCreds, 'Authenticated E2E requires E2E_USER_EMAIL and E2E_USER_PASSWORD')
    await loginAsOwner(page)
    await page.goto('/app/documents')
    await expect(page.locator('h1, h2, [class*="title"]')).toContainText(/文件|Documents/i)
  })
})

test.describe('Chat Flow', () => {
  test('should navigate to chat page', async ({ page }) => {
    test.skip(!hasCreds, 'Authenticated E2E requires E2E_USER_EMAIL and E2E_USER_PASSWORD')
    await loginAsOwner(page)
    await page.goto('/app')
    await expect(page.locator('textarea, input[placeholder*="問"], input[placeholder*="ask"]')).toBeVisible()
  })
})
