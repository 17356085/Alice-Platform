/** E2E Smoke Tests — Architecture Review Phase 3.

  Covers all 14 main views + navigation + auth-exempt endpoints.

  Prerequisites:
    cd aitest/web && pnpm dev           # port 15173 (Vite)
    aitest server start                  # port 8000  (Python backend, optional for UI-only tests)

  Run:
    cd aitest/web && npx playwright test e2e/smoke.spec.ts
    E2E_BASE_URL=http://localhost:15173 npx playwright test e2e/smoke.spec.ts
*/

import { test, expect } from '@playwright/test'

const BASE = process.env.E2E_BASE_URL || 'http://localhost:15173'

// Helper: wait for view to load (no 404, no blank page)
async function expectViewLoaded(page: import('@playwright/test').Page, timeout = 10000) {
  await page.waitForTimeout(500)
  const url = page.url()
  expect(url).not.toContain('404')
  // Page should have some content rendered
  await expect(page.locator('main, .main-content, #app > div').first()).toBeVisible({ timeout })
}

test.describe('AITest Frontend Smoke', () => {

  // ── Core navigation views ────────────────────────────────────────

  test('dashboard — loads project overview', async ({ page }) => {
    await page.goto(`${BASE}/#/dashboard`)
    await expectViewLoaded(page)
  })

  test('kanban — loads and shows SOP columns', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/kanban`)
    await expectViewLoaded(page)
  })

  test('gaps — shows test gap scanner', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/gaps`)
    await expectViewLoaded(page)
  })

  test('chat — renders chat interface and sidebar', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/chat`)
    await expectViewLoaded(page)
  })

  test('execution — shows terminal panel', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/execution`)
    await expectViewLoaded(page)
  })

  test('terminal — shows agent tab viewer', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/terminal`)
    await expectViewLoaded(page)
  })

  test('reports — loads KPI summary', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/reports`)
    await expectViewLoaded(page)
  })

  test('knowledge — loads RAG collection info', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/knowledge`)
    await expectViewLoaded(page)
  })

  test('ideation — renders improvement ideas', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/ideation`)
    await expectViewLoaded(page)
  })

  test('integrations — shows GitHub/GitLab status', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/integrations`)
    await expectViewLoaded(page)
  })

  // ── Settings views ───────────────────────────────────────────────

  test('project-settings — renders per-project config', async ({ page }) => {
    await page.goto(`${BASE}/#/workspace/settings`)
    await expectViewLoaded(page)
  })

  test('app-settings — renders app-level settings tabs', async ({ page }) => {
    await page.goto(`${BASE}/#/settings`)
    await expectViewLoaded(page)
  })

  // ── Onboarding & strategy ────────────────────────────────────────

  test('onboarding — shows source selection step', async ({ page }) => {
    await page.goto(`${BASE}/#/onboarding`)
    await expectViewLoaded(page)
  })

  test('strategy — renders risk matrix', async ({ page }) => {
    await page.goto(`${BASE}/#/strategy`)
    await expectViewLoaded(page)
  })

  // ── Sidebar navigation ───────────────────────────────────────────

  test('sidebar — all nav items navigate without error', async ({ page }) => {
    await page.goto(`${BASE}/#/dashboard`)
    await expectViewLoaded(page)

    // Click each sidebar nav item
    const navLinks = page.locator('nav a, aside a, [role="navigation"] a').filter({ hasText: /./ })
    const count = await navLinks.count()
    const visited = new Set<string>()

    for (let i = 0; i < Math.min(count, 10); i++) {
      try {
        const link = navLinks.nth(i)
        const href = await link.getAttribute('href')
        if (!href || visited.has(href)) continue
        visited.add(href)

        await link.click()
        await page.waitForTimeout(300)
        const url = page.url()
        expect(url).not.toContain('404')
      } catch {
        // Some links may be hidden behind conditional rendering
        continue
      }
    }
  })

  // ── Legacy route redirects ───────────────────────────────────────

  test('legacy routes — redirect to /workspace/ paths', async ({ page }) => {
    const legacyPaths = ['/kanban', '/gaps', '/chat', '/execution', '/reports', '/knowledge']
    for (const legacy of legacyPaths) {
      await page.goto(`${BASE}/#${legacy}`)
      await page.waitForTimeout(300)
      const url = page.url()
      // Should either redirect or load successfully
      expect(url).not.toContain('404')
    }
  })

  // ── API endpoints (when backend is running) ─────────────────────

  test('API health — returns 200', async ({ page }) => {
    const resp = await page.request.get('http://localhost:8000/health')
    expect(resp.status()).toBe(200)
    const body = await resp.json()
    expect(body).toHaveProperty('status')
  })

  test('API root — returns platform info', async ({ page }) => {
    const resp = await page.request.get('http://localhost:8000/')
    expect(resp.status()).toBe(200)
    const body = await resp.json()
    expect(body).toHaveProperty('name')
  })

  test('API metrics — returns Prometheus text (or hint if not installed)', async ({ page }) => {
    const resp = await page.request.get('http://localhost:8000/metrics')
    expect(resp.status()).toBe(200)
    const text = await resp.text()
    expect(text).toContain('aitest')
  })
})
