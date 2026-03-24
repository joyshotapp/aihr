import { test, expect } from '@playwright/test'

test.describe('Login Flow', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
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
    await page.goto('/documents')
    await expect(page).toHaveURL(/login/)
  })
})
