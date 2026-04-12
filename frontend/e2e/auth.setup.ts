/**
 * Playwright global authentication setup.
 * Runs once before all tests and saves browser storage/cookie state so tests
 * do NOT need to call the login API per-test (avoids tripping the 10-req/min
 * high-risk rate limit on /api/v1/auth/login).
 *
 * Required env vars:
 *   E2E_USER_EMAIL       – owner-role account email
 *   E2E_USER_PASSWORD    – owner-role account password
 *   E2E_MEMBER_EMAIL     – member-role account email
 *   E2E_MEMBER_PASSWORD  – member-role account password
 */
import { test as setup, expect } from '@playwright/test'
import path from 'path'

export const ownerStorageState = path.join(__dirname, '.auth/owner.json')
export const memberStorageState = path.join(__dirname, '.auth/member.json')

const OWNER_EMAIL = process.env.E2E_USER_EMAIL || ''
const OWNER_PASSWORD = process.env.E2E_USER_PASSWORD || ''
const MEMBER_EMAIL = process.env.E2E_MEMBER_EMAIL || ''
const MEMBER_PASSWORD = process.env.E2E_MEMBER_PASSWORD || ''

setup('authenticate as owner', async ({ page }) => {
  if (!OWNER_EMAIL || !OWNER_PASSWORD) {
    // Write empty state so the file exists; dependent tests will skip via hasCreds checks
    await page.context().storageState({ path: ownerStorageState })
    return
  }
  await page.goto('/login')
  await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', OWNER_EMAIL)
  await page.fill('input[type="password"]', OWNER_PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/, { timeout: 15000 })
  await page.context().storageState({ path: ownerStorageState })
})

setup('authenticate as member', async ({ page }) => {
  if (!MEMBER_EMAIL || !MEMBER_PASSWORD) {
    await page.context().storageState({ path: memberStorageState })
    return
  }
  await page.goto('/login')
  await page.fill('input[type="email"], input[name="email"], input[placeholder*="mail"]', MEMBER_EMAIL)
  await page.fill('input[type="password"]', MEMBER_PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).not.toHaveURL(/\/login(?:\?|$)/, { timeout: 15000 })
  await page.context().storageState({ path: memberStorageState })
})
