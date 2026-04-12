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
import { existsSync, statSync } from 'node:fs'
import { test as setup, expect, type Page } from '@playwright/test'
import { ownerStorageState, memberStorageState } from './e2e-config'

const OWNER_EMAIL = process.env.E2E_USER_EMAIL || ''
const OWNER_PASSWORD = process.env.E2E_USER_PASSWORD || ''
const MEMBER_EMAIL = process.env.E2E_MEMBER_EMAIL || ''
const MEMBER_PASSWORD = process.env.E2E_MEMBER_PASSWORD || ''
const MAX_STORAGE_STATE_AGE_MS = 12 * 60 * 60 * 1000

async function hasValidSession(page: Page, path: string) {
  if (!canReuseStorageState(path)) {
    return false
  }

  const browser = page.context().browser()
  if (!browser) {
    return false
  }

  const probeContext = await browser.newContext({
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3001',
    storageState: path,
  })

  try {
    const probePage = await probeContext.newPage()
    await probePage.goto('/app')
    await probePage.waitForURL(/\/app(?:\/|$)/, { timeout: 8000 })
    await probeContext.storageState({ path })
    return !/\/login(?:\?|$)/.test(probePage.url())
  } catch {
    return false
  } finally {
    await probeContext.close()
  }
}

function canReuseStorageState(path: string) {
  try {
    if (!existsSync(path)) {
      return false
    }

    return Date.now() - statSync(path).mtimeMs < MAX_STORAGE_STATE_AGE_MS
  } catch {
    return false
  }
}

setup('authenticate as owner', async ({ page }) => {
  if (await hasValidSession(page, ownerStorageState)) {
    return
  }

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
  if (await hasValidSession(page, memberStorageState)) {
    return
  }

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
