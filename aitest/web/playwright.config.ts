import { defineConfig } from '@playwright/test'
import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const webDir = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../../artifacts/playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:15173',
    launchOptions: {
      executablePath: process.env.E2E_BROWSER_PATH || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // Keep screenshot + trace evidence without requiring a separate ffmpeg download.
    video: 'off',
  },
  webServer: [
    {
      command: 'D:\\Desktop\\Alice\\.venv\\Scripts\\python.exe -m uvicorn aitest.server.main:app --host 127.0.0.1 --port 8000',
      url: 'http://127.0.0.1:8000/health',
      cwd: 'D:\\Desktop\\Alice',
      reuseExistingServer: true,
      timeout: 120_000,
      env: { ...process.env, AITEST_DB_BACKEND: 'sqlite', AITEST_RATE_MAX_REQUESTS: '1000' },
    },
    {
      command: 'node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 15173',
      url: 'http://127.0.0.1:15173/',
      cwd: webDir,
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
})
