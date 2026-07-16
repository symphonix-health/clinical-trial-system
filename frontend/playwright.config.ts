import { defineConfig, devices } from '@playwright/test'

const CTMS_BACKEND_PORT = process.env.CTMS_BACKEND_PORT || '9200'
const CTMS_FRONTEND_PORT = process.env.CTMS_FRONTEND_PORT || '5281'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'list',
  use: {
    baseURL: `http://localhost:${CTMS_FRONTEND_PORT}`,
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: `cd ..\\backend && .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port ${CTMS_BACKEND_PORT}`,
      url: `http://127.0.0.1:${CTMS_BACKEND_PORT}/api/v1/health`,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev',
      url: `http://localhost:${CTMS_FRONTEND_PORT}`,
      timeout: 120 * 1000,
      reuseExistingServer: !process.env.CI,
    },
  ],
})
