import { test, expect } from '@playwright/test'
import { ownerStorageState } from './auth.setup'

/**
 * These tests require a running backend with a valid test user.
 * Set E2E_USER_EMAIL and E2E_USER_PASSWORD env vars.
 * Auth state is pre-loaded via storageState (set up by auth.setup.ts).
 */
const hasCreds = !!process.env.E2E_USER_EMAIL && !!process.env.E2E_USER_PASSWORD

test.describe('Document Upload Flow', () => {
  test.use({ storageState: ownerStorageState })

  test('should navigate to documents page', async ({ page }) => {
    test.skip(!hasCreds, 'Authenticated E2E requires E2E_USER_EMAIL and E2E_USER_PASSWORD')
    await page.goto('/app/documents')
    await expect(page.locator('h1, h2, [class*="title"]')).toContainText(/文件|Documents/i)
  })
})

test.describe('Chat Flow', () => {
  test.use({ storageState: ownerStorageState })

  test('should navigate to chat page', async ({ page }) => {
    test.skip(!hasCreds, 'Authenticated E2E requires E2E_USER_EMAIL and E2E_USER_PASSWORD')
    await page.goto('/app')
    await expect(page.locator('textarea, input[placeholder*="問"], input[placeholder*="ask"]')).toBeVisible()
  })
})
