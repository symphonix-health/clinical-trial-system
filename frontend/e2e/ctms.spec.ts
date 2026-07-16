import { expect, test } from '@playwright/test'

test.describe('CTMS navigation and API integration', () => {
  test('dashboard shows API health', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h2')).toHaveText('Dashboard')
    await expect(page.locator('text=API status:')).toBeVisible()
    await expect(page.locator('.badge')).toContainText('ok')
  })

  test('studies page loads and lists columns', async ({ page }) => {
    await page.goto('/studies')
    await expect(page.locator('h2')).toHaveText('Studies')
    await expect(page.locator('th:has-text("Protocol")')).toBeVisible()
    await expect(page.locator('th:has-text("Title")')).toBeVisible()
    await expect(page.locator('th:has-text("Phase")')).toBeVisible()
  })

  test('subjects page loads and lists columns', async ({ page }) => {
    await page.goto('/subjects')
    await expect(page.locator('h2')).toHaveText('Subjects')
    await expect(page.locator('th:has-text("Subject Number")')).toBeVisible()
    await expect(page.locator('th:has-text("Status")')).toBeVisible()
  })

  test('agent subjects page loads and lists columns', async ({ page }) => {
    await page.goto('/agents')
    await expect(page.locator('h2')).toHaveText('Agent Subjects')
    await expect(page.locator('th:has-text("Principal")')).toBeVisible()
    await expect(page.locator('th:has-text("Attestation")')).toBeVisible()
  })

  test('sidebar navigation links work', async ({ page }) => {
    await page.goto('/')
    await page.click('nav a:has-text("Studies")')
    await expect(page).toHaveURL('/studies')
    await page.click('nav a:has-text("Subjects")')
    await expect(page).toHaveURL('/subjects')
    await page.click('nav a:has-text("Agent Subjects")')
    await expect(page).toHaveURL('/agents')
    await page.click('nav a:has-text("Dashboard")')
    await expect(page).toHaveURL('/')
  })
})
